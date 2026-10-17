#!/usr/bin/env python3
"""Generate exact MGM240P NCP/bootloader projects; never flashes hardware."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def inspect_sdk(sdk, cfg):
    version = re.search(r'^sdk_version:\s*"([^"]+)"', (sdk/'simplicity_sdk.slcs').read_text(), re.M)
    protocol = re.search(r'^#define\s+EZSP_PROTOCOL_VERSION\s+(0x[0-9a-fA-F]+|\d+)',
                         (sdk/'protocol/zigbee/app/util/ezsp/ezsp-protocol.h').read_text(), re.M)
    if not version or version.group(1) != cfg['sdk_tag'].removeprefix('v'):
        raise RuntimeError('SDK version differs from config.json')
    if not protocol or int(protocol.group(1), 0) != 18:
        raise RuntimeError('SDK does not declare EZSP protocol18')
    # Version headers alone cannot prove an unpacked tree's Git identity.
    return {'verified_sdk_version':version.group(1), 'verified_ezsp_protocol_version':int(protocol.group(1),0),
            'expected_source_commit':cfg['sdk_commit'], 'source_commit_verified':False,
            'scope':'Version/protocol header inspection; unpacked source tree identity is not attested.'}


def configure_headers(directory, item):
    """SLC's --configuration skips commented pin-tool placeholders.

    Set each requested macro in exactly one generated header. Refuse missing or
    ambiguous macros rather than silently compiling the example's default pins.
    The SDK and its original headers are never modified.
    """
    headers = list((directory/'config').glob('*.h'))
    for key, value in item['configuration'].items():
        expression = re.compile(r'^\s*(?://\s*)?#define\s+'+re.escape(key)+r'\s+[^\n]*$', re.M)
        hits = [(path, expression.findall(path.read_text())) for path in headers]
        hits = [(path, matches) for path, matches in hits if matches]
        if sum(len(matches) for _, matches in hits) != 1:
            raise RuntimeError('Expected one generated definition for '+key)
        path = hits[0][0]
        text = expression.sub('#define '+key+' '+value, path.read_text())
        path.write_text(text)
    for filename, warning in item['configured_pin_headers'].items():
        path = directory/'config'/filename
        text = path.read_text()
        exact = '#warning "'+warning+'"'
        if text.count(exact) != 1:
            raise RuntimeError('Unexpected pin-tool template: '+filename)
        text = text.replace(exact, '// Pins explicitly configured by ha-radio-hub generate.py.')
        path.write_text('// Modified by ha-radio-hub generate.py; see config.json.\n'+text)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk', type=Path, required=True)
    p.add_argument('--slc', type=Path, required=True)
    p.add_argument('--gcc', type=Path, required=True, help='Toolchain root containing bin/')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--java-home', type=Path)
    p.add_argument('--kind', choices=['application', 'bootloader', 'both'], default='both')
    args = p.parse_args()
    cfg = json.loads((HERE/'config.json').read_text())
    sdk, slc, gcc, out = [x.resolve() for x in (args.sdk, args.slc, args.gcc, args.output)]
    if out.exists():
        raise SystemExit('Output already exists; choose an empty new output path.')
    for path in [sdk/'simplicity_sdk.slcs', slc, gcc/'bin/arm-none-eabi-gcc']:
        if not path.is_file():
            raise SystemExit('Missing dependency: '+str(path))
    inspected_sdk = inspect_sdk(sdk, cfg)
    env = os.environ.copy()
    env['PATH'] = str(gcc/'bin') + os.pathsep + env['PATH']
    if args.java_home:
        env['JAVA_HOME'] = str(args.java_home.resolve())
        env['PATH'] = str(args.java_home.resolve()/'bin')+os.pathsep+env['PATH']
    def run(command, cwd=None):
        print('RUN', ' '.join(map(str, command)), flush=True)
        return subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)
    version = subprocess.check_output([str(slc), '--version'], env=env, text=True)
    if cfg['slc_version'] not in version:
        raise SystemExit('Expected SLC '+cfg['slc_version']+', got '+version)
    gcc_version = subprocess.check_output([str(gcc/'bin/arm-none-eabi-gcc'), '-dumpfullversion'], text=True).strip()
    if gcc_version != '12.2.1':
        raise SystemExit('Expected GCC12.2.1 from Arm12.2.Rel1, got '+gcc_version)
    out.mkdir(parents=True)
    (out/'sdk-inspection.json').write_text(json.dumps(inspected_sdk,indent=2)+'\n')
    cli_config = out/'slc-cli.cfg'
    run([slc,'configuration','--cli-config',cli_config,'--sdk',sdk,'--gcc-toolchain',gcc])
    run([slc,'signature','trust','--cli-config',cli_config,'--sdk',sdk])
    kinds = ['application','bootloader'] if args.kind=='both' else [args.kind]
    for kind in kinds:
        item = cfg[kind]
        run([slc,'generate',sdk/item['example'],'--cli-config',cli_config,'--sdk',sdk,
             '--with',cfg['target'],'--configuration',','.join(k+':'+v for k,v in item['configuration'].items()),
             '-np','-d',out/kind,'-o','makefile'])
        configure_headers(out/kind, item)
    (out/'input-config.json').write_text(json.dumps(cfg,indent=2)+'\n')


if __name__ == '__main__':
    main()
