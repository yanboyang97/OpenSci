"""Verify separately restored resource files using stable IDs and local mappings."""
import argparse
from pathlib import Path

from storage_paths import plain_path, safe_name
from common import digest, file_hash, print_json, read_json, require_hash, valid_id


def verify_resources(manifest, device):
    if manifest.get('schema_version') != 1 or device.get('schema_version') != 1:
        raise ValueError('Unsupported Resource Catalog or Device Mapping; use the supplied examples')
    resources = manifest.get('resources')
    locations = device.get('resource_locations')
    if not isinstance(resources, list) or not isinstance(locations, dict):
        raise ValueError('Declare resources and device resource_locations')
    reports, seen = [], set()
    for resource in resources:
        key = resource.get('resource_id')
        if not valid_id(key) or key in seen:
            raise ValueError('Unique stable resource_id required')
        seen.add(key)
        if not isinstance(resource.get('version'), str) or not resource['version'].strip():
            raise ValueError('Resource version required')
        files = resource.get('files')
        if not isinstance(files, list) or not files:
            raise ValueError('Each resource needs an explicit file inventory')
        expected, folded = [], set()
        for item in files:
            name = safe_name(item['path'])
            if name.casefold() in folded:
                raise ValueError('Duplicate portable resource path')
            folded.add(name.casefold()); require_hash(item['sha256'])
            expected.append((name, item['sha256']))
        location = locations.get(key)
        if not location:
            reports.append({'resource_id': key, 'status': 'unmapped', 'files': []})
            continue
        if not isinstance(location, str) or not Path(location).is_absolute():
            raise ValueError('Device locations must be absolute paths on this host')
        root = plain_path(location)
        results = []
        for name, checksum in expected:
            path = plain_path(root/name)
            status = 'missing' if not path.is_file() else 'verified' if file_hash(path) == checksum else 'mismatch'
            results.append({'path': name, 'status': status})
        reports.append({'resource_id': key, 'version': resource['version'],
                        'status': 'verified' if all(f['status'] == 'verified' for f in results) else 'incomplete',
                        'files': results})
    return {'schema_version': 1, 'resources': reports,
            'status': 'no_resources_declared' if not reports else 'verified' if all(r['status'] == 'verified' for r in reports) else 'incomplete',
            'scope': 'listed file bytes only; extra files, software, licensing and scientific reproducibility are not checked',
            'scientific_reproducibility': 'not_tested'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--device', type=Path, required=True)
    args = p.parse_args()
    try:
        manifest, raw = read_json(args.manifest, args.expected_sha256)
        device = read_json(args.device)[0]
        result = verify_resources(manifest, device)
        result['manifest_sha256'] = digest(raw)
        print_json(result)
        return 0 if result['status'] == 'verified' else 2
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
