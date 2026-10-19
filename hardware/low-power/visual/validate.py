#!/usr/bin/env python3
"""Validate the pin-to-pin atlas against firmware and the documented pin contract."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def block(text, name):
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(?:\n|$)", text)
    require(match is not None, f"Missing firmware block {name}")
    tail = text[match.end():]
    return re.split(r"(?m)^[a-zA-Z][a-zA-Z0-9_]*:", tail, maxsplit=1)[0]


def gpio(text, key, substitutions=None):
    if substitutions is not None:
        text = re.sub(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
                      lambda m: substitutions.get(m.group(1), m.group(0)), text)
    match = re.search(rf"(?m)^\s+{re.escape(key)}:\s*GPIO(\d+)\s*$", text)
    require(match is not None, f"Missing firmware GPIO field {key}")
    return int(match.group(1))


def pin_substitutions(*sources):
    """Resolve literal pin defaults, then the target's overrides; not arbitrary YAML."""
    result = {}
    for source in sources:
        if re.search(r"(?m)^substitutions:\s*$", source):
            for name, value in re.findall(r"(?m)^\s+(\w+):\s*(GPIO\d+)\s*$", block(source, 'substitutions')):
                result[name] = value
    return result


def validate(data, root=ROOT):
    require(data['schema_version'] == 1, 'Unsupported schema')
    comps = {c['id']: c for c in data['components']}
    require(len(comps) == len(data['components']), 'Duplicate component ID')
    pins = {}
    for cid, component in comps.items():
        positions = set()
        for pin in component['pins']:
            key = (cid, pin['id'])
            require(key not in pins, f'Duplicate pin {key}')
            pins[key] = pin
            physical = pin['physical']
            if physical['status'] == 'unknown':
                require(physical['position'] is None, f'Unknown pin has invented position: {key}')
            elif physical['status'] in ('datasheet_verified', 'project_contract_pending_physical_check'):
                require(physical['position'] is not None and physical['source_ids'], f'Unreferenced physical pin {key}')
                pos = (physical['namespace'], physical['position'])
                require(pos not in positions, f'Duplicate physical pad {cid} {pos}')
                positions.add(pos)
            else:
                raise ValueError(f'Unexpected physical status: {key}')
            for source in physical['source_ids']:
                require(source in data['sources'], f'Unknown source {source}')
            if 'bench_header' in pin:
                require(pin['bench_header']['status'] == 'unknown' and pin['bench_header']['position'] is None,
                        f'Unverified DevKit header position: {key}')
    nets = {n['id']: n for n in data['nets']}
    require(len(nets) == len(data['nets']), 'Duplicate net ID')
    connected = {}
    for nid, net in nets.items():
        require(net['members'], f'Empty net {nid}')
        for member in net['members']:
            key = (member['component'], member['pin'])
            require(key in pins, f'Unknown endpoint {key}')
            require(key not in connected, f'Pin connected to two nets: {key}')
            connected[key] = nid
            pin = pins[key]
            require('termination' not in pin, f'Explicitly unconnected pin wired: {key}')
            if net['kind'] == 'ground':
                require(pin['direction'] in ('ground', 'input'), f'Unsafe ground connection {key}')
            elif net['nominal_voltage_v'] is not None:
                require(pin['voltage_v'] == net['nominal_voltage_v'], f'Voltage mismatch {key} on {nid}')
    for key, pin in pins.items():
        require(key in connected or 'termination' in pin, f'Undocumented unconnected endpoint {key}')
    parts = {p['id']: p for p in data['support_parts']}
    require(len(parts) == len(data['support_parts']), 'Duplicate support part ID')
    for part in parts.values():
        require(len(part['between']) == 2 and len(set(part['between'])) == 2, f'Invalid support part {part["id"]}')
        require(all(n in nets for n in part['between']), f'Unknown support-part net {part["id"]}')
    require(connected[('pd','5V')] == '5v_pd' and connected[('ld2450','5V')] == '5v_fused', '5 V fuse bypass')
    require(parts['F_SECONDARY']['between'] == ['5v_pd','5v_fused'], 'Missing series fuse')
    for cid in ('s3','h2','mg24','sc16','zac93','cc1101','bme680'):
        for pin in comps[cid]['pins']:
            if pin['direction'] == 'power_input' and 'termination' not in pin:
                require(connected[(cid,pin['id'])] == '3v3', f'Wrong supply rail for {cid}')
    for key in [('pd',x) for x in ('VINA','VINB','VINC','VIND','CP1','CP2','ADJ','IC')]:
        require(key not in connected, f'PoE primary/control pin connected in secondary-only model: {key}')
    for name, value in [('cc1101_gdo0_tx',4700),('sc16_irq',1000),('h2_reset',10000),('h2_boot',10000),('sc16_reset',10000)]:
        part = parts['R_'+name]
        require(part['value'] == value and part['unit'] == 'ohm' and part['between'] == [name,'3v3'], f'Wrong pull-up {name}')
    require(not any(p['kind']=='resistor' and 'mg24_reset' in p['between'] for p in parts.values()), 'Forbidden external MG24 reset pull-up')
    require(pins[('s3','GPIO4')]['direction'] == 'open_drain', 'RF TX must be open-drain')
    for key in [('s3','GPIO47'),('s3','GPIO48'),('supervisor','RESET')]:
        require(pins[key]['direction'] == 'open_drain', f'Reset/boot driver must be open-drain: {key}')
    require(parts['Y_SC16']['value'] == 3686400, 'Wrong SC16 oscillator')
    # Independent critical physical-pin vectors: these are not derived from pinmap.json.
    physical_vectors = {('s3','GPIO43'):'37',('s3','GPIO44'):'36',('s3','GPIO17'):'10',('s3','GPIO18'):'11',
        ('h2','GPIO23'):'30',('h2','GPIO24'):'31',('h2','GPIO9'):'23',('h2','EN'):'8',
        ('mg24','RX'):'12',('mg24','TX'):'13',('mg24','CTS'):'5',('mg24','RTS'):'6',('mg24','RESET'):'31',
        ('sc16','TXA'):'3',('sc16','RXA'):'4',('sc16','IRQ'):'15',('sc16','RESET'):'5',
        ('supervisor','RESET'):'1',('supervisor','VDD'):'6',('supervisor','SENSE'):'5',
        ('w5500','MISO'):'J2.6',('w5500','MOSI'):'J1.3',('w5500','CS'):'J1.5'}
    for key, expected in physical_vectors.items():
        require(pins[key]['physical']['position'] == expected, f'Physical pad mismatch: {key}')
    for cid, expected in [('s3',{1,40,41}),('h2',{1,2,11,14,*range(36,54)}),('mg24',{1,14,23,32,34,35,36})]:
        actual = {int(p['physical']['position']) for p in comps[cid]['pins'] if p['direction']=='ground'}
        require(actual == expected, f'Missing/extra ground pads on {cid}')
    pairs = {
        'h2_tx':{('s3','GPIO43'),('h2','GPIO23')}, 'h2_rx':{('s3','GPIO44'),('h2','GPIO24')},
        'mg24_rts':{('s3','GPIO16'),('mg24','CTS')}, 'mg24_cts':{('s3','GPIO21'),('mg24','RTS')},
        'zwave_tx':{('sc16','TXA'),('zac93','RX')}, 'zwave_rx':{('sc16','RXA'),('zac93','TX')},
        'cc1101_gdo0_tx':{('s3','GPIO4'),('cc1101','GDO0')},'cc1101_gdo2_rx':{('s3','GPIO5'),('cc1101','GDO2')},
    }
    for nid, expected in pairs.items():
        actual = {(m['component'],m['pin']) for m in nets[nid]['members']}
        require(actual == expected, f'Crossed or missing signal endpoints: {nid}')
    pm = json.loads((root/'hardware/low-power/pinmap.json').read_text())
    roles = {p['role']:p['gpio'] for p in pm['exclusive_pins']}
    require(data['firmware_roles'] == roles, 'Firmware role map differs from pinmap.json')
    for row in pm['exclusive_pins']:
        key = ('s3',f'GPIO{row["gpio"]}')
        require(connected[key] == row['role'], f'Wrong S3 signal role: {key}')
        require(pins[key]['direction'] == row['direction_at_s3'], f'S3 direction mismatch: {key}')
    proof = (root/'firmware/low-power/proof.yaml').read_text()
    hub = (root/'firmware/low-power/hub.yaml').read_text()
    fields = [('ethernet',{'clk_pin':'w5500_sclk','mosi_pin':'w5500_mosi','miso_pin':'w5500_miso','cs_pin':'w5500_cs','interrupt_pin':'w5500_irq','reset_pin':'w5500_reset'}),
              ('low_power_otbr',{'tx_pin':'h2_tx','rx_pin':'h2_rx','reset_pin':'h2_reset','boot_pin':'h2_boot'}),
              ('spi',{'clk_pin':'shared_spi_sclk','mosi_pin':'shared_spi_mosi','miso_pin':'shared_spi_miso'}),
              ('i2c',{'sda':'bme680_sda','scl':'bme680_scl'}),('uart',{'tx_pin':'ld2450_tx','rx_pin':'ld2450_rx'})]
    for section, keys in fields:
        text = block(proof,section)
        for field,role in keys.items():require(gpio(text,field) == roles[role], f'Firmware mismatch {section}.{field}')
    for section,keys in [('sc16is752_uart',{'cs_pin':'sc16_cs','interrupt_pin':'sc16_irq'}),('zigbee_tcp',{'tx_pin':'mg24_tx','rx_pin':'mg24_rx','rts_pin':'mg24_rts','cts_pin':'mg24_cts'})]:
        for field,role in keys.items():require(gpio(block(hub,section),field)==roles[role],f'Firmware mismatch {section}.{field}')
    require('crystal_frequency: 3686400' in block(hub,'sc16is752_uart'), 'SC16 firmware crystal mismatch')
    rf = (root/'firmware/packages/rf-airbridge.yaml').read_text()
    rf_pins = pin_substitutions(rf, proof, hub)
    require(gpio(block(rf,'cc1101'),'cs_pin', rf_pins) == roles['cc1101_cs'], 'RF CS mismatch')
    require(gpio(block(rf,'remote_receiver'),'pin', rf_pins) == roles['cc1101_gdo2_rx'], 'RF RX mismatch')
    tx=block(rf,'remote_transmitter')
    require(gpio(tx,'number', rf_pins) == roles['cc1101_gdo0_tx'] and 'open_drain: true' in tx and 'eot_level: false' in tx, 'RF transmitter drive contract changed')
    mg = json.loads((root/'firmware/low-power/mg24/config.json').read_text())['application']['configuration']
    require([mg[f'SL_IOSTREAM_USART_VCOM_{name}_PIN'] for name in ('RX','TX','CTS','RTS')] == ['5','6','1','0'], 'MG24 firmware pins differ')
    return {'components':len(comps),'pins':len(pins),'nets':len(nets),'support_parts':len(parts),'firmware_roles':len(roles)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,default=HERE/'connections.json')
    args=parser.parse_args()
    result=validate(json.loads(args.model.read_text()))
    print('Connection model PASS: '+', '.join(f'{k}={v}' for k,v in result.items()))

if __name__ == '__main__':
    main()
