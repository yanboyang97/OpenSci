"""Create a task and an UNAPPROVED template. Never authorizes execution."""
import argparse
from pathlib import Path
import platform
import sys
from common import canonical, capture_environment, clean_commit, create_json, digest, file_hash, read_json, stamp
from task_contract import ARTIFACTS, DATASET, approval_template, validate_task
from environment_contract import task_environment, validate_environment
from review_contract import validate_manifest

ROOT = Path(__file__).resolve().parents[1]

def reference(root, relative):
    path = (root/relative).resolve(strict=True)
    if not path.is_relative_to(root.resolve()) or not path.is_file() or (root/relative).is_symlink():
        raise ValueError("Reference must be a regular file inside the repository")
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": file_hash(path)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Unique run ID")
    parser.add_argument("--study-id", default="DEMO-STUDY")
    parser.add_argument("--task-id", help="Logical task ID; defaults to run ID")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--question", default="Compare mean and median for the uncontaminated location under synthetic contamination")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--node", default=platform.node(), help="Exact target hostname")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--environment", type=Path, help="Environment record captured on the target node")
    parser.add_argument("--protocol", default="methodology/experiment_protocol.md")
    parser.add_argument("--packet", default="coordination/packets/DEMO.md")
    parser.add_argument("--compute-budget", type=float, default=0)
    parser.add_argument("--currency", choices=["USD", "CNY"], default="USD")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--human-review-reason")
    group.add_argument("--review-manifest", type=Path)
    args = parser.parse_args()
    try:
        commit = clean_commit(ROOT)
        environment = read_json(args.environment)[0] if args.environment else capture_environment(args.python, ROOT)
        validate_environment(environment, args.node)
        review = {"mode": "human_only", "reason": args.human_review_reason}
        if args.review_manifest:
            manifest, _ = read_json(args.review_manifest)
            validate_manifest(manifest, directory=args.review_manifest.parent)
            review = {"mode": "model_assisted", "manifest": manifest, "manifest_sha256": digest(canonical(manifest))}
        task = {"schema_version": 3, "study_id": args.study_id, "task_id": args.task_id or args.id,
                "run_id": args.id, "attempt": args.attempt, "created_utc": stamp(), "research_question": args.question,
                "git_commit": commit, "entrypoint": "demo", "data_class": "public", "dataset": DATASET,
                "protocol": reference(ROOT, args.protocol), "evidence": reference(ROOT, args.packet), "review": review,
                "parameters": {"seed": args.seed, "samples": args.samples, "trials": args.trials},
                "environment": task_environment(environment),
                "target": {"node": args.node, "os": "linux"},
                "limits": {"timeout_seconds": args.timeout, "cpu_threads": 1, "gpus": 0, "compute_budget": args.compute_budget, "currency": args.currency},
                "acceptance": {"required_artifacts": sorted(ARTIFACTS), "metrics_nonnegative_finite": True, "expected_trial_rows": 2*args.trials}}
        validate_task(task)
        if clean_commit(ROOT) != commit:
            raise ValueError("Source changed during preparation")
        dest = ROOT/"coordination/requests"/(args.id+".json")
        approval = dest.with_name(args.id+".approval.template.json")
        if dest.exists() or approval.exists():
            raise ValueError("Run ID already prepared; use a new ID")
        task_sha = digest(canonical(task))
        create_json(dest, task)
        create_json(approval, approval_template(task, task_sha))
        print("TASK="+str(dest))
        print("TASK_SHA256="+task_sha)
        print("APPROVAL_TEMPLATE="+str(approval))
        print("DRAFT ONLY. A human submission account must review and complete a separate approval record.")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
