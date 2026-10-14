"""Named Zotero grants in the current Windows user's Credential Manager.

Only explicit wincred references are read; credentials are never enumerated,
printed, added to configuration, included in backups, or sent to a worker.
"""
import ctypes
from ctypes import wintypes
import os
import re
from common import digest
from literature_contract import fail

def target_name(reference,instance):
    if not isinstance(reference,str) or not re.fullmatch(r'wincred:OpenSci/Zotero/[A-Za-z0-9_.-]{1,80}',reference):
        fail('invalid_request','Invalid named Windows Zotero credential reference')
    return reference[8:]+'/'+digest(instance.encode())[:24]

def api():
    if os.name!='nt': fail('credential_unavailable','Windows credential reference requires the same Windows user; use env references on other platforms')
    class Credential(ctypes.Structure):
        _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),
            ('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),
            ('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),
            ('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
    library=ctypes.WinDLL('Advapi32.dll',use_last_error=True)
    library.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
    library.CredReadW.restype=wintypes.BOOL
    library.CredWriteW.argtypes=[ctypes.POINTER(Credential),wintypes.DWORD]; library.CredWriteW.restype=wintypes.BOOL
    library.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD]; library.CredDeleteW.restype=wintypes.BOOL
    library.CredFree.argtypes=[ctypes.c_void_p]; library.CredFree.restype=None
    return library,Credential

def read(reference,instance):
    target=target_name(reference,instance); library,Credential=api(); pointer=ctypes.POINTER(Credential)()
    if not library.CredReadW(target,1,0,ctypes.byref(pointer)):
        if ctypes.get_last_error()==1168: return None
        fail('credential_unavailable','The named Windows credential could not be read')
    try:
        entry=pointer.contents
        if entry.CredentialBlobSize!=32: fail('credential_unavailable','Stored Zotero grant has an invalid length')
        key=ctypes.string_at(entry.CredentialBlob,32).decode('ascii')
        if not re.fullmatch(r'[A-Za-z0-9]{32}',key): fail('credential_unavailable','Stored Zotero grant is invalid')
        return key
    finally: library.CredFree(pointer)

def write(reference,instance,key):
    target=target_name(reference,instance)
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9]{32}',key): fail('credential_unavailable','Invalid Zotero grant')
    library,Credential=api(); blob=ctypes.create_string_buffer(key.encode('ascii'))
    entry=Credential(); entry.Type=1; entry.TargetName=target; entry.Comment='OpenSci Zotero local API grant; bound to this Zotero server'
    entry.CredentialBlobSize=32; entry.CredentialBlob=ctypes.cast(blob,ctypes.POINTER(ctypes.c_ubyte))
    entry.Persist=2; entry.UserName='OpenSci'
    if not library.CredWriteW(ctypes.byref(entry),0): fail('credential_unavailable','Windows could not securely retain the Zotero grant')

def forget(reference,instance):
    target=target_name(reference,instance); library,_=api()
    if not library.CredDeleteW(target,1,0) and ctypes.get_last_error()!=1168:
        fail('credential_unavailable','The revoked named Zotero grant could not be removed')
