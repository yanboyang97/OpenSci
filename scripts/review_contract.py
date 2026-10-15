"""Integrity and coverage of a bounded review; never proof of human authorization."""
from datetime import datetime
from pathlib import Path
import re
from common import VERSION, canonical, digest, file_hash, read_json, require_hash

PLAN_KEYS = {"schema_version", "pipeline_version", "packet_sha256", "packet_bytes", "providers", "rounds",
             "parallel", "timeout_seconds", "maximum_reviewer_invocations", "prompt_template_sha256", "subject"}
MANIFEST_KEYS = {"schema_version", "review_id", "mode", "status", "started_utc", "finished_utc",
                 "operator_account", "packet_sha256", "config_sha256", "plan", "requested_models",
                 "results", "maximum_reviewer_invocations", "artifacts_sha256"}

def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Review timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Review timestamps must include timezone")
    return result

def validate_plan(plan, historical=False):
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS or type(plan["schema_version"]) is not int or plan["schema_version"] != 2:
        raise ValueError("Unsupported Evidence Review plan; generate a new review plan")
    if historical and plan['pipeline_version'] not in ('1.2.0', '1.3.0', '1.4.0', '1.5.0', '1.6.0', '1.7.0-rc.1', '1.0.0', '1.0.1'):
        raise ValueError('Unsupported historical review pipeline')
    if not historical and plan["pipeline_version"] != VERSION:
        raise ValueError("Regenerate the plan with this review pipeline version")
    require_hash(plan["packet_sha256"])
    if type(plan["packet_bytes"]) is not int or not 1 <= plan["packet_bytes"] <= 120000:
        raise ValueError("Invalid review packet size")
    for field, low, high in (("rounds", 1, 2), ("parallel", 1, 2), ("timeout_seconds", 10, 3600)):
        if type(plan[field]) is not int or not low <= plan[field] <= high:
            raise ValueError("Invalid review bound: "+field)
    providers = plan["providers"]
    if not isinstance(providers, dict) or not 1 <= len(providers) <= 4:
        raise ValueError("Select 1..4 review providers")
    from review_round import frozen_providers, RULES
    if frozen_providers(providers, list(providers), live=True) != providers:
        raise ValueError("Review configuration is not fully frozen")
    require_hash(plan['prompt_template_sha256'])
    if not historical and plan["prompt_template_sha256"] != digest(RULES.encode("utf-8")):
        raise ValueError("Review prompt template mismatch")
    if type(plan["maximum_reviewer_invocations"]) is not int or plan["maximum_reviewer_invocations"] != len(providers)*plan["rounds"]:
        raise ValueError("Review invocation bound mismatch")
    subject = plan["subject"]
    if subject is not None:
        if not isinstance(subject, dict) or set(subject) != {"git_commit", "protocol"} or not isinstance(subject["git_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", subject["git_commit"]):
            raise ValueError("Invalid reviewed source binding")
        ref = subject["protocol"]
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            raise ValueError("Reviewed protocol required")
        require_hash(ref["sha256"])
        path = ref["path"]
        if not isinstance(path, str) or not path or "\\" in path or ":" in path or any(p in ("", ".", "..") for p in path.split("/")):
            raise ValueError("Invalid reviewed protocol path")
    return plan

def validate_manifest(manifest, directory=None, packet_sha256=None, subject=None, historical=False):
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS or type(manifest["schema_version"]) is not int or manifest["schema_version"] != 3:
        raise ValueError("A complete supported Evidence Review manifest is required")
    if manifest["mode"] != "execute" or manifest["status"] != "awaiting_human_review":
        raise ValueError("A completed live review is required")
    plan = validate_plan(manifest["plan"], historical=historical)
    if packet_sha256 is not None and plan["packet_sha256"] != packet_sha256:
        raise ValueError("Review concerns a different evidence packet")
    if subject is not None and plan["subject"] != subject:
        raise ValueError("Review does not bind this source commit and protocol")
    if manifest["packet_sha256"] != plan["packet_sha256"] or manifest["config_sha256"] != digest(canonical(plan)):
        raise ValueError("Review plan checksum mismatch")
    if manifest["maximum_reviewer_invocations"] != plan["maximum_reviewer_invocations"]:
        raise ValueError("Manifest invocation bound mismatch")
    for key in ("operator_account", "review_id"):
        if not isinstance(manifest[key], str) or not manifest[key].strip():
            raise ValueError("Review identity required")
    started, finished = timestamp(manifest["started_utc"]), timestamp(manifest["finished_utc"])
    if finished < started:
        raise ValueError("Review finishes before it starts")
    expected_models = {name: cfg.get("model") or "authenticated_default_unpinned" for name, cfg in plan["providers"].items()}
    if manifest["requested_models"] != expected_models:
        raise ValueError("Requested model summary mismatch")
    expected_pairs = {(name, r) for name in plan["providers"] for r in range(1, plan["rounds"]+1)}
    if not isinstance(manifest["results"], list) or len(manifest["results"]) != len(expected_pairs):
        raise ValueError("Missing review results")
    artifacts = {"config.snapshot.json", "packet.md"}
    if plan['pipeline_version'] in ('1.5.0', '1.6.0', '1.7.0-rc.1', '1.0.0', '1.0.1'):
        artifacts.add('rules.snapshot.md')
    seen = set()
    for result in manifest["results"]:
        if not isinstance(result, dict) or not isinstance(result.get("provider"), str) or type(result.get("round")) is not int:
            raise ValueError("Invalid review result")
        pair = (result["provider"], result["round"])
        if pair not in expected_pairs or pair in seen or result.get("status") != "ok" or type(result.get("exit_code")) is not int or result["exit_code"] != 0:
            raise ValueError("Failed, duplicated or unexpected review result")
        seen.add(pair)
        call = result.get("call")
        cfg = plan["providers"][pair[0]]
        stem = f"round{pair[1]}-{pair[0]}"
        suffixes = {".md", ".prompt.txt", ".call.json", ".usage.json", ".process.log"}
        suffixes |= {".response.jsonl", ".last-message.txt"} if cfg["kind"] == "codex" else {".response.json"}
        artifacts.update(stem+s for s in suffixes)
        if not isinstance(call, dict) or type(call.get("schema_version")) is not int or call["schema_version"] != 1 or call.get("status") != "complete" or type(call.get("exit_code")) is not int or call["exit_code"] != 0:
            raise ValueError("Complete successful provider call record required")
        if call.get("provider") != pair[0] or call.get("config_sha256") != manifest["config_sha256"] or call.get("requested_model") != (cfg.get("model") or None):
            raise ValueError("Provider call differs from the frozen plan")
        destination = {k: cfg[k] for k in ("kind", "project", "location", "base_url") if k in cfg}
        if call.get("destination") != destination or not isinstance(call.get("usage"), dict) or not call.get("finish_reason"):
            raise ValueError("Provider destination, usage and completion reason required")
        if not started <= timestamp(result.get("started_utc")) <= timestamp(result.get("finished_utc")) <= finished:
            raise ValueError("Invalid result timestamps")
        if not timestamp(result["started_utc"]) <= timestamp(call.get("started_utc")) <= timestamp(call.get("finished_utc")) <= timestamp(result["finished_utc"]):
            raise ValueError("Invalid call timestamps")
        require_hash(call.get("prompt_sha256"))
        if directory is not None:
            directory = Path(directory)
            if read_json(directory/(stem+".call.json"))[0] != call or read_json(directory/(stem+".usage.json"))[0] != call["usage"]:
                raise ValueError("Call/usage artifact differs from manifest")
            if file_hash(directory/(stem+".prompt.txt")) != call["prompt_sha256"]:
                raise ValueError("Call prompt checksum mismatch")
            report = (directory/(stem+".md")).read_bytes()
            if not report.strip() or len(report) > 32000:
                raise ValueError("Empty or oversized review report")
            report.decode("utf-8")
    checksums = manifest["artifacts_sha256"]
    if not isinstance(checksums, dict) or set(checksums) != artifacts:
        raise ValueError("Exact complete review artifact set required")
    for name, expected in checksums.items():
        require_hash(expected)
        if directory is not None:
            path = Path(directory)/name
            if not path.is_file() or path.is_symlink() or file_hash(path) != expected:
                raise ValueError("Review artifact missing, unsafe or modified: "+name)
    if checksums["config.snapshot.json"] != manifest["config_sha256"] or checksums["packet.md"] != manifest["packet_sha256"]:
        raise ValueError("Frozen packet/config artifact mismatch")
    if plan['pipeline_version'] in ('1.5.0', '1.6.0', '1.7.0-rc.1', '1.0.0', '1.0.1') and checksums['rules.snapshot.md'] != plan['prompt_template_sha256']:
        raise ValueError('Shared rules snapshot differs from the frozen plan')
    for result in manifest["results"]:
        prompt_name = f"round{result['round']}-{result['provider']}.prompt.txt"
        if result["call"]["prompt_sha256"] != checksums[prompt_name]:
            raise ValueError("Embedded call prompt differs from artifact manifest")
    if directory is not None and (Path(directory)/"packet.md").stat().st_size != plan["packet_bytes"]:
        raise ValueError("Packet byte count mismatch")
    return manifest
