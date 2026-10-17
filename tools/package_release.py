#!/usr/bin/env python3
"""Package committed public sources, printable parts and instructions together.

Never reads private staging files or dirty working-tree content. A manifest binds
every included file to its SHA-256 and the selected Git commit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

if __package__:
    from .check import SECRET_PATTERNS, private_path
else:
    from check import SECRET_PATTERNS, private_path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?\Z')


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True).stdout


def build_package(root: Path, ref: str, version: str, output: Path) -> tuple[Path, Path]:
    if not VERSION.fullmatch(version):
        raise ValueError('Version must look like v0.2.0 or v0.2.0-rc.1')
    commit = git(root, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}').decode().strip()
    epoch = int(git(root, 'show', '-s', '--format=%ct', commit))
    timestamp = datetime.fromtimestamp(max(epoch, 315532800), timezone.utc).timetuple()[:6]
    files = {}
    modes = {}
    for entry in git(root, 'ls-tree', '-r', '-z', '--full-tree', commit).split(b'\0'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        path = raw_path.decode('utf-8')
        if (PurePosixPath(path).is_absolute() or '\\' in path or '..' in PurePosixPath(path).parts
                or private_path(path) or path == 'RELEASE-MANIFEST.json'):
            raise ValueError(f'Non-public or reserved path in selected commit: {path}')
        if kind != 'blob' or mode not in {'100644', '100755'}:
            raise ValueError(f'Only regular committed files may be packaged: {path}')
        data = git(root, 'cat-file', 'blob', blob)
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = ''
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            raise ValueError(f'Credential-like content in selected commit: {path} (value suppressed)')
        files[path] = data
        modes[path] = int(mode, 8)
    if not files:
        raise ValueError('Selected commit contains no public files')
    manifest = {
        'version': version,
        'commit': commit,
        'status': 'engineering prototype; physical acceptance remains required',
        'files': {path: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                  for path, data in sorted(files.items())},
    }
    files['RELEASE-MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    modes['RELEASE-MANIFEST.json'] = 0o100644
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'ha-radio-hub-{version}-build-pack.zip'
    checksum = output / f'{archive.name}.sha256'
    if archive.exists() or checksum.exists():
        raise ValueError('Output already exists; use a new empty output directory')
    prefix = f'ha-radio-hub-{version}/'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, data in sorted(files.items()):
            info = zipfile.ZipInfo(prefix + path, timestamp)
            info.create_system = 3
            info.external_attr = modes[path] << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data, compresslevel=9)
    checksum.write_text(f'{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n')
    return archive, checksum


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='Committed revision to package (never the working tree)')
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.build/releases')
    args = parser.parse_args()
    try:
        paths = build_package(ROOT, args.ref, args.version, args.output)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Package failed: {error}\n')
    for path in paths:
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
