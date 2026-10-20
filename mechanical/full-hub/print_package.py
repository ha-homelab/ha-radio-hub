#!/usr/bin/env python3
"""Publish only allowlisted FH1 STLs with deterministic quantities and hashes.

Independent of the CAD libraries: the checked-in verification report proves
which mesh bytes are current; build.py checks their geometric equivalence.
"""
from pathlib import Path
import argparse
import hashlib
import html
import io
import json
import zipfile

HERE = Path(__file__).resolve().parent
REVISION = 'FH1-MC2-C-RF1'
PCB_REVISION = 'MC2-C'
ARCHIVE = 'FH1-MC2-C-RF1-print-package.zip'
OUTPUTS = ('PRINT-FIRST.txt', 'print-manifest.json', ARCHIVE)
# Explicit inventory, not a directory glob. A spare/private STL is never included.
# stage, stem, label, quantity, role, fit/check note
PARTS = (
    (1, 'fit-coupon', 'Fastener and SMA fit coupon', 1, 'trial', 'Check screw pilots and the actual SMA bulkhead before larger prints.'),
    (1, 'zwave-tray', 'Zooz ZAC93 cradle', 1, 'installed', 'Trial fit the delivered ZAC93, underside socket and mating header first; reuse this cradle if it fits.'),
    (2, 'poe-splitter-tray', 'PoE splitter tray', 1, 'installed', 'For the intact Waveshare POE-SPLITTER-25W-5.5-2.1 case; check captive tails.'),
    (2, 'buck-tray', 'Pololu regulator tray', 1, 'installed', 'Check D24V22F3 underside clearance and the two native mounting holes.'),
    (2, 'wk2132-tray', 'DFR0627 UART bridge tray', 1, 'installed', 'Use insulated edge support and a soft restraint; check actual board edges.'),
    (2, 'cc1101-tray', 'CC1101 tray', 1, 'installed', 'Existing CC1101 vendor variant is unknown; measure it before printing.'),
    (2, 'power-utility-tray', 'DC adapter and fuse tray', 1, 'installed', 'Adapter and fuse dimensions are allocations; confirm both actual parts.'),
    (2, 'radar-holder', 'LD2450 lid holder', 1, 'installed', 'Keep restraints at board ends, clear of the active antenna face.'),
    (2, 'bme680-pod', 'BME680 ventilated pod', 1, 'installed', 'For Adafruit BME680 STEMMA QT 3660; check wire passage and sensor clearance.'),
    (2, 'bme680-pod-lid', 'BME680 pod lid', 1, 'installed', 'Check the sensor and cable are not compressed on closure.'),
    (2, 'pod-arm', 'BME680 pod support arm', 2, 'installed', 'Print TWO identical arms; one STL file supplies both copies.'),
    (3, 'base', 'Main enclosure base', 1, 'installed', 'Print only after all actual modules and tray fits have been checked.'),
    (3, 'lid', 'Main enclosure lid', 1, 'installed', 'Check the 0.8 mm radar window in the slicer; fit and radar performance remain unverified.'),
    (4, 'cc1101-port-blank', 'CC1101 trial-opening blank', 1, 'optional', 'Print only if closing the unused trial opening; it is not an antenna adapter.'),
)
STAGES = {1: 'Print first', 2: 'Check small parts', 3: 'Print large shell last', 4: 'Optional'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'{path.name}: missing regular file (symlinks are not accepted)')
    return path.read_bytes()


def make_manifest(directory, report):
    if report.get('revision') != REVISION or report.get('units') != 'mm':
        raise ValueError('The print package requires the current FH1-MC2-C-RF1 report in millimetres')
    if report.get('native_pcb_revision') != PCB_REVISION:
        raise ValueError('The print package must be checked against the current MC2-C native carrier')
    expected = {row[1] for row in PARTS}
    if set(report.get('parts', {})) != expected:
        raise ValueError('Print inventory differs from the explicit FH1 part allowlist')
    rows = []
    for stage, stem, label, quantity, role, note in PARTS:
        part = report['parts'][stem]
        if type(part.get('quantity')) is not int or part['quantity'] != quantity:
            raise ValueError(f'{stem}: incorrect quantity (expected {quantity})')
        name = stem + '.stl'
        digest = sha(regular_bytes(directory / name))
        if part.get('sha256') != digest or report.get('generated_sha256', {}).get(name) != digest:
            raise ValueError(f'{name}: bytes do not match the current CAD verification hashes')
        rows.append({'stage': stage, 'stage_label': STAGES[stage], 'file': name,
                     'label': label, 'quantity': quantity, 'role': role,
                     'sha256': digest, 'note': note})
    return {'schema_version': 1, 'revision': REVISION, 'native_pcb_revision': PCB_REVISION, 'units': 'mm',
            'scale_percent': 100, 'physical_fit_verified': False,
            'source_report_sha256': sha(regular_bytes(directory / 'verification.json')),
            'unique_stl_files': len(rows),
            'installed_pieces': sum(row['quantity'] for row in rows if row['role'] == 'installed'),
            'trial_only_pieces': 1, 'optional_pieces': 1,
            'pieces_including_trial_and_optional': sum(row['quantity'] for row in rows),
            'parts': rows}


def instructions(manifest):
    lines = [
        'FH1-MC2-C-RF1 PRINT PACKAGE — READ BEFORE SLICING',
        'Engineering prototype. Digital checks do not verify physical fit.',
        'For MC2-C with TinyC6[D] TC6D-01, ESP32-DevKitC-VIE and XIAO MG24.',
        'The Series D Thread radio needs the MC2-C RCP firmware to select',
        'its external U.FL antenna; the original TC6-U-01 firmware will not.',
        'RF1 uses Taoglas CAB.618.E pigtails and ROUND 6.8 mm base holes.',
        'Use the 3 mm thick coupon to check supplied nut/washer engagement.',
        '',
        '1. Print fit-coupon.stl and zwave-tray.stl FIRST.',
        '   With power disconnected, check the real ZAC93 underside socket,',
        '   mating header, antenna clearance, screw pilots and SMA bulkhead.',
        '2. Measure every delivered module. Print and trial-fit the small trays,',
        '   radar holder and pod pieces. Unknown CC1101, fuse and adapter sizes',
        '   must be resolved before committing to the large enclosure.',
        '3. Print base.stl and lid.stl only after those checks pass.',
        '4. Print cc1101-port-blank.stl only if that trial opening is unused.',
        '',
        '14 unique STLs: 13 installed pieces + 1 fit coupon + 1 optional blank.',
        'The pod needs TWO copies of pod-arm.stl. Do not print two ZAC93 cradles:',
        'reuse the trial cradle if it fits. This package contains no G-code.',
        '',
        'SLICER SETTINGS / CHECKS',
        '- Millimetres; 100% scale; preserve each supplied bed orientation.',
        '- Import each STL separately. Assembly/exploded SCAD models are not',
        '  print parts and are deliberately excluded from this package.',
        '- Largest part: 215 x 215 mm. TRONXY XY-3 original nominal volume:',
        '  310 x 310 x 330 mm. Confirm the actual usable bed and nozzle travel.',
        '- A generic 220 x 220 mm bed has only 2.5 mm spare per edge. A 2 mm',
        '  brim is the checked allowance; a wider brim may not fit.',
        '- Use electrically insulating, unfilled filament. Check material',
        '  temperature suitability; no metal/carbon-filled material near radios.',
        '- Inspect layer preview, bridging and supports around horizontal holes.',
        '  Keep the lid radar window 0.8 mm thick; do not auto-fill or drill it.',
        '- No physical fit, structural, ingress-protection or RF approval is',
        '  implied. Dry-fit unpowered; inspect screw ends, wires and clearances.',
        '',
        'QUANTITIES AND PRINT ORDER',
    ]
    for row in manifest['parts']:
        lines += [f"[ ] Stage {row['stage']} | {row['quantity']} x {row['file']} | {row['role']}",
                  '    ' + row['note']]
    lines += ['', 'Assembly and wiring:',
              'https://github.com/ha-homelab/ha-radio-hub/blob/main/docs/full-hub-assembly.md',
              'Editable enclosure, dimensions, sources and fit limitations:',
              'https://github.com/ha-homelab/ha-radio-hub/tree/main/mechanical/full-hub',
              '', 'print-manifest.json records each STL SHA-256 and required quantity.',
              'Hashes identify bytes, not a successful physical trial.']
    return ('\n'.join(lines) + '\n').encode('utf-8')


def payload(directory):
    report = json.loads(regular_bytes(directory / 'verification.json'))
    manifest = make_manifest(directory, report)
    members = {'PRINT-FIRST.txt': instructions(manifest),
               'print-manifest.json': (json.dumps(manifest, indent=2) + '\n').encode('utf-8')}
    members.update({row['file']: regular_bytes(directory / row['file']) for row in manifest['parts']})
    buf = io.BytesIO()
    # STORED deliberately avoids zlib-version-dependent compressed bytes.
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            item.compress_type = zipfile.ZIP_STORED
            archive.writestr(item, data)
    return {'PRINT-FIRST.txt': members['PRINT-FIRST.txt'],
            'print-manifest.json': members['print-manifest.json'], ARCHIVE: buf.getvalue()}


def publish(directory, check=False):
    for name, data in payload(directory).items():
        if check:
            if regular_bytes(directory / name) != data:
                raise ValueError(f'{name}: print package is stale or corrupted; rebuild it')
        else:
            if (directory / name).is_symlink():
                raise ValueError(f'{name}: refusing to overwrite a symlink')
            (directory / name).write_bytes(data)


def print_table():
    rows = []
    for stage, stem, label, quantity, role, note in PARTS:
        rows.append(f'<tr><td>{stage}. {STAGES[stage]}</td><th scope="row"><a href="{stem}.stl">{html.escape(label)}</a></th>'
                    f'<td><strong>{quantity}</strong></td><td>{role}</td><td>{html.escape(note)}</td></tr>')
    return ('<div class="table-scroll"><table><caption>14 STL files: 13 installed pieces, one trial coupon and one optional blank. '
            'The two identical pod arms share one STL.</caption><thead><tr><th scope="col">Print stage</th>'
            '<th scope="col">Part / STL</th><th scope="col">Qty</th><th scope="col">Use</th>'
            '<th scope="col">Check before assembly</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    publish(HERE, check=args.check)
    print('FH1 print package verified.' if args.check else 'FH1 print package written.')


if __name__ == '__main__':
    main()
