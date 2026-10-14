"""Offline extension-contract demonstrator, separated from real experiment tasks.

No network, shell commands, licenses, approval files or real scientific results.
Submit persists a queued request and returns immediately. advance runs bounded
pure-Python fixture work; it is an explicit test worker, not a resident service.
"""
import argparse
import copy
import inspect
from pathlib import Path

from common import FileLock, canonical, create_json, digest, file_hash, print_json, read_json, stamp, valid_id, write_json
from simulation_adapters import REGISTRY
from storage_paths import plain_path

TYPE = 'opensci_simulation_request'


def adapter_identity(name):
    if name not in REGISTRY:
        raise ValueError('Adapter is not in the reviewed simulation registry')
    adapter = REGISTRY[name]
    if adapter.api_version != 1:
        raise ValueError('Unsupported simulation adapter interface')
    return {'name': name, 'api_version': adapter.api_version, 'version': adapter.version,
            'source_sha256': file_hash(inspect.getfile(type(adapter))), 'engine_sha256': file_hash(Path(__file__))}


def prepare(name, parameters):
    identity = adapter_identity(name)
    parameters = REGISTRY[name].prepare(parameters)
    return {'schema_version': 1, 'record_type': TYPE, 'adapter': identity, 'parameters': parameters,
            'simulation_only': True, 'execution_approval': None}


def validate_request(request):
    if (not isinstance(request, dict) or set(request) != {'schema_version', 'record_type', 'adapter', 'parameters', 'simulation_only', 'execution_approval'}
            or request['schema_version'] != 1 or request['record_type'] != TYPE
            or request['simulation_only'] is not True or request['execution_approval'] is not None):
        raise ValueError('Only isolated simulation requests are accepted')
    name = request['adapter']['name']
    if request['adapter'] != adapter_identity(name):
        raise ValueError('Simulation adapter or engine changed; prepare a new request')
    if canonical(REGISTRY[name].prepare(request['parameters'])) != canonical(request['parameters']):
        raise ValueError('Parameters differ from prepared inputs')
    return REGISTRY[name]


class SimulationRunner:
    def __init__(self, store):
        self.store = plain_path(Path(store)/'simulation-runs')

    def path(self, key):
        if not valid_id(key):
            raise ValueError('Use a unique simulation ID with 3..48 uppercase letters, digits or hyphens')
        return plain_path(self.store/key)

    def lock(self, key):
        self.path(key)  # Validate before FileLock can create directories or files.
        return FileLock(plain_path(self.store/(key+'.lock')))

    def submit(self, request, key):
        validate_request(request)
        root = self.path(key)
        checksum = digest(canonical(request))
        with self.lock(key):
            if root.exists():
                state = self.query(key)
                if state['request_sha256'] != checksum:
                    raise ValueError('Simulation ID already binds different input')
                return state
            root.mkdir(parents=True, exist_ok=False)
            write_json(root/'request.json', request)
            state = {'schema_version': 1, 'record_type': 'opensci_simulation_status', 'simulation_only': True,
                     'simulation_id': key, 'request_sha256': checksum, 'status': 'queued', 'updated_utc': stamp(),
                     'submitted_real_experiments': 0}
            write_json(root/'state.json', state)
            return state

    def query(self, key):
        root = self.path(key)
        state = read_json(root/'state.json')[0]
        if (state.get('record_type') != 'opensci_simulation_status' or state.get('schema_version') != 1
                or state.get('simulation_only') is not True or state.get('simulation_id') != key
                or state.get('status') not in ('queued', 'running', 'finished', 'completed', 'cancelled', 'failed', 'failed_validation')):
            raise ValueError('Invalid simulation state; reconcile without resubmission')
        request = read_json(root/'request.json', state['request_sha256'])[0]
        validate_request(request)
        return state

    def advance(self, key):
        with self.lock(key):
            state = self.query(key)
            if state['status'] == 'running':
                raise ValueError('Interrupted simulation is not automatically rerun; inspect it and choose a new ID')
            if state['status'] != 'queued':
                return state
            root = self.path(key)
            request = read_json(root/'request.json', state['request_sha256'])[0]
            state.update(status='running', updated_utc=stamp())
            write_json(root/'state.json', state)
            try:
                result = validate_request(request).execute(copy.deepcopy(request['parameters']))
                write_json(root/'result.json', result)
                state.update(status='finished', result_sha256=file_hash(root/'result.json'))
            except Exception as exc:
                state.update(status='failed', error_type=type(exc).__name__)
            state['updated_utc'] = stamp()
            write_json(root/'state.json', state)
            return state

    def cancel(self, key):
        with self.lock(key):
            state = self.query(key)
            if state['status'] == 'running':
                raise ValueError('Running/interrupted work needs reconciliation; no process-kill claim')
            if state['status'] == 'queued':
                state.update(status='cancelled', updated_utc=stamp())
                write_json(self.path(key)/'state.json', state)
            return state

    def collect(self, key):
        state = self.query(key)
        if state['status'] not in ('finished', 'completed'):
            raise ValueError('No complete fixture output to collect')
        result = read_json(self.path(key)/'result.json', state['result_sha256'])[0]
        return {'simulation_id': key, 'simulation_only': True, 'result': result,
                'result_sha256': state['result_sha256'], 'scientific_validity': 'not_assessed'}

    def validate(self, key):
        with self.lock(key):
            state = self.query(key)
            result = self.collect(key)['result']
            request = read_json(self.path(key)/'request.json', state['request_sha256'])[0]
            ok = validate_request(request).validate(request['parameters'], result)
            state.update(status='completed' if ok else 'failed_validation', updated_utc=stamp(),
                         fixture_validation=bool(ok), scientific_validity='not_assessed')
            write_json(self.path(key)/'state.json', state)
            return state


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    pre = sub.add_parser('preflight'); pre.add_argument('--adapter', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--adapter', required=True)
    prep.add_argument('--parameters', type=Path, required=True); prep.add_argument('--output', type=Path, required=True)
    submit = sub.add_parser('submit'); submit.add_argument('--request', type=Path, required=True)
    submit.add_argument('--expected-sha256', required=True); submit.add_argument('--id', required=True)
    for name in ('query', 'advance', 'cancel', 'collect', 'validate'):
        command = sub.add_parser(name); command.add_argument('--id', required=True)
    args = p.parse_args()
    try:
        if args.command == 'preflight':
            result = {'adapter': adapter_identity(args.adapter), 'simulation_only': True, 'professional_tools_checked': False}
        elif args.command == 'prepare':
            request = prepare(args.adapter, read_json(args.parameters)[0]); create_json(args.output, request)
            result = {'request': str(args.output), 'sha256': file_hash(args.output), 'simulation_only': True}
        else:
            if not args.store:
                raise ValueError('--store is required for persistent simulation state')
            runner = SimulationRunner(args.store)
            result = (runner.submit(read_json(args.request, args.expected_sha256)[0], args.id) if args.command == 'submit'
                      else getattr(runner, args.command)(args.id))
        print_json(result); return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__, 'submitted_real_experiments': 0})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
