"""Linux/WSL experiment runner. Human approval records are NOT authentication."""
import argparse
import contextlib
import csv
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
from common import (FileLock, atomic_write, capture_environment, clean_commit, digest,
                    file_hash, finite_number, interpreter_path, limited_env, parse_json,
                    read_json, require_hash, stamp, write_json)
from task_contract import ARTIFACTS, validate_approval, validate_task
from environment_contract import task_environment, validate_environment

ROOT = Path(__file__).resolve().parents[1]

class Cancelled(Exception):
    def __init__(self, signum):
        self.signum = signum

@contextlib.contextmanager
def cancellation_handlers():
    old = {}
    def cancel(signum, frame):
        raise Cancelled(signum)
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            old[signum] = signal.signal(signum, cancel)
        yield
    finally:
        for signum, handler in old.items():
            signal.signal(signum, handler)

def stop_group(proc):
    """Stop the entire experiment group, including descendants of an exited leader."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()

def validate_results(out, task):
    if any(not (out/name).is_file() or (out/name).is_symlink() for name in ARTIFACTS):
        raise ValueError("Missing or unsafe required artifact")
    metrics, _ = read_json(out/"metrics.json")
    expected = {f"{scenario}_{estimator}_mse" for scenario in ("clean", "contaminated") for estimator in ("mean", "median")}
    if set(metrics) != expected or not all(finite_number(v) for v in metrics.values()):
        raise ValueError("Invalid metric keys or non-finite/negative metrics")
    with (out/"trials.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != task["acceptance"]["expected_trial_rows"]:
        raise ValueError("Incorrect trial count")
    for scenario in ("clean", "contaminated"):
        subset = [r for r in rows if r["scenario"] == scenario]
        if sorted(int(r["trial"]) for r in subset) != list(range(task["parameters"]["trials"])):
            raise ValueError("Missing or duplicate trial")
        for estimator in ("mean", "median"):
            values = [float(r[estimator+"_error_sq"]) for r in subset]
            if not all(finite_number(v) for v in values):
                raise ValueError("Invalid trial value")
            import math
            if not math.isclose(sum(values)/len(values), metrics[scenario+"_"+estimator+"_mse"], rel_tol=1e-12, abs_tol=1e-15):
                raise ValueError("Metrics disagree with trial data")

def execute_run(task, task_raw, approval_raw, environment, python, out, root):
    """Lifecycle separated from preflight to permit offline fault-injection tests."""
    out.mkdir(mode=0o700)
    params = task["parameters"]
    command = [str(python), "-I", str(root/"experiments/demo.py"), "--outdir", str(out),
               "--seed", str(params["seed"]), "--samples", str(params["samples"]), "--trials", str(params["trials"])]
    meta = {"schema_version": 3, "task": task, "task_sha256": digest(task_raw),
            "approval_sha256": digest(approval_raw), "started_utc": stamp(), "heartbeat_utc": stamp(),
            "host": platform.node(), "platform": platform.platform(), "runner_pid": os.getpid(),
            "command": command, "status": "starting", "source_sequence": 1}
    proc, code, state = None, 1, "initialization_failed"
    initialized, status_persisted = False, False
    status_sha256 = None
    env = limited_env()
    env.update(OMP_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="", PYTHONUTF8="1")
    try:
        atomic_write(out/"task.json", task_raw)
        atomic_write(out/"approval.json", approval_raw)
        write_json(out/"environment.json", environment)
        write_json(out/"status.json", meta)
        initialized = True
        with (out/"run.log").open("w", encoding="utf-8") as log:
            # Preflight and initial filesystem writes may outlive the approval.
            validate_approval(parse_json(approval_raw), task, digest(task_raw), platform.node())
            proc = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            meta.update(status="running", child_pid=proc.pid, source_sequence=meta['source_sequence']+1)
            write_json(out/"status.json", meta)
            deadline = time.monotonic()+task["limits"]["timeout_seconds"]
            while True:
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, task["limits"]["timeout_seconds"])
                try:
                    code = proc.wait(timeout=min(remaining, 2))
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        raise
                    meta["heartbeat_utc"] = stamp()
                    meta['source_sequence'] += 1
                    write_json(out/"status.json", meta)
        state = "completed" if code == 0 else "failed"
        if code == 0:
            validate_results(out, task)
            if clean_commit(root) != task["git_commit"]:
                raise ValueError("Source changed during execution")
    except subprocess.TimeoutExpired:
        code, state = 124, "timeout"
    except (Cancelled, KeyboardInterrupt) as exc:
        code, state = 128+getattr(exc, "signum", signal.SIGINT), "cancelled"
    except Exception as exc:
        code, state = 1, ("initialization_failed" if not initialized else
                         "launch_failed" if proc is None else "failed_validation_or_runtime")
        meta["error_type"] = type(exc).__name__
        meta["error"] = str(exc)[:500]
    finally:
        # Ignore a second termination signal during bounded cleanup and final recording.
        with contextlib.ExitStack() as stack:
            old_handlers = {}
            for sig in (signal.SIGINT, signal.SIGTERM):
                old_handlers[sig] = signal.signal(sig, signal.SIG_IGN)
            try:
                if proc is not None:
                    try:
                        stop_group(proc)
                    except Exception as exc:
                        code, state = 1, "cleanup_failed"
                        meta["cleanup_error_type"] = type(exc).__name__
                meta.update(finished_utc=stamp(), heartbeat_utc=stamp(), status=state, exit_code=code)
                meta['source_sequence'] += 1
                meta["artifacts_sha256"] = {}
                try:
                    for name in sorted(ARTIFACTS):
                        path = out/name
                        if path.is_file() and not path.is_symlink():
                            meta["artifacts_sha256"][name] = file_hash(path)
                    write_json(out/"status.json", meta)
                    status_sha256 = file_hash(out/"status.json")
                    status_persisted = True
                except Exception as exc:
                    code, state = 1, "recording_failed"
                    print("Final status could not be persisted; preserve this run for human reconciliation: "
                          +type(exc).__name__+": "+str(exc)[:500], file=sys.stderr)
            finally:
                for sig, handler in old_handlers.items():
                    signal.signal(sig, handler)
    print(__import__("json").dumps({"run_dir": str(out), "status": state, "exit_code": code,
                                    "status_sha256": status_sha256, "status_persisted": status_persisted}))
    return code if 0 <= code <= 255 else 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--approve", required=True, help="SHA-256 of the human-completed APPROVAL file, not the task")
    parser.add_argument("--python", type=Path, default=Path(sys.executable), help="Approved experiment interpreter")
    parser.add_argument("--run-root", type=Path, default=Path.home()/"research-runs")
    args = parser.parse_args()
    try:
        require_hash(args.approve)
        if not sys.platform.startswith("linux"):
            raise ValueError("Experiment execution requires Linux/WSL; no native Windows execution")
        task, raw = read_json(args.task)
        validate_task(task)
        approval, approval_raw = read_json(args.approval, args.approve)
        validate_approval(approval, task, digest(raw), platform.node())
        if clean_commit(ROOT) != task["git_commit"]:
            raise ValueError("Source commit differs")
        for key in ("evidence", "protocol"):
            path = ROOT/task[key]["path"]
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or file_hash(path) != task[key]["sha256"]:
                raise ValueError("Evidence or protocol changed")
        python = interpreter_path(args.python)
        environment = capture_environment(python, ROOT)
        validate_environment(environment, task["target"]["node"])
        if task_environment(environment) != task["environment"]:
            raise ValueError("Experiment environment differs from approved fingerprint")
        run_root = args.run_root.expanduser().resolve()
        with FileLock(run_root/".node.lock"):
            validate_approval(approval, task, digest(raw), platform.node())
            with cancellation_handlers():
                return execute_run(task, raw, approval_raw, environment, python, run_root/task["run_id"], ROOT)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    raise SystemExit(main())
