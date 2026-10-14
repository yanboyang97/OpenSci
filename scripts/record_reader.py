"""Read explicitly supported historical records without granting execution authority."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import digest, print_json, read_json
from project_store import decode_record, LEGACY_LIMIT
from review_contract import validate_manifest
from task_contract import validate_task, validate_approval, time_value


def inspect_record(path, expected, kind, legacy_large=False, task_path=None, task_sha256=None):
    path = Path(path)
    value, raw = read_json(path, expected, limit=LEGACY_LIMIT if kind == 'project' and legacy_large else 4_000_000)
    if kind == 'project':
        decode_record(raw, legacy_large=legacy_large)
    elif kind == 'review':
        validate_manifest(value, directory=path.parent, historical=True)
    elif kind == 'task':
        validate_task(value, historical=True)
    elif kind == 'approval':
        if not task_path or not task_sha256:
            raise ValueError('Historical approval inspection requires its trusted task and task hash')
        task, task_raw = read_json(task_path, task_sha256)
        validate_task(task, historical=True)
        approved_at = time_value(value['approved_at_utc'])
        if approved_at > datetime.now(timezone.utc):
            raise ValueError('Approval date is in the future')
        validate_approval(value, task, digest(task_raw), task['target']['node'], now=approved_at)
    elif kind == 'status':
        if value.get('schema_version') not in (2, 3) or not isinstance(value.get('status'), str):
            raise ValueError('Unsupported historical status')
        time_value(value['heartbeat_utc'])
    else:
        raise ValueError('Unsupported record kind')
    return {'kind': kind, 'schema_version': value['schema_version'], 'sha256': digest(raw),
            'validation': 'status envelope only' if kind == 'status' else 'supported historical contract',
            'execution_authorized': False, 'submitted_experiments': 0,
            'note': 'Read-only historical verification. Approval expiry is not renewed and current execution rules remain strict.',
            'record': value}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--path', type=Path, required=True); p.add_argument('--expected-sha256', required=True)
    p.add_argument('--kind', choices=('project', 'review', 'task', 'approval', 'status'), required=True)
    p.add_argument('--legacy-large', action='store_true'); p.add_argument('--include-content', action='store_true')
    p.add_argument('--task', type=Path); p.add_argument('--task-sha256')
    args = p.parse_args()
    try:
        result = inspect_record(args.path, args.expected_sha256, args.kind, args.legacy_large, args.task, args.task_sha256)
        if not args.include_content:
            result.pop('record')
        print_json(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                    'execution_authorized': False})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
