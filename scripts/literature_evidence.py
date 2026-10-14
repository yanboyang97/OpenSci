"""Immutable evidence and a rebuildable local index, separate from Zotero storage."""
import importlib.metadata
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from common import atomic_write, canonical, digest, stamp
from literature_contract import fail, snapshot_id, validate_snapshot
from literature_store import LiteratureStore
from storage_paths import plain_path, safe_name

def parse_pdf(path):
    path=Path(path)
    if path.stat().st_size > 256_000_000: fail('attachment_too_large','PDF exceeds local parser limit')
    raw=path.read_bytes()
    if len(raw)<32 or not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:]:
        fail('invalid_pdf','Attachment is not a complete PDF; HTML and broken downloads are rejected')
    result={'sha256':digest(raw),'bytes':len(raw),'parser':'PyMuPDF','pages':[], 'failed_pages':[],
            'status':'unparsed','ocr':'not_run','coverage':'none'}
    try: import fitz
    except ImportError:
        result.update(status='parser_unavailable',reason='Install a reviewed local PDF parser before full-text acceptance'); return result
    result['parser_version']=importlib.metadata.version('PyMuPDF')
    try:
        with fitz.open(stream=raw,filetype='pdf') as doc:
            if doc.needs_pass: result['status']='encrypted'; return result
            result['total_pages']=len(doc)
            if len(doc)>5000: fail('attachment_too_large','PDF page count exceeds parser limit')
            for i,page in enumerate(doc):
                try:
                    text=page.get_text()
                    result['pages'].append({'pdf_page':i+1,'printed_page':page.get_label() or None,'text':text,
                                           'has_text':bool(text.strip())})
                    if not text.strip(): result['failed_pages'].append({'pdf_page':i+1,'reason':'needs_ocr_or_visual_reading'})
                except Exception:
                    result['failed_pages'].append({'pdf_page':i+1,'reason':'page_parse_failed'})
            result['status']='partial' if result['failed_pages'] else 'parsed'
            result['coverage']='extracted_text_only; figures, equations and supplements require separate verification'
    except (ValueError,RuntimeError) as exc:
        if hasattr(exc,'code'): raise
        result.update(status='parse_failed',reason=type(exc).__name__)
    return result

class EvidenceService:
    def __init__(self,store): self.store=store

    def snapshot(self,client,keys,level='discovery'):
        if level not in ('discovery','regular','deep'): fail('invalid_request','Unknown reading level')
        if not client.settings['binding_id']: fail('binding_required','Bind the personal library first')
        files={}; items=[]; problems=[]
        client.probe()
        for key in keys:
            try: item=client.get(key)
            except (ValueError,OSError) as exc:
                problems.append({'item_key':key,'reason':getattr(exc,'code','read_failed')}); continue
            data=item['data']
            if data.get('itemType') in ('note','attachment','annotation'): fail('invalid_request','Select parent literature items')
            entry={'item_ref':{'binding_id':client.settings['binding_id'],'item_key':key},
                   'version':item['version'],'metadata':data,'attachments':[],'notes':[],'annotations':[],
                   'reading_status':'abstract_read' if data.get('abstractNote') else 'metadata_only'}
            files[key+'/metadata.json']=canonical(item)
            if level!='discovery':
                try: children=client.children(key)
                except (ValueError,OSError) as exc:
                    children=[]; problems.append({'item_key':key,'reason':'children_'+getattr(exc,'code','read_failed')})
                for child in children:
                    kind=child['data'].get('itemType')
                    if kind=='note': entry['notes'].append(child)
                    if kind!='attachment': continue
                    att={'attachment_key':child['key'],'version':child['version'],'status':'fulltext_missing'}
                    try:
                        annotations=[x for x in client.children(child['key']) if x['data'].get('itemType')=='annotation']
                        entry['annotations'].extend(annotations)
                    except (ValueError,OSError) as exc:
                        problems.append({'item_key':key,'attachment_key':child['key'],
                                         'reason':'annotations_'+getattr(exc,'code','read_failed')})
                    try:
                        if child['data'].get('contentType')!='application/pdf':
                            att.update(status='unsupported_attachment',reason='PDF parser only; no invented page locations')
                        else:
                            parsed=parse_pdf(client.attachment_path(child['key']))
                            att.update({k:v for k,v in parsed.items() if k!='pages'})
                            att['page_labels']={str(p['pdf_page']):p['printed_page'] for p in parsed['pages'] if p['has_text']}
                            relative=key+'/'+child['key']+'/text.json'
                            files[relative]=canonical(parsed); att['text_path']=relative
                            if parsed['status'] in ('parsed','partial'): entry['reading_status']='text_extracted'
                    except (ValueError,OSError) as exc:
                        att.update(status=getattr(exc,'code','read_failed'),reason=str(exc) if hasattr(exc,'code') else type(exc).__name__)
                    entry['attachments'].append(att)
                files[key+'/notes.json']=canonical(entry['notes'])
                files[key+'/annotations.json']=canonical(entry['annotations'])
                if entry['reading_status']!='text_extracted': problems.append({'item_key':key,'reason':'full_text_not_available'})
            items.append(entry)
        manifest={'schema_version':1,'binding_id':client.settings['binding_id'],'instance_id':client.instance,
                  'created_utc':stamp(),'items':items,'files':[{'path':n,'sha256':digest(b),'bytes':len(b)} for n,b in sorted(files.items())],
                  'coverage':{'level':level,'items':len(items),'requested_items':len(keys),'problems':problems,'deep_verified':False}}
        manifest['snapshot_id']=snapshot_id(manifest)
        return self.publish(manifest,files)

    def publish(self,manifest,files):
        validate_snapshot(manifest)
        if set(files)!={f['path'] for f in manifest['files']}: fail('invalid_snapshot','Snapshot file set differs from manifest')
        base='snapshots/'+manifest['snapshot_id']+'/'
        for row in manifest['files']:
            name=safe_name(row['path']); raw=files[name]
            if len(raw)!=row['bytes'] or digest(raw)!=row['sha256']: fail('invalid_snapshot','Evidence file checksum mismatch')
            path=self.store.path(base+name)
            if path.exists() and path.read_bytes()!=raw: fail('invalid_snapshot','Immutable evidence was changed')
            if not path.exists(): atomic_write(path,raw)
        # The manifest is the publication marker. Workers reject incomplete transfers.
        self.store.write(base+'manifest.json',manifest)
        return {'snapshot_id':manifest['snapshot_id'],'manifest':base+'manifest.json','coverage':manifest['coverage']}

    def load(self,identity):
        from common import require_hash
        require_hash(identity)
        base='snapshots/'+identity+'/'
        manifest=self.store.read(base+'manifest.json')
        if manifest is None: fail('snapshot_not_received','Complete evidence snapshot has not been received')
        validate_snapshot(manifest)
        for row in manifest['files']:
            path=self.store.path(base+safe_name(row['path']))
            if not path.is_file() or path.stat().st_size!=row['bytes'] or digest(path.read_bytes())!=row['sha256']:
                fail('invalid_snapshot','Snapshot file is absent or changed')
        return manifest

    def index(self,snapshot,library_versions=None):
        manifest=self.load(snapshot)
        path=self.store.path('cache/library.sqlite3'); path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS literature_fts USING fts5(binding, item_key, snapshot, title, body)')
            db.execute('CREATE TABLE IF NOT EXISTS literature_versions (binding TEXT, item_key TEXT, version INTEGER, observed_utc TEXT, library_digest TEXT, PRIMARY KEY(binding,item_key))')
            for item in manifest['items']:
                ref=item['item_ref']; text=item['metadata'].get('abstractNote','')
                prior=db.execute('SELECT observed_utc FROM literature_versions WHERE binding=? AND item_key=?',(ref['binding_id'],ref['item_key'])).fetchone()
                if prior and prior[0]>manifest['created_utc']: continue
                for att in item['attachments']:
                    if att.get('text_path'):
                        parsed=self.store.read('snapshots/'+snapshot+'/'+att['text_path'])
                        text+='\n'+'\n'.join(p['text'] for p in parsed['pages'])
                db.execute('DELETE FROM literature_fts WHERE binding=? AND item_key=?',(ref['binding_id'],ref['item_key']))
                db.execute('INSERT INTO literature_fts VALUES (?,?,?,?,?)',(ref['binding_id'],ref['item_key'],snapshot,item['metadata'].get('title',''),text))
                db.execute('INSERT OR REPLACE INTO literature_versions VALUES (?,?,?,?,?)',(ref['binding_id'],ref['item_key'],item['version'],manifest['created_utc'],digest(canonical(library_versions)) if library_versions is not None else None))
            db.commit()
        return {'indexed_items':len(manifest['items']),'snapshot_id':snapshot,'cache':'cache/library.sqlite3','rebuildable':True}

    def freshness(self,client):
        """Never present a cached snapshot as current after an unobserved library edit.

        A full versions-map digest also catches newly added children. Conservatively
        mark unrelated rows stale until refreshed; historical evidence is retained.
        """
        path=self.store.path('cache/library.sqlite3')
        if not path.exists(): return {}
        versions,_=client.list('items',{'format':'versions'})
        checksum=digest(canonical(versions)); states={}
        with closing(sqlite3.connect(path)) as db:
            try: rows=db.execute('SELECT binding,item_key,version,library_digest FROM literature_versions').fetchall()
            except sqlite3.OperationalError: return {}
            for binding,key,version,previous in rows:
                if binding!=client.settings['binding_id']: states[key]='different_binding'
                elif key not in versions: states[key]='deleted'
                elif versions[key]!=version: states[key]='changed'
                else: states[key]='current' if previous==checksum else 'requires_refresh'
        return states

    def search(self,query,limit=20):
        path=self.store.path('cache/library.sqlite3')
        if not path.exists(): return []
        terms=re.findall(r'\w+',query)
        if not terms: return []
        with closing(sqlite3.connect(path)) as db:
            rows=db.execute('SELECT binding,item_key,snapshot,title,bm25(literature_fts) FROM literature_fts WHERE literature_fts MATCH ? ORDER BY bm25(literature_fts) LIMIT ?',
                            (' AND '.join('"'+x+'"' for x in terms),limit)).fetchall()
        return [dict(zip(('binding_id','item_key','snapshot_id','title','score'),row)) for row in rows]

def validate_claim(claim,manifest):
    from literature_contract import exact, bounded_text
    exact(claim, ('text','kind','item_key','attachment_key','attachment_sha256','location','coverage','conditions','counterevidence','verification'))
    bounded_text(claim['text'])
    if not isinstance(claim['location'],dict) or not isinstance(claim['conditions'],list) or not isinstance(claim['counterevidence'],list): fail('invalid_claim','Structured location, conditions and counterevidence are required')
    exact(claim['location'],(),('pdf_page','printed_page','section','paragraph','equation','figure','table','note_key','note_version','annotation_key','annotation_version'))
    for field in ('conditions','counterevidence'):
        if len(claim[field])>100: fail('invalid_claim','Claim context is too large')
        for value in claim[field]: bounded_text(value,4000)
    if claim['kind'] not in ('author_statement','user_annotation','ai_summary','inference'): fail('invalid_claim','Unknown attribution kind')
    if claim['verification'] not in ('unverified','source_checked','human_checked'): fail('invalid_claim','Unknown verification state')
    item=next((x for x in manifest['items'] if x['item_ref']['item_key']==claim['item_key']),None)
    if item is None: fail('invalid_claim','Claim cites an item outside the received snapshot')
    if claim['attachment_key'] is None:
        if claim['attachment_sha256'] is not None or claim['location'].get('pdf_page') is not None: fail('invalid_claim','Abstract evidence cannot have invented PDF pages')
        if claim['coverage']=='note':
            location=claim['location']
            if set(location)!={'note_key','note_version'} or not any(n['key']==location['note_key'] and n['version']==location['note_version'] for n in item['notes']):
                fail('invalid_claim','Note claim must identify an actual note version')
        else:
            if claim['location'] or claim['coverage'] not in ('metadata','abstract'): fail('invalid_claim','Claim lacks full-text evidence')
            if claim['coverage']=='abstract' and not item['metadata'].get('abstractNote','').strip(): fail('invalid_claim','No abstract was received for this item')
    else:
        att=next((x for x in item['attachments'] if x['attachment_key']==claim['attachment_key']),None)
        if att is None or not att.get('sha256') or att['sha256']!=claim['attachment_sha256']: fail('invalid_claim','Wrong attachment version')
        page=claim['location'].get('pdf_page')
        if att.get('status') not in ('parsed','partial') or not att.get('text_path'): fail('invalid_claim','Attachment text was not parsed')
        if type(page) is not int or not 1<=page<=att.get('total_pages',0): fail('invalid_claim','A valid PDF page location is required')
        if page in {p['pdf_page'] for p in att.get('failed_pages',[])}: fail('invalid_claim','Claim cites an unread or failed PDF page')
        if claim['coverage'] not in ('extracted_text','annotation'): fail('invalid_claim','Only extracted text or an existing annotation is available')
        printed=claim['location'].get('printed_page')
        if printed is not None and printed!=att.get('page_labels',{}).get(str(page)): fail('invalid_claim','Printed page label was not observed')
        if claim['coverage']=='annotation':
            location=claim['location']
            annotation=next((a for a in item['annotations'] if a['key']==location.get('annotation_key') and a['version']==location.get('annotation_version')),None)
            if not annotation or annotation['data'].get('parentItem')!=att['attachment_key']: fail('invalid_claim','Annotation version was not received for this attachment')
            try: position=json.loads(annotation['data']['annotationPosition'])
            except (ValueError,KeyError,TypeError): fail('invalid_claim','Annotation lacks a stable page position')
            if position.get('pageIndex')!=page-1: fail('invalid_claim','Annotation page differs from the cited location')
        elif any(k in claim['location'] for k in ('note_key','note_version','annotation_key','annotation_version')):
            fail('invalid_claim','Text claim cannot invent note or annotation identifiers')
    return claim
