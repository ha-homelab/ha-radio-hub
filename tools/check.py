#!/usr/bin/env python3
"""Offline release hygiene: Python syntax, local links, assets and secrets.

Does not claim to validate electronics or runtime behavior. Firmware schema and
compile plus mesh geometry are checked by their own tools.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = [
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
    re.compile(r'AKIA[A-Z0-9]{16}'),
]


def private_path(path: str) -> bool:
    """Reject installation material even if somebody accidentally tracks it."""
    normalized = path.replace('\\', '/').casefold()
    parts = Path(normalized).parts
    name = parts[-1]
    return (
        any(part in {'.git', '.esphome', '.build', '.terraform', '__pycache__',
                     'node_modules', 'private', 'backups', 'otbr-data'}
            or part.startswith('.venv') for part in parts)
        or normalized.startswith('software/runtime/')
        or name == 'secrets.yaml'
        or (name.startswith('.env') and name != '.env.example')
        or 'bot_pat' in name
        or '.tfstate' in name
        or name.endswith(('.tfplan', '.bin', '.gbl', '.hex', '.uf2', '.log', '.pem', '.key'))
    )


def public_paths(root: Path) -> list[Path]:
    # Downloaded build packages have no .git directory. Their manifest provides
    # the public source inventory without walking later-created private files.
    manifest = root / 'RELEASE-MANIFEST.json'
    if not (root / '.git').exists() and manifest.is_symlink():
        raise ValueError('Release inventory must be a regular file')
    if not (root / '.git').exists() and manifest.is_file():
        inventory = json.loads(manifest.read_text())['files']
        if not isinstance(inventory, dict):
            raise ValueError('Invalid public release inventory')
        for name in inventory:
            path = PurePosixPath(name)
            if (not name or path.is_absolute() or '..' in path.parts
                    or '\\' in name or path.as_posix() != name):
                raise ValueError('Release inventory contains an invalid path')
        return [root / name for name in sorted(inventory)] + [manifest]
    # Honor gitignore without overlooking an accidentally tracked private file.
    # In particular, never traverse an operator's private migration workspace.
    result = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=root, check=True, capture_output=True,
    )
    return [root / name for name in sorted(set(result.stdout.decode().split('\0'))) if name]


def main() -> int:
    errors = []
    count = 0
    for path in public_paths(ROOT):
        relative = path.relative_to(ROOT)
        if private_path(relative.as_posix()):
            errors.append(f'{relative}: private/generated installation material must not be tracked')
            continue
        if path.is_symlink():
            errors.append(f'{relative}: symlinks are not permitted in the public build package')
            continue
        if not path.is_file():
            continue
        if path.suffix not in {'.py', '.md', '.json', '.yaml', '.yml', '.sh', '.txt', '.toml'}:
            continue
        text = path.read_text(encoding='utf-8')
        count += 1
        try:
            if path.suffix == '.py':
                ast.parse(text, filename=str(relative))
            elif path.suffix == '.json':
                json.loads(text)
            elif path.suffix == '.sh':
                subprocess.run(['bash', '-n', str(path)], check=True)
            elif path.suffix == '.md':
                for match in re.finditer(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)', text):
                    target = unquote(match.group(1)).split('#', 1)[0]
                    if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                        continue
                    if target.startswith('/') or not (path.parent / target).exists():
                        errors.append(f'{relative}: missing or absolute local link {target}')
        except (ValueError, SyntaxError, subprocess.CalledProcessError) as error:
            errors.append(f'{relative}: {error}')
        if str(relative) != 'tools/check.py':
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    errors.append(f'{relative}: credential-like content detected (value suppressed)')
    required = [
        'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'firmware/hub-s3-eth.yaml',
        'firmware/rf-ethernet.yaml',
        'firmware/packages/ld2450.yaml', 'firmware/packages/bme680.yaml',
        'hardware/README.md', 'hardware/wiring.md', 'docs/enclosure.md',
        'docs/firmware.md', 'docs/home-assistant.md', 'docs/thread-devices.md',
        'mechanical/generated/base.stl', 'mechanical/generated/lid.stl',
    ]
    errors.extend(f'Missing deliverable: {name}' for name in required if not (ROOT / name).is_file())
    pinmap_path = ROOT / 'hardware/pinmap.json'
    if pinmap_path.is_file():
        pinmap = json.loads(pinmap_path.read_text())
        pins = pinmap['exclusive_pins']
        if len({pin['gpio'] for pin in pins}) != len(pins):
            errors.append('Hardware pin map assigns an exclusive GPIO more than once')
        if any(pin['logic_voltage'] != 3.3 for pin in pins):
            errors.append('ESP32 signal map contains a non-3.3V logic domain')
        radio = pinmap['rf_ethernet']
        rf_pins = list(radio['pins'].values())
        reserved = {pin['gpio'] for pin in pins if pin['role'].startswith(('w5500_', 'usb_'))}
        if len(set(rf_pins)) != len(rf_pins) or reserved.intersection(rf_pins):
            errors.append('RF Ethernet GPIO assignment conflicts with another radio signal, W5500 or USB')
        if radio['logic_voltage'] != 3.3 or radio['radio_supply_voltage'] != 3.3:
            errors.append('RF Ethernet CC1101 supply and signal domains must be 3.3V')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Offline checks passed: {count} text files, required assets, local links and credential patterns.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
