"""OpenSci's small project controller. No experiment submission authority.

One coordinator copy owns the study records; agent workspaces are Git checkouts.
Show/resume are read-only. Writes need an expected revision and a local lock.
"""
import argparse
import copy
from datetime import datetime, timezone
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import uuid
from common import (VERSION, FileLock, atomic_write, canonical, create_json, digest, file_hash, parse_json,
                    print_json, read_json, require_hash, stamp, valid_id, write_json)
from task_contract import time_value, validate_task
from workspace_probe import observe
from project_store import ProjectStore, PROJECT_LIMIT

ROOT = Path(__file__).resolve().parents[1]
PHASES = ('evidence', 'plan_review', 'implementation', 'awaiting_approval',
          'experiment_running', 'analysis', 'archived')
PHASE_NAMES = dict(zip(PHASES, ('Evidence', 'Plan review', 'Implementation', 'Awaiting approval', 'Experiment running', 'Analysis', 'Archived')))
NEXT = {
    'evidence': 'Organize evidence and record sources and versions.',
    'plan_review': 'Use Preview Evidence Review to inspect the plan; live model calls require separate authorization.',
    'implementation': 'Implement, test and commit in the Development Workspace; use Record Progress to register the source commit.',
    'awaiting_approval': 'Choose an Execution Node and use Task Preparation to create a draft for independent human approval.',
    'experiment_running': 'Inspect the original run ID on its Execution Node; do not resubmit.',
    'analysis': 'Validate results, analyze statistics, link manuscript evidence and archive.',
    'archived': 'Preserve study records, run IDs, provenance and independent backups.',
}
SAFE_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}')
NODE_KEYS = {'role', 'enabled', 'transport', 'workspace', 'python', 'account',
             'ssh_host', 'distribution', 'hostname', 'capabilities'}


def validate_config(config):
    if not isinstance(config, dict) or set(config) != {'schema_version', 'default_agent', 'nodes'} or type(config['schema_version']) is not int or config['schema_version'] not in (1, 2):
        raise ValueError('Unsupported Research Workspace configuration; use the supplied configuration example')
    nodes = config['nodes']
    if not isinstance(nodes, dict) or not nodes and config['schema_version'] == 1:
        raise ValueError('Define nodes')
    for name, node in nodes.items():
        if not SAFE_NAME.fullmatch(name) or not isinstance(node, dict) or set(node)-NODE_KEYS:
            raise ValueError('Invalid node or unknown fields (credentials do not belong here)')
        if node.get('role') not in ('agent', 'compute', 'control') or type(node.get('enabled')) is not bool:
            raise ValueError('Each node needs one role and an explicit enabled boolean')
        if node.get('transport') not in ('wsl', 'ssh', 'local'):
            raise ValueError('Unknown transport')
        if (node['transport'] != 'ssh' and 'ssh_host' in node) or (node['transport'] != 'wsl' and 'distribution' in node):
            raise ValueError('Transport-specific fields cannot be used on another transport')
        for key in ('account', 'workspace', 'python'):
            if not isinstance(node.get(key), str) or not node[key].strip() or any(ord(c) < 32 for c in node[key]):
                raise ValueError('Invalid node '+key)
        if not SAFE_NAME.fullmatch(node['account']):
            raise ValueError('Use a concrete OS account name')
        if node['transport'] in ('ssh', 'wsl') and not PurePosixPath(node['workspace']).is_absolute():
            raise ValueError('SSH/WSL workspace must be an absolute Linux path; expand ~')
        if node['transport'] == 'local' and not Path(node['workspace']).is_absolute():
            raise ValueError('Local workspace must be absolute')
        if not (SAFE_NAME.fullmatch(node['python']) or PurePosixPath(node['python']).is_absolute() or Path(node['python']).is_absolute()) or node['python'].startswith('-'):
            raise ValueError('Python must be an executable name or absolute path, without arguments')
        required = {'ssh': 'ssh_host', 'wsl': 'distribution'}.get(node['transport'])
        if required and (not isinstance(node.get(required), str) or not SAFE_NAME.fullmatch(node[required])):
            raise ValueError('Use a concrete SSH alias or WSL distribution name')
        if node['role'] == 'compute' and (not isinstance(node.get('hostname'), str) or not SAFE_NAME.fullmatch(node['hostname'])):
            raise ValueError('Compute nodes need their exact hostname')
        if not isinstance(node.get('capabilities'), dict) or any(v not in ('unknown', 'available', 'unavailable') for v in node['capabilities'].values()):
            raise ValueError('Capabilities are declarations: unknown / available / unavailable')
    default = nodes.get(config['default_agent'], {})
    if not (config['schema_version'] == 2 and config['default_agent'] is None) and (default.get('role') != 'agent' or not default.get('enabled')):
        raise ValueError('default_agent must be an enabled agent node')
    # Aliases cannot reveal physical co-location; this catches explicit reuse only.
    for name, node in nodes.items():
        for other_name, other in nodes.items():
            def endpoint(n):
                return n['ssh_host'] if n['transport'] == 'ssh' else n['distribution'] if n['transport'] == 'wsl' else 'local'
            def workspace(n):
                return os.path.normcase(str(Path(n['workspace']).resolve())) if n['transport'] == 'local' else posixpath.normpath(n['workspace'])
            if name < other_name and endpoint(node) == endpoint(other) and node['transport'] == other['transport'] and node['role'] != other['role']:
                if node['account'] == other['account'] or workspace(node) == workspace(other):
                    raise ValueError('Co-located roles require distinct accounts AND workspaces')
    return config


def node_for(config, name, role):
    node = config['nodes'].get(name)
    if not node or node['role'] != role or not node['enabled']:
        raise ValueError('Select an enabled '+role+' node')
    if 'REPLACE' in canonical(node).decode():
        raise ValueError('Fill node placeholders in config/hub.local.json before connecting')
    return node


def transport_command(node, argv):
    if node['transport'] == 'ssh':
        return ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
                '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
                node['ssh_host'], shlex.join(argv)]
    if node['transport'] == 'wsl' and os.name == 'nt':
        return ['wsl', '--distribution', node['distribution'], '--user', node['account'], '--exec', *argv]
    return argv


def probe(node):
    source = (ROOT/'scripts/workspace_probe.py').read_text(encoding='utf-8')
    try:
        command = transport_command(node, [node['python'], '-B', '-c', source, node['workspace']])
        result = subprocess.run(command, capture_output=True, timeout=40)
        if result.returncode:
            raise ValueError('Host unavailable, workspace inaccessible or Git/Python missing; check the selected host manually')
        report = parse_json(result.stdout)
        if report.get('schema_version') != 1 or report.get('account') != node['account']:
            raise ValueError('Probe schema/account mismatch; check SSH alias or WSL user')
        if node['transport'] != 'local' and report.get('os') != 'linux':
            raise ValueError('WSL/remote Agent must be Linux')
        expected_path = str(Path(node['workspace']).resolve()) if node['transport'] == 'local' else posixpath.normpath(node['workspace'])
        if report.get('workspace') != expected_path:
            raise ValueError('Workspace real path mismatch; configure the actual directory')
        if tuple(int(v) for v in report['python'].split('.')[:2]) < (3, 10):
            raise ValueError('Agent requires Python 3.10+')
        return report
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError('Agent unavailable: '+type(exc).__name__+'; preserve run IDs and reconcile before migration') from None


def matching(observation, anchor):
    if observation.get('dirty') is not False:
        raise ValueError('Workspace has uncommitted changes; commit/reconcile first')
    if observation.get('commit') != anchor['commit']:
        raise ValueError('Workspace Git version mismatch; stop and reconcile commits')
    if observation.get('origin_sha256') != anchor['origin_sha256']:
        raise ValueError('Repository origin mismatch; use the same reviewed origin URL')


class Hub:
    def __init__(self, root=ROOT, config=None, runtime_root=ROOT):
        from storage_paths import plain_path
        self.runtime_root = plain_path(runtime_root)
        self.coordinator_root = plain_path(root)
        self.root = self.coordinator_root  # Compatibility alias for state/evidence callers.
        self.directory = self.root/'coordination/projects'
        self.store = ProjectStore(self.root)
        if config is None:
            local = self.root/'config/hub.local.json'
            config = read_json(local)[0] if local.exists() else {'schema_version': 2, 'default_agent': None, 'nodes': {}}
        self.config = validate_config(config)

    def path(self, study):
        if not valid_id(study):
            raise ValueError('Study ID must be 3–48 uppercase letters/digits/hyphens')
        path = self.directory/(study+'.json')
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise ValueError('Unsafe project record path')
        return path

    def read(self, study):
        record, raw = self.store.read(study)
        return record, digest(raw)

    def research_path(self, record):
        from study_context import source_path
        return source_path(record, self.root)

    def anchor(self, record=None):
        obs = observe(self.research_path(record) if record is not None else self.root)
        if obs['dirty']:
            raise ValueError('Coordinator Git checkout must be clean; commit reviewed source first')
        return {key: obs[key] for key in ('commit', 'origin_sha256')}

    def init(self, study, goal):
        path = self.path(study)
        with FileLock(self.root/'coordination/projects/.hub.lock'), FileLock(self.directory/(study+'.lock')):
            if path.exists():
                raise ValueError('Project already exists; use show or resume')
            record = self.store.commit(None, self.initial_record(study, goal), 'init', 'Create project')
        return record

    def initial_record(self, study, goal):
        self.path(study)
        if not goal.strip():
            raise ValueError('Research goal is required')
        path = self.path(study)
        agent = self.config['default_agent']
        node_for(self.config, agent, 'agent')
        anchor = self.anchor()
        return {'schema_version': 1, 'study_id': study, 'goal': goal, 'revision': 1,
                'phase': 'evidence', 'created_utc': stamp(), 'updated_utc': stamp(),
                'anchor': anchor, 'active_agent': agent,
                'agent_snapshot': copy.deepcopy(self.config['nodes'][agent]),
                'compute_target': None, 'compute_snapshot': None,
                'references': [], 'runs': {}, 'history': []}

    def mutate(self, study, revision, event, edit):
        path = self.path(study)
        with FileLock(self.root/'coordination/projects/.hub.lock'), FileLock(self.directory/(study+'.lock')):
            record, before = self.read(study)
            if record['schema_version'] != 2:
                raise ValueError('This interface is read-only for this study; use the Operation Service (hub_command.py) for updates. If preparation is required, follow docs/UPGRADE_GUIDE.md')
            self.store.check(study)
            previous_raw = self.store.path(study).read_bytes()
            if record['revision'] != revision:
                raise ValueError('Project revision changed; reread before writing')
            previous = copy.deepcopy(record)
            edit(record)
            if record == previous:
                return record
            record['revision'] += 1
            record['updated_utc'] = stamp()
            record = self.store.commit(previous_raw, record, event, record.get('checkpoint_note') or event)
        return record

    def create_study_record(self, study, goal, research_workspace=None):
        from study_context import extend_record, validate_workspace
        from storage_paths import plain_path
        self.path(study)
        if not isinstance(goal, str) or not goal.strip() or len(goal.encode('utf-8')) > 16000:
            raise ValueError('Use a nonempty research goal within 16000 UTF-8 bytes')
        validate_workspace(research_workspace)
        anchor = None
        if research_workspace is not None:
            folder = research_workspace['primary']
            if folder['host_id'] != 'local':
                raise ValueError('Create without source first or verify a repository on the record host; remote provenance is not inferred')
            location = plain_path(folder['path'])
            if not location.is_dir():
                raise ValueError('Research workspace is not an accessible directory')
            if (location/'.git').exists():
                observation = observe(location)
                if observation['dirty']:
                    raise ValueError('Research source must be clean before registering Git provenance')
                anchor = {k: observation[k] for k in ('commit', 'origin_sha256')}
        agent = self.config['default_agent']
        record = {'schema_version': 4, 'study_id': study, 'goal': goal, 'revision': 1,
            'phase': 'evidence', 'created_utc': stamp(), 'updated_utc': stamp(),
            'anchor': anchor, 'active_agent': agent,
            'agent_snapshot': copy.deepcopy(self.config['nodes'].get(agent, {})),
            'compute_target': None, 'compute_snapshot': None, 'references': [], 'runs': {}, 'history': []}
        return extend_record(record, research_workspace)

    def active(self, record):
        node = node_for(self.config, record['active_agent'], 'agent')
        if node != record['agent_snapshot']:
            raise ValueError('Active Agent configuration changed; restore its recorded configuration and migrate explicitly')
        return node

    def references_ok(self, record):
        refs = list(record['references'])
        for run in record['runs'].values():
            for kind in ('task', 'status'):
                if run.get(kind+'_sha256'):
                    refs.append({'path': run[kind+'_path'], 'sha256': run[kind+'_sha256']})
        for ref in refs:
            if file_hash(self.reference_path(ref['path'])) != ref['sha256']:
                raise ValueError('Recorded reference changed: '+ref['path'])

    def reference_path(self, relative):
        if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative or any(p in ('', '.', '..') for p in relative.split('/')):
            raise ValueError('Use a regular file with a safe repository-relative path')
        path = self.root/relative
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(self.root) or not path.is_file():
            raise ValueError('Reference must stay within the coordinator workspace')
        return path

    def show(self, study):
        record, sha = self.read(study)
        missing = []
        try:
            self.references_ok(record)
            if record['schema_version'] == 4 and record['anchor'] is None:
                missing.append('Source-dependent work requires a reviewed Git research workspace; discussion and literature remain available')
            else:
                self.active(record)
                matching(observe(self.research_path(record)), record['anchor'])
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            missing.append(str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        if record['compute_target'] is None:
            missing.append('Select a compute node separately before preparing an experiment')
        return {'project': record, 'record_sha256': sha, 'phase_name': PHASE_NAMES[record['phase']],
                'agent_connectivity': 'not_checked', 'next_step': NEXT[record['phase']],
                'missing': missing, 'submission': 'human_only', 'auto_submit': False,
                'capacity': {'bytes': self.path(study).stat().st_size, 'limit': PROJECT_LIMIT,
                             'near_capacity': self.path(study).stat().st_size >= PROJECT_LIMIT * .8},
                'history_scope': 'Immutable study snapshots; missing historical notes remain unknown'}

    def resume(self, study):
        result = self.show(study)
        record = result['project']
        # Compute selection is not needed for evidence/review/development.
        self.references_ok(record)
        if record['schema_version'] == 4 and record['anchor'] is None:
            result['note'] = 'Discussion and literature can continue. Source-dependent checkpoints and experiments require a reviewed Git workspace.'
            return result
        matching(observe(self.research_path(record)), record['anchor'])
        obs = probe(self.active(record))
        matching(obs, record['anchor'])
        result['agent_connectivity'] = 'available'
        result['agent_observation'] = obs
        result['note'] = 'Workspace verified. Model authentication, service readiness and unattended execution remain unverified.'
        return result

    def select_agent(self, study, revision, target):
        return self.mutate(study, revision, 'select_agent',
            lambda record: self.edit_select_agent(record, target))

    def edit_select_agent(self, record, target):
        study = record['study_id']
        matching(observe(self.research_path(record)), record['anchor'])
        self.references_ok(record)
        source = self.active(record)
        destination = node_for(self.config, target, 'agent')
        # Both endpoints must be reachable: no silent failover or implicit sync.
        matching(probe(source), record['anchor'])
        if target != record['active_agent']:
            if record['anchor']['origin_sha256'] is None:
                raise ValueError('Set a reviewed origin on every checkout before cross-workspace migration')
            matching(probe(destination), record['anchor'])
            record['active_agent'] = target
            record['agent_snapshot'] = copy.deepcopy(destination)


    def select_compute(self, study, revision, target):
        return self.mutate(study, revision, 'select_compute',
            lambda record: self.edit_select_compute(record, target))

    def edit_select_compute(self, record, target):
        study = record['study_id']
        node = node_for(self.config, target, 'compute')
        record['compute_target'] = target
        record['compute_snapshot'] = copy.deepcopy(node)


    def checkpoint(self, study, revision, phase, note):
        return self.mutate(study, revision, 'checkpoint',
            lambda record: self.edit_checkpoint(record, phase, note))

    def edit_checkpoint(self, record, phase, note):
        study = record['study_id']
        if phase not in PHASES or not note.strip():
            raise ValueError('Choose a phase and write a checkpoint note')
        # This deliberately reanchors a newly reviewed commit on BOTH copies.
        anchor = self.anchor(record)
        if anchor['origin_sha256'] != record['anchor']['origin_sha256']:
            raise ValueError('Checkpoint cannot change repository identity; restore the recorded origin')
        matching(probe(self.active(record)), anchor)
        self.references_ok(record)
        if phase == 'experiment_running' and not record['runs']:
            raise ValueError('Register the existing task/run ID first')
        record['anchor'] = anchor
        record['phase'] = phase
        record['checkpoint_note'] = note


    def attach(self, study, revision, kind, relative, expected):
        return self.mutate(study, revision, 'attach_'+kind,
            lambda record: self.edit_attach(record, kind, relative, expected))

    def edit_attach(self, record, kind, relative, expected):
        study = record['study_id']
        require_hash(expected)
        path = self.reference_path(relative)
        from project_store import bounded_read
        from common import parse_json
        raw = bounded_read(path, 4_000_000)
        value = parse_json(raw) if kind in ('task', 'approval', 'run') else None
        if digest(raw) != expected:
            raise ValueError('Reference checksum mismatch')
        if len(raw) > 4_000_000:
            raise ValueError('Register a small evidence/record file (maximum 4 MB); manage datasets separately')
        snapshot_relative = 'coordination/imports/snapshots/'+expected+'.blob'
        snapshot = self.root/snapshot_relative
        if snapshot.is_symlink() or not snapshot.resolve().is_relative_to(self.root):
            raise ValueError('Unsafe snapshot destination')
        ref = {'kind': kind, 'source_path': relative, 'path': snapshot_relative, 'sha256': expected}
        if kind == 'task':
            self.research_path(record)
            validate_task(value)
            if value['study_id'] != study or value['git_commit'] != record['anchor']['commit']:
                raise ValueError('Task study/commit mismatch')
            node = node_for(self.config, record['compute_target'], 'compute')
            if node != record['compute_snapshot'] or value['target']['node'] != node['hostname']:
                raise ValueError('Task must target the independently selected compute node')
            old = record['runs'].get(value['run_id'])
            if old and old['task_sha256'] != expected:
                raise ValueError('Run ID already reserved with another task; never overwrite')
            if not old:
                record['runs'][value['run_id']] = {'task_sha256': expected, 'task_path': snapshot_relative,
                    'compute_target': record['compute_target'], 'node': node['hostname'],
                    'recorded_status': 'prepared', 'status_sha256': None}
        elif kind in ('approval', 'run'):
            run_id = value.get('run_id') if kind == 'approval' else value.get('task', {}).get('run_id')
            run = record['runs'].get(run_id)
            if not run or value.get('task_sha256') != run['task_sha256']:
                raise ValueError('Record must bind a registered task and run ID')
            if kind == 'approval':
                if (run.get('status_sha256') or run.get('runtime_source') or run['recorded_status'] != 'prepared') and run.get('approval_sha256') != expected:
                    raise ValueError('Approval for an observed run is immutable; reconcile the original run before a new attempt')
                from task_contract import validate_approval
                task = read_json(self.reference_path(run['task_path']), run['task_sha256'])[0]
                approved_at = time_value(value['approved_at_utc'])
                if approved_at > datetime.now(timezone.utc):
                    raise ValueError('Approval cannot be dated in the future')
                # Archiving an expired approval must not turn it into a fresh authorization.
                validate_approval(value, task, run['task_sha256'], run['node'], now=approved_at)
                run['approval_sha256'] = expected
                run['approval_expires_utc'] = value['expires_utc']
            else:
                if value.get('schema_version') != 3 or value.get('host') != run['node'] or not isinstance(value.get('status'), str):
                    raise ValueError('Invalid run state or host; use inspect_run.py on the original node')
                registered_task = read_json(self.reference_path(run['task_path']), run['task_sha256'])[0]
                if canonical(value['task']) != canonical(registered_task):
                    raise ValueError('Run embeds a different task')
                run['recorded_status'] = value['status']
                run['status_sha256'] = expected
                run['status_path'] = snapshot_relative
        if snapshot.exists():
            if file_hash(snapshot) != expected:
                raise ValueError('Immutable snapshot was changed; preserve it for reconciliation')
        else:
            atomic_write(snapshot, raw)
        if ref not in record['references']:
            record['references'].append(ref)


    def step(self, study, action):
        # Fixed safe operations only: no arbitrary shell, approval or submission API.
        result = self.resume(study)
        node = self.active(result['project'])
        if result['project']['schema_version'] == 4 and node['transport'] != 'local':
            raise ValueError('Run the named maintenance tool from the verified OpenSci installation on the target host')
        actions = {'doctor': ['doctor.py', '--profile', 'offline'],
                   'review-plan': ['review_round.py'], 'review-demo': ['review_round.py', '--demo']}
        script, *args = actions[action]
        argv = [node['python'], '-B', str(PurePosixPath(node['workspace'])/'scripts'/script), *args]
        if node['transport'] == 'local':
            argv[2] = str(self.runtime_root/'scripts'/script)
        try:
            completed = subprocess.run(transport_command(node, argv), timeout=60)
        except subprocess.TimeoutExpired:
            raise ValueError('Connection/step timed out; inspect the workspace before retrying (no compute was submitted)') from None
        if completed.returncode:
            raise ValueError('Step failed; inspect its diagnostic output')
        return {'action': action, 'completed': True, 'submitted_experiments': 0}


def display(result):
    record = result['project']
    print('\nStudy: '+record['study_id']+'  '+record['goal'])
    print('Development Workspace: '+record['active_agent']+'  '+record['agent_snapshot']['workspace'])
    print('Planning phase: '+result['phase_name']+'; Execution Node: '+(record['compute_target'] or 'Not selected'))
    print('Next: '+result['next_step'])
    for missing in result['missing']: print('Pending: '+missing)
    for run_id, run in record['runs'].items():
        print('Run: '+run_id+'; Recorded status: '+run['recorded_status']+'; Node: '+run['node'])
    print('Record revision: '+str(record['revision'])+'; Experiments are executed by the human submission account.')


def choose_option(options, title):
    """Display labels while accepting either a numbered choice or a stable API ID."""
    print(title+':')
    for number, (key, label) in enumerate(options, 1):
        print(f'{number} {label} [{key}]')
    answer = input('Enter a number or ID; leave blank to cancel: ').strip()
    if not answer:
        return None
    # Prefer exact IDs: configured node IDs can also consist of digits.
    if answer in dict(options):
        return answer
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer)-1][0]
    raise ValueError('Choose one of the displayed options')


def execute_update(hub, study, revision, operation, arguments, request_id=None, remote_allowed=False, stream=None):
    from command_service import CommandService, Context
    request = {'schema_version': 1, 'request_id': request_id or 'OPENSCI-'+uuid.uuid4().hex,
               'study_id': study, 'expected_revision': revision, 'operation': operation, 'arguments': arguments}
    print('Request ID: '+request['request_id']+'; retain this ID for receipt recovery.', file=stream)
    return CommandService(hub).execute(request, Context.local(allow_remote_checks=remote_allowed))


def menu(hub):
    print(f'OpenSci {VERSION} | Research Workspace\nStudy records have one coordinator; remote connections require an explicit action.')
    try:
        git_ready = subprocess.run(['git', '-C', str(hub.root), 'rev-parse', '--verify', 'HEAD'], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        git_ready = False
    if not git_ready:
        print('Discussion and literature studies can start without Git. Source-dependent checkpoints and experiments require a reviewed research repository.')
    while True:
        print('\n1 Browse Studies\n2 Create Study\n3 Resume Study\n4 Choose Development Workspace\n5 Choose Execution Node\n6 Check Development Environment\n7 Preview Evidence Review\n8 Record Progress\n9 Literature Workspace\n10 Study Overview\n11 Save Discussion Progress\n0 Exit')
        choice = input('Select: ').strip()
        if choice == '0':
            return
        try:
            if choice == '9':
                from command_service import CommandService, Context, validate_request
                service=CommandService(hub)
                action=input('Literature Workspace: type capabilities or enter a request JSON path (relative to the OpenSci folder); blank cancels: ').strip()
                if not action:
                    continue
                request=({'schema_version':1,'request_id':'LIT-'+uuid.uuid4().hex,'study_id':'LIBRARY',
                          'expected_revision':0,'operation':'literature.capabilities','arguments':{'payload':{}}}
                         if action=='capabilities' else read_json(hub.root/Path(action),limit=64000)[0])
                if not isinstance(request, dict) or not str(request.get('operation', '')).startswith('literature.'):
                    raise ValueError('Literature Workspace accepts only literature.* operations; use Research Workspace or the Operation Service for other requests')
                validate_request(request)
                remote_allowed=False
                if request['operation'] in ('literature.job_dispatch','literature.job_import','literature.job_pause','literature.job_resume','literature.job_cancel') or request['arguments'].get('payload',{}).get('refresh'):
                    print('This literature operation may contact the configured executor.')
                    remote_allowed=input('Type yes to connect, or leave blank to retain the local request only: ').strip()=='yes'
                result = service.execute(request,Context.local(allow_remote_checks=remote_allowed))
                if result.get('read_only'):
                    print('Read-only result: committed=false means no study update was requested. Check each capability status below.')
                print_json(result)
                continue
            if choice == '1':
                projects = sorted(hub.directory.glob('*.json')) if hub.directory.exists() else []
                if not projects:
                    print('No studies yet; choose 2 to create one.')
                for path in projects:
                    display(hub.show(path.stem))
                continue
            if choice not in ('2', '3', '4', '5', '6', '7', '8', '10', '11'):
                print('Choose a menu number from 0 to 11.')
                continue
            study = input('Study ID (for example STUDY-001): ').strip()
            if choice == '2':
                goal = input('Research goal: ')
                operation = 'init' if git_ready else 'create_study'
                arguments = {'goal': goal} if git_ready else {'goal': goal, 'research_workspace': None, 'binding': None}
                print_json(execute_update(hub, study, 0, operation, arguments))
                display(hub.show(study))
                continue
            record, raw = hub.store.read(study)
            if choice == '10':
                from study_context import brief
                print_json(brief(record, raw))
                continue
            if choice == '11':
                progress = {'summary': input('Saved summary: ')}
                for field in ('decisions', 'hypotheses', 'evidence_refs', 'open_questions', 'next_steps'):
                    value = input(field.replace('_', ' ').title()+' (one item; blank means none): ').strip()
                    progress[field] = [value] if value else []
                print_json(execute_update(hub, study, record['revision'], 'save_progress', {'progress': progress}))
                continue
            arguments = {}
            if choice in ('4', '5'):
                role, title = ('agent', 'Development Workspace') if choice == '4' else ('compute', 'Execution Node')
                options = [(k, k+' | '+v['transport']+' | '+v['workspace']) for k, v in hub.config['nodes'].items()
                           if v['role'] == role and v['enabled']]
                if not options:
                    print('No enabled '+title+' is configured. Follow Configuration before making this selection; no study was changed.')
                    continue
                target = choose_option(options, title)
                if target is None:
                    continue
                arguments = {'target': target}
            elif choice == '8':
                phase = choose_option(list(PHASE_NAMES.items()), 'Planning phase')
                if phase is None:
                    continue
                arguments = {'phase': phase, 'note': input('Notes and conclusions: ')}
            names = {record['active_agent']}
            if choice == '4':
                names.add(arguments['target'])
            remote_allowed = not (choice == '3' and record['schema_version'] == 4 and record['anchor'] is None) and choice in ('3', '4', '6', '7', '8') and any(
                hub.config['nodes'].get(n, {}).get('transport') != 'local' for n in names)
            if remote_allowed:
                print('The configured WSL or SSH connection will check the Development Workspace or run the selected development step.')
                if input('Type yes to connect: ').strip() != 'yes':
                    continue
            if record['schema_version'] in (3, 4) and choice in ('4', '5', '8'):
                operation = {'4': 'select_agent', '5': 'select_compute', '8': 'checkpoint'}[choice]
                print_json(execute_update(hub, study, record['revision'], operation, arguments, remote_allowed=remote_allowed))
                display(hub.show(study))
                continue
            if choice == '3':
                result = hub.resume(study)
            elif choice == '4':
                result = hub.select_agent(study, record['revision'], arguments['target'])
            elif choice == '5':
                result = hub.select_compute(study, record['revision'], arguments['target'])
            elif choice in ('6', '7'):
                result = hub.step(study, 'doctor' if choice == '6' else 'review-plan')
            else:
                result = hub.checkpoint(study, record['revision'], arguments['phase'], arguments['note'])
            display(result if 'project' in result else hub.show(study))
        except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            from command_service import CommandError, failure
            if isinstance(exc, CommandError):
                print_json(failure(exc))
            else:
                print('Stopped: '+(str(exc) if isinstance(exc, ValueError) else type(exc).__name__))


def main():
    parser = argparse.ArgumentParser(description='OpenSci Research Workspace; never submits experiments')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--coordinator-root', type=Path, default=ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('menu')
    sub.add_parser('list')
    for command in ('init', 'show', 'brief', 'history', 'resume', 'select-agent', 'select-compute', 'checkpoint', 'attach', 'step'):
        p = sub.add_parser(command)
        p.add_argument('--study', required=True)
        if command in ('select-agent', 'select-compute', 'checkpoint', 'attach'):
            p.add_argument('--revision', type=int, required=True)
        if command in ('init', 'select-agent', 'select-compute', 'checkpoint', 'attach'):
            p.add_argument('--request-id', help='Stable operation ID for receipt recovery; generated and printed if omitted')
        if command == 'init': p.add_argument('--goal', required=True)
        if command == 'history':
            p.add_argument('--limit', type=int, default=20)
            p.add_argument('--before-revision', type=int)
        if command in ('select-agent', 'select-compute'): p.add_argument('--target', required=True)
        if command == 'checkpoint':
            p.add_argument('--phase', choices=PHASES, required=True)
            p.add_argument('--note', required=True)
        if command == 'attach':
            p.add_argument('--kind', choices=('evidence', 'review', 'task', 'approval', 'run'), required=True)
            p.add_argument('--path', required=True)
            p.add_argument('--expected-sha256', required=True)
        if command == 'step': p.add_argument('--action', choices=('doctor', 'review-plan', 'review-demo'), required=True)
    args = parser.parse_args()
    try:
        hub = Hub(args.coordinator_root, config=read_json(args.config)[0] if args.config else None)
        if args.command == 'menu':
            menu(hub)
            return 0
        if args.command == 'list':
            result = [hub.show(p.stem) for p in sorted(hub.directory.glob('*.json'))]
        elif args.command == 'init':
            result = execute_update(hub, args.study, 0, 'init', {'goal': args.goal}, args.request_id, stream=sys.stderr)
        elif args.command in ('select-agent', 'select-compute', 'checkpoint', 'attach') and hub.read(args.study)[0]['schema_version'] in (3, 4):
            if args.command in ('select-agent', 'select-compute'):
                arguments = {'target': args.target}
            elif args.command == 'checkpoint':
                arguments = {'phase': args.phase, 'note': args.note}
            else:
                path = (hub.root/args.path).resolve()
                if not path.is_relative_to(hub.root):
                    raise ValueError('Import the file into coordination/imports before registering it')
                arguments = {'kind': args.kind, 'relative': path.relative_to(hub.root).as_posix(), 'expected': args.expected_sha256}
            result = execute_update(hub, args.study, args.revision, args.command.replace('-', '_'), arguments,
                                    args.request_id, remote_allowed=True, stream=sys.stderr)
        elif getattr(args, 'request_id', None):
            raise ValueError('Receipt recovery requires study preparation; follow docs/UPGRADE_GUIDE.md')
        elif args.command in ('show', 'resume'): result = getattr(hub, args.command)(args.study)
        elif args.command == 'brief':
            from project_brief import build_brief
            result = build_brief(hub, args.study)
        elif args.command == 'history': result = hub.store.history(args.study, args.limit, args.before_revision)
        elif args.command in ('select-agent', 'select-compute'):
            result = getattr(hub, args.command.replace('-', '_'))(args.study, args.revision, args.target)
        elif args.command == 'checkpoint': result = hub.checkpoint(args.study, args.revision, args.phase, args.note)
        elif args.command == 'attach': result = hub.attach(args.study, args.revision, args.kind, args.path, args.expected_sha256)
        else: result = hub.step(args.study, args.action)
        print_json(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        from command_service import CommandError, failure
        if isinstance(exc, CommandError):
            print_json(failure(exc))
            return 2
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                    'next': 'Check config, record revision and workspace. Reconcile existing runs before retrying.',
                    'submitted_experiments': 0})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
