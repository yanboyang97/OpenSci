"""Literature Workspace contracts. Research data never supplies caller authority."""
import copy
import re
from urllib.parse import urlsplit
from common import canonical, digest, require_hash

SCHEMA_VERSION = 1
KEY = re.compile(r'[A-Z0-9]{8}')
IDENTIFIER = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,79}')
READ_OPERATIONS = {'literature.capabilities', 'literature.get', 'literature.search_library',
                   'literature.job_status'}
OPERATIONS = READ_OPERATIONS | {'literature.search', 'literature.collect', 'literature.organize',
    'literature.read', 'literature.analyze', 'literature.cite', 'literature.export',
    'literature.preview_change', 'literature.apply_change', 'literature.config_update',
    'literature.bind_study', 'literature.job_pause', 'literature.job_resume', 'literature.job_cancel'}
OPERATIONS |= {'literature.job_dispatch','literature.job_import'}
OPERATIONS |= {'literature.search_import'}
OPERATIONS |= {'literature.fetch_fulltext'}
OPERATIONS |= {'literature.reconcile'}
AGENT_OPERATIONS = OPERATIONS - {'literature.config_update', 'literature.apply_change'}
SOURCE_IDS = ('web_of_science', 'scopus', 'pubmed', 'ieee', 'google_scholar')
STATES = {'queued', 'running', 'waiting_local', 'waiting_user', 'waiting_budget', 'paused',
          'succeeded', 'partial', 'failed', 'cancelled'}

class LiteratureError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

def fail(code, message):
    raise LiteratureError(code, message)

def exact(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value)-set(required)-set(optional):
        fail('invalid_request', 'Unexpected or missing literature fields')
    return value

def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        fail('invalid_request', 'Invalid literature identifier')
    return value

def item_key(value):
    if not isinstance(value, str) or not KEY.fullmatch(value):
        fail('invalid_request', 'Expected an eight-character Zotero key')
    return value

def item_ref(value):
    exact(value, ('binding_id', 'item_key'))
    identifier(value['binding_id']); item_key(value['item_key'])
    return value

def bounded_text(value, maximum=16000, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or len(value.encode('utf-8')) > maximum:
        fail('invalid_request', 'Expected bounded text')
    return value

def integer(value, minimum=0, maximum=100000000):
    if type(value) is not int or not minimum <= value <= maximum:
        fail('invalid_request', 'Integer is outside its permitted range')
    return value

def no_secrets(value):
    """Reject credential material, authority claims and executable request fields."""
    forbidden = {'api_key', 'apikey', 'password', 'secret', 'token', 'cookie', 'authorization',
                 'shell', 'script', 'command', 'principal', 'role'}
    if isinstance(value, dict):
        if any(k.lower() in forbidden for k in value):
            fail('invalid_request', 'Secrets, caller identities and executable fields are not literature data')
        for v in value.values(): no_secrets(v)
    elif isinstance(value, list):
        for v in value: no_secrets(v)

def default_config():
    source_names = ('Web of Science', 'Scopus', 'PubMed', 'IEEE Xplore', 'Google Scholar')
    return {'schema_version': 1, 'revision': 0,
        'research': {'directions': [],
                     'sources': [{'id': i, 'name': n, 'enabled': True, 'adapter': i,
                                  'access_mode': 'browser' if i == 'google_scholar' else 'api',
                                  'credential_ref': None, 'rate_limit': 1.0,
                                  'capabilities': []} for i, n in zip(SOURCE_IDS, source_names)]},
        'browser': {'preferred': 'edge'},
        'zotero': {'base_url': 'http://127.0.0.1:23119', 'binding_id': None, 'instance_id': None,
                   'user_id': None, 'credential_ref': None, 'allow_authorization_prompt': False,
                   'allowed_operations': []},
        'execution': {'node_ref': None, 'timeout_seconds': 300, 'max_retries': 0},
        'models': {'provider_ref': None},
        'limits': {'max_requests': None, 'max_tokens': None, 'max_cost_usd': None,
                   'concurrency': None, 'node_concurrency': None, 'model_concurrency': None,
                   'study_concurrency': None},
        'accounting': {'period_id': None,'max_requests': None,'max_tokens': None,'max_cost_usd': None},
        'grants': {}, 'retention': {'unreferenced_cache_days': 30}}

def validate_config(cfg):
    exact(cfg, default_config())
    if cfg['schema_version'] != 1: fail('unsupported_schema', 'Unsupported Literature Workspace configuration; use the supplied example')
    integer(cfg['revision'])
    exact(cfg['research'], ('directions', 'sources'))
    for name, required in (('directions', ('id','name','keywords','exclude','enabled')),
                           ('sources', ('id','name','enabled','adapter','access_mode','credential_ref','rate_limit','capabilities'))):
        rows = cfg['research'][name]
        if not isinstance(rows, list) or len(rows) > 100: fail('invalid_request', 'Bounded research settings required')
        seen = set()
        for row in rows:
            exact(row, required); identifier(row['id']); bounded_text(row['name'], 200)
            if row['id'] in seen or type(row['enabled']) is not bool: fail('invalid_request', 'Duplicate ID or invalid enabled flag')
            seen.add(row['id'])
            for field in ('keywords','exclude') if name == 'directions' else ('capabilities',):
                if not isinstance(row[field], list) or len(row[field]) > 100: fail('invalid_request', 'Expected bounded list')
                for v in row[field]: bounded_text(v, 500)
            if name == 'sources':
                identifier(row['adapter'])
                if row['access_mode'] not in ('api', 'browser', 'import'): fail('invalid_request', 'Unknown access mode')
                if type(row['rate_limit']) not in (int,float) or not 0 < row['rate_limit'] <= 10: fail('invalid_request', 'Invalid source rate')
                credential_ref(row['credential_ref'])
    exact(cfg['browser'], ('preferred',))
    if cfg['browser']['preferred'] not in ('edge','chrome'): fail('invalid_request', 'Choose Edge or Chrome')
    z = cfg['zotero']; exact(z, default_config()['zotero'])
    url = urlsplit(z['base_url'])
    if (url.scheme != 'http' or url.hostname not in ('127.0.0.1','localhost','::1')
            or url.port != 23119 or url.path not in ('','/') or url.query or url.fragment or url.username or url.password):
        fail('invalid_request', 'Zotero must remain on the local loopback port 23119')
    for k in ('binding_id','instance_id'):
        if z[k] is not None: bounded_text(z[k], 100)
    if (z['binding_id'] is None) != (z['instance_id'] is None): fail('invalid_request', 'Bind identity and instance together')
    if z['binding_id'] is not None: identifier(z['binding_id'])
    if z['user_id'] is not None: integer(z['user_id'])
    credential_ref(z['credential_ref'],native=True)
    if type(z['allow_authorization_prompt']) is not bool: fail('invalid_request', 'Explicit authorization-prompt setting required')
    if not isinstance(z['allowed_operations'], list) or set(z['allowed_operations'])-{'create','update','delete','annotation'}:
        fail('invalid_request', 'Unknown Zotero write capability')
    exact(cfg['models'], ('provider_ref',))
    if cfg['models']['provider_ref'] is not None: identifier(cfg['models']['provider_ref'])
    exact(cfg['execution'], ('node_ref','timeout_seconds','max_retries'))
    if cfg['execution']['node_ref'] is not None: identifier(cfg['execution']['node_ref'])
    integer(cfg['execution']['timeout_seconds'], 1, 3600); integer(cfg['execution']['max_retries'], 0, 10)
    exact(cfg['limits'], default_config()['limits'])
    for k,v in cfg['limits'].items():
        if v is None: continue
        if k == 'max_cost_usd':
            if type(v) not in (int,float) or not 0 < v <= 100000: fail('invalid_request', 'Finite positive cost limit required')
        else: integer(v, 1, 100000000)
    exact(cfg['accounting'], default_config()['accounting'])
    if cfg['accounting']['period_id'] is not None: identifier(cfg['accounting']['period_id'])
    for k,v in cfg['accounting'].items():
        if k=='period_id' or v is None: continue
        if k=='max_cost_usd':
            if type(v) not in (int,float) or not 0 < v <= 100000: fail('invalid_request','Finite period cost limit required')
        else: integer(v,1)
    if not isinstance(cfg['grants'], dict): fail('invalid_request', 'Grant mapping required')
    for study, grant in cfg['grants'].items():
        identifier(study); exact(grant, ('operations','item_keys','collection_keys'), ('manuscript_paths',))
        if not isinstance(grant['operations'], list) or set(grant['operations']) - AGENT_OPERATIONS: fail('forbidden','Invalid delegated operation')
        for k in ('item_keys','collection_keys'):
            if not isinstance(grant[k], list): fail('invalid_request','Grant targets must be lists')
            for v in grant[k]: item_key(v)
        if 'manuscript_paths' in grant:
            from storage_paths import safe_name
            if not isinstance(grant['manuscript_paths'],list): fail('invalid_request','Manuscript grants must be a list')
            for value in grant['manuscript_paths']:
                safe_name(value)
                if not value.startswith('manuscript/'): fail('invalid_request','Manuscript grant must name a manuscript file')
    exact(cfg['retention'], ('unreferenced_cache_days',)); integer(cfg['retention']['unreferenced_cache_days'], 1, 36500)
    no_secrets(cfg)
    return cfg

def credential_ref(value,native=False):
    pattern=r'env:[A-Z][A-Z0-9_]{0,100}'
    if native: pattern+='|wincred:OpenSci/Zotero/[A-Za-z0-9_.-]{1,80}'
    if value is not None and (not isinstance(value, str) or not re.fullmatch(pattern,value)):
        fail('invalid_request', 'Use an environment reference or a named Windows Zotero grant')

def effective_config(global_config, binding, overrides=None):
    cfg = copy.deepcopy(binding['pinned_config'] if binding.get('config_mode') == 'pinned' else global_config)
    # Pinning research settings never raises current global spending ceilings.
    # Started jobs keep their already frozen reservation; new jobs use the current
    # accounting period and the smaller global/study allowance.
    cfg['accounting']=copy.deepcopy(global_config['accounting'])
    for key,ceiling in global_config['limits'].items():
        if ceiling is not None: cfg['limits'][key]=ceiling if cfg['limits'][key] is None else min(ceiling,cfg['limits'][key])
    # Write authority is always current protected policy, never inherited from an old task snapshot.
    cfg.pop('grants', None)
    cfg['zotero'].pop('allowed_operations', None)
    cfg['zotero'].pop('allow_authorization_prompt', None)
    if overrides:
        exact(overrides, (), ('browser','limits'))
        if 'browser' in overrides:
            if overrides['browser'] not in ('edge','chrome'): fail('invalid_request','Unknown browser')
            cfg['browser']['preferred'] = overrides['browser']
        for key, value in overrides.get('limits', {}).items():
            if key not in cfg['limits']: fail('invalid_request','Unknown budget dimension')
            if key == 'max_cost_usd':
                if type(value) not in (int,float) or not 0 < value <= 100000: fail('invalid_request','Invalid cost limit')
            else: integer(value, 1)
            previous = cfg['limits'][key]
            cfg['limits'][key] = value if previous is None else min(previous, value)
    return cfg

def snapshot_id(manifest):
    return digest(canonical({k:v for k,v in manifest.items() if k != 'snapshot_id'}))

def validate_snapshot(manifest):
    exact(manifest, ('schema_version','snapshot_id','binding_id','instance_id','created_utc','items','files','coverage'))
    if manifest['schema_version'] != 1 or snapshot_id(manifest) != manifest['snapshot_id']:
        fail('invalid_snapshot','Evidence manifest checksum mismatch')
    require_hash(manifest['snapshot_id']); identifier(manifest['binding_id'])
    for row in manifest['files']:
        exact(row, ('path','sha256','bytes')); require_hash(row['sha256']); integer(row['bytes'])
    return manifest
