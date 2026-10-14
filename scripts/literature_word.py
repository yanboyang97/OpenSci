"""Recoverable desktop tasks; only Zotero's native plugin writes Word fields.

The desktop agent follows the observed plugin UI. This module prepares bounded
work and verifies saved OOXML without ever creating or rewriting a field.
"""
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from common import atomic_write,canonical,digest,stamp
from literature_contract import fail,identifier,item_ref,bounded_text
from storage_paths import plain_path,safe_name

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def inspect_word(path):
    path=plain_path(path)
    if path.suffix.lower()!='.docx': fail('unsupported_manuscript','Native writing requires a docx copy')
    if path.stat().st_size>64_000_000: fail('manuscript_too_large','Word file exceeds inspection limit')
    raw=path.read_bytes(); fields=[]; body=[]; styles=[]
    with zipfile.ZipFile(path) as archive:
        if sum(x.file_size for x in archive.infolist())>128_000_000: fail('manuscript_too_large','Expanded Word document exceeds limit')
        for info in archive.infolist():
            if not (info.filename.startswith('word/') and info.filename.endswith('.xml')): continue
            if info.file_size>16_000_000: fail('manuscript_too_large','Word XML exceeds inspection limit')
            source=archive.read(info)
            if b'<!DOCTYPE' in source or b'<!ENTITY' in source: fail('invalid_manuscript','DTD is not permitted')
            stack=[]
            for el in ET.fromstring(source).iter():
                if el.tag==W+'fldChar':
                    kind=el.get(W+'fldCharType')
                    if kind=='begin': stack.append({'code':'','text':'','part':info.filename})
                    elif kind=='end' and stack:
                        value=stack.pop(); code=value['code']
                        if 'ADDIN ZOTERO_ITEM CSL_CITATION' in code:
                            try: data=json.loads(code[code.index('{'):].strip())
                            except (ValueError,KeyError): fail('invalid_manuscript','Unrecognized native citation field')
                            refs=[]
                            for item in data.get('citationItems',[]):
                                for uri in item.get('uris',[]):
                                    match=re.fullmatch(r'https?://(?:www\.)?zotero.org/users/(?:local/[A-Za-z0-9]+|\d+)/items/([A-Z0-9]{8})',uri)
                                    if not match: fail('citation_conflict','Native citation is not bound to a personal library item')
                                    refs.append({'item_key':match.group(1),'uri':uri})
                            fields.append({'kind':'citation','citation_id':data.get('citationID'),'refs':refs,'text':value['text'],'code_sha256':digest(code.encode()),'part':info.filename})
                        elif 'ADDIN ZOTERO_BIBL' in code:
                            fields.append({'kind':'bibliography','text':value['text'],'code_sha256':digest(code.encode()),'part':info.filename})
                        elif info.filename=='word/document.xml': body.append(value['text'])
                elif el.tag==W+'instrText' and stack: stack[-1]['code']+=el.text or ''
                elif el.tag==W+'t':
                    if stack: stack[-1]['text']+=el.text or ''
                    elif info.filename=='word/document.xml': body.append(el.text or '')
            if stack: fail('invalid_manuscript','Unclosed Word field')
        if 'docProps/custom.xml' in archive.namelist():
            tree=ET.fromstring(archive.read('docProps/custom.xml')); prefs={}
            for el in tree:
                match=re.fullmatch(r'ZOTERO_PREF_(\d+)',el.get('name',''))
                if match: prefs[int(match.group(1))]=''.join(el.itertext())
            if prefs:
                try:
                    root=ET.fromstring(''.join(prefs[k] for k in sorted(prefs)))
                    styles=[el.get('id') for el in root.findall('style')]
                except ET.ParseError: fail('invalid_manuscript','Unreadable Zotero document preferences')
    ids=[x['citation_id'] for x in fields if x['kind']=='citation']
    if any(not x for x in ids) or len(ids)!=len(set(ids)): fail('citation_conflict','Missing or duplicate native citation IDs')
    return {'sha256':digest(raw),'fields':fields,'body_text':''.join(body),'styles':styles,'checked_utc':stamp()}

def prepare(store,study,operation,relative,expected,refs,marker,action='insert'):
    identifier(operation); identifier(study)
    if not relative.startswith('manuscript/'): fail('forbidden','Native task must be inside manuscript/')
    if action not in ('insert','edit','refresh','bibliography','style'): fail('invalid_request','Unknown native action')
    for ref in refs: item_ref(ref)
    bounded_text(marker,1000,empty=action in ('refresh','bibliography'))
    record='native-word/'+operation+'.json'; old=store.read(record)
    specification={'study_id':study,'path':relative,'expected_sha256':expected,'item_refs':refs,'marker':marker,'action':action}
    if old:
        if old['specification']!=specification: fail('request_conflict','Native task ID was reused')
        return old
    path=plain_path(store.root/safe_name(relative)); before=inspect_word(path)
    if before['sha256']!=expected: fail('version_conflict','Save the manuscript and reread its version')
    if action=='insert' and (not refs or before['body_text'].count(marker)!=1): fail('ambiguous_location','Insertion requires items and exactly one marker outside native fields')
    if action=='edit' and (not refs or marker not in [x.get('citation_id') for x in before['fields']]): fail('ambiguous_location','Select items and a native citation ID from the saved manuscript')
    if action=='style' and not re.fullmatch(r'https?://www.zotero.org/styles/[a-z0-9-]+',marker): fail('invalid_request','Use an installed Zotero style identifier')
    # An unfinished operation holds this manuscript until it is verified. There
    # is no time-based lease expiry that could permit a second desktop writer.
    slot='native-word/active-'+digest(relative.encode())[:24]+'.json'
    active=store.read(slot)
    if active and active['task_id']!=operation:
        previous=store.read('native-word/'+active['task_id']+'.json')
        if not previous or previous.get('status')!='succeeded': fail('waiting_local','Reconcile the existing native task before editing this manuscript')
    store.write(slot,{'task_id':operation,'study_id':study,'path':relative})
    recovery=store.path('manuscript-recovery/'+expected+'.docx')
    if not recovery.exists(): atomic_write(recovery,path.read_bytes())
    task={'schema_version':1,'task_id':operation,'status':'waiting_local','reason':'Waiting for an observed native Zotero Word session',
          'specification':specification,'before':before,'recovery':recovery.relative_to(store.root).as_posix(),
          'created_utc':stamp(),'driver':'observed_native_plugin','steps':[
              'Open the exact saved manuscript in Word; confirm its path and saved version before editing.',
              'Stop for unsaved or concurrent edits, unknown focus, missing plugin, or ambiguous targets.',
              'Use only Zotero Add/Edit Citation, Add/Edit Bibliography, Refresh, or Document Preferences for the requested action.',
              'For insertion, select only the unique marker; select the requested real personal-library items in Zotero.',
              'Do not manufacture fields or invoke Unlink Citations. Save and submit this task ID for native verification.',
              'After an interruption, inspect the saved manuscript and original task before any further insertion.']}
    store.write(record,task); return task

def verify(store,study,task_id,relative,expected):
    record='native-word/'+identifier(task_id)+'.json'; task=store.read(record)
    if not task or task['specification']['study_id']!=study: fail('not_found','Native task does not belong to this study')
    spec=task['specification']
    if relative!=spec['path']: fail('forbidden','Native task manuscript cannot change')
    after=inspect_word(plain_path(store.root/safe_name(relative)))
    if after['sha256']!=expected: fail('version_conflict','Saved manuscript changed during verification')
    if task['status']=='succeeded':
        if task['after']['sha256']!=expected: fail('version_conflict','Completed receipt refers to an earlier saved document')
        return task
    before=task['before']; action=spec['action']; marker=spec['marker']
    old={x['citation_id']:x for x in before['fields'] if x['kind']=='citation'}
    new={x['citation_id']:x for x in after['fields'] if x['kind']=='citation'}
    removed=set(old)-set(new); added_ids=set(new)-set(old); edited_id=marker
    if action not in ('insert','edit') and set(new)!=set(old): fail('scope_conflict','This native action cannot add or remove citations')
    old_bib=sum(x['kind']=='bibliography' for x in before['fields']); new_bib=sum(x['kind']=='bibliography' for x in after['fields'])
    if new_bib<old_bib or (action!='bibliography' and new_bib!=old_bib): fail('scope_conflict','Unrelated bibliography fields changed')
    # Zotero 10 may assign a fresh citationID while editing the selected field.
    # Accept only the single requested replacement and preserve its migration map.
    if action=='edit' and removed=={marker} and len(added_ids)==1:
        edited_id=next(iter(added_ids)); task['citation_id_migration']={marker:edited_id}
    elif removed: fail('citation_conflict','An existing native citation disappeared; preserve the recovery copy')
    desired={x['item_key'] for x in spec['item_refs']}
    if action=='insert':
        added=[new[k] for k in set(new)-set(old)]
        if len(added)!=1 or {r['item_key'] for r in added[0]['refs']}!=desired: fail('postcondition_failed','Expected exactly one new native citation with the requested items')
        if before['body_text'].replace(marker,'',1)!=after['body_text']: fail('scope_conflict','Text outside the authorized marker changed')
    elif action=='edit':
        if len(new)!=len(old) or edited_id not in new or {r['item_key'] for r in new[edited_id]['refs']}!=desired: fail('postcondition_failed','Native edit differs from the requested item set')
    elif action=='bibliography':
        if not any(x['kind']=='bibliography' for x in after['fields']): fail('postcondition_failed','No dynamic Zotero bibliography was saved')
    elif action=='style' and after['styles']!=[marker]: fail('postcondition_failed','Zotero style does not match the requested identifier')
    if action!='insert' and before['body_text']!=after['body_text']: fail('scope_conflict','Manuscript body outside native fields changed')
    for key,value in old.items():
        if action=='edit' and key==marker: continue
        if value['refs']!=new[key]['refs']: fail('scope_conflict','Unrelated native citation targets changed')
    task.update(status='succeeded',reason='Saved native field structure, targets and edit scope verified',after=after,verified_utc=stamp(),
                assurance='Saved-document checks; plugin edit/refresh/reopen acceptance is recorded separately by the desktop operator')
    store.write(record,task)
    mapping=store.read('citations/word-'+digest(relative.encode())[:24]+'.json',{})
    mapping.update(schema_version=1,manuscript=relative,sha256=after['sha256'],native_citations=list(new.values()),task_id=task_id)
    store.write('citations/word-'+digest(relative.encode())[:24]+'.json',mapping)
    return task
