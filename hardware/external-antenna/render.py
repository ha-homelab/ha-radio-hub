#!/usr/bin/env python3
"""Render the MC2 guide from the carrier connector ledger and RF selection."""
import argparse
import csv
from html import escape
from io import StringIO
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

DIRECTIONS = {
    'to_device': ('→', 'Carrier to device'),
    'to_carrier': ('←', 'Device to carrier'),
    'bidirectional': ('↔', 'Bidirectional'),
    'ground': ('—', 'Common ground'),
}


def validate_harnesses(data, connectors, parts):
    """Reject an incomplete or stale off-board map before publishing it."""
    native = {p['ref']: p for p in connectors}
    schematic = {p['ref']: p for p in parts}
    refs = [h['ref'] for h in data['harnesses']]
    if sorted(refs) != sorted([f'J{n}' for n in range(1, 8)] + ['J10']):
        raise ValueError('Harness lookup must cover J1–J7 and J10 exactly once')
    if data['revision'] != 'MC2-D':
        raise ValueError('Harness lookup is for MC2-D only')
    for h in data['harnesses']:
        ref = h['ref']
        pins = {p['carrier_pin']: p['net'] for p in h['pins']}
        if len(pins) != len(h['pins']) or pins != native[ref]['pins'] or pins != schematic[ref]['pins']:
            raise ValueError(f'{ref}: harness pins differ from native connector/schematic ledger')
        if {p['number']: p['net'] for p in native[ref]['pad_centers_mm']} != pins:
            raise ValueError(f'{ref}: physical pad map differs from harness')
        if native[ref]['side'] != 'front':
            raise ValueError(f'{ref}: front-view illustration requires a front connector')
        for pin in h['pins']:
            if pin['direction'] not in DIRECTIONS or not pin['device_contact'].strip() or not pin['function'].strip():
                raise ValueError(f'{ref}: missing endpoint or invalid direction')
        if ref == 'J10':
            actual = {p['carrier_pin']: (p.get('device_pin'), p['net']) for p in h['pins']}
            if actual != {'1': ('TP8', 'THREAD_EN'), '2': ('TP2', 'THREAD_BOOT')}:
                raise ValueError('J10: XIAO recovery test-pad map differs from TP8 EN / TP2 BOOT')
        if ref == 'J4':
            expected = dict(re.findall(r'(?:Carrier)?(\d+)->(?:ZAC)?pin(\d+)', native[ref]['notes']))
            actual = {p['carrier_pin']: p.get('device_pin') for p in h['pins']}
            if len(expected) != 5 or actual != expected:
                raise ValueError('J4: ZAC93 physical pin remap differs from native ledger notes')
            if any(not p['device_contact'].startswith(f'Physical pin {p["device_pin"]} — ') for p in h['pins']):
                raise ValueError('J4: displayed contact disagrees with the ZAC93 physical pin')


def connector_diagram(connector):
    """Draw actual pad coordinates viewed from the component side, not the socket."""
    pads = connector['pad_centers_mm']
    x0, y0 = min(p['x'] for p in pads), min(p['y'] for p in pads)
    scale = 14
    width = (max(p['x'] for p in pads) - x0) * scale + 48
    height = (max(p['y'] for p in pads) - y0) * scale + 70
    parts = [f'<svg class="connector-map" viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{escape(connector["ref"])} carrier component-side pad positions; square pad is pin 1">']
    for pad in pads:
        x, y = 24 + (pad['x']-x0)*scale, 22 + (pad['y']-y0)*scale
        if pad['number'] == '1':
            parts.append(f'<rect x="{x-9:g}" y="{y-9:g}" width="18" height="18" fill="#2dd4bf"/>')
        else:
            parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="9" fill="#91b5dc"/>')
        parts.append(f'<text x="{x:g}" y="{y+32:g}" text-anchor="middle" fill="currentColor" font-size="14">{escape(pad["number"])}</text>')
    return ''.join(parts)+'</svg>'


def render_harnesses(data, connectors):
    native = {p['ref']: p for p in connectors}
    cards, options = [], []
    csv_out = StringIO(newline='')
    writer = csv.writer(csv_out, lineterminator='\n')
    writer.writerow(['Carrier connector', 'Carrier pad', 'Net', 'Device', 'Device contact', 'Direction', 'Function'])
    for h in data['harnesses']:
        ref, device = h['ref'], h['device']
        options.append(f'<option value="{ref}">{escape(ref+" · "+device)}</option>')
        rows = []
        for pin in h['pins']:
            symbol, direction = DIRECTIONS[pin['direction']]
            pad = ref+'.'+pin['carrier_pin']
            terms = ' '.join([ref, device, pad, pin['net'], pin['device_contact'], pin['function']])
            rows.append(f'<tr data-search="{escape(terms.lower(), quote=True)}"><th scope="row"><span class="pad-name">{pad}</span><code>{escape(pin["net"])}</code></th><td><span class="wire-direction"><span aria-hidden="true">{symbol}</span> {direction}</span><strong>{escape(pin["device_contact"])}</strong><span class="pin-function">{escape(pin["function"])}</span></td></tr>')
            writer.writerow([ref, pin['carrier_pin'], pin['net'], device, pin['device_contact'], direction, pin['function']])
        cards.append(f'<article class="harness-card" data-connector="{ref}" id="connector-{ref}"><h3>{ref} <span>{escape(device)}</span></h3><p class="connector-view">Carrier component side · square pad = pin 1 · not a cable mating view</p>{connector_diagram(native[ref])}<p class="harness-note">{escape(h["note"])}</p><table><caption class="sr-only">{ref} carrier pad to {escape(device)} contact</caption><thead><tr><th scope="col">Carrier pad / net</th><th scope="col">Other end / signal direction</th></tr></thead><tbody>{"".join(rows)}</tbody></table><p class="source-link"><a href="../../guide/assembly.html#{escape(h["source_anchor"])}">Assembly details for {ref}</a></p></article>')
    return ''.join(cards), ''.join(options), csv_out.getvalue()


def render():
    rf = json.loads((HERE / 'rf-bom.json').read_text())
    design = json.loads((HERE / 'cad/design.json').read_text())
    connectors = json.loads((HERE / 'cad/connectors.json').read_text())['connectors']
    harnesses = json.loads((HERE / 'harnesses.json').read_text())
    validate_harnesses(harnesses, connectors, design['parts'])
    harness_cards, harness_options, harness_csv = render_harnesses(harnesses, connectors)
    params = json.loads((ROOT / 'mechanical/full-hub/parameters.json').read_text())
    assert rf['pigtail']['nominal_length_mm'] == 150
    assert [p['label'] for p in rf['paths']] == [p['label'] for p in params['rf_ports']]
    assert design['board']['width_mm'] == design['board']['height_mm'] == 100
    colors = ['#2dd4bf', '#60a5fa', '#c084fc']
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="560" viewBox="0 0 1080 560" role="img" aria-labelledby="title desc">',
           '<title id="title">MC2 — three separate external 2.4 GHz antennas</title>',
           '<desc id="desc">BLE, Thread and Zigbee each have a dedicated U.FL cable, standard SMA bulkhead and 2.4 GHz antenna. The modules are on a 100 by 100 mm carrier. Logical diagram, not a mechanical drawing.</desc>',
           '<rect width="1080" height="560" rx="24" fill="#101e2f"/>',
           '<g font-family="Arial,sans-serif" fill="#eff6ff"><text x="40" y="51" font-size="28" font-weight="700">MC2 / THREE INDEPENDENT RF PATHS</text>',
           '<text x="40" y="83" font-size="16" fill="#b8c9dd">2.4 GHz · 50 Ω · standard SMA · one antenna per radio</text>',
           '<rect x="28" y="220" width="1024" height="234" rx="16" fill="#1a2b41" stroke="#52637b"/>']
    for i, p in enumerate(rf['paths']):
        x = 205 + 335*i
        c = colors[i]
        svg += [f'<path d="M{x} 132 v65" stroke="{c}" stroke-width="13" stroke-linecap="round"/>',
                f'<circle cx="{x}" cy="217" r="9" fill="{c}"/>',
                f'<path d="M{x} 226 v58" stroke="{c}" stroke-width="3" stroke-dasharray="7 4"/>',
                f'<text x="{x}" y="119" text-anchor="middle" fill="{c}" font-size="20" font-weight="700">{escape(p["label"])}</text>',
                f'<rect x="{x-144}" y="290" width="288" height="125" rx="12" fill="#0c1726" stroke="{c}"/>',
                f'<text x="{x}" y="325" text-anchor="middle" fill="{c}" font-size="17" font-weight="700">{["ESP32-DevKitC-VIE", "XIAO ESP32C6", "XIAO MG24"][i]}</text>',
                f'<text x="{x}" y="355" text-anchor="middle" font-size="16">{["BLE + host services", "Thread RCP", "Ember Zigbee NCP"][i]}</text>',
                f'<text x="{x}" y="387" text-anchor="middle" font-size="14" fill="#b8c9dd">{["Factory external RF", "GPIO3=0 / GPIO14=1", "Firmware: PB04=1 / PB05=1"][i]}</text>']
    svg += ['<text x="540" y="439" text-anchor="middle" font-size="14" fill="#b8c9dd">Fixed base wall · 3 SMA bulkheads · dedicated 150 mm pigtails</text>',
            '<text x="40" y="491" font-size="18">PoE switch → isolated splitter → regulated rails + WIZ850io Ethernet</text>',
            '<text x="40" y="526" font-size="15" fill="#b8c9dd">Logical connections, not to scale. Printed case and 1,000 ft² coverage require physical testing.</text></g></svg>']
    nets = {}
    for p in design['parts']:
        for pin, net in p['pins'].items():
            if net:
                nets.setdefault(net, []).append(f'{p["ref"]}:{pin} ({p["model"]})')
    rows = ''.join('<tr><th>'+escape(n)+'</th><td>'+ '<br>'.join(escape(v) for v in vs)+'</td></tr>' for n,vs in sorted(nets.items()))
    descriptions = {
        'U1': 'Factory external antenna, 8 MB flash and 8 MB quad PSRAM. Two 19-pin factory headers; GPIO1/3 stay reserved for USB-UART. R4/R5 hold GPIO12/2 LOW at reset. Legacy BLE4.2 only; no BLE5 extended advertisements or Coded PHY.',
        'U2': '102010636: factory 2×7 headers, native USB, 4 MB flash. Firmware selects external U.FL with GPIO3 LOW / GPIO14 HIGH. Two hand-soldered underside leads join TP8/EN to J10.1 and TP2/BOOT9 to J10.2 above the carrier access window. The onboard GPIO8 pull-up replaces carrier R3.',
        'U3': 'Pre-soldered header version. Ember UART with hardware flow control; external antenna selected before startup with PB04=1 and PB05=1.',
        'U4': '3.3 V SPI Ethernet module with two 1×6 headers. Its jack receives data downstream of the separate PoE splitter.',
    }
    modules = ''.join(f'<li><strong>{escape(p["ref"])} — {escape(p["model"])}</strong><br>{escape(descriptions[p["ref"]])}</li>' for p in connectors if p['ref'].startswith('U'))
    page = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC2 · External-antenna radio hub</title>
<style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0b1421;color:#e6effb}*{box-sizing:border-box}body{margin:0}main{max-width:1160px;margin:auto;padding:28px}nav{display:flex;flex-wrap:wrap;gap:18px;margin-bottom:36px}a{color:#83c9ff;text-underline-offset:3px}h1{font-size:clamp(34px,6vw,64px);line-height:1.06;max-width:850px;margin:10px 0 22px}h2{margin-top:38px;font-size:27px}p,li{line-height:1.65;color:#bdcde1}li{margin:13px 0}strong,th{color:#edf5ff}.eyebrow{letter-spacing:.14em;color:#2dd4bf;font-size:13px;font-weight:700}.lead{font-size:20px;max-width:880px}.notice{border-left:4px solid #eab85d;background:#302a22;padding:16px 22px;border-radius:4px;color:#f4dfbb}.hero{width:100%;display:block;margin:26px 0;border-radius:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.card{background:#142237;border:1px solid #293c55;border-radius:14px;padding:22px}.card b{font-size:25px;display:block;color:#fff}.card p{margin-bottom:0}.figure{display:block;width:100%;background:#f3f7fb;border-radius:12px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:13px;text-align:left;border-bottom:1px solid #2d4059;vertical-align:top}td{min-width:270px;color:#bdcde1}th{white-space:nowrap}input{background:#16263e;border:1px solid #527193;border-radius:6px;color:white;padding:14px;width:100%;max-width:600px;font-size:16px;margin:12px 0}footer{margin-top:42px;border-top:1px solid #293c55;padding:24px 0;color:#96abc5;font-size:14px}code{color:#e3bfef}button{background:#203b56;border:1px solid #527193;border-radius:5px;color:white;padding:9px 14px;cursor:pointer}@media(max-width:600px){main{padding:18px}.lead{font-size:17px}.hero{border-radius:8px}}@media print{:root{color-scheme:light;background:white;color:#111}p,li,td,strong,th{color:#111}nav,button,input{display:none}.card,.notice{background:#eee}.scroll{overflow:visible}}[hidden]{display:none!important}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}:focus-visible{outline:3px solid #2dd4bf;outline-offset:4px}.harness-controls{display:flex;gap:14px;align-items:flex-end;flex-wrap:wrap;margin:24px 0}.harness-controls>div{flex:1 1 260px}.harness-controls label{display:block;font-weight:650}.harness-controls input,.harness-controls select{width:100%;max-width:none;margin:9px 0 0;min-height:48px}.harness-controls select{background:#16263e;border:1px solid #527193;border-radius:6px;color:white;padding:12px;font-size:16px}.harness-controls button{min-height:48px}.harness-card{border:1px solid #36516e;border-radius:12px;padding:20px;margin:18px 0;background:#101f31;break-inside:avoid}.harness-card h3{font-size:24px;margin:0 0 8px;color:#2dd4bf}.harness-card h3 span{color:#edf5ff;font-size:20px}.connector-view{font-size:13px;margin:0}.connector-map{display:block;width:auto;height:70px;max-width:100%;margin:8px 0 0}.harness-note{font-size:15px;margin:8px 0 18px}.harness-card table{table-layout:fixed}.harness-card th:first-child{width:32%}.harness-card td{min-width:0;overflow-wrap:anywhere}.harness-card th{white-space:normal}.pad-name{display:block;font-size:18px}.harness-card code{font-size:12px;overflow-wrap:anywhere}.wire-direction{display:block;font-size:12px;color:#b5c9dd;margin-bottom:6px}.wire-direction span{font-size:18px;color:#2dd4bf}.pin-function{display:block;margin-top:6px;font-size:13px}.source-link{font-size:14px;margin-bottom:0}section[id],h2[id],article[id]{scroll-margin-top:16px}@media(max-width:600px){.harness-card{padding:12px}.harness-card h3 span{display:block;margin-top:5px}.harness-card td,.harness-card th{padding:10px 5px}.harness-card th:first-child{width:30%}.harness-controls button{width:100%}}@media print{.harness-controls{display:none!important}.harness-card{background:white;border:1px solid #999;break-inside:auto}.harness-card h3,.harness-card h3 span,.wire-direction,.wire-direction span,.harness-card code{color:#111}.harness-card tr{break-inside:avoid}.connector-map{color:#111}.harness-card a{color:#111}}
</style>
<main><nav aria-label="Build guide"><a href="../../guide/start-here.html">Start here</a><a href="../../guide/assembly.html">Assembly instructions</a><a href="cad/BOM.csv">Carrier BOM</a><a href="rf-bom.json">Antenna BOM</a><a href="../../guide/firmware.html">Firmware</a><a href="#harness">Connector lookup</a><a href="#wiring">Carrier nets</a><button onclick="print()">Print</button></nav>
<div class="eyebrow">HA RADIO HUB / MC2-D / 20 OCTOBER 2026</div><h1>Give every radio<br>its own antenna.</h1><p class="lead">A dedicated external path for Zigbee, Thread and Bluetooth, with the existing local Home Assistant functions preserved on a wired PoE connection.</p>
<div class="notice"><strong>Engineering prototype.</strong> The carrier, software and printed enclosure have separate digital checks. Physical fit, simultaneous-radio operation and coverage of a 1,000 ft² house remain unmeasured. MC1 and MC2-A files are historical; MC2-A S3 boards and firmware are not interchangeable with MC2-D.</div>
<img class="hero" src="../../mechanical/full-hub/full-assembly-preview.png" alt="Current MC2-D full assembly CAD render"><p>Current model with simplified component bodies, factory module headers and the XIAO service-wire allowance. <a href="../../guide/shopping.html">Exact factory-assembled module choices</a>. Digital geometry does not replace a physical fit check.</p>
<img class="hero" src="antenna-paths.svg" alt="Three independent antenna paths, BLE, Thread and Zigbee">
<section class="grid"><article class="card"><b>3 × 2.4 GHz</b><p>Separate 50 Ω antenna feeds; no shared RF combiner.</p></article><article class="card"><b>100 × 100 mm</b><p>Two-layer carrier. All components on one side. Through-hole module attachment.</p></article><article class="card"><b>__CASE_SIZE__ mm</b><p>Full-hub main shell, with dedicated module mounts and an attached ventilated BME680 pod.</p></article></section>
<h2>Exact modules, not generic substitutes</h2><ul>__MODULES__</ul><p><strong>Availability:</strong> DigiKey showed 21 pre-soldered XIAO ESP32C6 boards (102010636) at USD $6.38 on 20 October 2026. Stock and checkout charges can change. Use the MC2-D PCB and 4 MB XIAO RCP, not TinyC6 firmware. See the <a href="../../guide/pcb-order.html">prototype ordering record</a>.</p>
<h2>Antenna and cable selection</h2><p>Buy three <a href="https://www.te.com/en/product-L9000082-01.html">TE ANT-2.4-LCW-SMA</a> antennas (2400–2485 MHz, 2.8 dBi peak) and three <a href="https://www.taoglas.com/product/cab-618-e-i-pex-mhf-i-u-fl-to-150mm-1-13mm-coax-black-cable-smaf-bulkhead-straight/">Taoglas CAB.618.E</a> cables. Standard SMA male antenna mates with a standard SMA female bulkhead; the radio end is I-PEX MHF I/U.FL compatible. RP-SMA and smaller MHF connector variants are not substitutes.</p><p>BLE, THREAD and ZIGBEE bulkheads stay on the fixed base. Their 65 mm adjacent pitch is a layout target, not an isolation measurement. Use the FH1-MC2-D-PWR1 round-hole coupon and routing, which reserves a 144 mm design-length budget plus 25 mm service allowance within it. This is an engineering allowance, not a supplier length guarantee. <a href="../../guide/pigtails.html">Cable selection and fit checks</a>. Leave slack and use strain relief. Connect antennas before powering the radios.</p>
<h2>Full assembly and Z-Wave placement</h2><img class="hero" src="../../mechanical/full-hub/exploded-preview.png" alt="Current PWR1 CAD exploded view, including the RECOM converter and capacitor mount"><p>Current CAD with simplified component bodies; dimensions and connections come from the model and wiring below. <strong>Zooz ZAC93 sits in a separate insulated cradle beside the carrier.</strong> Its underside 2×5 socket connects by a remapped harness to J4, while the DFR0627 UART bridge connects to J3. <a href="../../guide/assembly.html">Complete assembly and ZAC93 pin map</a>.</p><div class="grid"><article><a href="cad/assembly-top.svg"><img class="figure" src="cad/assembly-top.svg" alt="MC2 front assembly from CAD"></a><p><a href="cad/schematic.svg">Circuit schematic</a> · <a href="cad/">Native KiCad files</a></p></article><article><a href="../../mechanical/full-hub/index.html"><img class="figure" src="../../mechanical/full-hub/layout.svg" alt="Exact full-hub component layout and mounts"></a><p><a href="../../mechanical/full-hub/index.html">All print parts and dimensions</a> · <a href="../../guide/print.html">Assembly and fit checks</a></p></article></div><p>These images are design renders. Print the connector fit coupon first. Dedicated trays retain the isolated splitter, buck converter, UART bridge, Z-Wave, CC1101, DC adapter and fuse. The radar mounts behind the lid window; BME680 sits in an attached ventilated pod outside the warm shell. Exact purchased heights, connector fit, thermal behavior and RF performance remain unmeasured. <a href="full-hub-wiring.svg">Full-hub wiring diagram</a> · <a href="../../mechanical/full-hub/components.json">Full assembly inventory</a>.</p>
<h2>Peripheral power: 5 V to 3.3 V</h2><p>The RECOM R-78K3.3-1.0 and local 27 µF input capacitor replace the previous Pololu converter on J2. The same PWR1 power circuit is retained in MC2-D; use its perfboard mount and input capacitor. The XIAO footprint and RCP firmware are revised. <a href="power-design.json">Current load budget and acceptance gates</a> · <a href="../../guide/assembly.html#power-and-ethernet">Assembly instructions</a>.</p><img class="hero" src="power-wiring.svg" alt="RECOM input, output, local capacitor and four-wire J2 connections"><section id="harness" aria-labelledby="harness-title"><h2 id="harness-title">Which wire goes where?</h2><p>Choose a carrier connector to see both ends of every wire. <strong>J4 pad 4 goes to ZAC93 physical pin 8, not pin 4.</strong> The carrier has eight off-board harnesses; a connector's pad order does not imply the order on the attached device.</p><p>__ORIENTATION__ <a href="cad/assembly-top.svg">Locate J1–J7 and J10 on the carrier</a>.</p><div class="harness-controls" id="harness-controls" hidden><div><label for="connector-select">Carrier connector</label><select id="connector-select"><option value="">All connectors</option>__HARNESS_OPTIONS__</select></div><div><label for="harness-search">Device, signal or either end of a wire</label><input id="harness-search" type="search" placeholder="Try ZAC93, J4.4, RX1 or VIN" aria-describedby="harness-count"></div><button type="button" id="harness-clear">Clear filters</button></div><noscript><p>All connections are shown below. Use your browser's Find command to locate a device or pad.</p></noscript><p id="harness-count" role="status" aria-live="polite">__WIRE_COUNT__ wire connections across __CONNECTOR_COUNT__ connectors.</p><p id="harness-empty" class="notice" hidden>No matching wire. Clear the search or choose All connectors to broaden the lookup.</p><div id="harness-cards">__HARNESS_CARDS__</div><p><a href="harness.csv" download>Download all __WIRE_COUNT__ connections as CSV</a> · <a href="harnesses.json">Harness source data</a> · <a href="full-hub-wiring.svg">Full wiring diagram</a></p></section>
<h2 id="wiring">Find a carrier net or physical pad</h2><p>Generated from the MC2 design ledger, including the resistors and diodes. Labels identify <strong>carrier reference:physical pad</strong>, not a generic GPIO header. THREAD_RX and ZB_RX name the radio receiver: connect the host transmitter there. Confirm orientation against the schematic before soldering.</p><label for="search">Net, module reference or pin</label><br><input id="search" type="search" placeholder="Try THREAD, U2:8, RADAR or GND"><p id="count" aria-live="polite"></p><p id="net-empty" hidden>No matching carrier net. Try a module reference such as U2, a net such as GND, or clear the search.</p><div class="scroll"><table><thead><tr><th>Net</th><th>Connected endpoints</th></tr></thead><tbody id="nets">__ROWS__</tbody></table></div><p><a href="cad/connectors.json">Full connector ledger</a> · <a href="cad/pin-plan.json">ESP32 GPIO mapping</a></p>
<h2>Firmware and first installation</h2><p>Use the <a href="../../guide/firmware.html">MC2 build instructions</a>. Program the loose ESP32, C6 and MG24 before mounting. The ESP32-DevKitC-VIE has 8 MB flash; MC2-A S3 binaries and MC1's 16 MB layout are unsuitable. MG24 requires the explicit external mode (PB04=1, PB05=1); C6 requires its own RCP binary. The <a href="../../firmware/external-antenna/updates/README.md">network updater</a> checks target and antenna metadata.</p>
<h2>Measure coverage before migration</h2><p>Compare open bench, closed case and installed central position. Exercise Zigbee and Thread commands, BLE reports and active BLE connections in weak rooms, then repeat with all radios busy. Follow the <a href="../../guide/commissioning.html">commissioning procedure</a> and record actual results in the <a href="coverage-results.csv">unmeasured results sheet</a>. The target is reliable two-way communication, not a high RSSI number alone.</p><p>Retain the existing 433.92 MHz antenna and the regional ZAC93's stock antenna. LD2450 uses its own 24 GHz array. They do not connect to these 2.4 GHz bulkheads.</p>
<footer>Source-driven guide · <a href="../../hardware/designs.json">Active design registry</a> · <a href="../../docs/design-history.md">MC1 and earlier history</a><br>Power: battery-fed PoE switch → isolated splitter → regulated low-voltage rails. No new battery feed or injector is part of this revision.</footer></main>
<script>const input=document.getElementById('search');const rows=[...document.querySelectorAll('#nets tr')];function filter(){const q=input.value.trim().toLowerCase();let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++}document.getElementById('count').textContent=n+' of '+rows.length+' nets shown';document.getElementById('net-empty').hidden=n!==0}input.addEventListener('input',filter);filter();
const connectorSelect=document.getElementById('connector-select');const harnessSearch=document.getElementById('harness-search');const cards=[...document.querySelectorAll('.harness-card')];
function filterHarness(){const terms=harnessSearch.value.toLowerCase().trim().split(/\s+/).filter(Boolean);let wires=0,connectors=0;for(const card of cards){let visible=0;const selected=!connectorSelect.value||card.dataset.connector===connectorSelect.value;for(const row of card.querySelectorAll('tbody tr')){row.hidden=!selected||!terms.every(term=>row.dataset.search.includes(term));if(!row.hidden)visible++}card.hidden=visible===0;if(visible){connectors++;wires+=visible}}document.getElementById('harness-count').textContent=wires+' of __WIRE_COUNT__ wire connections across '+connectors+' of __CONNECTOR_COUNT__ connectors shown';document.getElementById('harness-empty').hidden=wires!==0}
connectorSelect.addEventListener('change',filterHarness);harnessSearch.addEventListener('input',filterHarness);document.getElementById('harness-clear').addEventListener('click',()=>{connectorSelect.value='';harnessSearch.value='';filterHarness();harnessSearch.focus()});document.getElementById('harness-controls').hidden=false;filterHarness();</script></html>'''
    return {'antenna-paths.svg': '\n'.join(svg)+'\n', 'index.html': page.replace('__WIRE_COUNT__', str(sum(len(h['pins']) for h in harnesses['harnesses']))).replace('__CONNECTOR_COUNT__', str(len(harnesses['harnesses']))).replace('__MODULES__',modules).replace('__ROWS__',rows).replace('__HARNESS_CARDS__',harness_cards).replace('__HARNESS_OPTIONS__',harness_options).replace('__ORIENTATION__',escape(harnesses['orientation'])).replace('__CASE_SIZE__', ' × '.join(str(v) for v in [params['case']['width'], params['case']['length'], params['case']['height'] + params['case']['lid']]))+'\n', 'harness.csv': harness_csv}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    stale=[]
    for name,data in render().items():
        p=HERE/name
        if args.check:
            if not p.exists() or p.read_text()!=data: stale.append(name)
        else: p.write_text(data)
    if stale: raise SystemExit('Stale MC2 guide: '+', '.join(stale))
    print('MC2 guide and RF/mechanical contract: OK')

if __name__ == '__main__': main()
