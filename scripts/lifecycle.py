"""Plan-bound project upgrades, relocation and state rollback. Never submits jobs.

Apply changes only the project head; config files are supplied by the operator
and are never rewritten. Stopping every old writer remains a human prerequisite.
"""
import argparse
import ast
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import VERSION, FileLock, canonical, create_json, digest, print_json, read_json, require_hash, stamp
from hub import Hub, matching, node_for, probe
from project_store import finalize_record
from task_contract import time_value
from workspace_probe import observe

OPERATIONS = ('upgrade', 'relocate', 'rollback', 'enable-commands', 'enable-study')


def code_version(root):
    tree = ast.parse((root/'scripts/common.py').read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Workspace version not declared')


def observations(hub, record, agent, allow_remote=False):
    local = observe(hub.research_path(record))
    if local['dirty'] or code_version(hub.runtime_root) != VERSION:
        raise ValueError(f'Use a clean committed v{VERSION} workspace; keep old source/records separately')
    if local['origin_sha256'] != record['anchor']['origin_sha256']:
        raise ValueError('Restore the reviewed Git origin before upgrade or relocation')
    node = node_for(hub.config, agent, 'agent')
    if node['transport'] != 'local' and not allow_remote:
        raise ValueError('Remote checks require explicit --allow-remote-check; no connection made')
    target = probe(node)
    anchor = {k: local[k] for k in ('commit', 'origin_sha256')}
    matching(target, anchor)
    return anchor, copy.deepcopy(node)


def candidate(hub, current, plan):
    record = copy.deepcopy(current)
    if plan['operation'] in ('enable-commands', 'enable-study'):
        from study_context import extend_record
        extend_record(record, {'primary': {'host_id': 'local', 'path': str(hub.root)}, 'additional': []})
    if plan['operation'] == 'rollback':
        old, raw = hub.store.version(current['study_id'], plan['to_revision'])
        if digest(raw) != plan['to_sha256']:
            raise ValueError('Rollback version changed')
        # Roll back editable planning state only. Preserve every later run,
        # approval/evidence reference, device binding and source identity.
        for key in ('goal', 'phase', 'checkpoint_note', *(['progress'] if current['schema_version'] == 4 else [])):
            if key in old:
                record[key] = old[key]
            else:
                if key == 'progress': record[key] = None
                else: record.pop(key, None)
        if record['phase'] == 'experiment_running':
            record['phase'] = 'analysis'
    else:
        record['anchor'] = plan['target_anchor']
        record['active_agent'] = plan['target_agent']
        record['agent_snapshot'] = copy.deepcopy(plan['target_agent_snapshot'])
        # The previous compute remains a historical fact; no job is moved.
    record['revision'] = current['revision'] + 1
    record['lifecycle'] = {'operation': plan['operation'], 'plan_sha256': digest(canonical(plan)),
                           'reason': plan['reason'], 'applied_utc': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                           'source_record_sha256': plan['source_sha256'],
                           'old_writer_stopped': 'operator declaration; not a distributed lease',
                           'old_runs': 'preserved; query original nodes before any new attempt',
                           'execution_approval': 'none; new environment/source needs a new task and approval'}
    record['history'] = []
    return finalize_record(record, current, plan['source_sha256'], plan['operation'], plan['reason'])[0]


def preflight(hub, study, operation, reason, target_agent=None, to_revision=None,
              allow_remote=False, legacy_large=False):
    if operation not in OPERATIONS or not isinstance(reason, str) or not reason.strip() or len(reason.encode('utf-8')) > 32000:
        raise ValueError('Choose an operation and a bounded nonempty reason')
    current, raw = hub.store.read(study, legacy_large)
    history = hub.store.check(study, legacy_large)
    hub.references_ok(current)
    target_agent = target_agent or current['active_agent']
    if operation == 'enable-study':
        if current['schema_version'] != 3:
            raise ValueError('enable-study requires an existing v3 Operation Service record')
        if target_agent != current['active_agent']:
            raise ValueError('Record-format migration cannot change the research workspace; use a separate verified relocation')
        anchor, node = copy.deepcopy(current['anchor']), copy.deepcopy(current['agent_snapshot'])
    elif current['schema_version'] == 4 and current['anchor'] is None and operation == 'rollback':
        anchor, node = None, copy.deepcopy(current['agent_snapshot'])
    else:
        anchor, node = observations(hub, current, target_agent, allow_remote)
    if operation == 'enable-commands' and current['schema_version'] != 2:
        raise ValueError('Study preparation is required before enable-commands; run lifecycle upgrade preflight/apply first')
    if operation in ('relocate', 'rollback') and current['schema_version'] not in (2, 3, 4):
        raise ValueError('Upgrade the legacy record first (upgrade can select the new Agent)')
    if operation == 'relocate' and anchor != current['anchor']:
        raise ValueError('Relocation preserves the code commit; use upgrade for an intentional code change')
    if operation == 'rollback' and (anchor != current['anchor'] or node != current['agent_snapshot'] or target_agent != current['active_agent']):
        raise ValueError('Planning rollback cannot change code or device; use a separate upgrade/relocation')
    old_hash = None
    if operation == 'rollback':
        if type(to_revision) is not int or to_revision >= current['revision']:
            raise ValueError('Choose an earlier committed revision')
        old, old_raw = hub.store.version(study, to_revision)
        hub.references_ok(old)
        old_hash = digest(old_raw)
    elif to_revision is not None:
        raise ValueError('to_revision is only for rollback')
    now = datetime.now(timezone.utc)
    plan = {'schema_version': 1, 'record_type': 'opensci_lifecycle_plan', 'tool_version': VERSION,
            'operation': operation, 'workspace': str(hub.root), 'study_id': study,
            'source_revision': current['revision'], 'source_sha256': digest(raw),
            'source_schema': current['schema_version'], 'config_sha256': digest(canonical(hub.config)),
            'target_agent': target_agent, 'target_agent_snapshot': node, 'target_anchor': anchor,
            'to_revision': to_revision, 'to_sha256': old_hash, 'legacy_large': legacy_large,
            'created_utc': now.isoformat(), 'expires_utc': (now + timedelta(hours=1)).isoformat(),
            'reason': reason, 'can_submit_experiments': False,
            'facts': {'run_ids': sorted(current['runs']), 'reference_count': len(current['references']),
                      'history': history},
            'required_declarations': ['all_old_writers_stopped', 'source_backup_saved', 'original_runs_reconciled']}
    candidate(hub, current, plan)
    return plan


def apply_plan(hub, plan, expected_sha256, quiesced=False, backup_saved=False,
               runs_reconciled=False, allow_remote=False):
    require_hash(expected_sha256)
    if digest(canonical(plan)) != expected_sha256:
        raise ValueError('Lifecycle plan hash mismatch')
    if not all((quiesced, backup_saved, runs_reconciled)):
        raise ValueError('Confirm stopped writers, independent backup and original run reconciliation first')
    if (plan.get('schema_version') != 1 or plan.get('record_type') != 'opensci_lifecycle_plan'
            or plan.get('tool_version') != VERSION or plan.get('workspace') != str(hub.root)
            or plan.get('can_submit_experiments') is not False):
        raise ValueError('Unsupported lifecycle plan')
    now = datetime.now(timezone.utc)
    if not time_value(plan['created_utc']) <= now <= time_value(plan['expires_utc']):
        raise ValueError('Lifecycle plan expired or future dated')
    study = plan['study_id']
    path = hub.store.path(study)
    with FileLock(hub.root/'coordination/projects/.hub.lock'), FileLock(path.with_suffix('.lock')):
        current, raw = hub.store.read(study, plan['legacy_large'])
        if digest(raw) != plan['source_sha256'] or current['revision'] != plan['source_revision']:
            raise ValueError('Project changed; generate a new preflight plan')
        fresh = preflight(hub, study, plan['operation'], plan['reason'], plan['target_agent'],
                          plan['to_revision'], allow_remote, plan['legacy_large'])
        stable = set(fresh) - {'created_utc', 'expires_utc'}
        if set(plan) != set(fresh) or any(fresh[k] != plan[k] for k in stable):
            raise ValueError('Configuration, code, facts or target changed; regenerate plan')
        updated = candidate(hub, current, plan)
        result = hub.store.commit(raw, updated, plan['operation'], plan['reason'])
    return {'project': result, 'record_sha256': digest(canonical(result)), 'operation': plan['operation'],
            'submitted_experiments': 0, 'resumed_experiment_processes': 0,
            'note': 'Only coordinator state continued; historical approvals unchanged; original runs remain on their nodes'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--config', type=Path, help='Operator-prepared target config; never rewritten')
    sub = p.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('preflight')
    plan.add_argument('--study', required=True); plan.add_argument('--operation', choices=OPERATIONS, required=True)
    plan.add_argument('--reason', required=True); plan.add_argument('--target-agent'); plan.add_argument('--to-revision', type=int)
    plan.add_argument('--output', type=Path, required=True); plan.add_argument('--legacy-large', action='store_true')
    plan.add_argument('--allow-remote-check', action='store_true')
    apply = sub.add_parser('apply')
    apply.add_argument('--plan', type=Path, required=True); apply.add_argument('--expected-sha256', required=True)
    for flag in ('quiesced', 'backup-saved', 'runs-reconciled', 'allow-remote-check'):
        apply.add_argument('--'+flag, action='store_true')
    args = p.parse_args()
    try:
        hub = Hub(args.workspace, read_json(args.config)[0] if args.config else None)
        if args.command == 'preflight':
            if args.output.resolve().is_relative_to(hub.root):
                raise ValueError('Save plans outside the workspace to keep the source commit clean')
            result = preflight(hub, args.study, args.operation, args.reason, args.target_agent, args.to_revision,
                               args.allow_remote_check, args.legacy_large)
            create_json(args.output, result)
            print_json({'plan': str(args.output), 'plan_sha256': digest(canonical(result)), 'submitted_experiments': 0})
        else:
            value, raw = read_json(args.plan, args.expected_sha256)
            # The command accepts only the canonical plan emitted by preflight.
            print_json(apply_plan(hub, value, args.expected_sha256, args.quiesced, args.backup_saved,
                                  args.runs_reconciled, args.allow_remote_check))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                    'submitted_experiments': 0})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
