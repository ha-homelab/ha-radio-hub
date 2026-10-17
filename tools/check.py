#!/usr/bin/env python3
"""Offline release hygiene: Python syntax, local links, assets and secrets.

Does not claim to validate electronics or runtime behavior. Firmware schema and
compile plus mesh geometry are checked by their own tools.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {'.git', '.venv', '.esphome', '__pycache__', 'node_modules'}
SECRET_PATTERNS = [
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
    re.compile(r'AKIA[A-Z0-9]{16}'),
]


def main() -> int:
    errors = []
    count = 0
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or EXCLUDE.intersection(relative.parts) or any(p.startswith('.venv') for p in relative.parts):
            continue
        if path.name == 'secrets.yaml':
            # Local operator input is intentionally ignored by release checks.
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
        'README.md', 'LICENSE', 'firmware/hub-s3-eth.yaml',
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
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Offline checks passed: {count} text files, required assets, local links and credential patterns.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
