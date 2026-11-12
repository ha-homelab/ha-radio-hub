#!/usr/bin/env python3
"""Stage the committed public project for GitHub Pages, never operator files."""
import argparse
from pathlib import Path
import shutil
import subprocess
from check import private_path, public_file

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output = output.resolve()
    if output.exists():
        raise ValueError('Choose a new, empty output directory')
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = []
    for name in sorted(set(names) - {''}):
        if private_path(name) or not public_file(ROOT, ROOT / name):
            raise ValueError(f'Unsafe public source: {name}')
        files.append(name)
    if 'guide/index.html' not in files:
        raise ValueError('Missing generated guide')
    output.mkdir(parents=True)
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (output / '.nojekyll').write_text('')
    (output / 'index.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta http-equiv="refresh" content="0;url=guide/index.html"><title>HA Radio Hub build guide</title>
<link rel="canonical" href="https://ha-homelab.github.io/ha-radio-hub/guide/index.html"></head>
<body><h1>HA Radio Hub</h1><p><a href="guide/index.html">Open the build guide</a></p></body></html>
''')
    print(f'Staged {len(files)} committed public files at {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    build(parser.parse_args().output)
