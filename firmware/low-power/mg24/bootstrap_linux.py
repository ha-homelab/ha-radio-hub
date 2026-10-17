#!/usr/bin/env python3
"""Download hash-pinned public MG24 tools into a new directory; never flashes."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise SystemExit('This bootstrap is for Linux x86_64; see README for macOS tools.')
    out = args.output.resolve()
    if out.exists():
        raise SystemExit('Output exists; choose a fresh tool directory.')
    out.mkdir(parents=True)
    lock = json.loads((HERE/'dependencies-linux.json').read_text())
    for item in lock['archives']:
        dest = out/item['url'].split('/')[-1]
        print('Downloading', item['name'], item['bytes'], 'bytes', flush=True)
        digest = hashlib.sha256()
        with urllib.request.urlopen(item['url'], timeout=120) as response, dest.open('wb') as f:
            while chunk := response.read(1024*1024):
                digest.update(chunk)
                f.write(chunk)
        if dest.stat().st_size != item['bytes'] or digest.hexdigest() != item['sha256']:
            raise SystemExit('Archive length/SHA256 mismatch: '+item['name'])
        target = out/item['extract_to']
        target.mkdir(exist_ok=True)
        if dest.suffix == '.zip':
            subprocess.run(['unzip','-q',str(dest),'-d',str(target)],check=True)
        else:
            subprocess.run(['tar','-xf',str(dest),'-C',str(target)],check=True)
    paths = {'sdk':str(out/'sdk'), 'slc':str(out/'tools/slc_cli/slc'),
             'gcc':str(out/'tools/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi'),
             'commander':str(out/'tools/commander/commander')}
    for name, path in paths.items():
        if not Path(path).exists():
            raise SystemExit('Missing expected '+name+' path: '+path)
    (out/'paths.json').write_text(json.dumps(paths,indent=2)+'\n')
    print(json.dumps(paths,indent=2))


if __name__ == '__main__':
    main()
