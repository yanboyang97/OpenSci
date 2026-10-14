"""Report a stale heartbeat without inventing completion or killing any process."""
import argparse
from datetime import datetime, timezone
from common import print_json, read_json
from task_contract import time_value
from pathlib import Path

def inspect(run, stale_seconds=60):
    run = Path(run)
    if not run.is_dir():
        raise ValueError("Run directory does not exist")
    if stale_seconds < 1:
        raise ValueError("Stale threshold must be positive")
    try:
        if (run/"status.json").is_symlink():
            raise ValueError("Status must not be a symlink")
        status, _ = read_json(run/"status.json")
        if status.get("schema_version") not in (2, 3) or not isinstance(status.get("status"), str):
            raise ValueError("Unrecognized status schema")
        age = (datetime.now(timezone.utc)-time_value(status["heartbeat_utc"])).total_seconds()
        active = status["status"] in ("starting", "running")
        return {"recorded_status": status["status"], "heartbeat_age_seconds": age,
                "needs_human_reconciliation": (active and age > stale_seconds) or
                    status["status"] in ("initialization_failed", "recording_failed", "cleanup_failed"),
                "host": status["host"], "runner_pid": status.get("runner_pid"), "child_pid": status.get("child_pid"),
                "note": "Stale is not proof of process death. Check host and process identity before intervention."}
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        return {"recorded_status": "missing_or_invalid", "needs_human_reconciliation": True,
                "error_type": type(exc).__name__, "error": str(exc)[:500],
                "existing_files": sorted(p.name for p in run.iterdir()),
                "note": "Preserve partial files. Verify host/processes and storage before a human-approved new run ID."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--stale-seconds", type=int, default=60)
    args = parser.parse_args()
    try:
        print_json(inspect(args.run, args.stale_seconds))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
