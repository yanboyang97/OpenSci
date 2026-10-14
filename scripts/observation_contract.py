"""Shared monotonic runtime observations. Never approve, submit, cancel or retry jobs."""
import copy
from datetime import datetime, timezone
from common import canonical, require_hash, valid_id
from task_contract import time_value

ACTIVE = {'starting', 'running'}
TERMINAL = {'completed', 'failed', 'timeout', 'cancelled', 'initialization_failed',
            'launch_failed', 'failed_validation_or_runtime', 'cleanup_failed'}
CONDITIONS = {'current', 'stale', 'unavailable', 'invalid', 'needs_reconciliation', 'conflict'}
FIELDS = {'source_id', 'status_sha256', 'source_sequence', 'started_utc', 'heartbeat_utc',
          'observed_utc', 'status', 'condition', 'artifacts_verified', 'task_sha256',
          'approval_sha256', 'node', 'run_id', 'reason', 'fresh_until_utc'}


def significant(value):
    return {k: v for k, v in value.items() if k != 'observed_utc'}


def effective_observation(value, now=None):
    """Dated stored facts stay immutable; reads can derive that freshness expired."""
    value = copy.deepcopy(value)
    if value and value['condition'] == 'current' and value['status'] in ACTIVE:
        if not value.get('fresh_until_utc') or time_value(value['fresh_until_utc']) < (now or datetime.now(timezone.utc)):
            value.update(condition='stale', reason='observation_freshness_expired')
    return value


def apply_observation(record, run_id, observation):
    if not valid_id(run_id) or run_id not in record['runs']:
        raise ValueError('Observation must bind a registered run')
    run = record['runs'][run_id]
    value = copy.deepcopy(observation)
    if (not isinstance(value, dict) or set(value) != FIELDS or value['run_id'] != run_id
            or value['node'] != run['node'] or value['task_sha256'] != run['task_sha256']
            or value['approval_sha256'] != run.get('approval_sha256')
            or value['condition'] not in CONDITIONS or type(value['artifacts_verified']) is not bool
            or not isinstance(value['source_id'], str) or not valid_id(value['source_id'])
            or not isinstance(value['reason'], str) or len(value['reason']) > 300):
        raise ValueError('Invalid observation binding or fields')
    time_value(value['observed_utc'])
    prior = run.get('runtime_source')
    if value['status'] is not None:
        if value['status'] not in ACTIVE | TERMINAL:
            raise ValueError('Unrecognized execution state')
        require_hash(value['status_sha256'])
        seq = value['source_sequence']
        if seq is not None and (type(seq) is not int or seq < 1):
            raise ValueError('Invalid source sequence')
        start, heartbeat = time_value(value['started_utc']), time_value(value['heartbeat_utc'])
        if start > heartbeat or heartbeat > time_value(value['observed_utc']):
            raise ValueError('Source clock is ahead of observation or time ordering is invalid')
        if value['status'] in ACTIVE:
            if not 0 < (time_value(value['fresh_until_utc'])-heartbeat).total_seconds() <= 86400:
                raise ValueError('Invalid observation freshness bound')
        elif value['fresh_until_utc'] is not None:
            raise ValueError('Terminal observations do not claim continuing liveness')
        if value['status'] == 'completed' and not value['artifacts_verified']:
            raise ValueError('Completed observations require verified artifacts')
        conflict = None
        if not prior and run.get('recorded_status') in TERMINAL and (
                value['status'] != run['recorded_status'] or value['status_sha256'] != run.get('status_sha256')):
            conflict = 'existing_terminal_record_requires_reconciliation'
        if prior:
            if value['source_id'] != prior['source_id'] or value['started_utc'] != prior['started_utc']:
                conflict = 'source_or_run_identity_changed'
            elif prior['status'] in TERMINAL and (value['status'] != prior['status']
                    or value['status_sha256'] != prior['status_sha256']):
                conflict = 'terminal_state_cannot_be_overwritten'
            elif prior['status'] == 'running' and value['status'] == 'starting':
                conflict = 'execution_state_moved_backwards'
            elif heartbeat < time_value(prior['heartbeat_utc']):
                conflict = 'source_time_moved_backwards'
            elif prior['source_sequence'] is not None:
                if seq is None or seq < prior['source_sequence']:
                    conflict = 'source_sequence_moved_backwards'
                elif seq == prior['source_sequence'] and value['status_sha256'] != prior['status_sha256']:
                    conflict = 'same_source_sequence_has_different_content'
            elif heartbeat == time_value(prior['heartbeat_utc']) and value['status_sha256'] != prior['status_sha256']:
                conflict = 'legacy_timestamp_has_different_content'
        if conflict:
            value.update(condition='conflict', reason=conflict)
        elif value['condition'] in ('current', 'stale', 'needs_reconciliation'):
            run['recorded_status'] = value['status']
            run['status_sha256'] = value['status_sha256']
            run['status_path'] = 'coordination/imports/snapshots/'+value['status_sha256']+'.blob'
            run['runtime_source'] = {k: value[k] for k in ('source_id', 'started_utc', 'heartbeat_utc',
                'source_sequence', 'status_sha256', 'status', 'artifacts_verified')}
    elif (value['condition'] not in ('unavailable', 'invalid') or value['status_sha256'] is not None
          or value['source_sequence'] is not None or value['started_utc'] is not None
          or value['heartbeat_utc'] is not None or value['fresh_until_utc'] is not None or value['artifacts_verified']):
        raise ValueError('Invalid missing-source observation')
    if significant(run.get('observation', {})) != significant(value):
        run['observation'] = value
    # Project phase remains a planning decision; observed execution is a separate fact.

