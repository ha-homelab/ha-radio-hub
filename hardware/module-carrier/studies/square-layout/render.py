#!/usr/bin/env python3
"""Render the square packing study from the two actual placement ledgers."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parent
BASE = R.parents[1] / 'cad/design.json'
CANDIDATE = R / 'cad-candidate/design.json'
BODY = {
    'U1': [-1.27, -1.4, 24.13, 61.34],
    'U2': [-1.27, -1.575, 24.13, 46.685],
    'U3': [-1.27, -2.921, 16.51, 18.034],
    'U4': [-1.34, -6.4, 21.66, 18.6],
}
NAMES = {'U1': 'S3', 'U2': 'H2', 'U3': 'MG24', 'U4': 'Ethernet'}
esc = html.escape

def point(p, x, y):
    a = math.radians(p['rotation'])
    return p['xy'][0] + x*math.cos(a) + y*math.sin(a), p['xy'][1] - x*math.sin(a) + y*math.cos(a)

def bounds(p, b):
    q = [point(p, b[i], b[j]) for i in (0, 2) for j in (1, 3)]
    return [min(x for x, y in q), min(y for x, y in q), max(x for x, y in q), max(y for x, y in q)]

def board(d, x, y, scale, title):
    out = []
    w, h = d['board']['width_mm'], d['board']['height_mm']
    def txt(px, py, text, size=13, fill='#e4edf5', anchor='start'):
        out.append(f'<text x="{px:.2f}" y="{py:.2f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>')
    def box(b, fill, stroke, extra=''):
        out.append(f'<rect x="{x+b[0]*scale:.2f}" y="{y+b[1]*scale:.2f}" width="{(b[2]-b[0])*scale:.2f}" height="{(b[3]-b[1])*scale:.2f}" fill="{fill}" stroke="{stroke}" {extra}/>')
    txt(x, y-38, title, 24)
    txt(x, y-15, f'{w} × {h} mm · top view', 15, '#a9bfd0')
    box([0, 0, w, h], '#163f46', '#81a7b0')
    for b in d['mechanics']['rf_copper_keepouts_mm']:
        box(b, '#805936', '#f4bc7a', 'fill-opacity=".55" class="rf"')
    for ref, b in d['mechanics']['usb_service_envelopes_mm'].items():
        b = [max(-4,b[0]), max(-4,b[1]), min(w+4,b[2]), min(h+6,b[3])]
        box(b, '#184d67', '#70bbe5', 'fill-opacity=".4" stroke-dasharray="4 3" class="service"')
        txt(x+scale*(b[0]+b[2])/2, y+scale*(b[1]+b[3])/2, ref+' USB', 11, '#97d6fa', 'middle')
    for ref, b in d['mechanics']['header_mating_envelopes_mm'].items():
        box(b, '#50655b', '#a5c4b7', 'fill-opacity=".3" stroke-dasharray="3 2"')
    for p in d['parts']:
        ref = p['ref']
        if ref in BODY:
            b = bounds(p, BODY[ref])
            box(b, '#d2e6da' if ref != 'U4' else '#b7d8ed', '#f1f7f9')
            if ref == 'U4':
                box(bounds(p, [2.11, -9.1, 18.21, 16]), '#bfc8d1', '#edf3f6')
            if ref == 'U2':
                box(bounds(p, [4.83, -6.975, 18.03, -1.575]), '#c0a36c', '#efcf94')
            if ref == 'U3':
                box(bounds(p, [8.7, 16.034, 13.9, 18.034]), '#c0a36c', '#efcf94')
            txt(x+scale*(b[0]+b[2])/2, y+scale*(b[1]+b[3])/2, NAMES[ref], 14, '#18363f', 'middle')
        elif ref.startswith('J'):
            pads = p['pad_centers_mm']
            b = [min(t['x'] for t in pads)-1.27, min(t['y'] for t in pads)-1.27,
                 max(t['x'] for t in pads)+1.27, max(t['y'] for t in pads)+1.27]
            box(b, '#1a2738', '#93b8c5')
            txt(x+scale*(b[0]+b[2])/2, y+scale*b[1]-4, ref, 11, '#f4f7fa', 'middle')
        else:
            a, b = p['pad_centers_mm']
            ax, ay, bx, by = x+scale*a['x'], y+scale*a['y'], x+scale*b['x'], y+scale*b['y']
            out.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="#cab37c" stroke-width="5"/>')
            txt((ax+bx)/2, (ay+by)/2-6, ref, 10, '#f4ddb1', 'middle')
        for p1 in p['pad_centers_mm']:
            out.append(f'<circle cx="{x+scale*p1["x"]:.2f}" cy="{y+scale*p1["y"]:.2f}" r="2.0" fill="#d6b56a" stroke="#203637" stroke-width=".7"/>')
    for mx, my in d['mechanics']['mounting_holes_mm']:
        out.append(f'<circle cx="{x+scale*mx}" cy="{y+scale*my}" r="{1.35*scale}" fill="#0c1828" stroke="#c2d4dc"/>')
    r = d['mechanics']['rj45']
    a, b = r['face_global_mm']
    cx, cy = (a[0]+b[0])/2, (a[1]+b[1])/2
    nx, ny = r['outward_normal_global']
    out.append(f'<path d="M{x+scale*(cx+nx*2)} {y+scale*(cy+ny*2)} l{nx*40} {ny*40}" stroke="#73e2c5" stroke-width="3" marker-end="url(#arrow)"/>')
    txt(x+10, y+scale*h+35, f'Width {w} mm', 14, '#b9ccd9')
    txt(x-8, y+scale*h/2, f'{h}', 13, '#b9ccd9', 'end')
    return ''.join(out)

def outputs():
    base, candidate = json.loads(BASE.read_text()), json.loads(CANDIDATE.read_text())
    result = json.loads((R/'result.json').read_text())
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="830" viewBox="0 0 1240 830"><style>text{font-family:Arial,sans-serif}</style><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#73e2c5"/></marker></defs><rect width="1240" height="830" fill="#0c1828"/>'
    svg += '<text x="50" y="43" font-size="30" fill="#edf6fa" font-family="Arial">MC1 · square layout study</text><text x="50" y="73" font-size="16" fill="#adc4d5" font-family="Arial">Same scale · 17 parts · 145 pad assignments · all USB sockets retained</text>'
    svg += board(base, 55, 162, 4.7, 'Current routed carrier')
    svg += board(candidate, 700, 162, 4.7, '100 × 100 mm candidate')
    svg += '<g font-family="Arial" fill="#b9d0df" font-size="17"><text x="50" y="710">Blue dashed: USB plug access. Orange: copper exclusions, not RF certification.</text><text x="50" y="740">The square candidate moves MG24 left and puts Ethernet below H2, with RJ45 exiting downward.</text><text x="50" y="770">+11.1% PCB area versus 100 × 90 mm; both fit the ≤100 × 100 mm prototype size class.</text><text x="50" y="800">Carrier dimensions exclude projecting connectors, service cables and external finished modules.</text></g></svg>'
    rows = ''.join(f'<tr><th>{esc(p["ref"])}</th><td>{esc(p["model"])}</td><td>{p["xy"][0]:g}, {p["xy"][1]:g}</td><td>{p["rotation"]}°</td></tr>' for p in candidate['parts'])
    points = ''.join(f'<li>{esc(t)}</li>' for t in result['findings'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC1 · 100 × 100 mm study</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#0c1828;color:#e4edf5;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1240px;margin:auto;padding:28px}}h1{{font-size:32px;line-height:1.15}}h2{{font-size:23px;margin-top:40px}}a{{color:#7fdbc6}}.muted{{color:#adc4d5}}.lead{{font-size:21px;max-width:850px}}img{{width:100%;height:auto}}.band{{border-left:3px solid #73e2c5;padding:10px 18px;margin:22px 0;background:#122c37}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:25px}}.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{text-align:left;padding:9px;border-bottom:1px solid #29404e}}li{{margin:10px 0}}code{{overflow-wrap:anywhere}}@media(max-width:500px){{main{{padding:18px}}h1{{font-size:28px}}}}</style>
<main><a href="../../index.html#pcb">← Current 100 × 90 mm MC1</a> · <a href="../compact-s3/index.html">Compact S3 review →</a><p class="muted">Engineering study · 17 October 2026 · same electrical interfaces</p><h1>MG24 left. Ethernet below H2.<br>A square carrier without USB removal.</h1><p class="lead">{esc(result['conclusion'])}</p><div class="band">{esc(result['status'])}</div>
<figure style="margin:30px 0"><a href="comparison.svg"><img src="comparison.svg" alt="Same-scale placement comparison of the current 100 by 90 millimetre carrier and square candidate"></a><figcaption class="muted">Open the drawing for readable full-size detail. Module bodies and pad positions come from the CAD ledgers.</figcaption></figure>
<div class="grid"><section><h2>What improves</h2><ul>{''.join('<li>'+esc(t)+'</li>' for t in result['benefits'])}</ul></section><section><h2>What still needs proof</h2><ul>{''.join('<li>'+esc(t)+'</li>' for t in result['limits'])}</ul></section></div>
<h2>Measured findings</h2><ul>{points}</ul><h2>Why keep the USB ports?</h2><p>Removing a socket does not shrink the module PCB or remove its antenna requirements. This arrangement keeps the ports and their access space. XIAO uses its onboard USB programming probe; removing that interface would add recovery work.</p><p><a href="usb-rf-review.md">USB and antenna review</a> · <a href="service-review.md">Programming and service review</a></p>
<h2>Ceiling mounting</h2><p>Assuming the populated side faces the room, the open space helps propagation. It does not remove the influence of nearby carrier copper on the antenna itself. Keep copper, vias and permanent wiring out of the antenna-specific clearance region; retain the intended ground plane under the other circuitry. Spacers from the ceiling do not change the antenna-to-carrier separation.</p><p>The interior H2 antenna is still a compromise. Espressif recommends an edge-facing antenna and explicitly discourages a central placement with a four-sided internal cutout. A small hole alone is not a proven fix. <a href="usb-rf-review.md#ceiling-mounting-and-copper-beneath-the-antenna">Ceiling and near-field explanation</a> · <a href="https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board">Manufacturer placement guidance</a>.</p><h2>Fabrication cost</h2><p>10,000 versus 9,000 mm² is an 11.1% area increase. Both outlines satisfy the size criterion for advertised ≤100 × 100 mm two-layer prototype offers from <a href="https://jlcpcb.com/help/article/how-do-i-place-an-order">JLCPCB</a> and <a href="https://m.pcbway.com/activitypcb.aspx">PCBWay</a>. This is not a quotation or a guarantee of equal delivered cost.</p>
<h2>Candidate placements</h2><p class="muted">Top-view coordinates in millimetres. Origin: upper-left carrier corner. Rotation follows the native KiCad footprint convention.</p><div class="scroll"><table><thead><tr><th>Ref</th><th>Module / part</th><th>X, Y (mm)</th><th>Rotation</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Evidence</h2><p><a href="result.json">Study results</a> · <a href="cad-candidate/design.json">Candidate pad ledger</a> · <a href="README.md">Study notes</a></p><p><a href="cad-candidate/assembly-top.svg">Full-size assembly drawing</a> · <a href="cad-candidate/mc1.kicad_pcb">Native candidate PCB</a> · <a href="cad-candidate/README.md">CAD reproduction and limitations</a></p><p class="muted">{esc(result['validation'])}</p></main></html>'''
    return {'comparison.svg': svg+'\n', 'index.html': page+'\n'}

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--check', action='store_true'); args = p.parse_args()
    for name, content in outputs().items():
        if args.check:
            assert (R/name).read_text() == content, f'Stale {name}'
        else:
            (R/name).write_text(content)
    print('Square study outputs '+('verified' if args.check else 'rendered'))
