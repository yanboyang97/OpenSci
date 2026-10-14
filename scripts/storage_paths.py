"""Portable relative names and local paths without symbolic links/junctions."""
import os
from pathlib import Path, PurePosixPath
import re
import stat


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Unsafe archive path')
    parts = name.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if any(not p or p in ('.', '..') or p.endswith((' ', '.')) or
           p.split('.')[0].upper() in reserved or re.search(r'[\x00-\x1f<>"|?*]', p) for p in parts):
        raise ValueError('Unsafe or non-portable archive path')
    if PurePosixPath(name).is_absolute():
        raise ValueError('Absolute archive path')
    return name


def plain_path(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Symlinks/junctions/reparse points are not supported')
    return Path(os.path.abspath(path))
