#!/usr/bin/env python3
"""Render actual native silkscreen/mask, then decode its QR independently.

Requires KiCad 10.0.6, CairoSVG, Pillow and zxing-cpp. Green substrate and gold
pad colours are illustrative; shapes and glyph strokes come from KiCad export.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image
import zxingcpp

ROOT = Path(__file__).resolve().parent
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def render(cli):
    version = subprocess.check_output([cli, 'version'], text=True).strip()
    if version != '10.0.6':
        raise ValueError('Rendering requires pinned KiCad 10.0.6')
    qr = json.loads((ROOT / 'silkscreen-qr.json').read_text())
    design = json.loads((ROOT / 'design.json').read_text())
    x1, y1, x2, y2 = design['mechanics']['service_cutout']['bounds_mm']
    with tempfile.TemporaryDirectory() as tmp:
        for side, layer in [('front', 'F'), ('back', 'B')]:
            native = Path(tmp) / (side + '.svg')
            cmd = [cli, 'pcb', 'export', 'svg', '--layers',
                   f'{layer}.Mask,{layer}.Silkscreen,Edge.Cuts', '--mode-single',
                   '--page-size-mode', '2', '--exclude-drawing-sheet', '--subtract-soldermask',
                   '--output', str(native), str(ROOT / 'mc2.kicad_pcb')]
            if side == 'back':
                cmd.insert(4, '--mirror')
            subprocess.run(cmd, check=True)
            copper = ROOT / ('board-top.svg' if side == 'front' else 'board-bottom.svg')
            copper_cmd = [cli, 'pcb', 'export', 'svg', '--layers',
                          f'{layer}.Cu,{layer}.Silkscreen,Edge.Cuts', '--mode-single',
                          '--page-size-mode', '2', '--exclude-drawing-sheet',
                          '--output', str(copper), str(ROOT / 'mc2.kicad_pcb')]
            if side == 'back':
                copper_cmd.insert(4, '--mirror')
            subprocess.run(copper_cmd, check=True)
            raw = native.read_text().replace('#D864FF', '#d4bc75').replace('#F2EDA1', '#faf8ed').replace('#D0D2CD', '#9ac6a7').replace('#02FFEE', '#d4bc75').replace('#E8B2A7', '#faf8ed').replace('#FFFFFF', '#0b1420')
            tree = ET.fromstring(raw)
            tree.find(f'{{{NS}}}title').text = f'MC2-D S1 {side}: native silk and mask, illustrative colours'
            bg = ET.Element(f'{{{NS}}}rect', width='100%', height='100%', fill='#174d38')
            tree.insert(0, bg)
            tree.insert(1, ET.Element(f'{{{NS}}}rect', x=str(x1 if side == 'front' else 100-x2),
                                     y=str(y1), width=str(x2-x1), height=str(y2-y1),
                                     rx='1.5', fill='#0b1420'))
            svg = ROOT / f'silkscreen-{side}.svg'
            svg.write_bytes(ET.tostring(tree, encoding='utf-8', xml_declaration=True))
            cairosvg.svg2png(url=str(svg), write_to=str(svg.with_suffix('.png')),
                            output_width=1600, output_height=1600)
    image = Image.open(ROOT / 'silkscreen-front.png')
    decodes = []
    for size in (1600, 800):
        scanned = zxingcpp.read_barcodes(image.resize((size, size)))
        assert [b.text for b in scanned] == [qr['url']], f'QR decode failed at {size}px'
        decodes.append({'image_width_px': size, 'decoded_url': scanned[0].text})
    files = ['mc2.kicad_pcb', 'silkscreen.py', 'silkscreen-qr.json',
             'render_silkscreen.py', 'silkscreen-front.svg', 'silkscreen-back.svg',
             'silkscreen-front.png', 'silkscreen-back.png', 'board-top.svg', 'board-bottom.svg']
    report = {'artwork_revision': 'S1', 'native_exporter': 'KiCad 10.0.6',
              'qr_decoder': 'zxing-cpp 2.3.0', 'qr_decodes': decodes,
              'qr_module_mm': qr['module_mm'], 'qr_outer_size_mm': len(qr['matrix'])*qr['module_mm'],
              'quiet_zone_modules': 4, 'physical_print_scan_tested': False,
              'source_sha256': {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}}
    (ROOT / 'silkscreen-preview-verification.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cli', required=True)
    render(ap.parse_args().cli)
