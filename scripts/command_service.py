"""Desktop-independent commands, committed receipts and history-derived events.

Only accepted commands have durable receipts. Rejected requests never promise
exactly-once external effects. Trust Context only from a protected adapter/OS.
"""
import copy
from collections import deque
from dataclasses import dataclass
import re

from common import FileLock, atomic_write, canonical, digest, parse_json, valid_id
from project_store import bounded_read
from storage_paths import plain_path
from literature_contract import OPERATIONS as LITERATURE_OPERATIONS, READ_OPERATIONS as LITERATURE_READS

REQUEST_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}')
ARGUMENTS = {
    'create_study': {'goal', 'research_workspace', 'binding'},
    'bind_project': {'binding'}, 'unbind_project': {'identity'},
    'save_progress': {'progress'},
    'init': {'goal'}, 'note': {'note'}, 'checkpoint': {'phase', 'note'},
    'select_agent': {'target'}, 'select_compute': {'target'},
    'attach': {'kind', 'relative', 'expected'},
    'observe': {'run_id', 'observation', 'status_snapshot'},
}
ARGUMENTS.update({op: {'payload'} for op in LITERATURE_OPERATIONS})
AGENT_OPERATIONS = {'note', 'checkpoint', 'attach', 'save_progress'}
STRUCTURED_OPERATIONS = {'create_study', 'bind_project', 'unbind_project', 'save_progress'}


class CommandError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Context:
    principal: str
    role: str
    allow_remote_checks: bool = False
    source_entry: dict | None = None

    @classmethod
    def local(cls, role='operator', allow_remote_checks=False):
        # Transport/OS context, never an identity supplied inside a tool request.
        from os_identity import principal
        return cls(principal(), role, allow_remote_checks)


def failure(exc):
    code = getattr(exc, 'code', 'outcome_unknown')
    return {'committed': None if code in ('outcome_unknown', 'history_invalid') else False,
            'error': code, 'detail': str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
            'recovery': 'Keep the original request unchanged. Query its receipt; retry with the SAME request ID and caller context.',
            'submitted_experiments': 0}


def validate_request(request):
    if (not isinstance(request, dict) or set(request) != {'schema_version', 'request_id', 'study_id',
            'expected_revision', 'operation', 'arguments'} or type(request['schema_version']) is not int
            or request['schema_version'] != 1 or not isinstance(request['request_id'], str)
            or not REQUEST_ID.fullmatch(request['request_id']) or not valid_id(request['study_id'])
            or type(request['expected_revision']) is not int or request['expected_revision'] < 0
            or not isinstance(request['operation'], str) or request['operation'] not in ARGUMENTS
            or not isinstance(request['arguments'], dict)
            or set(request['arguments']) != ARGUMENTS[request['operation']]):
        raise CommandError('invalid_request', 'Use the documented Operation Service request fields and a supported operation')
    limit = 16_000_000 if request['operation'] == 'observe' else 64000
    if len(canonical(request)) > limit:
        raise CommandError('invalid_request', 'Command exceeds its UTF-8 byte limit')
    args = request['arguments']
    if request['operation'] in LITERATURE_OPERATIONS:
        if not isinstance(args['payload'], dict):
            raise CommandError('invalid_request', 'Literature operations require one structured payload')
    elif request['operation'] not in STRUCTURED_OPERATIONS | {'observe'} and any(not isinstance(v, str) or not v.strip() for v in args.values()):
        raise CommandError('invalid_request', 'Command arguments must be nonempty strings')
    return request


def authorize(request, context):
    if (not isinstance(context, Context) or context.role not in ('operator', 'agent', 'observer')
            or not isinstance(context.principal, str) or not context.principal or len(context.principal) > 256):
        raise CommandError('forbidden', 'Trusted caller context required')
    op, args = request['operation'], request['arguments']
    if op in LITERATURE_OPERATIONS:
        from literature_contract import AGENT_OPERATIONS as LITERATURE_AGENT
        if context.role == 'observer' or context.role == 'agent' and op not in LITERATURE_AGENT:
            raise CommandError('forbidden', 'Literature operation is outside this trusted caller role')
        return
    if context.role == 'observer' and op != 'observe' or context.role != 'observer' and op == 'observe':
        raise CommandError('forbidden', 'Observation is reserved for the independent observer')
    if context.role == 'agent':
        if op not in AGENT_OPERATIONS:
            raise CommandError('forbidden', 'Operation not available to desktop agents')
        if op == 'attach' and args['kind'] not in ('evidence', 'review', 'task'):
            raise CommandError('forbidden', 'Agents cannot register approvals or run states')
        if op == 'checkpoint' and args['phase'] in ('experiment_running', 'archived'):
            raise CommandError('forbidden', 'This phase requires the operator and verified runtime facts')
    if op == 'attach':
        if args['kind'] not in ('evidence', 'review', 'task', 'approval'):
            raise CommandError('forbidden', 'Register run state through the independent observer')
        if not args['relative'].startswith('coordination/imports/') or args['relative'].startswith('coordination/imports/snapshots/'):
            raise CommandError('invalid_request', 'Import a file into coordination/imports before registering it')


def receipt(record, raw):
    result = {'schema_version': 1, 'record_type': 'opensci_command_receipt', 'committed': True,
            **copy.deepcopy(record['journal']['command']), 'record_sha256': digest(raw),
            'committed_utc': record['updated_utc'], 'submitted_experiments': 0}
    for ref in record['references']:
        if ref.get('kind') == 'literature' and ref.get('request_id') == result['request_id']:
            result['literature_result_ref'] = copy.deepcopy(ref)
    return result


class CommandService:
    def __init__(self, hub):
        self.hub = hub

    def find_receipt(self, study, request_id, context, expected=None):
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            raise CommandError('invalid_request', 'Invalid request ID')
        found = None
        # Verify the ENTIRE reachable chain even if the requested receipt is recent.
        for record, raw in self.hub.store.versions(study):
            cmd = record.get('journal', {}).get('command')
            if cmd and cmd['request_id'] == request_id:
                if cmd['principal'] != context.principal or cmd['role'] != context.role:
                    raise CommandError('request_conflict', 'Request ID belongs to a different caller context')
                if expected is not None and cmd['request_sha256'] != expected:
                    raise CommandError('request_conflict', 'Request ID was already committed with different content')
                if found is not None:
                    raise CommandError('history_invalid', 'Duplicate committed request ID')
                found = receipt(record, raw)
        return found

    def execute(self, request, context):
        validate_request(request)
        authorize(request, context)
        study, op, args = request['study_id'], request['operation'], request['arguments']
        if op in LITERATURE_READS:
            from literature_service import LiteratureService
            # Capabilities are safe before a study exists; other reads remain study scoped.
            if op != 'literature.capabilities': self.hub.store.read(study)
            return {'schema_version': 1, 'read_only': True, 'committed': False,
                    'result': LiteratureService(self.hub).read(request, context), 'submitted_experiments': 0}
        request_sha = digest(canonical(request))
        path = self.hub.store.path(study)
        with FileLock(self.hub.root/'coordination/projects/.hub.lock'), FileLock(path.with_suffix('.lock')):
            if path.exists():
                previous, raw = self.hub.store.read(study)
                prior = self.find_receipt(study, request['request_id'], context, request_sha)
                if prior is not None:
                    return prior
                if previous['schema_version'] != 4:
                    raise CommandError('upgrade_required', 'Upgrade required: preserve backups and run lifecycle enable-study preflight/apply (enable-commands for v2); follow docs/UPGRADE_GUIDE.md')
                if op in ('init', 'create_study') or previous['revision'] != request['expected_revision']:
                    raise CommandError('revision_conflict', 'Reread the project; this request was not committed')
                record = copy.deepcopy(previous)
                if op in LITERATURE_OPERATIONS:
                    from literature_service import LiteratureService
                    ref = LiteratureService(self.hub).execute(request, context)
                    ref.update(request_id=request['request_id'], operation=op)
                    # Bounded current pointers; older result pointers remain in immutable history.
                    record['references'] = [r for r in record['references'] if not (
                        r.get('kind') == 'literature' and r.get('operation') == op)]
                    record['references'].append(ref)
                else:
                    self.edit(record, op, args, context)
                outcome = 'no_effect' if record == previous else 'changed'
                record['revision'] += 1
            else:
                if op not in ('init', 'create_study') or request['expected_revision'] != 0:
                    raise CommandError('not_found', 'Project does not exist; operator init requires expected_revision=0')
                if op == 'init':
                    from study_context import extend_record
                    record = extend_record(self.hub.initial_record(study, args['goal']),
                        {'primary': {'host_id': 'local', 'path': str(self.hub.root)}, 'additional': []})
                else:
                    record = self.hub.create_study_record(study, args['goal'], args['research_workspace'])
                    if args['binding'] is not None:
                        from project_binding import bind
                        bind(record, args['binding'], self.hub.store)
                previous, raw, outcome = None, None, 'changed'
            command = {'request_id': request['request_id'], 'request_sha256': request_sha,
                       'principal': context.principal, 'role': context.role, 'operation': op,
                       'outcome': outcome, 'revision': record['revision'], 'study_id': study}
            try:
                saved = self.hub.store.commit(raw, record, op, args.get('note') or op,
                                              actor=context.principal, command=command)
                return receipt(saved, canonical(saved))
            except (ValueError, OSError, KeyError, TypeError) as exc:
                raise CommandError('outcome_unknown', 'Commit outcome needs receipt recovery using the original request ID') from exc

    def edit(self, record, operation, args, context):
        if operation == 'save_progress':
            from study_context import validate_progress, validate_entry, UNKNOWN_ENTRY
            content = validate_progress(args['progress'])
            entry = validate_entry(context.source_entry or UNKNOWN_ENTRY)
            record['progress'] = {'content': copy.deepcopy(content), 'source_entry': copy.deepcopy(entry)}
            return
        if operation in ('bind_project', 'unbind_project'):
            from project_binding import bind, unbind
            if operation == 'bind_project':
                bind(record, args['binding'], self.hub.store)
            else:
                unbind(record, args['identity'])
            return
        if operation == 'note':
            record['checkpoint_note'] = args['note']
            return
        if operation == 'observe':
            from observation_contract import apply_observation
            value, snapshot = args['observation'], args['status_snapshot']
            if not isinstance(value, dict):
                raise CommandError('invalid_request', 'Observation must be an object')
            if value.get('status') is not None:
                if not isinstance(snapshot, str) or len(snapshot.encode('utf-8')) > 4_000_000:
                    raise CommandError('invalid_request', 'Observation needs its bounded original status bytes')
                raw = snapshot.encode('utf-8')
                status = parse_json(raw)
                if (digest(raw) != value.get('status_sha256') or status.get('status') != value['status']
                        or status.get('task_sha256') != value.get('task_sha256')
                        or status.get('approval_sha256') != value.get('approval_sha256')
                        or status.get('host') != value.get('node')
                        or status.get('task', {}).get('run_id') != args['run_id']
                        or status.get('task', {}).get('study_id') != record['study_id']
                        or any(status.get(k) != value.get(k) for k in ('source_sequence', 'started_utc', 'heartbeat_utc'))):
                    raise CommandError('invalid_request', 'Observation and original status bytes disagree')
            elif snapshot is not None:
                raise CommandError('invalid_request', 'Missing-source observations cannot carry a status snapshot')
            apply_observation(record, args['run_id'], args['observation'])
            if snapshot is not None:
                relative = 'coordination/imports/snapshots/'+digest(raw)+'.blob'
                path = plain_path(self.hub.root/relative)
                if path.exists():
                    if bounded_read(path, 4_000_000) != raw:
                        raise ValueError('Immutable observed status snapshot changed')
                else:
                    atomic_write(path, raw)
                ref = {'kind': 'observation', 'run_id': args['run_id'], 'source_path': 'observer:'+value['source_id'],
                       'path': relative, 'sha256': digest(raw)}
                # One current pointer per run; prior pointers and bytes remain
                # reachable through immutable project history. Heartbeats must
                # not grow the head's reference list without bound.
                record['references'] = [r for r in record['references'] if not (
                    r['kind'] == 'observation' and r.get('run_id') == args['run_id'])]
                record['references'].append(ref)
            return
        if operation in ('checkpoint', 'select_agent') and not context.allow_remote_checks:
            names = {record['active_agent']}
            if operation == 'select_agent':
                names.add(args['target'])
            if any(self.hub.config['nodes'].get(n, {}).get('transport') != 'local' for n in names):
                raise CommandError('remote_check_required', 'This command probes remote workspaces; enable checks in trusted launch policy')
        if operation == 'checkpoint':
            from observation_contract import effective_observation
            if args['phase'] == 'experiment_running' and not any(
                    effective_observation(r.get('observation', {})).get('condition') == 'current' and r['recorded_status'] in ('starting', 'running')
                    for r in record['runs'].values()):
                raise CommandError('precondition_failed', 'A current verified running observation is required')
        getattr(self.hub, 'edit_'+operation)(record, **args)

    def query(self, study):
        from project_brief import brief_from_view
        # show/brief do not contact the Agent or an execution host.
        view = self.hub.show(study)
        return {'project': view, 'brief': brief_from_view(view),
                'cursor': {'revision': view['project']['revision'], 'sha256': view['record_sha256']},
                'submitted_experiments': 0}

    def events(self, study, after=None, limit=50):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise CommandError('invalid_cursor', 'Event page size must be 1..100')
        start = 0
        if after is not None:
            if not isinstance(after, dict) or set(after) != {'revision', 'sha256'} or type(after['revision']) is not int:
                raise CommandError('resync_required', 'Read a full snapshot and its cursor')
            start = after['revision']
        items = deque(maxlen=limit)
        found = after is None
        latest = 0
        for r, raw in self.hub.store.versions(study):
            latest = max(latest, r['revision'])
            sha = digest(raw)
            if after and r['revision'] == start and sha == after['sha256']:
                found = True
            if r['revision'] <= start:
                continue
            items.appendleft({'revision': r['revision'], 'sha256': sha, 'updated_utc': r['updated_utc'],
                          'phase': r['phase'], 'journal': copy.deepcopy(r.get('journal'))})
        if not found:
            raise CommandError('resync_required', 'Cursor is outside the committed lineage; read a full snapshot')
        items = list(items)
        cursor = {'revision': items[-1]['revision'], 'sha256': items[-1]['sha256']} if items else after
        return {'study_id': study, 'events': items, 'cursor': cursor,
                'has_more': bool(cursor and cursor['revision'] < latest),
                'scope': 'Committed per-study history; receipt means state registration, never experiment approval'}
