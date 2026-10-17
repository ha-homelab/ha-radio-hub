#!/usr/bin/env python3
"""Build the offline wiring atlas and printable pin-to-pin diagrams.

The electrical data is reviewed separately in connections.json. Drawings use
logical port placement, not invented physical header positions.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def physical(pin: dict) -> str:
    p = pin['physical']
    if p.get('position') is None or p.get('status') == 'unknown':
        return 'Physical position: verify module markings'
    if p.get('status') != 'datasheet_verified':
        return f"Project pin {p['position']} — confirm exact board revision"
    kind = p.get('namespace', '').replace('_', ' ')
    return f"{kind}: {p['position']}"


def rows_for(component: dict, data: dict) -> list[dict]:
    components = {c['id']: c for c in data['components']}
    result = []
    for pin in component['pins']:
        matched = False
        for net in data['nets']:
            if not any(m['component'] == component['id'] and m['pin'] == pin['id'] for m in net['members']):
                continue
            matched = True
            others = []
            for m in net['members']:
                if m['component'] == component['id'] and m['pin'] == pin['id']:
                    continue
                other = components[m['component']]
                other_pin = next(p for p in other['pins'] if p['id'] == m['pin'])
                others.append(f"{other['title']} / {other_pin['label']} ({physical(other_pin)})")
            if net['kind'] in ('power', 'ground'):
                destination = net['title'] + ' — shared supply net'
            else:
                destination = '; '.join(others) or net['title']
            result.append({'pin': pin, 'net': net, 'destination': destination})
        if not matched and pin.get('termination'):
            text = pin['termination'].replace('_', ' ').capitalize()
            result.append({'pin': pin, 'net': {'id': 'not_wired', 'kind': 'unconnected'}, 'destination': text})
    return result


def diagram(component: dict, data: dict) -> str:
    rows = rows_for(component, data)
    y, blocks = 190, []
    for row in rows:
        pin, net = row['pin'], row['net']
        destination = textwrap.wrap(row['destination'], 52) or ['Unconnected']
        h = max(92, 32 + len(destination) * 19)
        color = '#b45309' if net['kind'] == 'power' else '#526375' if net['kind'] == 'ground' else '#0f766e'
        direction = pin.get('direction', '') if net['kind'] != 'unconnected' else 'unconnected'
        attrs = ''
        if direction == 'output':
            attrs = ' marker-end="url(#arrow)"'
        elif direction == 'input':
            attrs = ' marker-start="url(#arrowback)"'
        elif direction == 'bidirectional':
            attrs = ' marker-end="url(#arrow)" marker-start="url(#arrowback)"'
        blocks.append(f'<rect x="28" y="{y}" width="1124" height="{h-8}" rx="6" fill="#f1f5f8"/>')
        blocks.append(f'<text x="44" y="{y+27}" class="pin">{esc(pin["label"])}</text>')
        blocks.append(f'<text x="44" y="{y+49}" class="small">{esc(physical(pin))}</text>')
        if net['kind'] == 'unconnected':
            blocks.append(f'<path d="M485 {y+23}l18 18m-18 0l18 -18" stroke="#526375" stroke-width="2"/>')
        else:
            blocks.append(f'<path d="M365 {y+32} H625" fill="none" stroke="{color}" stroke-width="2"{attrs}/>')
        blocks.append(f'<text x="495" y="{y+60}" text-anchor="middle" class="small">{esc(net["id"])}</text>')
        for index, line in enumerate(destination):
            blocks.append(f'<text x="652" y="{y+27+index*19}" class="target">{esc(line)}</text>')
        y += h
    height = y + 80
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 {height}" role="img" aria-labelledby="title desc">
<title id="title">{esc(component['title'])}: pin-to-pin connection sheet</title>
<desc id="desc">Logical connection drawing. Port positions do not represent a physical header. Verified pad numbers and unknown positions are identified separately.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#0f766e"/></marker><marker id="arrowback" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M10 0L0 5L10 10z" fill="#0f766e"/></marker></defs>
<style>text{{font-family:Arial,sans-serif;fill:#172b3a}}.pin{{font-size:19px;font-weight:600}}.target{{font-size:16px}}.small{{font-size:13px;fill:#526375}}</style>
<rect width="1180" height="{height}" fill="white"/>
<text x="28" y="44" font-size="16" fill="#0f766e">HA RADIO HUB · {esc(data['revision'])} · CONNECTION ATLAS</text>
<text x="28" y="82" font-size="30" font-weight="700">{esc(component['title'])}</text>
<text x="28" y="114" font-size="17">{esc(component['model'])}</text>
<text x="28" y="144" class="small">Logical port order — NOT a connector face. Use verified pad labels; check unverified module markings.</text>
<text x="44" y="177" class="small">THIS COMPONENT</text><text x="652" y="177" class="small">CONNECTED ENDPOINT / SUPPLY</text>
{''.join(blocks)}
<text x="28" y="{y+24}" class="small">Orange = supply; gray = ground; green = signal. MG24 RESETn uses internal DVDD; never drive it high.</text>
<text x="28" y="{y+46}" class="small">Design contract, not a record of tested hardware. Source: hardware/low-power/visual/connections.json.</text>
</svg>'''


def generate() -> dict[str, bytes]:
    raw = (ROOT / 'connections.json').read_bytes()
    data = json.loads(raw)
    inputs = {'connections.json': hashlib.sha256(raw).hexdigest()}
    assets = {}
    data['boards'] = []
    for key, directory, title in [
            ('carrier', 'carrier', 'Ready-module carrier'),
            ('integrated', 'integrated', 'Integrated radio board'),
            ('mg24-adapter', 'carrier/mg24-adapter', 'MG24 daughterboard for carrier'),
            ('diy', 'diy', 'DIY single-sided board with insulated links')]:
        path = ROOT.parent / directory / 'connectors.json'
        if path.exists():
            board_raw = path.read_bytes()
            inputs[f'../{directory}/connectors.json'] = hashlib.sha256(board_raw).hexdigest()
            board = json.loads(board_raw)
            board.update(id=key, title=title)
            if key == 'diy':
                board['wiring_note'] = ('D0 uses bottom copper plus the numbered insulated wire links in its assembly instructions. '
                                        'It needs the external M0 radio adapter. J10 is JST XH 2.50 mm, not the C0 JST SH/QT socket; '
                                        'use the verified XH-to-factory-QT cable. The net roles are unchanged.')
            overview = ROOT.parent / directory / ('fabrication' if key == 'integrated' else 'outputs') / 'assembly-top.svg'
            if overview.exists():
                payload = overview.read_bytes()
                name = key + '-assembly.svg'
                assets[name] = payload
                board['overview_file'] = name
                inputs['../' + str(overview.relative_to(ROOT.parent))] = hashlib.sha256(payload).hexdigest()
            data['boards'].append(board)
    catalog_path = ROOT / 'physical' / 'catalog.json'
    data['physical_drawings'] = {}
    if catalog_path.exists():
        inputs['physical/catalog.json'] = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
        for module in json.loads(catalog_path.read_text())['modules']:
            filename = module['id'] + '-contacts.svg'
            path = ROOT / 'physical' / 'generated' / filename
            payload = path.read_bytes()
            inputs['physical/generated/' + filename] = hashlib.sha256(payload).hexdigest()
            assets[filename] = payload
            component_id = {'wiz850io': 'w5500', 'pololu': 'buck'}.get(module['id'], module['id'])
            data['physical_drawings'][component_id] = {
                'file': filename, 'title': module['title'], 'notes': module['notes'],
                'check': module['check'], 'source': module['source'],
            }
    encoded = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    template = (ROOT / 'viewer.template.html').read_text()
    assert template.count('__CONNECTION_DATA__') == 1
    inputs['viewer.template.html'] = hashlib.sha256(template.encode()).hexdigest()
    output = {'index.html': template.replace('__CONNECTION_DATA__', encoded).encode(), **assets}
    for component in data['components']:
        if rows_for(component, data):
            output[component['id'] + '-connections.svg'] = diagram(component, data).encode()
    manifest = {'schema_version': 2, 'input_sha256': dict(sorted(inputs.items())),
                'files': {name: hashlib.sha256(value).hexdigest() for name, value in sorted(output.items())}}
    output['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    destination = ROOT / 'generated'
    output = generate()
    if args.check:
        stale = [name for name, value in output.items() if not (destination / name).is_file() or (destination / name).read_bytes() != value]
        extra = [p.name for p in destination.iterdir() if p.is_file() and p.name not in output] if destination.exists() else []
        if stale or extra:
            raise SystemExit(f'Stale wiring atlas: {stale}; unexpected files: {extra}')
        print(f'PASS: {len(output)} reproducible wiring-atlas files.')
    else:
        destination.mkdir(exist_ok=True)
        for name, value in output.items():
            (destination / name).write_bytes(value)
        print(f'Built {len(output)} wiring-atlas files in {destination}')


if __name__ == '__main__':
    main()
