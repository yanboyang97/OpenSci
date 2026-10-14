"""Versioned environment identity; a package list alone is not an interpreter."""
from datetime import datetime
from pathlib import PurePosixPath, PureWindowsPath
from common import canonical, digest, require_hash

IDENTITY_KEYS = {"executable", "executable_realpath", "prefix", "base_prefix", "os", "machine"}
RECORD_KEYS = {"schema_version", "spec", "sha256", "captured_utc", "host", "platform"} | IDENTITY_KEYS

def validate_spec(spec):
    if not isinstance(spec, dict) or set(spec) != {"python_implementation", "python_version", "packages"}:
        raise ValueError("Invalid environment specification")
    if any(not isinstance(spec[k], str) or not spec[k].strip() for k in ("python_implementation", "python_version")):
        raise ValueError("Python implementation and version required")
    if not isinstance(spec["packages"], list):
        raise ValueError("Package inventory must be a list")
    entries = []
    for package in spec["packages"]:
        if not isinstance(package, dict) or set(package) != {"name", "version"} or any(not isinstance(v, str) or not v.strip() for v in package.values()):
            raise ValueError("Invalid package inventory entry")
        entries.append((package["name"], package["version"]))
    if entries != sorted(set(entries)):
        raise ValueError("Package inventory must be sorted and unique")

def validate_identity(identity, expected_os):
    if not isinstance(identity, dict) or set(identity) != IDENTITY_KEYS:
        raise ValueError("Complete interpreter identity required")
    if any(not isinstance(v, str) or not v.strip() for v in identity.values()) or identity["os"] != expected_os:
        raise ValueError("Wrong interpreter OS or incomplete identity")
    path_type = PureWindowsPath if expected_os == "windows" else PurePosixPath
    for key in ("executable", "executable_realpath", "prefix", "base_prefix"):
        path = path_type(identity[key])
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Interpreter paths must be absolute")

def task_environment(record):
    return {"spec": record["spec"], "sha256": record["sha256"],
            "interpreter": {key: record[key] for key in sorted(IDENTITY_KEYS)}}

def validate_task_environment(environment):
    if not isinstance(environment, dict) or set(environment) != {"spec", "sha256", "interpreter"}:
        raise ValueError("Task environment requires specification and interpreter identity")
    validate_spec(environment["spec"])
    require_hash(environment["sha256"])
    if digest(canonical(environment["spec"])) != environment["sha256"]:
        raise ValueError("Environment checksum mismatch")
    validate_identity(environment["interpreter"], "linux")

def validate_environment(record, node, expected_os="linux"):
    if not isinstance(record, dict) or set(record) != RECORD_KEYS or type(record["schema_version"]) is not int or record["schema_version"] != 2:
        raise ValueError("Unsupported Execution Environment record; recapture on the target node")
    validate_spec(record["spec"])
    require_hash(record["sha256"])
    if digest(canonical(record["spec"])) != record["sha256"]:
        raise ValueError("Environment checksum mismatch")
    validate_identity({key: record[key] for key in IDENTITY_KEYS}, expected_os)
    if not isinstance(record["host"], str) or not record["host"] or record["host"] != node:
        raise ValueError("Environment was captured on a different target node")
    if not isinstance(record["platform"], str) or not record["platform"].lower().startswith(expected_os):
        raise ValueError("Environment platform disagrees with target OS")
    if not isinstance(record["captured_utc"], str):
        raise ValueError("Capture time required")
    captured = datetime.fromisoformat(record["captured_utc"].replace("Z", "+00:00"))
    if captured.tzinfo is None:
        raise ValueError("Capture time must include timezone")
    return record
