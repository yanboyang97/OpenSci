"""Build a read-only, explicitly dated brief for a human or Dot to relay.

No remote query, automatic sharing, approval conversion or experiment submission.
"""
from common import stamp
from observation_contract import effective_observation


def build_brief(hub, study):
    return brief_from_view(hub.show(study))


def brief_from_view(view):
    """Use one authoritative read for brief, project revision and cursor."""
    record = view['project']
    pending = list(view['missing'])
    if record['phase'] == 'awaiting_approval':
        pending.append('Review the fixed task, model/data versions, resource limits and acceptance criteria; the independent human submission account grants formal approval.')
    if record['phase'] == 'experiment_running':
        pending.append('Query the original run_id on its execution node; this brief contains recorded snapshots.')
    return {
        'schema_version': 1, 'record_type': 'opensci_readonly_brief',
        'study_id': record['study_id'], 'goal': record['goal'],
        'generated_utc': stamp(), 'record_updated_utc': record['updated_utc'],
        'record_revision': record['revision'], 'record_sha256': view['record_sha256'],
        'phase': record['phase'], 'phase_name': view['phase_name'],
        'checkpoint_note': record.get('checkpoint_note'), 'next_step': view['next_step'],
        'pending_decisions_or_checks': pending,
        'runs': [{'run_id': key, 'node': run['node'], 'recorded_status': run['recorded_status'],
                  'task_sha256': run['task_sha256'], 'status_sha256': run.get('status_sha256'),
                  'approval_expires_utc': run.get('approval_expires_utc'),
                  'observation': effective_observation(run.get('observation'))}
                 for key, run in sorted(record['runs'].items())],
        'evidence_count': len(record['references']),
        'live_node_status': 'not_queried', 'scientific_result_validation': 'not_performed_by_this_read; see each run observation for artifact checks',
        'approval_authority': False, 'submitted_experiments': 0,
        'sharing': 'local output only; review project data permissions before relaying',
    }
