"""Independent, read-only-source observer; once or foreground loop. Never submits jobs."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import time
import uuid

from common import canonical, digest, print_json, read_json, valid_id
from command_service import CommandService, Context, failure
from hub import Hub, ROOT
from observation_contract import ACTIVE, TERMINAL, apply_observation
from project_store import bounded_read
from storage_paths import plain_path
from task_contract import ARTIFACTS, time_value, validate_approval, validate_task

ARTIFACT_LIMIT = 16_000_000
TOTAL_LIMIT = 64_000_000


def validate_config(config):
    if (not isinstance(config, dict) or set(config) != {'schema_version', 'stale_seconds', 'sources'}
            or type(config['schema_version']) is not int or config['schema_version'] != 1
            or type(config['stale_seconds']) is not int or not 1 <= config['stale_seconds'] <= 86400
            or not isinstance(config['sources'], list) or not 1 <= len(config['sources']) <= 100):
        raise ValueError('Invalid observer config')
    identities = set()
    for source in config['sources']:
        if (not isinstance(source, dict) or set(source) != {'source_id', 'study_id', 'run_id', 'node', 'run_directory'}
                or any(not valid_id(source[k]) for k in ('source_id', 'study_id', 'run_id'))
                or not isinstance(source['node'], str) or not source['node']
                or not isinstance(source['run_directory'], str) or not Path(source['run_directory']).is_absolute()):
            raise ValueError('Each source needs explicit IDs, node and absolute run_directory')
        key = (source['study_id'], source['run_id'])
        if key in identities:
            raise ValueError('Only one authoritative source mapping per run')
        identities.add(key)
        plain_path(source['run_directory'])
    return config


def base_observation(source, run):
    return {'source_id': source['source_id'], 'run_id': source['run_id'], 'node': source['node'],
            'task_sha256': run['task_sha256'], 'approval_sha256': run.get('approval_sha256'),
            'observed_utc': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
            'status': None, 'status_sha256': None, 'source_sequence': None, 'started_utc': None,
            'heartbeat_utc': None, 'fresh_until_utc': None, 'condition': 'unavailable', 'artifacts_verified': False, 'reason': ''}


def read_source(source, run, stale_seconds):
    value = base_observation(source, run)
    snapshot = None
    try:
        directory = plain_path(source['run_directory'])
        status_path = plain_path(directory/'status.json')
        if source['node'] != run['node']:
            raise ValueError('Configured source node differs from registered run')
        raw = bounded_read(status_path, 4_000_000)
        from common import parse_json
        status = parse_json(raw)
        task = status['task']
        validate_task(task, historical=True)
        if (status.get('schema_version') != 3 or status.get('status') not in ACTIVE | TERMINAL
                or status.get('host') != run['node'] or task['target']['node'] != run['node']
                or task['run_id'] != source['run_id'] or task['study_id'] != source['study_id']
                or status.get('task_sha256') != run['task_sha256']
                or status.get('approval_sha256') != run.get('approval_sha256') or not run.get('approval_sha256')):
            raise ValueError('Source task, node or registered approval mismatch')
        task_raw = bounded_read(plain_path(directory/'task.json'), 4_000_000)
        if digest(task_raw) != run['task_sha256'] or parse_json(task_raw) != task:
            raise ValueError('Source task bytes differ from registered task')
        approval_raw = bounded_read(plain_path(directory/'approval.json'), 4_000_000)
        if digest(approval_raw) != run['approval_sha256']:
            raise ValueError('Source approval differs from registered approval')
        start, heartbeat = time_value(status['started_utc']), time_value(status['heartbeat_utc'])
        now = datetime.now(timezone.utc)
        if not start <= heartbeat <= now:
            raise ValueError('Source timestamps are inconsistent or in the future')
        validate_approval(parse_json(approval_raw), task, run['task_sha256'], run['node'], now=start)
        if status['status'] in TERMINAL:
            finish = time_value(status['finished_utc'])
            if not start <= finish <= heartbeat:
                raise ValueError('Terminal timestamp is invalid')
            if type(status.get('exit_code')) is not int or (status['status'] != 'completed' and status['exit_code'] == 0):
                raise ValueError('Terminal state requires a consistent integer exit code')
        sequence = status.get('source_sequence')
        if sequence is not None and (type(sequence) is not int or sequence < 1):
            raise ValueError('Source sequence must be a positive integer')
        verified = False
        if status['status'] == 'completed':
            if type(status.get('exit_code')) is not int or status['exit_code'] != 0:
                raise ValueError('Completed source requires integer zero exit code')
            if set(status.get('artifacts_sha256', {})) != ARTIFACTS:
                raise ValueError('Incomplete sealed artifacts')
            # Copy bounded, verified bytes to a separate temporary directory. Never
            # write a lock, receipt or cache into the execution directory.
            with tempfile.TemporaryDirectory(prefix='opensci-observer-') as temp:
                fixed_copy = Path(temp)
                total = 0
                for name in sorted(ARTIFACTS):
                    data = bounded_read(plain_path(directory/name), ARTIFACT_LIMIT)
                    total += len(data)
                    if total > TOTAL_LIMIT or digest(data) != status['artifacts_sha256'][name]:
                        raise ValueError('Artifact bound or hash mismatch')
                    (fixed_copy/name).write_bytes(data)
                (fixed_copy/'status.json').write_bytes(raw)
                # Existing full result/provenance validation, against the fixed copy.
                from environment_contract import task_environment, validate_environment
                from run_task import validate_results
                copied_task, _ = read_json(fixed_copy/'task.json', run['task_sha256'])
                if copied_task != task:
                    raise ValueError('Snapshot task mismatch')
                read_json(fixed_copy/'approval.json', run['approval_sha256'])
                environment = read_json(fixed_copy/'environment.json')[0]
                validate_environment(environment, run['node'])
                if task_environment(environment) != task['environment']:
                    raise ValueError('Environment mismatch')
                validate_results(fixed_copy, task)
            verified = True
        # Detect status replacement while reading artifacts. Changes are retried
        # at a later scan, never combined into a fabricated source snapshot.
        if bounded_read(status_path, 4_000_000) != raw:
            raise ValueError('Source changed during verification')
        value.update(status=status['status'], status_sha256=digest(raw), source_sequence=sequence,
                     started_utc=status['started_utc'], heartbeat_utc=status['heartbeat_utc'],
                     observed_utc=datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                     condition='current', artifacts_verified=verified, reason='verified_source_snapshot')
        value['fresh_until_utc'] = (heartbeat+timedelta(seconds=stale_seconds)).isoformat() if status['status'] in ACTIVE else None
        if status['status'] in ACTIVE and (now-heartbeat).total_seconds() > stale_seconds:
            value.update(condition='stale', reason='heartbeat_stale_process_state_not_proven')
        if status['status'] in ('initialization_failed', 'cleanup_failed'):
            value.update(condition='needs_reconciliation', reason='inspect_original_host_and_processes')
        snapshot = raw.decode('utf-8')
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        snapshot = None
        value.update(condition='unavailable' if isinstance(exc, OSError) else 'invalid',
                     reason=type(exc).__name__ + ': source unavailable or failed validation; inspect original run')
    return value, snapshot


def scan(service, config):
    config = validate_config(config)
    output = []
    for source in config['sources']:
        try:
            record, _ = service.hub.read(source['study_id'])
            if record['schema_version'] != 4:
                raise ValueError('Upgrade this study through the explicit lifecycle plan before observation')
            run = record['runs'][source['run_id']]
            if source['node'] != run['node']:
                raise ValueError('Source mapping does not match the registered node')
            value, snapshot = read_source(source, run, config['stale_seconds'])
            candidate = copy.deepcopy(record)
            apply_observation(candidate, source['run_id'], value)
            if candidate == record:
                output.append({'study_id': source['study_id'], 'run_id': source['run_id'], 'unchanged': True})
                continue
            request = {'schema_version': 1, 'request_id': 'OBS-'+uuid.uuid4().hex,
                       'study_id': source['study_id'], 'expected_revision': record['revision'],
                       'operation': 'observe', 'arguments': {'run_id': source['run_id'], 'observation': value,
                                                           'status_snapshot': snapshot}}
            output.append(service.execute(request, Context.local('observer')))
        except (ValueError, OSError, KeyError, TypeError, RecursionError) as exc:
            output.append({'study_id': source['study_id'], 'run_id': source['run_id'], **failure(exc)})
    return {'observations': output, 'submitted_experiments': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=ROOT)
    p.add_argument('--config', type=Path)
    p.add_argument('--sources', type=Path, required=True, help='Protected fixed source mappings; local directories or trusted read-only mounts')
    p.add_argument('--watch', action='store_true')
    p.add_argument('--interval', type=float, default=30)
    args = p.parse_args()
    try:
        if not 1 <= args.interval <= 86400:
            raise ValueError('Interval must be 1..86400 seconds')
        service = CommandService(Hub(plain_path(args.workspace), read_json(args.config)[0] if args.config else None))
        config = validate_config(read_json(plain_path(args.sources))[0])
        while True:
            result = scan(service, config)
            print_json(result)
            if not args.watch:
                return 2 if any('error' in item for item in result['observations']) else 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print_json({'error': type(exc).__name__, 'submitted_experiments': 0})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
