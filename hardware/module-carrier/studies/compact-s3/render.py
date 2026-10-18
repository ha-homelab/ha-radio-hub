#!/usr/bin/env python3
"""Render the compact-host review. Outlines are not a new carrier PCB."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
esc = html.escape


def outline_svg(data):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="600" viewBox="0 0 1100 600" role="img" aria-labelledby="title desc">',
           '<title id="title">S3 module outline comparison in millimetres</title>',
           '<desc id="desc">Same-scale rectangular board outlines. These show module dimensions, not a routed carrier or connector clearance.</desc>',
           '<rect width="1100" height="600" fill="#0c1828"/>',
           '<g font-family="Arial,sans-serif">',
           '<text x="35" y="40" fill="#e4edf5" font-size="25">Smaller host module, unchanged radio roles</text>',
           '<text x="35" y="70" fill="#adc4d5" font-size="15">Same scale · dimensions in mm · outlines only, no new PCB placement or routing</text>']
    for i, item in enumerate(data['outlines']):
        x, y, scale = 55 + i * 350, 145, 5.1
        w, h = item['width_mm'], item['height_mm']
        color = '#1b555b' if item.get('preferred') else '#26394b'
        out += [f'<text x="{x}" y="110" fill="#e4edf5" font-size="19">{esc(item["short_name"])}</text>',
                f'<text x="{x}" y="132" fill="#adc4d5" font-size="14">{esc(item["memory"])}</text>',
                f'<rect x="{x}" y="{y}" width="{w*scale:.2f}" height="{h*scale:.2f}" fill="{color}" stroke="#9ebfc8"/>',
                f'<text x="{x+w*scale+10:.2f}" y="{y+h*scale/2:.2f}" fill="#adc4d5" font-size="16">{h:g} mm</text>',
                f'<text x="{x}" y="{y+h*scale+27:.2f}" fill="#adc4d5" font-size="16">{w:g} mm wide</text>',
                f'<text x="{x}" y="510" fill="#e4edf5" font-size="16">{w*h:,.1f} mm² module area</text>',
                f'<text x="{x}" y="535" fill="#adc4d5" font-size="14">{esc(item["footnote"])}</text>']
    out += ['<text x="35" y="578" fill="#adc4d5" font-size="14">Carrier area and fabrication price cannot be inferred from module-area reduction alone.</text>', '</g></svg>']
    return '\n'.join(out) + '\n'


def architecture_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="430" viewBox="0 0 1100 430" role="img" aria-labelledby="title desc">
<title id="title">Preserved MC1 architecture with a compact S3</title><desc id="desc">Ethernet connects directly to S3 over SPI. Separate Thread and Zigbee radios retain their host protocols. Peripheral connections remain on S3.</desc>
<rect width="1100" height="430" fill="#0c1828"/><g font-family="Arial,sans-serif" fill="#e4edf5">
<text x="35" y="40" font-size="25">Keep Ethernet on the host</text><text x="35" y="68" fill="#adc4d5" font-size="15">Preferred topology: no additional microcontroller, no new inter-processor network protocol</text>
<g stroke="#8eb5c2" stroke-width="2" fill="none"><path d="M260 201H420M690 173H820M690 229H820M520 253V324H530M460 253V367H600M350 201V329H320"/></g>
<g fill="#26394b" stroke="#8eb5c2"><rect x="40" y="159" width="220" height="84" rx="5"/><rect x="820" y="130" width="240" height="84" rx="5"/><rect x="820" y="226" width="240" height="84" rx="5"/><rect x="40" y="295" width="280" height="92" rx="5"/></g>
<rect x="420" y="135" width="270" height="118" rx="5" fill="#1b555b" stroke="#8bd6c7"/>
<text x="70" y="192" font-size="20">WIZ850io / W5500</text><text x="70" y="218" font-size="15">RJ45 at carrier edge</text>
<text x="448" y="172" font-size="22">Compact ESP32-S3</text><text x="448" y="199" font-size="15">Ethernet · local Thread BR</text><text x="448" y="225" font-size="15">BLE proxy · application services</text>
<text x="843" y="164" font-size="20">Existing H2</text><text x="843" y="191" font-size="15">Thread RCP · Spinel UART</text>
<text x="843" y="260" font-size="20">Existing XIAO MG24</text><text x="843" y="287" font-size="15">Zigbee NCP · Ember UART</text>
<text x="62" y="329" font-size="20">CC1101</text><text x="62" y="356" font-size="15">Shared SPI, separate CS + GDO</text>
<text x="543" y="329" font-size="17">LD2450 · dedicated UART</text><text x="613" y="373" font-size="17">BME680 + WK2132 / Z-Wave · I²C</text>
<text x="284" y="190" font-size="14" fill="#adc4d5">Shared SPI</text><text x="709" y="161" font-size="14" fill="#adc4d5">UART</text><text x="709" y="250" font-size="14" fill="#adc4d5">UART</text>
<text x="35" y="413" fill="#adc4d5" font-size="14">Logical connections only. RF, power, service clearance and PCB routing require a separate physical review.</text></g></svg>
'''


def outputs():
    d = json.loads((ROOT / 'decision.json').read_text())
    a = json.loads((ROOT / 'architecture-options.json').read_text())
    rows = ''.join(f'<tr><th>{esc(r["board"])}</th><td>{esc(r["size"])}</td><td>{esc(r["memory"])}</td><td>{esc(r["assembly"])}</td><td>{esc(r["decision"])}</td></tr>' for r in d['comparison'])
    choices = ''.join(f'<tr><th>{esc(r["label"])}</th><td>{r.get("host_application_gpio", str(r.get("host_application_gpio_minimum"))+" minimum")}</td><td>{"Required" if r["new_inter_mcu_protocol"] else "None"}</td><td>{esc(r["tradeoff"])}</td></tr>' for r in a['options'])
    steps = ''.join(f'<li><strong>{esc(r["title"])}</strong><p>{esc(r["detail"])}</p></li>' for r in d['steps'])
    build = ''.join(f'<li>{esc(s)}</li>' for s in d['validation'])
    sources = ''.join(f'<li><a href="{esc(s["url"], quote=True)}">{esc(s["label"])}</a></li>' for s in d['sources'])
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC1 · compact S3 review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#0c1828;color:#e4edf5;font:16px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:28px}h1{font-size:34px;line-height:1.18;max-width:850px}h2{font-size:24px;margin-top:40px}h3{font-size:19px}a{color:#8bd6c7}p{max-width:940px}.muted,figcaption{color:#adc4d5}.lead{font-size:21px}.band{border-left:3px solid #8bd6c7;background:#163139;padding:12px 18px;margin:26px 0}.caution{border-left-color:#deb676;background:#302b22}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:30px}figure{margin:26px 0}img{width:100%;height:auto}figcaption{font-size:14px}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #29404e}li{margin:10px 0}li p{margin:4px 0 18px}code{overflow-wrap:anywhere}details{border-top:1px solid #29404e;padding:13px 0}summary{cursor:pointer;font-weight:600}nav{display:flex;gap:20px;flex-wrap:wrap}strong{color:#f2f7fa}@media(max-width:500px){main{padding:18px}h1{font-size:28px}.lead{font-size:18px}}</style>
<main><nav><a href="../../index.html#pcb">Current MC1</a><a href="../square-layout/index.html">100 × 100 mm study</a></nav>
<p class="muted">Engineering review · 17 October 2026 · three independent workstreams</p>'''
    page += f'<h1>{esc(d["title"])}</h1><p class="lead">{esc(d["lead"])}</p><div class="band">{esc(d["decision"])}</div><div class="band caution">{esc(d["limitation"])}</div>'
    page += '<figure><a href="outlines.svg"><img src="outlines.svg" alt="Same-scale dimensioned comparison of S3 module outlines"></a><figcaption>Manufacturer board dimensions, not a new carrier layout. Click to enlarge.</figcaption></figure>'
    page += '<h2>Which ready-made board actually fits the assembly method?</h2><div class="scroll"><table><thead><tr><th>Board</th><th>Dimensions</th><th>Flash / PSRAM</th><th>Connections</th><th>Assessment</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
    page += f'<p>{esc(d["assembly_note"])}</p><figure><a href="architecture.svg"><img src="architecture.svg" alt="Direct Ethernet on compact S3, with existing H2 and MG24 radios"></a></figure>'
    page += '<h2>Does an Ethernet intermediary help?</h2><p>It can release host pins, but W5500, RJ45 and all three processors remain. A transparent frame transport does not remove the host’s application and network-stack memory requirements.</p><div class="scroll"><table><thead><tr><th>Architecture</th><th>Host GPIO</th><th>New inter-MCU protocol</th><th>Tradeoff</th></tr></thead><tbody>'+choices+'</tbody></table></div><p class="muted">'+esc(a['gpio_scope'])+'</p>'
    page += '<details><summary>Shared SPI and startup constraints</summary><p>'+esc(d['shared_spi_note'])+'</p></details><details><summary>Memory: capacity is not measured demand</summary><p>'+esc(d['memory_note'])+'</p></details>'
    page += '<h2>Implementation sequence</h2><ol>'+steps+'</ol><h2>What has actually been checked?</h2><ul>'+build+'</ul>'
    page += '<h2>Review and reproducible artifacts</h2><ul><li><a href="hardware-review.md">Hardware candidates and header map</a></li><li><a href="firmware-review.md">Firmware and Ethernet-intermediary review</a></li><li><a href="independent-review.md">Independent physical, RF and service review</a></li><li><a href="pin-plan.json">Machine-readable pin plan</a></li><li><a href="firmware/README.md">Isolated candidate firmware and reproduction</a></li><li><a href="firmware/build-evidence-nano.json">Nano full-build evidence</a> · <a href="firmware/build-evidence-mini.json">Mini comparison build</a></li><li><a href="decision.json">Decision data</a> · <a href="architecture-options.json">Architecture assumptions</a></li></ul><h2>Primary sources</h2><ul>'+sources+'</ul><p class="muted">No hardware was flashed, bought or ordered. The active MC1 PCB and deployment firmware are unchanged.</p></main></html>\n'
    return {'index.html': page, 'outlines.svg': outline_svg(d), 'architecture.svg': architecture_svg()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, content in outputs().items():
        if args.check:
            if (ROOT / name).read_text() != content:
                raise SystemExit('Stale generated artifact: ' + name)
        else:
            (ROOT / name).write_text(content)
    print('Compact S3 review ' + ('verified' if args.check else 'rendered'))
