"""Native project links are record facts, never connection grants.

The coordinator lock serializes all link mutations. The reverse index is derived
from authoritative heads on demand, so a crash cannot publish a stale index.
"""
import copy
from common import canonical, digest

IDENTITY_FIELDS = {'provider', 'namespace', 'project_id', 'project_type', 'host_id'}
PROJECT_TYPES = ('chatgpt_project', 'local_folder', 'remote_folder')


def text(value, limit=512):
    return isinstance(value, str) and bool(value.strip()) and len(value.encode('utf-8')) <= limit and not any(ord(c) < 32 for c in value)


def validate_identity(value):
    if (not isinstance(value, dict) or set(value) != IDENTITY_FIELDS
            or any(not text(v) for v in value.values()) or value['project_type'] not in PROJECT_TYPES):
        raise ValueError('Use provider, namespace, native project_id, project_type and host_id; names and paths are not identity')
    return value


def key(identity):
    return digest(canonical(validate_identity(identity)))


def validate_binding(value):
    if (not isinstance(value, dict) or set(value) != {'identity', 'display_name', 'availability'}
            or not text(value['display_name']) or value['availability'] not in ('available', 'unavailable', 'unknown')):
        raise ValueError('Invalid project binding')
    validate_identity(value['identity'])
    return value


def index(store):
    result = {}
    directory = store.root/'coordination/projects'
    for path in sorted(directory.glob('*.json')):
        record, _ = store.read(path.stem)
        for binding in record.get('project_bindings', []):
            identity = key(binding['identity'])
            if identity in result:
                raise ValueError('Ambiguous project binding; reconcile authoritative records before writing')
            result[identity] = {'study_id': record['study_id'], 'binding': copy.deepcopy(binding)}
    return result


def bind(record, binding, store):
    validate_binding(binding)
    identity = key(binding['identity'])
    existing = index(store).get(identity)
    if existing and existing['study_id'] != record['study_id']:
        raise ValueError('Project already linked to another study; unlink there with its own receipt first')
    links = record['project_bindings']
    for pos, item in enumerate(links):
        if key(item['identity']) == identity:
            links[pos] = copy.deepcopy(binding)
            return
    if len(links) >= 100:
        raise ValueError('Study link capacity reached')
    links.append(copy.deepcopy(binding))
    links.sort(key=lambda item: key(item['identity']))


def unbind(record, identity):
    target = key(identity)
    record['project_bindings'] = [b for b in record['project_bindings'] if key(b['identity']) != target]


def resolve(store, studies, identity=None):
    if identity is None:
        if len(studies) != 1:
            return {'status': 'selection_required', 'study_id': None, 'reason': 'Trusted native project context is unavailable'}
        store.read(studies[0])
        return {'status': 'explicit_single_study', 'study_id': studies[0], 'native_project_identity': 'unknown'}
    value = index(store).get(key(identity))
    if value is None or value['study_id'] not in studies:
        return {'status': 'unlinked_or_inaccessible', 'study_id': None}
    return {'status': 'linked' if value['binding']['availability'] == 'available' else 'unavailable', **value}
