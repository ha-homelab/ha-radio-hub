#!/usr/bin/env python3
"""Render the MC2 guide from the carrier connector ledger and RF selection."""
import argparse
from html import escape
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def render():
    rf = json.loads((HERE / 'rf-bom.json').read_text())
    design = json.loads((HERE / 'cad/design.json').read_text())
    connectors = json.loads((HERE / 'cad/connectors.json').read_text())['connectors']
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
                f'<text x="{x}" y="325" text-anchor="middle" fill="{c}" font-size="17" font-weight="700">{["ESP32-DevKitC-VIE", "TinyC6-U-01", "XIAO MG24"][i]}</text>',
                f'<text x="{x}" y="355" text-anchor="middle" font-size="16">{["BLE + host services", "Thread RCP", "Ember Zigbee NCP"][i]}</text>',
                f'<text x="{x}" y="387" text-anchor="middle" font-size="14" fill="#b8c9dd">{["Factory external RF", "Factory external RF", "Firmware: PB04=1 / PB05=1"][i]}</text>']
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
        'U2': 'Original U.FL variant, native USB, 8 MB flash. Solder its supplied 1×12 and 1×11 headers. Carrier pull-up R3 holds its GPIO8 strap high for ROM recovery; no LiPo fitted.',
        'U3': 'Pre-soldered header version. Ember UART with hardware flow control; external antenna selected before startup with PB04=1 and PB05=1.',
        'U4': '3.3 V SPI Ethernet module with two 1×6 headers. Its jack receives data downstream of the separate PoE splitter.',
    }
    modules = ''.join(f'<li><strong>{escape(p["ref"])} — {escape(p["model"])}</strong><br>{escape(descriptions[p["ref"]])}</li>' for p in connectors if p['ref'].startswith('U'))
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC2 · External-antenna radio hub</title>
<style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0b1421;color:#e6effb}*{box-sizing:border-box}body{margin:0}main{max-width:1160px;margin:auto;padding:28px}nav{display:flex;flex-wrap:wrap;gap:18px;margin-bottom:36px}a{color:#83c9ff;text-underline-offset:3px}h1{font-size:clamp(34px,6vw,64px);line-height:1.06;max-width:850px;margin:10px 0 22px}h2{margin-top:38px;font-size:27px}p,li{line-height:1.65;color:#bdcde1}li{margin:13px 0}strong,th{color:#edf5ff}.eyebrow{letter-spacing:.14em;color:#2dd4bf;font-size:13px;font-weight:700}.lead{font-size:20px;max-width:880px}.notice{border-left:4px solid #eab85d;background:#302a22;padding:16px 22px;border-radius:4px;color:#f4dfbb}.hero{width:100%;display:block;margin:26px 0;border-radius:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.card{background:#142237;border:1px solid #293c55;border-radius:14px;padding:22px}.card b{font-size:25px;display:block;color:#fff}.card p{margin-bottom:0}.figure{display:block;width:100%;background:#f3f7fb;border-radius:12px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:13px;text-align:left;border-bottom:1px solid #2d4059;vertical-align:top}td{min-width:270px;color:#bdcde1}th{white-space:nowrap}input{background:#16263e;border:1px solid #527193;border-radius:6px;color:white;padding:14px;width:100%;max-width:600px;font-size:16px;margin:12px 0}footer{margin-top:42px;border-top:1px solid #293c55;padding:24px 0;color:#96abc5;font-size:14px}code{color:#e3bfef}button{background:#203b56;border:1px solid #527193;border-radius:5px;color:white;padding:9px 14px;cursor:pointer}@media(max-width:600px){main{padding:18px}.lead{font-size:17px}.hero{border-radius:8px}}@media print{:root{color-scheme:light;background:white;color:#111}p,li,td,strong,th{color:#111}nav,button,input{display:none}.card,.notice{background:#eee}.scroll{overflow:visible}}</style>
<main><nav><a href="../../docs/external-antennas.md">Assembly instructions</a><a href="cad/BOM.csv">Carrier BOM</a><a href="rf-bom.json">Antenna BOM</a><a href="../../firmware/external-antenna/README.md">Firmware</a><a href="#wiring">Pin lookup</a><button onclick="print()">Print</button></nav>
<div class="eyebrow">HA RADIO HUB / MC2-B / 19 OCTOBER 2026</div><h1>Give every radio<br>its own antenna.</h1><p class="lead">A dedicated external path for Zigbee, Thread and Bluetooth, with the existing local Home Assistant functions preserved on a wired PoE connection.</p>
<div class="notice"><strong>Engineering prototype.</strong> The carrier, software and printed enclosure have separate digital checks. Physical fit, simultaneous-radio operation and coverage of a 1,000 ft² house remain unmeasured. MC1 and MC2-A files are historical; MC2-A S3 boards and firmware are not interchangeable with MC2-B.</div>
<img class="hero" src="images/mc2b-assembled-concept.png" alt="MC2-B classic ESP32 assembled appearance concept, not a photograph">
<p>AI-generated MC2-B appearance concept with ESP32-DevKitC-VIE and two additional boot resistors. Module internals, pin counts and copper are approximate; use the native drawing below for assembly. Antennas are omitted for visibility; connect all three before operation. <a href="images/README.md">Image provenance</a> · <a href="../../docs/mc2-shopping.md">Exact shopping list and AliExpress checks</a></p>
<img class="hero" src="antenna-paths.svg" alt="Three independent antenna paths, BLE, Thread and Zigbee">
<section class="grid"><article class="card"><b>3 × 2.4 GHz</b><p>Separate 50 Ω antenna feeds; no shared RF combiner.</p></article><article class="card"><b>100 × 100 mm</b><p>Two-layer carrier. All components on one side. Through-hole module attachment.</p></article><article class="card"><b>__CASE_SIZE__ mm</b><p>Full-hub main shell, with dedicated module mounts and an attached ventilated BME680 pod.</p></article></section>
<h2>Exact modules, not generic substitutes</h2><ul>__MODULES__</ul><p><strong>Availability:</strong> TinyC6-U-01 was backorder/on-request in the checked listings. Verify the U.FL SKU before ordering. TinyC6[D], H2 and onboard-antenna variants are not interchangeable with this design.</p>
<h2>Antenna and cable selection</h2><p>Buy three <a href="https://www.te.com/en/product-L9000082-01.html">TE ANT-2.4-LCW-SMA</a> antennas (2400–2485 MHz, 2.8 dBi peak) and three <a href="https://www.amphenolrf.com/en-us/part/095-902-545-150/8897/">Amphenol 095-902-545-150</a> cables. Standard SMA male antenna mates with a standard SMA female bulkhead; the radio end is AMC/U.FL compatible. RP-SMA and smaller MHF connector variants are not substitutes.</p><p>BLE, THREAD and ZIGBEE bulkheads stay on the fixed base. Their 65 mm adjacent pitch is a layout target, not an isolation measurement. Leave slack, use strain relief and test the 150 mm cable route. Connect antennas before powering the radios.</p>
<h2>Full assembly and Z-Wave placement</h2><img class="hero" src="images/full-hub-exploded-concept.png" alt="AI appearance concept of the full hub, exploded to show its modules"><p>AI illustration; dimensions and connections come from the CAD and wiring below. <strong>Zooz ZAC93 sits in a separate insulated cradle beside the carrier.</strong> Its underside 2×5 socket connects by a remapped harness to J4, while the DFR0627 UART bridge connects to J3. <a href="../../docs/full-hub-assembly.md">Complete assembly and ZAC93 pin map</a>.</p><div class="grid"><article><a href="cad/assembly-top.svg"><img class="figure" src="cad/assembly-top.svg" alt="MC2 front assembly from CAD"></a><p><a href="cad/schematic.svg">Circuit schematic</a> · <a href="cad/">Native KiCad files</a></p></article><article><a href="../../mechanical/full-hub/index.html"><img class="figure" src="../../mechanical/full-hub/layout.svg" alt="Exact full-hub component layout and mounts"></a><p><a href="../../mechanical/full-hub/index.html">All print parts and dimensions</a> · <a href="../../mechanical/full-hub/README.md">Assembly and fit checks</a></p></article></div><p>These images are design renders. Print the connector fit coupon first. Dedicated trays retain the isolated splitter, buck converter, UART bridge, Z-Wave, CC1101, DC adapter and fuse. The radar mounts behind the lid window; BME680 sits in an attached ventilated pod outside the warm shell. Exact purchased heights, connector fit, thermal behavior and RF performance remain unmeasured. <a href="full-hub-wiring.svg">Full-hub wiring diagram</a> · <a href="../../mechanical/full-hub/components.json">Full assembly inventory</a>.</p>
<h2 id="wiring">Find a net or physical pad</h2><p>Generated from the MC2 design ledger, including the resistors and diodes. Labels identify <strong>carrier reference:physical pad</strong>, not a generic GPIO header. THREAD_RX and ZB_RX name the radio receiver: connect the host transmitter there. Confirm orientation against the schematic before soldering.</p><label for="search">Net, module reference or pin</label><br><input id="search" type="search" placeholder="Try THREAD, U2:12, RADAR or GND"><p id="count" aria-live="polite"></p><div class="scroll"><table><thead><tr><th>Net</th><th>Connected endpoints</th></tr></thead><tbody id="nets">__ROWS__</tbody></table></div><p><a href="cad/connectors.json">Full connector ledger</a> · <a href="cad/pin-plan.json">ESP32 GPIO mapping</a></p>
<h2>Firmware and first installation</h2><p>Use the <a href="../../firmware/external-antenna/README.md">MC2 build instructions</a>. Program the loose ESP32, C6 and MG24 before mounting. The ESP32-DevKitC-VIE has 8 MB flash; MC2-A S3 binaries and MC1's 16 MB layout are unsuitable. MG24 requires the explicit external mode (PB04=1, PB05=1); C6 requires its own RCP binary. The <a href="../../firmware/external-antenna/updates/README.md">network updater</a> checks target and antenna metadata.</p>
<h2>Measure coverage before migration</h2><p>Compare open bench, closed case and installed central position. Exercise Zigbee and Thread commands, BLE reports and active BLE connections in weak rooms, then repeat with all radios busy. Follow the <a href="../../docs/rf-commissioning.md">commissioning procedure</a> and record actual results in the <a href="coverage-results.csv">unmeasured results sheet</a>. The target is reliable two-way communication, not a high RSSI number alone.</p><p>Retain the existing 433.92 MHz antenna and the regional ZAC93's stock antenna. LD2450 uses its own 24 GHz array. They do not connect to these 2.4 GHz bulkheads.</p>
<footer>Source-driven guide · <a href="../../hardware/designs.json">Active design registry</a> · <a href="../../docs/design-history.md">MC1 and earlier history</a><br>Power: battery-fed PoE switch → isolated splitter → regulated low-voltage rails. No new battery feed or injector is part of this revision.</footer></main>
<script>const input=document.getElementById('search');const rows=[...document.querySelectorAll('#nets tr')];function filter(){const q=input.value.trim().toLowerCase();let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++}document.getElementById('count').textContent=n+' of '+rows.length+' nets shown'}input.addEventListener('input',filter);filter();</script></html>'''
    return {'antenna-paths.svg': '\n'.join(svg)+'\n', 'index.html': page.replace('__MODULES__',modules).replace('__ROWS__',rows).replace('__CASE_SIZE__', ' × '.join(str(v) for v in [params['case']['width'], params['case']['length'], params['case']['height'] + params['case']['lid']]))+'\n'}


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
