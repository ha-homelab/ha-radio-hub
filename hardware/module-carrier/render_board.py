#!/usr/bin/env python3
"""Render MC1 from its native PCB, keeping source and output provenance."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dimensions(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    return list(struct.unpack('>II', raw[16:24]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', default='kicad-cli')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    board = HERE / 'cad/mc1.kicad_pcb'
    out = HERE / 'images'
    manifest_path = out / 'native-render-provenance.json'
    if args.check:
        manifest = json.loads(manifest_path.read_text())
        assert manifest['board_sha256'] == digest(board), 'Stale native render source'
        for name, record in manifest['images'].items():
            assert record['sha256'] == digest(out / name), name
            assert record['dimensions_px'] == dimensions(out / name), name
        print('MC1 native render provenance verified')
        return
    manifest = {
        'source': board.relative_to(ROOT).as_posix(),
        'board_sha256': digest(board),
        'kicad_version': subprocess.check_output([args.kicad_cli, 'version'], text=True).strip(),
        'representation': 'Native PCB render, not a physical assembly photograph',
        'images': {},
    }
    for side in ['top', 'bottom']:
        name = f'mc1-board-{side}.png'
        options = ['--width', '1600', '--height', '1050', '--side', side,
                   '--background', 'transparent', '--quality', 'high',
                   '--perspective', '--rotate', '335,0,15', '--zoom', '0.70']
        subprocess.run([args.kicad_cli, 'pcb', 'render', str(board), '-o', str(out/name), *options], check=True)
        manifest['images'][name] = {'sha256': digest(out/name),
                                   'dimensions_px': dimensions(out/name), 'options': options}
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print('Rendered MC1 top and bottom from native PCB')

if __name__ == '__main__':
    main()
