"""Explicit full-text retrieval with public HTTPS destinations and PDF validation."""
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from literature_contract import fail

PMC_BASE='https://pmc-oa-opendata.s3.amazonaws.com/'

def pmc_get(url,accept,maximum):
    # Fixed official origin only. Reuse the host's configured HTTPS transport,
    # including institutional proxies/fake-IP DNS; never extend this path to
    # arbitrary caller URLs. TLS verification and redirect rejection stay on.
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='pmc-oa-opendata.s3.amazonaws.com' or parsed.fragment:
        fail('forbidden','PMC transport is restricted to its official public bucket')
    if parsed.path!='/' and not re.fullmatch(r'/PMC[1-9][0-9]*\.[1-9][0-9]*/PMC[1-9][0-9]*\.[1-9][0-9]*\.(?:json|pdf)',parsed.path):
        fail('forbidden','Unsupported PMC object path')
    from zotero_adapter import NoRedirect
    request=urllib.request.Request(url,headers={'Accept':accept})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=30) as response:
            raw=response.read(maximum+1); media=response.headers.get_content_type()
    except (urllib.error.URLError,TimeoutError,OSError):
        fail('fulltext_unavailable','Official PMC object is unavailable through the configured HTTPS transport')
    if len(raw)>maximum: fail('fulltext_unavailable','PMC response exceeds the bounded download size')
    return raw,media

class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self,host,address):
        super().__init__(host,timeout=30,context=ssl.create_default_context())
        self.address=address

    def connect(self):
        # Connect to the validated address, while TLS still verifies the original
        # hostname. A second DNS resolution cannot redirect this fetch into LAN.
        connection=socket.create_connection((self.address,443),self.timeout)
        try: self.sock=self._context.wrap_socket(connection,server_hostname=self.host)
        except BaseException:
            connection.close(); raise

def public_get(url,accept,maximum):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        fail('fulltext_unavailable','Full text requires an authenticated browser or a public HTTPS PDF URL')
    try:
        addresses=socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            fail('forbidden','Full-text download must not access local or private network services')
        connection=PinnedHTTPSConnection(parsed.hostname,addresses[0][4][0])
        try:
            connection.request('GET',urllib.parse.urlunsplit(('', '',parsed.path or '/',parsed.query,'')),headers={'Accept':accept})
            response=connection.getresponse()
            if response.status!=200: fail('fulltext_unavailable','PDF endpoint requires a different URL or browser authorization')
            media=response.headers.get_content_type(); raw=response.read(maximum+1)
        finally: connection.close()
    except (OSError,ValueError) as exc:
        from literature_contract import LiteratureError
        if isinstance(exc,LiteratureError): raise
        fail('fulltext_unavailable','PDF could not be retrieved without browser authorization')
    if len(raw)>maximum: fail('fulltext_unavailable','Response exceeded the bounded download size')
    return raw,media

def retrieve_pdf(url):
    getter=pmc_get if url.startswith(PMC_BASE) else public_get
    raw,media=getter(url,'application/pdf',256000000)
    if media not in ('application/pdf','application/octet-stream','binary/octet-stream') or len(raw)<32 or not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:]:
        fail('invalid_pdf','Server returned a login/error page or incomplete PDF')
    return raw,{'content_type':media,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def resolve_pmc(pmcid,expected_doi='',expected_pmid=None):
    """Resolve the current PMC Cloud layout, without assuming article version 1.

    See https://pmc-oa-opendata.s3.amazonaws.com/README.txt . The former OA
    service is retired. Only public licensed objects from this fixed bucket
    are returned; no cookies, AWS account, proxy or subscription is required.
    """
    if not isinstance(pmcid,str) or not re.fullmatch(r'PMC[1-9][0-9]{0,11}',pmcid):
        fail('invalid_request','A PMC accession identifier is required')
    base=PMC_BASE
    listing,_=pmc_get(base+'?'+urllib.parse.urlencode({'list-type':'2','prefix':pmcid+'.','delimiter':'/','max-keys':100}), 'application/xml',1000000)
    if b'<!DOCTYPE' in listing or b'<!ENTITY' in listing: fail('invalid_source','Untrusted PMC XML declaration')
    try:
        tree=ET.fromstring(listing); ns='{http://s3.amazonaws.com/doc/2006-03-01/}'
        if tree.findtext(ns+'IsTruncated')=='true': fail('fulltext_unavailable','PMC article version list is incomplete')
        versions=[]
        for prefix in tree.findall(ns+'CommonPrefixes/'+ns+'Prefix'):
            match=re.fullmatch(re.escape(pmcid)+r'\.([1-9][0-9]*)/',prefix.text or '')
            if match: versions.append(int(match.group(1)))
        if not versions: fail('fulltext_unavailable','No open PMC article version was found')
        version=max(versions); name=pmcid+'.'+str(version)
        raw,_=pmc_get(base+name+'/'+name+'.json','application/json',1000000)
        meta=json.loads(raw)
    except (ET.ParseError,json.JSONDecodeError,UnicodeError): fail('invalid_source','PMC metadata could not be parsed')
    if not isinstance(meta,dict) or meta.get('pmcid')!=pmcid or meta.get('version')!=version:
        fail('invalid_source','PMC article identity differs from the requested object')
    from literature_sources import doi
    if expected_doi and doi(meta.get('doi'))!=doi(expected_doi): fail('invalid_source','PMC DOI differs from the selected item')
    if expected_pmid and str(meta.get('pmid'))!=str(expected_pmid): fail('invalid_source','PMC PMID differs from the selected item')
    if meta.get('is_pmc_openaccess') is not True or not meta.get('license_code'):
        fail('fulltext_unavailable','No open-access license is recorded for this PMC version')
    target=urllib.parse.urlsplit(meta.get('pdf_url') or '')
    if target.scheme!='s3' or target.netloc!='pmc-oa-opendata' or target.path!='/'+name+'/'+name+'.pdf' or target.fragment:
        fail('fulltext_unavailable','PMC does not provide a licensed PDF for this article version')
    parameters=urllib.parse.parse_qs(target.query)
    md5=parameters.get('md5',[])
    if set(parameters)!={'md5'} or len(md5)!=1 or not re.fullmatch('[a-f0-9]{32}',md5[0]):
        fail('invalid_source','PMC PDF checksum is missing or malformed')
    return {'pdf_url':base+name+'/'+name+'.pdf','md5':md5[0],'pmcid':pmcid,'version':version,
            'license':meta['license_code'],'is_manuscript':meta.get('is_manuscript'),
            'is_retracted':meta.get('is_retracted'),'metadata_sha256':hashlib.sha256(raw).hexdigest(),
            'source':'NIH NLM NCBI PubMed Central Article Datasets'}
