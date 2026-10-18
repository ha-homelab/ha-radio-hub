#!/usr/bin/env python3
"""Render the SMLIGHT comparison from review data; no hardware is generated."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
esc = html.escape


def diagram():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="650" viewBox="0 0 1140 650" role="img" aria-labelledby="title desc">',
           '<title id="title">Where the Thread border router runs</title>',
           '<desc id="desc">Classic remote-radio mode places OTBR on another computer. New SLZB U devices and the MC1 proposal run OTBR on their ESP32 host. Their radios remain separate.</desc>',
           '<rect width="1140" height="650" fill="#0c1828"/>',
           '<g font-family="Arial,sans-serif" fill="#e4edf5">',
           '<text x="32" y="38" font-size="25">The important difference is the location of OTBR</text>',
           '<text x="32" y="67" font-size="15" fill="#adc4d5">Logical architecture · not a PCB drawing · current vendor firmware and our compiled candidate</text>']
    lanes = [
        (112, 'Classic SLZB remote-radio mode', 'Thread radio / RCP', 'SLZB host', 'Serial-to-network bridge', 'HA / Linux host', 'OTBR runs here', 'UART', 'Serial over TCP', '#26394b'),
        (282, 'SLZB-MRxU · native SLZB-OS', 'Thread + Zigbee radios', 'ESP32-S3 + W5500', 'Local OTBR · BLE advertisements', 'Home Assistant', 'REST integration + IPv6 traffic', 'Local radio links', 'Ethernet', '#1b555b'),
        (452, 'MC1 compact-S3 candidate', 'H2 Thread + MG24 Zigbee', 'S3-Nano + W5500', 'Local OTBR · 3 active BLE slots', 'Home Assistant', 'Same local-BR topology', 'Local radio links', 'Ethernet', '#1b555b'),
    ]
    for y, title, radio, host, detail, ha, ha_detail, left_link, right_link, fill in lanes:
        out += [f'<text x="32" y="{y}" font-size="19">{esc(title)}</text>',
                f'<path d="M282 {y+65}H389 M715 {y+65}H840" stroke="#8eb5c2" stroke-width="2" fill="none"/>',
                f'<rect x="32" y="{y+27}" width="250" height="76" rx="5" fill="#26394b" stroke="#8eb5c2"/>',
                f'<rect x="389" y="{y+27}" width="326" height="76" rx="5" fill="{fill}" stroke="#8eb5c2"/>',
                f'<rect x="840" y="{y+27}" width="268" height="76" rx="5" fill="#26394b" stroke="#8eb5c2"/>',
                f'<text x="47" y="{y+71}" font-size="16">{esc(radio)}</text>',
                f'<text x="405" y="{y+58}" font-size="19">{esc(host)}</text>',
                f'<text x="405" y="{y+85}" font-size="14">{esc(detail)}</text>',
                f'<text x="856" y="{y+58}" font-size="19">{esc(ha)}</text>',
                f'<text x="856" y="{y+85}" font-size="14">{esc(ha_detail)}</text>',
                f'<text x="293" y="{y+50}" font-size="12" fill="#adc4d5">{esc(left_link)}</text>',
                f'<text x="733" y="{y+50}" font-size="12" fill="#adc4d5">{esc(right_link)}</text>']
    out += ['<text x="32" y="606" font-size="15" fill="#adc4d5">MRxU and MC1 keep a host plus two radio MCUs. Sharing one radio is not the simplification used here.</text>',
            '<text x="32" y="632" font-size="14" fill="#adc4d5">SLZB local OTBR: documented beta. MC1: full firmware compiled; hardware and concurrent operation untested.</text>',
            '</g></svg>']
    return '\n'.join(out) + '\n'


def outputs():
    d = json.loads((ROOT / 'decision.json').read_text())
    findings = ''.join(f'<section><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p><a href="{esc(x["source"], quote=True)}">Evidence</a></section>' for x in d['findings'])
    rows = ''.join('<tr>' + ''.join(f'<{tag}>{esc(x[k])}</{tag}>' for k, tag in [('name', 'th'), ('thread', 'td'), ('zigbee', 'td'), ('ble', 'td'), ('extra', 'td')]) + '</tr>' for x in d['modes'])
    tasks = ''.join(f'<li><span class="tag">{esc(x["priority"])}</span><strong>{esc(x["title"])}</strong><p>{esc(x["text"])}</p></li>' for x in d['improvements'])
    alternatives = ''.join(f'<section><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p></section>' for x in d['buy_or_build'])
    sources = ''.join(f'<li><a href="{esc(x["url"], quote=True)}">{esc(x["label"])}</a></li>' for x in d['sources'])
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC1 · SMLIGHT Thread comparison</title>
<style>*{box-sizing:border-box}body{margin:0;background:#0c1828;color:#e4edf5;font:16px/1.6 system-ui,sans-serif}main{max-width:1220px;margin:auto;padding:28px}h1{font-size:34px;line-height:1.2;max-width:950px}h2{font-size:24px;margin-top:40px}h3{font-size:19px}a{color:#8bd6c7}p{max-width:1000px}.lead{font-size:21px}.muted,figcaption{color:#adc4d5}.band{padding:14px 18px;background:#163139;border-left:3px solid #8bd6c7;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:12px 34px}figure{margin:28px 0}img{width:100%;height:auto}figcaption{font-size:14px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{vertical-align:top;text-align:left;padding:10px;border-bottom:1px solid #29404e}li{margin:12px 0}li p{margin:5px 0 23px}.tag{display:inline-block;color:#adc4d5;margin-right:12px}nav{display:flex;gap:18px;flex-wrap:wrap}code{overflow-wrap:anywhere}@media(max-width:500px){main{padding:18px}h1{font-size:28px}.lead{font-size:18px}}</style>
<main><div class="band"><strong>Historical design study.</strong> Its findings describe the pre-Nano revision. The selected design is now implemented in the <a href="../../index.html#pcb">current MC1 carrier and firmware</a>; use those files for construction.</div><nav><a href="../compact-s3/index.html">Compact S3 review</a><a href="../../index.html#pcb">Current MC1</a></nav>'''
    page += f'<p class="muted">SMLIGHT SLZB review · {esc(d["date"])} · three specialist reviews</p><h1>{esc(d["title"])}</h1><p class="lead">{esc(d["lead"])}</p><div class="band">{esc(d["decision"])}</div><p class="muted">{esc(d["scope"])}</p>'
    page += '<figure><a href="comparison.svg"><img src="comparison.svg" alt="Three paths: remote Thread radio, local SLZB U border router, local MC1 border router"></a><figcaption>Follow the OTBR location, not just a Thread logo. Click for the full-size diagram.</figcaption></figure>'
    page += '<h2>What changes our conclusion?</h2><div class="grid">'+findings+'</div>'
    page += '<h2>Firmware modes are different products in practice</h2><div class="scroll"><table><thead><tr><th>Mode</th><th>Thread</th><th>Zigbee</th><th>Bluetooth</th><th>Consequence</th></tr></thead><tbody>'+rows+'</tbody></table></div><p class="muted">A mode advertised for the family is not proof of every feature running simultaneously on every model. A local border router is also not a Matter controller.</p>'
    page += '<h2>Changes worth making to our implementation plan</h2><ol>'+tasks+'</ol><p>These are verification and design tasks, not completed runtime fixes. The source-level recovery findings are detailed in the firmware review below.</p>'
    page += '<h2>Could we use the finished product instead?</h2><div class="grid">'+alternatives+'</div><h2>Reviews and reproducible evidence</h2><ul><li><a href="hardware-review.md">Hardware, memory, Ultima and pin budget</a></li><li><a href="firmware-review.md">Firmware, source availability and our recovery gaps</a></li><li><a href="compatibility-review.md">HA compatibility, feature matrix and migration</a></li><li><a href="decision.json">Decision data</a> · <a href="README.md">Scope and reproduction</a></li></ul><h2>Primary sources</h2><ul>'+sources+'</ul></main></html>\n'
    return {'index.html': page, 'comparison.svg': diagram()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, content in outputs().items():
        if args.check:
            if (ROOT / name).read_text() != content:
                raise SystemExit('Stale generated artifact: '+name)
        else:
            (ROOT / name).write_text(content)
    print('SMLIGHT review '+('verified' if args.check else 'rendered'))
