#!/usr/bin/env python3
"""Check the offboard power substitution against the unchanged MC2-D interface."""
import argparse
import csv
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
EXPECTED_J2 = [('1', '+5V', '1'), ('2', 'GND', '2'), ('3', '+3V3', '3'), ('4', 'GND', '2')]


def read_json(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data, parts, connectors, harnesses):
    """Cross-check the assembly, source boundaries and actual carrier endpoints."""
    parts = {p['ref']: p for p in parts}
    connectors = {p['ref']: p for p in connectors}
    harnesses = {h['ref']: h for h in harnesses}
    require(data['regulator']['part'] == 'R-78K3.3-1.0', 'regulator substitution requires a fresh electrical review')
    mapping = [(p['carrier_pin'], p['net'], p['regulator_pin']) for p in data['j2_mapping']]
    require(mapping == EXPECTED_J2, 'J2 regulator mapping must preserve VIN/GND/VOUT/GND')
    require(data['regulator']['pin_map'] == {'1': 'VIN', '2': 'GND', '3': 'VOUT'}, 'RECOM SIP pin map')
    for pin, net, regulator_pin in mapping:
        require(parts['J2']['pins'][pin] == net, 'J2 native schematic power mismatch')
        physical = next(p for p in connectors['J2']['pad_centers_mm'] if p['number'] == pin)
        require(physical['net'] == net, 'J2 physical pad power mismatch')
        harness = next(p for p in harnesses['J2']['pins'] if p['carrier_pin'] == pin)
        require(harness['net'] == net and harness['device_pin'] == regulator_pin, 'J2 public harness mapping mismatch')
    require(parts['J1']['pins'] == {'1': '+5V', '2': 'GND'}, 'fused input must remain 5 V')
    require(data['input_connection']['carrier_net'] == '+5V' and data['input_connection']['before_radio_isolation_diodes'], 'buck must use fused 5 V before radio diodes')
    for ref, supply, pin in [('U1', '+5V_HOST', 'J2.19'), ('U2', '+5V_C6', '14'), ('U3', '+5V_ZB', '14')]:
        require(parts[ref]['pins'][pin] == supply and '+3V3' not in parts[ref]['pins'].values(), f'{ref} local regulator must not join peripheral rail')
    for ref, supply in [('D1', '+5V_HOST'), ('D2', '+5V_C6'), ('D3', '+5V_ZB')]:
        require(parts[ref]['pins'] == {'1': supply, '2': '+5V'}, f'{ref} isolation/input boundary changed')
    require(parts['J6']['pins']['1'] == '+5V', 'radar must remain on 5 V')
    expected_consumers = {('U4', 'J2.2'), ('U4', 'J2.3'), ('J3', '1'), ('J4', '1'), ('J5', '1'), ('J7', '2'), ('R1', '1'), ('R2', '1')}
    actual_consumers = {(ref, pin) for ref, p in parts.items() for pin, net in p['pins'].items() if net == '+3V3' and ref != 'J2'}
    require(actual_consumers == expected_consumers, 'peripheral rail consumers changed: recalculate the budget')
    loads = data['rail_loads']
    require({p['id'] for p in loads} == {'ethernet', 'zwave', 'rf', 'uart', 'environment', 'misc'}, 'load budget incomplete')
    reserve = sum(p['engineering_reserve_ma'] for p in loads)
    rated = data['regulator']['rated_output_ma']
    require(0 < reserve < rated and reserve == data['budget']['peripheral_reserve_ma'], 'peripheral reserve total/rating mismatch')
    require(rated - reserve == data['budget']['unused_rated_capacity_ma'], 'reserve margin mismatch')
    require(rated / reserve == data['budget']['rated_capacity_to_reserve_ratio'], 'reserve ratio mismatch')
    require(not data['hardware_measured'] and data['acceptance']['status'] == 'not_run', 'Do not promote engineering reserves to measured qualification')
    require(data['acceptance']['input_min_v'] >= data['regulator']['input_v'][0], 'acceptance permits undervoltage operation')
    cap = data['input_capacitor']
    require(cap['capacitance_uf'] == 27 and cap['voltage_rating_v'] >= 10, 'hard-plug input capacitor missing or unsuitable')
    require((cap['positive_regulator_pin'], cap['negative_regulator_pin']) == ('1', '2'), 'input capacitor polarity/rail mismatch')
    validate_measurement_plan(data, parts)
    validate_perfboard(data)
    return {'reserve_ma': reserve, 'rated_ma': rated, 'hardware_measured': False}


def validate_measurement_plan(data, parts):
    """Keep the unmeasured bench gate separate from schematic/build evidence."""
    plan = data['acceptance']['measurement_plan']
    require(plan['status'] == 'not_run', 'measurement plan is not physical qualification')
    require(plan['worksheet'] == 'power-measurements.csv', 'measurement worksheet path changed')
    rows = {row['id']: row for row in plan['rows']}
    expected = {'recom_input', 'peripheral_output', 'zac93_local_supply',
                'host_regulator_input', 'host_local_3v3', 'c6_local_3v3',
                'mg24_local_3v3', 'host_gpio12_boot', 'host_gpio2_download'}
    require(set(rows) == expected and len(rows) == len(plan['rows']), 'missing or duplicated rail/strap measurement')
    for key, ref, pin, ground in [('host_local_3v3', 'U1', 'J2.1', 'J2.14'),
                                   ('c6_local_3v3', 'U2', '12', '13'),
                                   ('mg24_local_3v3', 'U3', '12', '13')]:
        require(rows[key]['positive_probe'] == f'{ref}.{pin} local 3V3', 'local rail measurement must probe its own regulator')
        require(rows[key]['ground_probe'] == f'{ref}.{ground} GND', 'local rail measurement ground mismatch')
        require(parts[ref]['pins'][pin] is None and parts[ref]['pins'][ground] == 'GND', 'local rail test point must remain unconnected except by the meter')
    for key in ['peripheral_output', 'zac93_local_supply', 'host_local_3v3', 'c6_local_3v3', 'mg24_local_3v3']:
        require(rows[key]['kind'] == 'regulated_rail' and rows[key]['acceptance_v'] == [3.135, 3.465], '3.3 V measurement target must include each independent rail')
    require(rows['recom_input']['minimum_v'] >= data['regulator']['input_v'][0], 'measurement plan permits RECOM undervoltage')
    host = rows['host_regulator_input']
    require(host['kind'] == 'regulator_headroom' and 'minimum_v' not in host, 'host input needs a fitted-regulator dropout assessment, not a RECOM cutoff')
    require(host['positive_probe'] == 'U1.J2.19 / D1 cathode / EXT_5V', 'host dropout must be measured after D1')
    for key, probe in [('host_gpio12_boot', 'U1.J2.13 GPIO12 / R4.2'),
                       ('host_gpio2_download', 'U1.J3.15 GPIO2 / R5.2')]:
        require(rows[key]['kind'] == 'boot_low' and rows[key]['positive_probe'] == probe, 'boot measurement endpoint mismatch')
        require(rows[key]['maximum_fraction_of_local_vdd'] == 0.25, 'boot LOW limit must use local VDD and the datasheet threshold')


def render_measurements(data):
    """Export a blank copyable checklist; never overwrite an operator's results."""
    fields = ['id', 'positive_probe', 'ground_probe', 'conditions', 'acceptance',
              'source', 'measured_min_v', 'measured_max_v', 'load_ma',
              'temperature_c', 'waveform_file', 'status', 'notes']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in data['acceptance']['measurement_plan']['rows']:
        record = {key: row[key] for key in fields if key in row}
        record['status'] = 'not_run'
        writer.writerow(record)
    return stream.getvalue()


def require_blank_worksheet(text):
    for row in csv.DictReader(io.StringIO(text)):
        entered = any(row.get(key, '') for key in ['measured_min_v', 'measured_max_v',
                      'load_ma', 'temperature_c', 'waveform_file', 'notes'])
        require(not entered and row.get('status', '') in ['', 'not_run'],
                'save filled measurement results under another name before regenerating the blank worksheet')


def validate_perfboard(data):
    board = data['perfboard']
    require(board['size_mm'] == [24, 24, 1.6], 'power daughterboard envelope changed')
    require(board['removed_pad_rows'] == [8] and board['bare_strap_band_y_mm'] == [20.5, 23], 'rear strap band must remain bare FR4')
    reg = board['regulator_pads']
    cap = board['capacitor_pads']
    harness = board['harness_pads']
    require(reg == {'1': 'B3', '2': 'C3', '3': 'D3'}, 'SIP orientation changed')
    require(cap == {'positive': 'G3', 'negative': 'H3'}, 'capacitor pad orientation changed')
    expected = {
        '+5V': {reg['1'], cap['positive'], harness['1']},
        'GND': {reg['2'], cap['negative'], harness['2'], harness['4']},
        '+3V3': {reg['3'], harness['3']},
    }
    pad_net = {pad: net for net, pads in expected.items() for pad in pads}
    require(len(pad_net) == sum(map(len, expected.values())), 'different power nets share a pad')
    edges = {pad: set() for pad in pad_net}
    for link in board['links']:
        a, b, net = link['from'], link['to'], link['net']
        require(a in pad_net and b in pad_net and pad_net[a] == pad_net[b] == net, 'perfboard link shorts power nets')
        edges[a].add(b)
        edges[b].add(a)
    for net, pads in expected.items():
        visited, pending = set(), [next(iter(pads))]
        while pending:
            pad = pending.pop()
            if pad in visited:
                continue
            visited.add(pad)
            pending.extend(edges[pad] - visited)
        require(visited == pads, f'perfboard {net} has disconnected pads')


def validate_companions(data, mechanical, procurement):
    buck = next(p for p in mechanical['components'] if p['id'] == 'buck')
    require(data['regulator']['part'] in buck['model'], 'mechanical buck model differs')
    require(buck['body_mm'] == data['regulator']['body_mm'], 'mechanical regulator body differs')
    mount = buck['mount']
    require(mount['perfboard_mm'] == data['perfboard']['size_mm'], 'mechanical power PCB differs')
    require('EEU-FS1H270' in mount['capacitor_model'], 'mechanical capacitor model differs')
    require(mount['capacitor_max_body_mm'] == [5.5, 5.5, 12.5], 'mechanical capacitor envelope differs')
    offers = procurement['major_component_offers']
    require(any(data['regulator']['part'] in p['part'] for p in offers), 'purchase list lacks selected regulator')
    require(any('EEU-FS1H270' in p['part'] for p in procurement['power_accessory_offers']), 'purchase list lacks input capacitor')


def render_perfboard(data):
    """Two actual viewing sides; letters reverse on the solder-side view."""
    colors = {'+5V': '#b91c1c', 'GND': '#334155', '+3V3': '#047857'}
    scale = 15
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="790" viewBox="0 0 1220 790">',
           '<rect width="1220" height="790" fill="#f8fafc"/>',
           '<g font-family="Arial, sans-serif" fill="#0f172a">',
           '<text x="36" y="43" font-size="25" font-weight="bold">PWR1 — hand-wired RECOM power daughterboard</text>',
           '<text x="36" y="74" font-size="16">24 × 24 × 1.6 mm isolated-pad perfboard · 2.54 mm pitch · no stripboard tracks · not to scale for drilling</text>']
    def xy(pad, ox, oy, mirror):
        x = 3.11 + 'ABCDEFGH'.index(pad[0]) * 2.54
        y = 3.11 + (int(pad[1])-1) * 2.54
        return ox + (24-x if mirror else x)*scale, oy+y*scale
    for ox, mirror, title in [(50, False, 'COMPONENT SIDE — fit parts'), (670, True, 'SOLDER SIDE — flip left/right')]:
        oy = 155
        svg.append(f'<text x="{ox}" y="122" font-size="20" font-weight="bold">{title}</text>')
        svg.append(f'<rect x="{ox}" y="{oy}" width="360" height="360" rx="5" fill="#dce7db" stroke="#3f6212" stroke-width="2"/>')
        svg.append(f'<rect x="{ox+30}" y="{oy+30}" width="300" height="300" fill="none" stroke="#64748b" stroke-dasharray="4 4"/>')
        svg.append(f'<rect x="{ox+30}" y="{oy+20.5*scale}" width="300" height="{2.5*scale}" fill="#f1e7d0" stroke="#64748b" stroke-dasharray="3 3"/>')
        for col in 'ABCDEFGH':
            x, _ = xy(col+'1', ox, oy, mirror)
            svg.append(f'<text x="{x}" y="{oy-10}" text-anchor="middle" font-size="15">{col}</text>')
        for row in range(1,9):
            _, y = xy('A'+str(row), ox, oy, mirror)
            svg.append(f'<text x="{ox-16}" y="{y+5}" text-anchor="middle" font-size="15">{row}</text>')
        if not mirror:
            # Manufacturer body projection: SIP leads sit 2 mm from the front edge.
            svg.append(f'<rect x="{ox+2.44*scale}" y="{oy+2.64*scale}" width="{11.5*scale}" height="{7.55*scale}" rx="4" fill="#111827" opacity="0.82"/>')
            svg.append(f'<text x="{ox+8.19*scale}" y="{oy+5.5*scale}" text-anchor="middle" fill="white" font-size="13">R-78K3.3-1.0</text>')
            cx, cy = ox+19.62*scale, oy+8.19*scale
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="{2.75*scale}" fill="#1e3a5f" stroke="#94a3b8" stroke-width="3"/>')
            svg.append(f'<text x="{cx}" y="{cy-14}" text-anchor="middle" fill="white" font-size="12">27 µF</text>')
            svg.append(f'<text x="{cx+22}" y="{cy+8}" fill="white" font-size="20">−</text>')
        else:
            for link in data['perfboard']['links']:
                x1,y1=xy(link['from'],ox,oy,mirror)
                x2,y2=xy(link['to'],ox,oy,mirror)
                # Offset the two capacitor links so opposite rails never share a drawn segment.
                if (link['from'], link['to']) == ('B3', 'G3'):
                    route = f'M{x1},{y1} L{x1},{y1-40} L{x2},{y2-40} L{x2},{y2}'
                elif (link['from'], link['to']) == ('C3', 'H3'):
                    route = f'M{x1},{y1} L{x1},{y1-20} L{x2},{y2-20} L{x2},{y2}'
                else:
                    route = f'M{x1},{y1} L{x2},{y2}'
                svg.append(f'<path d="{route}" fill="none" stroke="white" stroke-width="9"/>')
                svg.append(f'<path d="{route}" fill="none" stroke="{colors[link["net"]]}" stroke-width="5"/>')
        for col in 'ABCDEFGH':
            for row in range(1,9):
                if row in data['perfboard']['removed_pad_rows']:
                    continue
                pad=col+str(row)
                x,y=xy(pad,ox,oy,mirror)
                svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#c18e37" stroke="#e5d2a1" stroke-width="1"/><circle cx="{x}" cy="{y}" r="2" fill="#f8fafc"/>')
        labels={'B3':'1 VIN','C3':'2 GND','D3':'3 OUT','G3':'+','H3':'−','A7':'J2.1','B7':'J2.2','C7':'J2.3','D7':'J2.4'}
        for pad,label in labels.items():
            x,y=xy(pad,ox,oy,mirror)
            ty=y+22 if pad.endswith('7') else y+28
            svg.append(f'<text x="{x}" y="{ty}" text-anchor="middle" font-size="11" font-weight="bold" fill="{ "white" if not mirror and pad in ["B3","C3","D3"] else "#0f172a"}">{escape(label)}</text>')
        svg.append(f'<text x="{ox}" y="550" font-size="15">2 mm bare rim; row 8 removed for rear retaining strap.</text>')
    lines = [
        'Regulator: B3 = pin 1 VIN; C3 = pin 2 GND; D3 = pin 3 VOUT. Identify the pin-1 dot before soldering.',
        'Capacitor: positive G3; negative stripe H3. Form the 2.0 mm leads gently to 2.54 mm without stressing the seal.',
        'Six insulated links: A7–B3, B3–G3 (+5 V); B7–C3, D7–C3, C3–H3 (GND); C7–D3 (+3.3 V).',
        'Crossing wires do NOT join. Solder only at named pads. Keep all solder / trimmed leads / wires within 2 mm below board.',
        'Keep rear strap band Y20.5–23 mm bare; strain-relieve J2 cable. Meter continuity and polarity, then test from current-limited 5 V with J2 unplugged.',
        'Engineering assembly plan; no hardware qualification claimed. See power-design.json and the full assembly guide.'
    ]
    for i,line in enumerate(lines):
        svg.append(f'<text x="36" y="{592+i*30}" font-size="15">{escape(line)}</text>')
    svg.append('</g></svg>')
    return '\n'.join(svg)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true', help='regenerate the perfboard illustration and blank bench worksheet after checking')
    args=parser.parse_args()
    data=read_json(HERE/'power-design.json')
    result=validate(data, read_json(HERE/'cad/design.json')['parts'], read_json(HERE/'cad/connectors.json')['connectors'], read_json(HERE/'harnesses.json')['harnesses'])
    validate_companions(data, read_json(HERE.parents[1]/'mechanical/full-hub/components.json'), read_json(HERE/'procurement.json'))
    rendered=render_perfboard(data)
    worksheet=render_measurements(data)
    if args.render:
        if (HERE/'power-measurements.csv').exists():
            require_blank_worksheet((HERE/'power-measurements.csv').read_text())
        (HERE/'power-perfboard.svg').write_text(rendered)
        (HERE/'power-measurements.csv').write_text(worksheet)
    else:
        require((HERE/'power-perfboard.svg').read_text() == rendered, 'perfboard illustration stale; run power_design.py --render')
        require((HERE/'power-measurements.csv').read_text() == worksheet, 'blank measurement worksheet stale; save filled results under another name before running power_design.py --render')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
