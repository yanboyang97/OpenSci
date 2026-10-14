"""Verify sealed runs, upload a fixed artifact list, and resume repeat uploads.

One designated uploader per run. Local locking does not serialize different machines.
"""
import argparse
import contextlib
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
from common import FileLock, atomic_write, canonical, digest, file_hash, print_json, read_json, require_hash, stamp, write_json
from task_contract import ARTIFACTS, validate_task
from environment_contract import task_environment, validate_environment
from run_task import validate_results

def validate_uri(uri):
    parts = urlsplit(uri)
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Tracking URI must not contain credentials, query or fragment")
    if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost", "::1")):
        raise ValueError("Use HTTPS or an explicitly selected loopback SSH tunnel")
    return uri.rstrip("/")

def verified_snapshot(run, expected_status_sha, dest):
    require_hash(expected_status_sha)
    status, status_raw = read_json(run/"status.json", expected_status_sha)
    if status.get("schema_version") != 3 or status.get("status") != "completed" or status.get("exit_code") != 0:
        raise ValueError("A completed run with a supported execution record is required")
    if set(status.get("artifacts_sha256", {})) != ARTIFACTS:
        raise ValueError("Missing or unexpected sealed artifact")
    for name in sorted(ARTIFACTS):
        source = run/name
        if not source.is_file() or source.is_symlink():
            raise ValueError("Unsafe artifact: "+name)
        # Copy to an upload-only snapshot and verify the exact bytes to be uploaded.
        import shutil
        shutil.copyfile(source, dest/name)
        if file_hash(dest/name) != status["artifacts_sha256"][name]:
            raise ValueError("Artifact checksum mismatch: "+name)
    atomic_write(dest/"status.json", status_raw)
    task, raw = read_json(dest/"task.json")
    validate_task(task)
    environment = read_json(dest/"environment.json")[0]
    validate_environment(environment, task["target"]["node"])
    if task_environment(environment) != task["environment"]:
        raise ValueError("Sealed environment differs from task")
    if task != status["task"] or digest(raw) != status["task_sha256"] or file_hash(dest/"approval.json") != status["approval_sha256"]:
        raise ValueError("Run provenance does not match sealed task/approval")
    validate_results(dest, task)
    return status

def upload_run(run, expected_status_sha, uri, client=None):
    require_hash(expected_status_sha)
    uri, run = validate_uri(uri), Path(run).resolve(strict=True)
    # A local receipt is operational metadata and is not part of sealed experiment artifacts.
    with FileLock(run/".mlflow-upload.lock"):
        with tempfile.TemporaryDirectory(prefix="opensci-upload-", dir=run.parent) as temp:
            snapshot = Path(temp)
            status = verified_snapshot(run, expected_status_sha, snapshot)
            key = digest(canonical({"status_sha256": expected_status_sha, "task_sha256": status["task_sha256"],
                                    "approval_sha256": status["approval_sha256"]}))
            if client is None:
                from mlflow import MlflowClient
                client = MlflowClient(tracking_uri=uri)
            experiment = client.get_experiment_by_name("OpenSci-synthetic-demo")
            experiment_id = experiment.experiment_id if experiment else client.create_experiment("OpenSci-synthetic-demo")
            receipt_path = run/"mlflow-upload.json"
            receipt = read_json(receipt_path)[0] if receipt_path.exists() else None
            if receipt and (receipt["tracking_uri"] != uri or receipt["run_key"] != key):
                raise ValueError("Existing upload receipt targets a different server or sealed run")
            matches = client.search_runs([experiment_id], filter_string=f"tags.opensci_run_key = '{key}'", max_results=3)
            if len(matches) > 1:
                raise ValueError("Duplicate remote runs detected; human reconciliation required")
            if matches:
                remote = matches[0]
            elif receipt:
                raise ValueError("Recorded remote run is missing; do not silently create a duplicate")
            else:
                remote = client.create_run(experiment_id, tags={"opensci_run_key": key,
                    "opensci_status_sha256": expected_status_sha, "opensci_upload_phase": "uploading",
                    "mlflow.runName": status["task"]["run_id"]})
            run_id = remote.info.run_id
            if receipt and receipt["mlflow_run_id"] != run_id:
                raise ValueError("Remote run differs from upload receipt")
            receipt = {"schema_version": 1, "tracking_uri": uri, "run_key": key, "mlflow_run_id": run_id,
                       "status_sha256": expected_status_sha, "phase": "uploading", "updated_utc": stamp()}
            write_json(receipt_path, receipt)
            if remote.data.tags.get("opensci_upload_phase") == "complete":
                receipt.update(phase="complete", updated_utc=stamp())
                write_json(receipt_path, receipt)
                return {"mlflow_run_id": run_id, "action": "already_uploaded"}
            try:
                task = status["task"]
                params = {"study_id": task["study_id"], "task_id": task["task_id"], "run_id": task["run_id"],
                          "attempt": task["attempt"], "source_commit": task["git_commit"], **task["parameters"],
                          "environment_sha256": digest(canonical(task["environment"])), "task_sha256": status["task_sha256"]}
                for name, value in params.items():
                    client.log_param(run_id, name, str(value), synchronous=True)
                metrics = read_json(snapshot/"metrics.json")[0]
                current = client.get_run(run_id).data.metrics
                for name, value in metrics.items():
                    if name in current:
                        if current[name] != value:
                            raise ValueError("Remote metric conflicts with sealed result")
                    else:
                        client.log_metric(run_id, name, value, step=0, synchronous=True)
                for name in sorted(ARTIFACTS | {"status.json"}):
                    client.log_artifact(run_id, str(snapshot/name))
                client.set_terminated(run_id, status="FINISHED")
                client.set_tag(run_id, "opensci_upload_phase", "complete", synchronous=True)
                receipt.update(phase="complete", updated_utc=stamp())
                write_json(receipt_path, receipt)
                return {"mlflow_run_id": run_id, "action": "uploaded_or_resumed"}
            except Exception:
                receipt.update(phase="retryable_failure", updated_utc=stamp())
                write_json(receipt_path, receipt)
                with contextlib.suppress(Exception):
                    client.set_tag(run_id, "opensci_upload_phase", "retryable_failure", synchronous=True)
                    client.set_terminated(run_id, status="FAILED")
                raise

def main():
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--status-sha256", required=True, help="Final digest printed by the trusted compute runner")
    parser.add_argument("--tracking-uri", default=os.environ.get("MLFLOW_TRACKING_URI"))
    args = parser.parse_args()
    if not args.tracking_uri:
        parser.error("Select a tracking URI explicitly; no implicit local MLflow store")
    try:
        print_json(upload_run(args.run, args.status_sha256, args.tracking_uri))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
