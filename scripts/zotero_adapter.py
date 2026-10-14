"""Zotero 10 local API adapter: loopback only, personal library, version preconditions.

No database writes, arbitrary routes, scripts, proxy forwarding or credential logs.
"""
import json
import os
import socket
import hashlib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from common import canonical, digest, parse_json, stamp
from literature_contract import LiteratureError, fail, item_key, validate_config, default_config

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class ZoteroClient:
    def __init__(self, settings, transport=None):
        cfg = default_config(); cfg['zotero'] = settings
        validate_config(cfg)
        self.settings = settings.copy()
        self.instance = settings['instance_id']
        self.key = None
        self.single_use_key = False
        self.transport = transport
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def _send(self, method, route, data=None, headers=None, timeout=15):
        if not route.startswith('/api/') or '..' in route or '\\' in route:
            fail('invalid_request','Invalid fixed API route')
        body = None if data is None else data if isinstance(data, bytes) else canonical(data)
        headers = {'Zotero-API-Version':'3', **({'Content-Type':'application/json'} if body is not None else {}), **(headers or {})}
        if self.instance: headers['Zotero-Server-ID'] = self.instance
        if method != 'GET' and self.key: headers['Zotero-API-Key'] = self.key
        if self.transport:
            status, response_headers, raw = self.transport(method, route, body, headers)
        else:
            request = urllib.request.Request(self.settings['base_url'].rstrip('/')+route, data=body, headers=headers, method=method)
            try:
                with self.opener.open(request, timeout=timeout) as response:
                    status, response_headers, raw = response.status, dict(response.headers), response.read(32000001)
            except urllib.error.HTTPError as exc:
                status, response_headers, raw = exc.code, dict(exc.headers), exc.read(64000)
            except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
                fail('waiting_local' if method == 'GET' else 'outcome_unknown', 'Zotero connection interrupted; retain the operation ID')
        response_headers = {k.lower():v for k,v in response_headers.items()}
        server = response_headers.get('zotero-server-id')
        if server and self.instance and server != self.instance:
            fail('instance_changed','Zotero database changed; reconcile before rebinding')
        if status == 412: fail('version_conflict','Zotero instance or object version changed; reread before applying')
        if status in (401,403): fail('authorization_required' if method != 'GET' else 'local_api_disabled','Zotero authorization or local communication is unavailable')
        if status == 404: fail('not_found','Zotero object does not exist')
        if status == 429: fail('rate_limited','Zotero is rate limited; retry later with the same operation')
        if not 200 <= status < 300:
            fail('outcome_unknown' if method != 'GET' and status >= 500 else 'api_rejected', 'Zotero returned HTTP '+str(status))
        if len(raw) > 32000000: fail('response_too_large','Zotero response exceeded the bounded reader')
        return raw, response_headers

    def probe(self):
        raw, headers = self._send('GET','/api/')
        server = headers.get('zotero-server-id')
        if headers.get('zotero-api-version') != '3' or not server:
            fail('unsupported_version','Zotero 10 API v3 with server identity is required')
        if self.instance is None: self.instance = server
        return {'schema_version':1, 'instance_id':server, 'api_version':3,
                'zotero_version':headers.get('zotero-version'), 'checked_utc':stamp(),
                'read':'available', 'write':'not_verified', 'personal_library_only':True}

    def authorize(self):
        self.probe()
        ref = self.settings['credential_ref']
        if ref and ref.startswith('env:') and os.environ.get(ref[4:]): self.key = os.environ[ref[4:]]; return
        if ref and ref.startswith('wincred:'):
            from literature_credentials import read
            self.key=read(ref,self.instance)
            if self.key: return
        if not self.settings['allow_authorization_prompt']:
            fail('authorization_required','Enable the operator-owned local authorization prompt or supply a credential reference')
        try:
            raw, _ = self._send('POST','/api/local/authorize', {'appName':'OpenSci'}, timeout=60)
        except LiteratureError as exc:
            # No object-write request has been sent. An unanswered permission
            # prompt must not strand a create intent as a possibly committed item.
            if exc.code == 'outcome_unknown':
                fail('authorization_required','Zotero authorization timed out before any object write')
            raise
        result = parse_json(raw)
        key = result.get('key')
        if not isinstance(key,str) or len(key) != 32: fail('authorization_required','No valid local write grant returned')
        self.key = key  # Never serialized into configuration, snapshots or receipts.
        self.single_use_key = not result.get('remember',False)
        if not self.single_use_key and ref and ref.startswith('wincred:'):
            from literature_credentials import write
            write(ref,self.instance,key)

    def _write(self, method, route, data, headers):
        if not self.instance: self.probe()
        if not self.key: self.authorize()
        try:
            result=self._send(method, route, data, headers)
            if self.single_use_key: self.key=None
            return result
        except LiteratureError as exc:
            if exc.code != 'authorization_required': raise
            self.key = None
            ref=self.settings['credential_ref']
            if ref and ref.startswith('wincred:'):
                from literature_credentials import forget
                forget(ref,self.instance)
            # No automatic re-prompt/retry; one-use grants can expire and users can revoke grants.
            raise

    def _personal(self, rows):
        for row in rows if isinstance(rows,list) else [rows]:
            lib = row.get('library',{})
            if lib.get('type') != 'user': fail('forbidden','Only personal-library objects are permitted')
            expected = self.settings['user_id']
            if expected is not None and lib.get('id') != expected:
                fail('instance_changed','Personal account identity changed; reconcile binding')
        return rows

    def list(self, kind='items', query=None):
        if kind not in ('items','collections','tags','deleted'): fail('invalid_request','Unsupported read kind')
        query = dict(query or {})
        if set(query)-{'q','qmode','since','itemKey','itemType','collectionKey','format','include','start','limit','sort','direction'}:
            fail('invalid_request','Unsupported Zotero query fields')
        route = '/api/users/0/'+kind
        if query.get('format') in ('versions','keys'):
            raw,headers=self._send('GET',route+'?'+urllib.parse.urlencode(query))
            return (raw.decode().splitlines() if query['format']=='keys' else parse_json(raw)),headers
        query.setdefault('limit',100)
        results, start = [], 0
        while True:
            query['start'] = start
            raw, headers = self._send('GET',route+'?'+urllib.parse.urlencode(query))
            rows = parse_json(raw)
            if not isinstance(rows,list): return rows, headers
            if kind in ('items','collections'): self._personal(rows)
            results.extend(rows)
            if len(results)>100000: fail('response_too_large','Library exceeds configured reader capacity')
            if len(rows)<query['limit']: return results, headers
            start += len(rows)

    def inventory(self):
        """Isolate per-object serialization failures without silently dropping coverage."""
        versions, headers=self.list('items',{'format':'versions'})
        rows=[]; failures=[]
        def batch(keys):
            if not keys: return
            try:
                raw,_=self._send('GET','/api/users/0/items?itemKey='+','.join(keys))
                rows.extend(x for x in self._personal(parse_json(raw)) if x['key'] in keys)
            except LiteratureError as exc:
                if exc.code!='api_rejected': raise
                if len(keys)==1: failures.append({'item_key':keys[0],'status':exc.code,'reason':str(exc)}); return
                middle=len(keys)//2; batch(keys[:middle]); batch(keys[middle:])
        keys=list(versions)
        for start in range(0,len(keys),50): batch(keys[start:start+50])
        rows=list({x['key']:x for x in rows}.values())
        actual={x['key'] for x in rows}
        failed={x['item_key'] for x in failures}
        for key in set(keys)-actual-failed:
            try: rows.append(self.get(key))
            except LiteratureError as exc: failures.append({'item_key':key,'status':exc.code,'reason':str(exc)})
        current,_=self.list('items',{'format':'versions'})
        return {'items':rows,'failures':failures,'declared_count':len(keys),'returned_count':len(rows),
                'complete':not failures and current==versions,'changed_during_read':current!=versions,
                'library_version':headers.get('last-modified-version'),'checked_utc':stamp()}

    def get(self, key, kind='items'):
        item_key(key)
        if kind not in ('items','collections'): fail('invalid_request','Unknown object type')
        raw, _ = self._send('GET','/api/users/0/'+kind+'/'+key)
        row=self._personal(parse_json(raw))
        if row.get('key')!=key: fail('invalid_response','Zotero returned a different object than requested')
        return row

    def children(self, key):
        item_key(key)
        raw, _ = self._send('GET','/api/users/0/items/'+key+'/children')
        return self._personal(parse_json(raw))

    def collection_items(self, key):
        self.get(key,'collections')
        rows, start = [], 0
        while True:
            raw, _ = self._send('GET','/api/users/0/collections/'+key+'/items?limit=100&start='+str(start))
            batch = self._personal(parse_json(raw)); rows.extend(batch)
            if len(batch)<100: return rows
            start += len(batch)

    def fulltext(self, key):
        self.get(key)
        raw, _ = self._send('GET','/api/users/0/items/'+key+'/fulltext')
        return parse_json(raw)

    def attachment_path(self, key):
        row = self.get(key)
        if row['data'].get('itemType') != 'attachment': fail('invalid_request','Not an attachment')
        raw, _ = self._send('GET','/api/users/0/items/'+key+'/file/view/url')
        url = urllib.parse.urlsplit(raw.decode('utf-8').strip())
        if url.scheme != 'file' or url.netloc not in ('','localhost'): fail('invalid_attachment','Expected a local attachment file URL')
        path = Path(urllib.request.url2pathname(url.path))
        if not path.is_file(): fail('fulltext_missing','Zotero attachment is missing on this machine')
        return path

    def create(self, kind, data, operation_token):
        if 'create' not in self.settings['allowed_operations']: fail('forbidden','Zotero create permission not enabled')
        if kind not in ('items','collections'): fail('invalid_request','Unsupported creation kind')
        item_key(data['key'])
        # A supplied key needs version 0 in the local API. Never let POST silently
        # become a PATCH of an unrelated pre-existing object with the same key.
        try: self.get(data['key'],kind)
        except LiteratureError as exc:
            if exc.code != 'not_found': raise
        else: fail('version_conflict','Creation key already exists; reconcile the original intent')
        raw, _ = self._write('POST','/api/users/0/'+kind,[{**data,'version':0}], {'Zotero-Write-Token':operation_token[:32]})
        result = parse_json(raw)
        if result.get('failed'):
            codes=sorted({str(v.get('code','unknown')) for v in result['failed'].values()})
            # Serialization itself can fail after saveTx. A per-object failure is
            # not proof that nothing committed; the durable intent must reconcile.
            fail('outcome_unknown','Zotero object response failed (codes '+','.join(codes)+'); reconcile the deterministic key')
        saved = self.get(data['key'],kind)
        return saved

    def update(self, kind, key, version, patch):
        if 'update' not in self.settings['allowed_operations']: fail('forbidden','Zotero update permission not enabled')
        if kind not in ('items','collections'): fail('invalid_request','Unsupported update kind')
        self.get(key,kind)
        self._write('PATCH','/api/users/0/'+kind+'/'+item_key(key),patch,{'If-Unmodified-Since-Version':str(version)})
        return self.get(key,kind)

    def delete(self, kind, key, version):
        if 'delete' not in self.settings['allowed_operations']: fail('forbidden','Zotero delete permission not enabled')
        self.get(key,kind)
        self._write('DELETE','/api/users/0/'+kind+'/'+item_key(key),None,{'If-Unmodified-Since-Version':str(version)})
        try: self.get(key,kind)
        except LiteratureError as exc:
            if exc.code == 'not_found': return {'key':key,'deleted':True,'base_version':version}
            raise
        fail('outcome_unknown','Deletion postcondition was not established')

    def upload_pdf(self,key,raw,filename):
        if 'create' not in self.settings['allowed_operations']: fail('forbidden','Attachment creation is not enabled')
        item_key(key)
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:] or len(raw)>256000000:
            fail('invalid_pdf','Only bounded complete PDF bytes can be uploaded')
        if '/' in filename or '\\' in filename or not filename.lower().endswith('.pdf'):
            fail('invalid_request','Attachment filename must be a PDF basename')
        row=self.get(key)
        if row['data'].get('itemType')!='attachment' or row['data'].get('linkMode') not in ('imported_url','imported_file'):
            fail('invalid_request','Upload requires a Zotero-managed attachment object')
        md5=hashlib.md5(raw).hexdigest()
        if row['data'].get('md5')==md5: return row
        if row['data'].get('md5'): fail('version_conflict','Existing attachment content will not be overwritten')
        route='/api/users/0/items/'+key+'/file'
        headers={'Content-Type':'application/x-www-form-urlencoded','If-None-Match':'*'}
        params=urllib.parse.urlencode({'md5':md5,'filename':filename,'filesize':len(raw),'mtime':0}).encode()
        response,_=self._write('POST',route,params,headers); upload=parse_json(response)
        if not upload.get('exists'):
            target=urllib.parse.urlsplit(upload['url']); base=urllib.parse.urlsplit(self.settings['base_url'])
            if target.scheme!='http' or target.hostname not in ('localhost','127.0.0.1','::1') or target.port!=base.port or not target.path.startswith('/api/local/uploads/') or target.query or target.fragment:
                fail('invalid_response','Zotero returned an unsafe upload URL')
            self._send('POST',target.path,raw,{'Content-Type':upload['contentType']})
            self._write('POST',route,urllib.parse.urlencode({'upload':upload['uploadKey']}).encode(),headers)
        saved=self.get(key)
        if saved['data'].get('md5')!=md5: fail('outcome_unknown','Uploaded attachment checksum has not been confirmed')
        return saved
