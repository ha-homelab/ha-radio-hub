#!/usr/bin/env python3
"""Render the H2 module-first architecture review. No hardware access."""
from pathlib import Path
import csv
import html
import json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

def count_parts(name):
    rows = csv.DictReader((REPO / 'hardware/low-power' / name / 'assembly-bom.csv').open())
    counts = {}
    for row in rows:
        key = row['Reference'][0]
        counts[key] = counts.get(key, 0) + int(row['Quantity'])
    return counts

data = {
    'title': 'H2 Quartet: finished modules on a through-hole carrier',
    'review_date': '2026-10-17',
    'status': 'historical experiment, not selected; MC1 is the current design; component compile only',
    'priority': 'Minimize builder-installed discrete parts; extra height and firmware work are acceptable.',
    'mounting': {'method': 'Factory male pins soldered directly into plated carrier holes',
                 'female_socket_quantity': 0, 'castellated_side_soldering': False},
    'h2_board': {'model': 'Waveshare ESP32-H2-Zero-M', 'sku': '32260', 'flash_mb': 4,
                 'headers': 'factory soldered', 'usb': 'native; no USB-UART bridge',
                 'quantity': 4, 'unit_usd_assumption': 5, 'subtotal_usd_assumption': 20},
    'gateway_gpio': {
        'spi_sclk': 4, 'spi_mosi': 5, 'spi_miso': 0, 'w5500_cs': 1, 'w5500_irq': 10,
        'cc1101_cs': 13, 'cc1101_tx_gdo0': 2, 'cc1101_rx_gdo2': 3,
        'peripheral_cs': 14, 'peripheral_ready': 11, 'radio_b_tx': 24, 'radio_b_rx': 23,
        'zigbee_tx': 12, 'zigbee_rx': 22},
    'peripheral_gpio': {'spi_sclk': 4, 'spi_mosi': 5, 'spi_miso': 0, 'spi_cs': 1,
                       'ready': 10, 'radar_tx': 24, 'radar_rx': 23,
                       'zwave_tx': 12, 'zwave_rx': 22, 'bme_sda': 2, 'bme_scl': 3},
    'reserved_gpio': [8, 9, 25, 26, 27],
    'uart': {'thread_baud': 460800, 'zigbee_baud': 115200, 'radar_baud': 256000,
             'zwave_baud': 115200, 'zigbee_flow_control': 'none; two-wire candidate'},
    'roles': [
        ['A', 'Gateway', 'Ethernet, BLE, CC1101; Thread host/BR requires a port'],
        ['B', 'Thread', 'Dedicated Thread RCP; UART to A'],
        ['C', 'Zigbee', 'ZBOSS NCP; UART to A; experimental host integration'],
        ['D', 'Peripherals', 'SPI slave; LD2450 + ZAC93 UARTs; BME680 I2C; radio off']],
    'assembly_counts_from_existing_boms': {k: count_parts(k) for k in ['carrier', 'carrier/mg24-adapter', 'integrated']},
    'sizing_not_measurements': {'uart_combined_bytes_per_second_one_direction': (256000 + 115200) // 10,
                              'proposed_spi_hz': 4000000, 'spi_raw_bytes_per_second_per_direction': 500000},
    'not_in_h2_subtotal': ['W5500 module', 'PoE splitter', 'power converter', 'peripheral modules',
                           'carrier and off-board connectors', 'shipping and taxes'],
    'open_gates': ['H2 local Thread BR build and platform port', 'full runtime memory',
                  'Zigbee backup and host compatibility', 'SPI transport implementation and arbitration',
                  'physical footprints, power transients, radio coexistence'],
    'sources': [
        ['H2-Zero-M manufacturer documentation', 'https://docs.waveshare.com/ESP32-H2-Zero'],
        ['H2-Zero schematic', 'https://files.waveshare.com/wiki/ESP32-H2-Zero/ESP32-H2-Zero-Schematic.pdf'],
        ['ESP-IDF 5.5.5 OpenThread link rules', 'https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/CMakeLists.txt'],
        ['Published Thread libraries', 'https://github.com/espressif/esp-thread-lib/tree/33209823e559560f54dcd41cbf3dbdd27f46d569'],
        ['ZBOSS support in Zigbee2MQTT', 'https://www.zigbee2mqtt.io/guide/adapters/zboss.html'],
        ['H2 coordinator firmware', 'https://github.com/tostmann/esp-coordinator'],
        ['Zephyr OpenThread BR sample', 'https://github.com/zephyrproject-rtos/zephyr/tree/main/samples/net/openthread/border_router']]
}

def esc(s): return html.escape(str(s))
def text(x, y, value, cls='body'):
    return f'<text x="{x}" y="{y}" class="{cls}">{esc(value)}</text>'
def box(x, y, w, h, title, lines, kind='module'):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" class="{kind}"/>'
    out += text(x+18, y+31, title, 'node')
    for i, line in enumerate(lines): out += text(x+18, y+59+i*23, line)
    return out
def line(points, kind='bus'):
    return f'<polyline points="{points}" class="{kind}"/>'
def svg_start(w,h,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<style>text{{font-family:Arial,sans-serif;fill:#182d3c}}.title{{font-size:30px;font-weight:700}}.sub{{font-size:17px;fill:#526879}}.node{{font-size:20px;font-weight:700}}.body{{font-size:16px}}.small{{font-size:14px;fill:#526879}}.module{{fill:#f2f7fb;stroke:#7196b2;stroke-width:2}}.host{{fill:#e0eff9;stroke:#236b98;stroke-width:3}}.peripheral{{fill:#f4f8f2;stroke:#759270;stroke-width:2}}.power{{fill:#fbf1e8;stroke:#b18051;stroke-width:2}}.bus{{fill:none;stroke:#236b98;stroke-width:3}}.uart{{fill:none;stroke:#658554;stroke-width:3}}.outline{{fill:#fff;stroke:#b5c6d0;stroke-width:2}}.board{{fill:#e6ede5;stroke:#6a8465;stroke-width:2}}</style>
<rect width="{w}" height="{h}" fill="#fff"/>'''

svg = svg_start(1320, 1100, data['title'])
svg += text(45, 53, 'H2 Quartet', 'title') + text(45, 84, 'Four finished H2 boards. One Ethernet. Through-hole carrier.', 'sub')
svg += text(45, 113, 'Candidate architecture • 17 Oct 2026 • full firmware and hardware not validated', 'small')
svg += box(45, 145, 1230, 109, 'Finished power modules', [
    'Active isolated PoE splitter → regulated 5 V → H2 board inputs + LD2450',
    'Assembled 3.3 V converter → WIZ850io + CC1101 + ZAC93 + BME680; common secondary ground'], 'power')
svg += line('305,370 390,370 390,410 470,410')
svg += line('305,560 390,560 390,410')
svg += line('390,560 390,735 475,735')
svg += line('790,365 930,365', 'uart')
svg += line('790,450 860,450 860,545 930,545', 'uart')
svg += line('650,845 650,905', 'uart')
svg += box(45, 310, 260, 130, 'WIZ850io', ['Assembled W5500 + RJ45', 'SPI / raw Ethernet', 'One external network link'])
svg += box(45, 500, 260, 135, 'Existing CC1101', ['433 MHz RF module', 'Shared SPI; own CS', 'RMT TX + RX on A'])
svg += box(470, 305, 320, 205, 'A · H2 gateway', ['Ethernet + BLE + RF', 'Thread host/BR port pending', '14 working GPIO', 'One shared SPI master bus', 'No local Linux or switch'], 'host')
svg += box(930, 300, 345, 135, 'B · H2 Thread radio', ['Standard RCP / Spinel UART', 'Separate 802.15.4 radio', 'Own native USB programming'])
svg += box(930, 480, 345, 135, 'C · H2 Zigbee radio', ['ZBOSS NCP / two-wire UART', 'One Zigbee2MQTT client', 'Host compatibility needs testing'])
svg += box(475, 675, 350, 170, 'D · H2 peripheral controller', ['SPI slave + READY handshake', 'Two independent hardware UARTs', 'BME680 via I2C', '2.4 GHz radio off'], 'peripheral')
svg += box(350, 905, 610, 106, 'Existing peripheral boards', ['LD2450 (256000 baud) · ZAC93 (115200 baud) · BME680', 'Local radar parsing and bounded per-channel queues'], 'peripheral')
svg += text(318, 294, 'Blue: shared SPI', 'small')
svg += text(818, 285, 'Green: serial / I2C', 'small')
svg += text(800, 354, 'UART', 'small') + text(870, 532, 'UART', 'small')
svg += text(45, 680, 'Four identical H2 boards:', 'node') + text(45, 714, '$20 at the user’s $5 assumption', 'body')
svg += text(45, 744, 'Other modules and carrier extra.', 'small')
svg += text(885, 707, 'Direct through-hole mounting', 'node')
svg += text(885, 738, 'Factory pins enter plated holes.', 'body')
svg += text(885, 764, 'No castellated-side soldering.', 'body')
svg += text(885, 790, 'Extra stack height is accepted.', 'body')
svg += text(45, 1052, 'Alternative software: A native Thread + B full BLE proxy; same module concept, new UART API transport required.', 'small')
svg += text(45, 1077, 'Power wires, pull-ups, exact connector orientation and board dimensions omitted. This is not a fabrication drawing.', 'small')
svg += '</svg>'
(ROOT/'architecture.svg').write_text(svg)

side = svg_start(1320, 675, 'Through-hole carrier assembly concept')
side += text(45, 53, 'Factory modules on a simple carrier', 'title')
side += text(45, 88, 'Concept only — footprints, row spacing and clearances require the exact boards', 'sub')
side += '<rect x="45" y="135" width="1230" height="245" rx="12" class="board"/>'
for i, name in enumerate(['A · gateway', 'B · Thread', 'C · Zigbee', 'D · peripherals']):
    side += box(85+i*290, 172, 240, 135, name, ['Finished H2-Zero-M', 'Factory male headers', 'Pins soldered to carrier'])
side += text(70, 353, 'Top view, not to scale: route only interconnect and power; keep antenna areas free of carrier copper.', 'body')
side += text(45, 429, 'Side section through one module', 'node')
side += '<rect x="120" y="465" width="470" height="20" class="module"/>'
side += '<rect x="120" y="562" width="470" height="15" class="board"/>'
for x in [170, 500]:
    side += f'<rect x="{x}" y="485" width="8" height="120" fill="#aa8348"/>'
    side += f'<ellipse cx="{x+4}" cy="580" rx="13" ry="6" fill="#84929c"/>'
side += text(670, 482, 'Ready-made module: leave factory components intact', 'body')
side += text(670, 531, 'Factory male pins: no female sockets', 'body')
side += text(670, 574, 'Carrier: plated through-holes and traces', 'body')
side += text(670, 607, 'Solder factory male pins from the underside', 'body')
side += text(45, 650, 'Selected construction: factory male pins soldered directly into plated carrier holes. No sockets or side-pad soldering.', 'small')
side += '</svg>'
(ROOT/'carrier-concept.svg').write_text(side)

proof = json.loads((REPO/'firmware/h2-quartet/build-evidence.json').read_text())
data['compile_probe'] = {'status': proof['status'], 'scope': proof['scope'],
                         'static_ram_used': proof['static_ram_used'],
                         'static_ram_report_capacity': proof['static_ram_report_capacity'],
                         'application_binary_bytes': proof['files']['firmware.ota.bin']['bytes']}
(ROOT/'assessment.json').write_text(json.dumps(data, indent=2)+'\n')

rows = ''.join('<tr>'+''.join(f'<td>{esc(c)}</td>' for c in row)+'</tr>' for row in data['roles'])
gpio_rows = ''.join(f'<tr><td>{esc(k)}</td><td>{v}</td></tr>' for k,v in data['gateway_gpio'].items())
sources = ''.join(f'<li><a href="{esc(url)}">{esc(label)}</a></li>' for label,url in data['sources'])
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>H2 Quartet — module-first review</title><style>
:root{{color-scheme:light;--ink:#182d3c;--muted:#526879;--line:#c7d5df;--blue:#236b98;--paper:#fff;--soft:#f2f7fb}}*{{box-sizing:border-box}}
body{{margin:0;font:16px/1.6 system-ui,sans-serif;color:var(--ink);background:#eef2f5}}main{{max-width:1250px;margin:auto;padding:30px;background:white}}
h1{{font-size:32px;line-height:1.2}}h2{{font-size:23px;margin-top:32px}}h3{{font-size:18px}}a{{color:var(--blue)}}.lead{{font-size:19px;max-width:1000px}}.muted,small{{color:var(--muted)}}
.strip{{border-left:5px solid var(--blue);padding:14px 20px;background:var(--soft)}}.columns{{display:grid;grid-template-columns:2fr 1fr;gap:32px}}.metric{{font-size:28px;font-weight:700}}
figure{{margin:26px 0}}figure img{{width:100%;height:auto}}figcaption{{font-size:14px;color:var(--muted)}}table{{border-collapse:collapse;width:100%;font-size:15px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}}th{{background:var(--soft)}}
select,button{{font:inherit;padding:8px;border:1px solid var(--line);border-radius:4px;background:#fff;color:var(--ink)}}details{{margin:20px 0}}summary{{cursor:pointer;font-weight:600}}
nav{{display:flex;gap:20px;flex-wrap:wrap}}.table-wrap{{overflow:auto}}.mono{{font-family:ui-monospace,monospace;font-size:13px;overflow-wrap:anywhere}}
@media(max-width:700px){{main{{padding:18px}}.columns{{display:block}}h1{{font-size:27px}}}}@media print{{body{{background:white}}main{{max-width:none;padding:0}}button,select,label{{display:none}}details>div{{display:block}}figure{{break-inside:avoid}}}}
</style></head><body><main>
<nav><a href="../module-carrier/index.html">Current MC1 design</a><a href="../../docs/h2-simplification.md">Historical English report</a><a href="assessment.json">Structured data</a><button onclick="print()">Print / PDF</button></nav>
<div class="strip"><strong>Historical experiment — not the selected build.</strong> On 17 October 2026 the project chose <a href="../module-carrier/index.html">MC1, one finished-module carrier with S3 + H2 + Ember MG24</a>, to preserve functions and Home Assistant compatibility. The analysis below remains a record of the rejected all-H2 option.</div>
<h1>H2 Quartet: ready-made modules on a through-hole carrier</h1>
<p class="lead">The main saving is assembly work: buy complete modules, insert their factory male pins directly into plated carrier holes, and solder from the underside. No female sockets. Extra height and custom firmware are acceptable.</p>
<p class="muted">17 October 2026 · architecture candidate · no complete hardware test or local H2 Thread BR build</p>
<div class="strip"><strong>Previously evaluated experiment:</strong> four identical H2-Zero-M boards, one W5500 module and finished power modules. This physical simplification did not retain the existing software/compatibility baseline.</div>
<h2>Compare the implementation choices</h2>
<label for="variant">Candidate </label><select id="variant"><option value="four">4 H2 · module-first target</option><option value="three">3 H2 + UART expander</option><option value="mixed">S3 + 2 H2 · fallback</option></select>
<div class="columns"><div><h3 id="variantTitle">4 H2 · module-first target</h3><p id="variantText">The fourth H2 connects as an SPI slave and gives both hardware UARTs to radar and Z-Wave. This removes SC16 and its support circuit. Gateway firmware remains the main development task.</p></div><div><p class="metric" id="subtotal">$20 for H2 boards</p><p class="muted">At the user's $5 assumption. Other modules, carrier, connectors, shipping and taxes excluded. No measured power claim.</p></div></div>
<figure><img src="architecture.svg" alt="Four H2 boards connected to one gateway, one Ethernet module and existing sensors"><figcaption>Logical connections. The local Thread border router on H2 is a development gate, not a completed feature.</figcaption></figure>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Role</th><th>Responsibility</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Alternative software can put native Thread on A and the complete BLE proxy on B. This reduces shared host memory but requires a new framed API transport; HCI alone does not move the BLE host stack off A.</p>
<h2>No side-pad soldering</h2>
<figure><img src="carrier-concept.svg" alt="Finished module pins soldered directly through carrier holes, without sockets"><figcaption>Assembly concept only; not a released footprint or fabrication drawing.</figcaption></figure>
<p><strong>H2 board candidate:</strong> Waveshare ESP32-H2-Zero-M, SKU 32260, 4 MB, native USB, factory-fitted headers. The selected GPIO map leaves RGB LED, boot straps and USB untouched. Existing C0/I0 footprints cannot be reused unchanged.</p>
<p>Use a finished WIZ850io Ethernet module, assembled isolated active PoE splitter, assembled power converter and existing radio/sensor boards. A few pull-ups and a fuse may still be needed. Do not parallel the H2 boards' regulator outputs or tie USB power to the PoE splitter output.</p>
<h2>Count the work the builder performs</h2>
<div class="table-wrap"><table><thead><tr><th>Existing board BOM</th><th>Capacitors</th><th>Resistors</th><th>Meaning</th></tr></thead><tbody>
<tr><td>C0 + M0</td><td>20</td><td>18</td><td>Manual component placements in the published assembly BOM</td></tr>
<tr><td>I0</td><td>44</td><td>35</td><td>Alternative integrated build; do not add it to C0 + M0</td></tr>
<tr><td>Quartet carrier target</td><td>Factory module decoupling</td><td>A few interface pull-ups if required</td><td>Through-hole connectors; final loose-part count pending selected module revisions</td></tr>
</tbody></table></div><p class="muted">Counts come from the committed assembly BOMs. Factory-installed parts still exist electronically; they are no longer the builder's SMD assembly task.</p>
<h2>A real component build succeeded</h2>
<p><strong>H2 + W5500 + active ESPHome BLE proxy, three connection slots:</strong> linked with ESPHome 2026.9.1 / ESP-IDF 5.5.5. Static report: 106,302 / 258,000 bytes (41.2%). Application binary: 1,061,120 bytes.</p>
<p>This probe excludes Thread, Zigbee, RF, sensors, API encryption and OTA service. Its GPIOs are placeholders. No board was flashed and runtime free heap was not measured.</p>
<p><a href="../../firmware/h2-quartet/README.md">Reproduce the build and inspect exact hashes</a></p>
<h2>Development gates</h2><ol>
<li><strong>Local Thread BR:</strong> ESP-IDF's public prebuilt BR library has no H2 target. Port the platform glue or evaluate the open Zephyr BR. Zephyr's existing ESP sample uses S3/PSRAM, so H2 remains an unverified port.</li>
<li><strong>Memory:</strong> measure heap and task stacks with the whole gateway running. A low static percentage for the small BLE probe is not full-system headroom.</li>
<li><strong>Zigbee:</strong> H2 ZBOSS firmware exists, but stock Z2M calls it experimental; test recovery on a spare H2. Current custom ZHA support has dependency incompatibilities.</li>
<li><strong>Shared SPI:</strong> implement ready/credits, bounded frames, per-channel queues and failure recovery; measure contention with W5500 and CC1101.</li>
<li><strong>Physical assembly:</strong> verify footprints, power transients and RF coexistence before ordering the carrier.</li></ol>
<details><summary>Candidate gateway GPIO map</summary><div class="table-wrap"><table><thead><tr><th>Signal</th><th>GPIO</th></tr></thead><tbody>{gpio_rows}</tbody></table></div><p>GPIO labels only. Two-wire Zigbee serial, no RTS/CTS. All 14 safe exposed GPIO are used. No fabrication pin numbering implied.</p></details>
<h2>Primary sources</h2><ul>{sources}</ul>
<script>const variants={{four:['4 H2 · module-first target','The fourth H2 connects as an SPI slave and gives both hardware UARTs to radar and Z-Wave. This removes SC16 and its support circuit. Gateway firmware remains the main development task.',20],three:['3 H2 + UART expander','Saves one H2, but retains a UART expander or requires another peripheral allocation. It does not automatically reduce the number of part types or manual assembly operations.',15],mixed:['S3 + 2 H2 · fallback','Retains the more mature S3 host build. All processors can still be purchased on ready-made boards. Zigbee migration and the UART expander remain separate issues.',10]}};document.getElementById('variant').addEventListener('change',event=>{{const v=variants[event.target.value];document.getElementById('variantTitle').textContent=v[0];document.getElementById('variantText').textContent=v[1];document.getElementById('subtotal').textContent='$'+v[2]+' for H2 boards';}});</script>
</main></body></html>'''
(ROOT/'index.html').write_text(page)
print('Rendered assessment.json, architecture.svg, carrier-concept.svg and index.html')
