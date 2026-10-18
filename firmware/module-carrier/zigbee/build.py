#!/usr/bin/env python3
"""Build/verify already generated MC1 XIAO MG24 projects; all Commander calls are offline."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def srecords(path):
    """Decode addressed data, rejecting malformed checksums or conflicting bytes."""
    data = {}
    for line in path.read_text().splitlines():
        if not line:
            continue
        if not re.fullmatch(r'S[0-9][0-9A-Fa-f]+', line):
            raise ValueError('Malformed S-record')
        record = bytes.fromhex(line[2:])
        if record[0] != len(record)-1 or sum(record) & 255 != 255:
            raise ValueError('S-record length/checksum mismatch')
        if line[1] not in '123':
            continue
        width = int(line[1])+1
        address = int.from_bytes(record[1:1+width], 'big')
        for offset, byte in enumerate(record[1+width:-1]):
            at = address+offset
            if at in data and data[at] != byte:
                raise ValueError('Conflicting S-record bytes')
            data[at] = byte
    if not data:
        raise ValueError('No S-record data')
    return data


def macro(directory, key):
    found = []
    for path in (directory/'config').glob('*.h'):
        found.extend(re.findall(r'^\s*#define\s+'+re.escape(key)+r'\s+([^\n]+)', path.read_text(), re.M))
    if len(found) != 1:
        raise ValueError('Expected exactly one active definition: '+key)
    return found[0].strip()


def check_configuration(project, config):
    if json.loads((project/'input-config.json').read_text()) != config:
        raise ValueError('Generated input does not match committed config.json')
    for kind in ('application', 'bootloader'):
        for key, expected in config[kind]['configuration'].items():
            if macro(project/kind, key) != expected:
                raise ValueError('Wrong generated configuration: '+key)
    board_source = (HERE/'mc1_board_init.h').read_text()
    if (project/'application/autogen/mc1_board_init.h').read_text() != board_source:
        raise ValueError('Board RF initialization differs from committed source')
    events = (project/'application/autogen/sl_event_handler.c').read_text()
    if events.count('  mc1_xiao_board_init();') != 1 or '  sl_gpio_init();\n  mc1_xiao_board_init();' not in events:
        raise ValueError('RF initialization must run in GPIO driver phase before radio stack')


def check_vectors(data, start, end):
    if not all(start+i in data for i in range(8)):
        raise ValueError('Missing vector table')
    sp = int.from_bytes(bytes(data[start+i] for i in range(4)), 'little')
    reset = int.from_bytes(bytes(data[start+i] for i in range(4,8)), 'little')
    if not 0x20000000 < sp <= 0x20040000 or not reset & 1 or not start <= reset-1 < end:
        raise ValueError('Invalid stack/reset vector')


def verify_images(app_path, boot_path, merged_path, roundtrip_path):
    app, boot, merged, roundtrip = map(srecords, (app_path, boot_path, merged_path, roundtrip_path))
    if not all(0x08000000 <= x < 0x08006000 for x in boot):
        raise ValueError('Bootloader data outside reserved 24KiB')
    if not all(0x08006000 <= x < 0x0817E000 for x in app):
        raise ValueError('Application data outside linked flash region')
    if app.keys() & boot.keys():
        raise ValueError('Application/bootloader overlap')
    if merged != {**boot, **app}:
        raise ValueError('Merged image changed or omitted bytes')
    if roundtrip != app:
        raise ValueError('GBL application roundtrip differs')
    check_vectors(boot, 0x08000000, 0x08006000)
    check_vectors(app, 0x08006000, 0x0817E000)
    return {name: {'data_bytes': len(data), 'first_address': hex(min(data)), 'last_address': hex(max(data))}
            for name, data in [('bootloader',boot), ('application',app), ('combined',merged)]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True, type=Path)
    p.add_argument('--gcc', required=True, type=Path)
    p.add_argument('--commander', required=True, type=Path)
    p.add_argument('--jobs', type=int, default=4)
    args = p.parse_args()
    project, gcc, commander = (x.resolve() for x in (args.project,args.gcc,args.commander))
    config = json.loads((HERE/'config.json').read_text())
    inspected_sdk = json.loads((project/'sdk-inspection.json').read_text())
    if inspected_sdk['verified_sdk_version'] != config['sdk_tag'].removeprefix('v') or inspected_sdk['verified_ezsp_protocol_version'] != 18:
        raise ValueError('SDK inspection does not match this recipe')
    check_configuration(project, config)
    version = subprocess.check_output([str(commander), '--version'], text=True)
    if '1v25p0b1995' not in version:
        raise SystemExit('Expected Simplicity Commander 1.25.0 build1995')
    if subprocess.check_output([str(gcc/'bin/arm-none-eabi-gcc'), '-dumpfullversion'],text=True).strip() != '12.2.1':
        raise SystemExit('Expected GNU Arm 12.2.Rel1 / GCC12.2.1')
    def run(command, cwd=None):
        print('RUN', ' '.join(map(str,command)), flush=True)
        subprocess.run(list(map(str,command)),cwd=cwd,check=True)
    for kind in ('application','bootloader'):
        run(['make','-f',config[kind]['name']+'.Makefile','release','-j'+str(args.jobs),
             'ARM_GCC_DIR='+str(gcc),'POST_BUILD_EXE='+str(commander)],project/kind)
    artifacts = project/'artifacts'
    artifacts.mkdir(exist_ok=True)
    app = project/'application/build/release/zigbee_ncp_uart_hw.s37'
    boot = project/'bootloader/artifact/bootloader-uart-xmodem-crc.s37'
    gbl, merged, roundtrip = [artifacts/name for name in ('mc1-xiao-mg24-ncp.gbl','mc1-xiao-mg24-initial.s37','ncp-roundtrip.s37')]
    run([commander,'gbl','create',gbl,'--app',app])
    run([commander,'convert',boot,app,'--outfile',merged])
    initial_hex = artifacts/'mc1-xiao-mg24-initial.hex'
    hex_roundtrip = artifacts/'initial-hex-roundtrip.s37'
    run([commander,'convert',merged,'--outfile',initial_hex])
    run([commander,'convert',initial_hex,'--outfile',hex_roundtrip])
    if srecords(hex_roundtrip) != srecords(merged):
        raise ValueError('CMSIS-DAP Intel HEX roundtrip differs from initial image')
    run([commander,'gbl','parse',gbl,'--app',roundtrip])
    ranges = verify_images(app,boot,merged,roundtrip)
    report = {'status':'build-and-offline-validation-pass', 'hardware_tested':False,
              'sdk_tag':config['sdk_tag'], 'sdk_inspection':inspected_sdk,
              'board':config['board'], 'board_sku':config['board_sku'],
              'board_configuration':config['application']['configuration'],
              'target':config['target'],'ezsp_protocol_version':inspected_sdk['verified_ezsp_protocol_version'],
              'flash_ranges':ranges,'files':{}}
    report['recipe_sha256'] = {
        name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        for name in ('config.json', 'mc1_board_init.h', 'generate.py', 'build.py')
    }
    report['tools'] = {
        'slc': config['slc_version'], 'gcc': '12.2.1',
        'commander': '1.25.0 build1995',
    }
    report['validation'] = [
        'Both generated projects match committed UART/pin/clock configuration',
        'Board RF initialization is present before radio stack startup',
        'Both Cortex-M vector tables and non-overlapping flash ranges are valid',
        'Initial S37 exactly equals bootloader plus application addressed bytes',
        'GBL and Intel HEX roundtrips retain all addressed bytes',
    ]
    python_inspection = project/'python-inspection.json'
    if python_inspection.is_file():
        report['python_inspection'] = json.loads(python_inspection.read_text())
    for path in (app,boot,gbl,merged,initial_hex):
        report['files'][str(path.relative_to(project))] = {
            'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (artifacts/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
