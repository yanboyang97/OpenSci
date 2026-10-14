"""Operator-only selection for a protected private single-study connection.

No grants are inferred from a project name or supplied by an Agent tool. Stop the
affected connection before running this command, then restart it after selection.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

from common import read_json
from hub import Hub
from hub_mcp import validate_policy
from storage_paths import plain_path


def select(policy, study_id, hub):
    policy = json.loads(json.dumps(validate_policy(policy)))
    if policy['schema_version'] != 2:
        raise ValueError('Use a version 2 connection policy')
    if study_id is not None:
        hub.store.read(study_id)
    policy.update(studies=[study_id] if study_id else [], allow_write=study_id is not None, native_project=None)
    return validate_policy(policy)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--coordinator-root', type=Path, required=True)
    p.add_argument('--policy', type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--study-id')
    group.add_argument('--clear', action='store_true')
    p.add_argument('--connection-stopped', action='store_true', required=True)
    args = p.parse_args()
    path = plain_path(args.policy)
    old = path.read_bytes()
    policy = select(read_json(path, limit=64000)[0], args.study_id, Hub(plain_path(args.coordinator_root)))
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            temp = Path(f.name)
            json.dump(policy, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        if path.read_bytes() != old:
            raise ValueError('Policy changed concurrently; reconcile before selecting')
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    print('Study selected.' if args.study_id else 'Selection cleared; the connection is read-only with no study access.')
    print('Restart the affected connection. Existing processes retain their previous policy until stopped.')


if __name__ == '__main__':
    main()
