"""Stdlib utilities. Hashes provide integrity, not authorization."""
import contextlib
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

VERSION = "1.0.0"
ID_PATTERN = r"[A-Z][A-Z0-9-]{2,47}"

def stamp():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+"\n").encode("utf-8")

def print_json(value):
    """Emit UTF-8 bytes even when a Windows console uses a legacy code page."""
    raw = canonical(value)
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(raw.decode("utf-8"))

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: "+key)
        result[key] = value
    return result

def parse_json(raw):
    def invalid(value):
        raise ValueError("Non-finite JSON value: "+value)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=invalid)

def read_json(path, expected_sha256=None, limit=4_000_000):
    if expected_sha256 is not None:
        require_hash(expected_sha256)
    raw = Path(path).read_bytes()
    if len(raw) > limit:
        raise ValueError("JSON exceeds size limit")
    if expected_sha256 is not None and digest(raw) != expected_sha256:
        raise ValueError("Checksum mismatch: "+Path(path).name)
    return parse_json(raw), raw

def atomic_write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="."+path.name+".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def write_json(path, value):
    atomic_write(path, canonical(value))

def create_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical(value))
    with contextlib.suppress(OSError):
        path.chmod(0o600)

class FileLock:
    """Local non-blocking lock, not a distributed lock or GPU allocator."""
    def __init__(self, path):
        self.path, self.handle = Path(path), None
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif os.name == "nt":
                import msvcrt
                self.handle.seek(0, 2)
                if self.handle.tell() == 0:
                    self.handle.write(b"0")
                    self.handle.flush()
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                raise RuntimeError("Unsupported locking platform")
        except BaseException:
            self.handle.close()
            raise
        return self
    def __exit__(self, *args):
        if self.handle:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.handle.seek(0)
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                self.handle.close()

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, encoding="utf-8").strip()

def clean_commit(root):
    if git(root, "status", "--porcelain"):
        raise ValueError("Repository must be clean; review and commit first")
    return git(root, "rev-parse", "HEAD")

def valid_id(value):
    return isinstance(value, str) and re.fullmatch(ID_PATTERN, value) is not None

def require_hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Expected a lowercase SHA-256 digest")

def runtime_spec():
    packages = sorted({(d.metadata["Name"].lower().replace("_", "-"), d.version)
                       for d in importlib.metadata.distributions() if d.metadata["Name"]})
    return {"python_implementation": platform.python_implementation(), "python_version": platform.python_version(),
            "packages": [{"name": name, "version": version} for name, version in packages]}

BASE_ENV = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP",
            "SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "PROCESSOR_ARCHITECTURE", "PROCESSOR_ARCHITEW6432")

def limited_env(extra=()):
    return {key: os.environ[key] for key in (*BASE_ENV, *extra) if key in os.environ}

def interpreter_path(python):
    # Resolving a venv's bin/python symlink selects the base interpreter instead.
    executable = Path(os.path.abspath(os.path.expanduser(str(python))))
    if not executable.is_file() or (os.name == "posix" and not os.access(executable, os.X_OK)):
        raise ValueError("Interpreter must be an executable file")
    return executable

def environment_record():
    spec = runtime_spec()
    executable = interpreter_path(sys.executable)
    return {"schema_version": 2, "spec": spec, "sha256": digest(canonical(spec)),
            "captured_utc": stamp(), "executable": str(executable),
            "executable_realpath": str(executable.resolve(strict=True)),
            "prefix": sys.prefix, "base_prefix": sys.base_prefix,
            "host": platform.node(), "os": platform.system().lower(),
            "platform": platform.platform(), "machine": platform.machine()}

def capture_environment(python, root):
    executable = str(interpreter_path(python))
    result = subprocess.run([executable, "-I", str(Path(root)/"scripts/capture_environment.py"), "--json"],
                            env=limited_env(), check=True, capture_output=True, timeout=60)
    record = parse_json(result.stdout)
    from environment_contract import validate_environment
    validate_environment(record, platform.node(), platform.system().lower())
    if record["executable"] != executable:
        raise ValueError("Captured interpreter differs from the invocation path")
    return record

def finite_number(value, minimum=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum
