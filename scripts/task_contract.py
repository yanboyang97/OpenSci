"""Versioned tasks and human approval records for the synthetic adapter."""
from datetime import datetime, timezone
import re
from common import canonical, digest, finite_number, require_hash, valid_id
from environment_contract import validate_task_environment

DATASET = {"kind": "synthetic", "revision": "synthetic-v1", "definition": {
    "clean_fraction": 0.0, "contaminated_fraction": 0.1, "normal_mean": 0.0,
    "normal_sd": 1.0, "outlier_shift": 8.0, "estimand": "uncontaminated_location", "target": 0.0}}
DATASET["definition_sha256"] = digest(canonical(DATASET["definition"]))
ARTIFACTS = {"task.json", "approval.json", "environment.json", "run.log", "metrics.json", "trials.csv"}
TASK_KEYS = {"schema_version", "study_id", "task_id", "run_id", "attempt", "created_utc",
             "research_question", "git_commit", "entrypoint", "data_class", "dataset", "protocol", "evidence",
             "review", "parameters", "environment", "target", "limits", "acceptance"}

def time_value(text):
    if not isinstance(text, str):
        raise ValueError("Timestamp must be an ISO 8601 string")
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return value.astimezone(timezone.utc)

def validate_task(task, historical=False):
    if not isinstance(task, dict) or set(task) != TASK_KEYS or type(task["schema_version"]) is not int or task["schema_version"] != 3:
        raise ValueError("Unsupported Task Specification; prepare a new task and approval")
    for key in ("study_id", "task_id", "run_id"):
        if not valid_id(task[key]):
            raise ValueError("Invalid "+key)
    if type(task["attempt"]) is not int or not 1 <= task["attempt"] <= 10000:
        raise ValueError("Invalid attempt number")
    time_value(task["created_utc"])
    if not isinstance(task["research_question"], str) or not task["research_question"].strip():
        raise ValueError("Research question is required")
    if not isinstance(task["git_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", task["git_commit"]):
        raise ValueError("Invalid Git commit")
    if task["entrypoint"] != "demo" or task["data_class"] != "public" or task["dataset"] != DATASET:
        raise ValueError("Only the reviewed public synthetic demo adapter is installed")
    params = task["parameters"]
    if not isinstance(params, dict) or set(params) != {"seed", "samples", "trials"} or any(type(v) is not int for v in params.values()):
        raise ValueError("Integer seed, samples and trials are required")
    if not 10 <= params["samples"] <= 100000 or not 2 <= params["trials"] <= 1000 or params["samples"]*params["trials"] > 10_000_000:
        raise ValueError("Synthetic sample budget exceeded")
    for key in ("protocol", "evidence"):
        ref = task[key]
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            raise ValueError("Invalid reference")
        require_hash(ref["sha256"])
        if not isinstance(ref["path"], str) or not ref["path"] or ref["path"].startswith("/") or "\\" in ref["path"] or ":" in ref["path"] or any(p in ("..", ".", "") for p in ref["path"].split("/")):
            raise ValueError("References must be safe repository-relative paths")
    review = task["review"]
    if not isinstance(review, dict):
        raise ValueError("Invalid review record")
    if review.get("mode") == "human_only":
        if set(review) != {"mode", "reason"} or not isinstance(review["reason"], str) or not review["reason"].strip():
            raise ValueError("Explain the human-only review")
    elif review.get("mode") == "model_assisted":
        if set(review) != {"mode", "manifest", "manifest_sha256"} or not isinstance(review["manifest"], dict):
            raise ValueError("Invalid model review record")
        require_hash(review["manifest_sha256"])
        if digest(canonical(review["manifest"])) != review["manifest_sha256"]:
            raise ValueError("Review checksum mismatch")
        manifest = review["manifest"]
        from review_contract import validate_manifest
        validate_manifest(manifest, packet_sha256=task["evidence"]["sha256"],
                          subject={"git_commit": task["git_commit"], "protocol": task["protocol"]}, historical=historical)
    else:
        raise ValueError("Explicit review record required")
    env = task["environment"]
    validate_task_environment(env)
    if not isinstance(task["target"], dict) or set(task["target"]) != {"node", "os"} or task["target"]["os"] != "linux" or not isinstance(task["target"]["node"], str) or not task["target"]["node"]:
        raise ValueError("A specific Linux target node is required")
    limits = task["limits"]
    if not isinstance(limits, dict) or set(limits) != {"timeout_seconds", "cpu_threads", "gpus", "compute_budget", "currency"}:
        raise ValueError("Invalid resource limits")
    if type(limits["timeout_seconds"]) is not int or not 1 <= limits["timeout_seconds"] <= 14400:
        raise ValueError("Invalid timeout")
    if type(limits["cpu_threads"]) is not int or limits["cpu_threads"] != 1 or type(limits["gpus"]) is not int or limits["gpus"] != 0:
        raise ValueError("Demo requires one CPU thread and no GPU")
    if not finite_number(limits["compute_budget"]) or limits["currency"] not in ("USD", "CNY"):
        raise ValueError("Invalid declared budget")
    expected = {"required_artifacts": sorted(ARTIFACTS), "metrics_nonnegative_finite": True, "expected_trial_rows": 2*params["trials"]}
    if canonical(task["acceptance"]) != canonical(expected):
        raise ValueError("Unexpected acceptance criteria")
    return task

def approval_bindings(task, task_sha256):
    return {"schema_version": 2, "run_id": task["run_id"], "task_sha256": task_sha256,
            "git_commit": task["git_commit"], "environment_sha256": digest(canonical(task["environment"])),
            "node": task["target"]["node"], "limits_sha256": digest(canonical(task["limits"])),
            "evidence_sha256": task["evidence"]["sha256"], "protocol_sha256": task["protocol"]["sha256"],
            "review_sha256": digest(canonical(task["review"]))}

def approval_template(task, task_sha256):
    return {**approval_bindings(task, task_sha256), "decision": "DRAFT", "approved_by": None,
            "approved_at_utc": None, "expires_utc": None, "rationale": None}

def validate_approval(approval, task, task_sha256, node, now=None):
    bindings = approval_bindings(task, task_sha256)
    expected = set(bindings) | {"decision", "approved_by", "approved_at_utc", "expires_utc", "rationale"}
    if not isinstance(approval, dict) or set(approval) != expected or type(approval.get("schema_version")) is not int:
        raise ValueError("Invalid approval schema")
    if any(approval[key] != value for key, value in bindings.items()):
        raise ValueError("Approval does not bind to this task/environment/node")
    if approval["decision"] != "APPROVED":
        raise ValueError("A draft is not an approval")
    for key in ("approved_by", "rationale"):
        if not isinstance(approval[key], str) or not approval[key].strip() or any(x in approval[key] for x in ("YOUR_", "REPLACE_")):
            raise ValueError("Human operator and rationale required")
    approved, expires = time_value(approval["approved_at_utc"]), time_value(approval["expires_utc"])
    now = now or datetime.now(timezone.utc)
    if not time_value(task["created_utc"]) <= approved <= now < expires:
        raise ValueError("Approval timestamps invalid or expired")
    if node != task["target"]["node"]:
        raise ValueError("Wrong execution node")
    return approval
