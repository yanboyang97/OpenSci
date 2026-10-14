"""Bounded official metadata search with independent, truthful source coverage."""
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from common import parse_json, stamp, digest, canonical
from literature_contract import fail, bounded_text, integer
from zotero_adapter import NoRedirect

ADAPTER_VERSION = '1.0'
BROWSER_URLS = {'web_of_science':'https://www.webofscience.com/wos/woscc/basic-search',
 'scopus':'https://www.scopus.com/search/form.uri?display=basic',
 'pubmed':'https://pubmed.ncbi.nlm.nih.gov/', 'ieee':'https://ieeexplore.ieee.org/search/searchresult.jsp',
 'google_scholar':'https://scholar.google.com/scholar'}

def doi(value):
    value = str(value or '').strip().lower()
    value = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)','',value)
    return value.rstrip(' .')

def title(value):
    return ' '.join(re.findall(r'\w+',str(value).lower()))

def normalized(source, source_id, data, raw):
    return {'candidate_id':digest(canonical([source,str(source_id)]))[:24], 'source':source,
        'source_id':str(source_id), 'metadata':data, 'raw':raw, 'retrieved_utc':stamp(),
        'abstract_available':bool(data.get('abstractNote')), 'fulltext_status':'not_checked',
        'duplicate_status':'not_checked', 'screening':{'status':'candidate','reason':'Source query match; relevance is not scientific verification'}}

def match_duplicate(candidate, items):
    data = candidate['metadata']; strong=[]; possible=[]
    for row in items:
        existing = row['data']
        if existing.get('itemType') in ('attachment','note','annotation'): continue
        same_doi = doi(data.get('DOI')) and doi(data.get('DOI')) == doi(existing.get('DOI'))
        pmid = re.search(r'^PMID:\s*(\d+)\s*$',data.get('extra',''),re.M)
        other = re.search(r'^PMID:\s*(\d+)\s*$',existing.get('extra',''),re.M)
        same_pmid = pmid and other and pmid.group(1) == other.group(1)
        if same_doi or same_pmid:
            # Identifier collisions and publication versions require human resolution.
            if title(data.get('title')) == title(existing.get('title')) and data.get('itemType') == existing.get('itemType'):
                strong.append(row['key'])
            else: possible.append(row['key'])
        elif title(data.get('title')) and title(data.get('title')) == title(existing.get('title')):
            possible.append(row['key'])
    return {'status':'matched' if len(strong)==1 and not possible else 'suspected' if strong or possible else 'new',
            'item_keys':strong+possible}

class SourceSearch:
    def __init__(self, transport=None):
        self.transport=transport
        self.opener=urllib.request.build_opener(NoRedirect())
        self.last={}

    def request(self, source, url, params, headers=None):
        delay=max(0,1/source['rate_limit']-(time.monotonic()-self.last.get(source['id'],0)))
        if delay: time.sleep(delay)
        self.last[source['id']]=time.monotonic()
        if self.transport: return self.transport(url,params,headers or {})
        req=urllib.request.Request(url+'?'+urllib.parse.urlencode(params),headers={'Accept':'application/json',**(headers or {})})
        try:
            with self.opener.open(req,timeout=25) as response: raw=response.read(8000001)
        except urllib.error.HTTPError as exc:
            fail('permission_denied' if exc.code in (401,403) else 'rate_limited' if exc.code==429 else 'source_failed',
                 'Source returned HTTP '+str(exc.code))
        except (urllib.error.URLError,TimeoutError,OSError): fail('source_unavailable','Source connection unavailable')
        if len(raw)>8000000: fail('source_failed','Source response exceeded limit')
        return raw

    def search(self, source, query, limit=20, cursor=0, browser='edge'):
        bounded_text(query,4000); integer(limit,1,50); integer(cursor)
        kind=source['adapter']
        result={'source_id':source['id'],'adapter':kind,'adapter_version':ADAPTER_VERSION,'query':query,
            'requested_limit':limit,'cursor':cursor,'started_utc':stamp(),'candidates':[],
            'status':'not_executed','browser':browser,'unsupported_conditions':[], 'total':None,
            'capabilities':[], 'next_cursor':cursor,'complete':False,'sort':'source_default'}
        if not source['enabled']: result['reason']='Source disabled'; return result
        if kind not in BROWSER_URLS:
            result['reason']='No implemented adapter for this configured source'; return result
        if kind=='google_scholar' or source['access_mode']!='api':
            result.update(status='waiting_user',reason='Browser-assisted search and native export require user interaction',
                          capabilities=['needs_browser','needs_user_action'],url=BROWSER_URLS[kind])
            return result
        ref=source['credential_ref']; secret=os.environ.get(ref[4:]) if ref else None
        if kind!='pubmed' and not secret:
            result.update(status='permission_denied',reason='API credential reference is absent; campus web access is independent',
                          browser_url=BROWSER_URLS[kind]); return result
        try:
            if kind=='pubmed':
                result['sort']='relevance'
                params={'db':'pubmed','term':query,'retmode':'json','retmax':limit,'retstart':cursor,'sort':'relevance','tool':'OpenSci'}
                if secret: params['api_key']=secret
                found=parse_json(self.request(source,'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',params))['esearchresult']
                if found.get('errorlist'): fail('source_failed','PubMed rejected part of the query')
                ids=found.get('idlist',[]); total=int(found['count']); candidates=[]
                if ids:
                    params={'db':'pubmed','id':','.join(ids),'retmode':'xml','tool':'OpenSci'}
                    if secret: params['api_key']=secret
                    raw=self.request(source,'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',params)
                    if b'<!ENTITY' in raw: fail('source_failed','XML entities are not supported')
                    tree=ET.fromstring(raw)
                    for article in tree.findall('PubmedArticle'):
                        pmid=article.findtext('MedlineCitation/PMID'); a=article.find('MedlineCitation/Article')
                        if a is None: continue
                        value=lambda path: ''.join(a.find(path).itertext()) if a.find(path) is not None else ''
                        data={'itemType':'journalArticle','title':value('ArticleTitle'),
                            'abstractNote':'\n'.join(''.join(x.itertext()) for x in a.findall('.//AbstractText')),
                            'publicationTitle':value('Journal/Title'),'date':value('Journal/JournalIssue/PubDate/Year') or value('Journal/JournalIssue/PubDate/MedlineDate'),
                            'DOI':next((x.text or '' for x in article.findall('PubmedData/ArticleIdList/ArticleId') if x.get('IdType')=='doi'),''),
                            'extra':'PMID: '+str(pmid),'url':'https://pubmed.ncbi.nlm.nih.gov/'+str(pmid)+'/',
                            'creators':[{'creatorType':'author','lastName':x.findtext('LastName',''),'firstName':x.findtext('ForeName','')}
                                        for x in a.findall('AuthorList/Author') if x.find('LastName') is not None]}
                        pmcid=next((x.text or '' for x in article.findall('PubmedData/ArticleIdList/ArticleId') if x.get('IdType')=='pmc'),None)
                        candidates.append(normalized(source['id'],pmid,data,{'pmid':pmid,'pmcid':pmcid,'xml':ET.tostring(article,encoding='unicode')}))
                result['unsupported_conditions']=found.get('warninglist',{})
            else:
                if kind=='scopus':
                    obj=parse_json(self.request(source,'https://api.elsevier.com/content/search/scopus',
                        {'query':query,'count':min(limit,25),'start':cursor,'view':'STANDARD'}, {'X-ELS-APIKey':secret}))['search-results']
                    total=int(obj.get('opensearch:totalResults',0)); rows=obj.get('entry',[])
                    rows=[r for r in rows if 'error' not in r]
                    candidates=[normalized(source['id'],r.get('dc:identifier',''),{'itemType':'journalArticle',
                        'title':r.get('dc:title',''),'DOI':r.get('prism:doi',''),'date':r.get('prism:coverDate',''),
                        'publicationTitle':r.get('prism:publicationName',''),'url':r.get('prism:url',''),
                        'creators':[{'creatorType':'author','name':r['dc:creator']}] if r.get('dc:creator') else []},r) for r in rows]
                elif kind=='ieee':
                    obj=parse_json(self.request(source,'https://ieeexploreapi.ieee.org/api/v1/search/articles',
                        {'apikey':secret,'format':'json','querytext':query,'max_records':limit,'start_record':cursor+1}))
                    total=int(obj.get('total_records',0)); rows=obj.get('articles',[])
                    candidates=[normalized(source['id'],r.get('article_number',''),{'itemType':'journalArticle',
                        'title':r.get('title',''),'DOI':r.get('doi',''),'date':str(r.get('publication_year','')),
                        'abstractNote':r.get('abstract',''),'url':r.get('html_url',''),'publicationTitle':r.get('publication_title',''),
                        'creators':[{'creatorType':'author','name':a.get('full_name','')} for a in r.get('authors',{}).get('authors',[])]},r) for r in rows]
                else:
                    if cursor % limit: fail('invalid_request','Web of Science resume requires a page-aligned cursor')
                    obj=parse_json(self.request(source,'https://api.clarivate.com/apis/wos-starter/v1/documents',
                        {'q':query,'db':'WOS','limit':limit,'page':cursor//limit+1},{'X-ApiKey':secret}))
                    total=int(obj.get('metadata',{}).get('total',0)); rows=obj.get('hits',[])
                    candidates=[normalized(source['id'],r.get('uid',''),{'itemType':'journalArticle',
                        'title':r.get('title',''),'DOI':r.get('identifiers',{}).get('doi',''),
                        'date':str(r.get('source',{}).get('publishYear','')),'publicationTitle':r.get('source',{}).get('sourceTitle',''),
                        'creators':[{'creatorType':'author','name':a.get('displayName','')} for a in r.get('names',{}).get('authors',[])]},r) for r in rows]
            result.update(candidates=candidates,total=total,next_cursor=cursor+len(candidates),
                complete=cursor+len(candidates)>=total,status='zero_results' if total==0 else 'succeeded' if cursor+len(candidates)>=total else 'partial',
                capabilities=['search_metadata','export_citation'])
            if kind in ('pubmed','ieee'): result['capabilities'].append('fetch_abstract')
        except (ValueError, KeyError, TypeError,ET.ParseError) as exc:
            result.update(status=getattr(exc,'code','source_failed'),reason=str(exc) if hasattr(exc,'code') else 'Unrecognized source response')
        result['finished_utc']=stamp()
        return result
