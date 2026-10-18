#!/usr/bin/env python3
"""Reproduce the support comparison from native front-view CAD coordinates."""
from pathlib import Path
import argparse
import hashlib
import html
import importlib.util

HERE = Path(__file__).resolve().parent
CARRIER = HERE.parents[1]
spec = importlib.util.spec_from_file_location('independent_carrier_audit', CARRIER / 'audit_carrier.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def render(board):
    baseline = HERE / 'baseline/mc1.kicad_pcb'
    sources = [('Previous: 51 × 75 mm', baseline, 72), ('Revised carrier', board, 666)]
    out = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="930" viewBox="0 0 1240 930">
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7Z" fill="#f6c765"/></marker></defs>
<style>text{font-family:Arial,sans-serif;fill:#dce8f2}.title{font-size:27px;font-weight:bold}.subtitle{font-size:15px;fill:#a9c0d3}.label{font-size:13px}.small{font-size:11px}.dim{font-size:12px;fill:#8ddacb}.warn{font-size:15px;fill:#f6c765}</style>
<rect width="1240" height="930" fill="#0d1926"/>
<text x="42" y="44" class="title">RJ45 support: carrier stiffness and connector restraint are separate</text>
<text x="42" y="72" class="subtitle">True front view · rear WIZ shown as a projected outline · all dimensions in mm · prototype geometry</text>''']
    scale, oy = 6.1, 184
    for title, path, ox in sources:
        parts = audit.read_board(path)
        outline = audit.board_outline(path)
        bounds = audit.board_bounds(path)
        if path == board:
            title = f'Revised: {bounds[2]-bounds[0]:g} × {bounds[3]-bounds[1]:g} bounding box'
        out.append(f'<text x="{ox-12}" y="112" class="title">{html.escape(title)}</text>')
        def point(x,y): return (ox+x*scale, oy+y*scale)
        def polygon(points, attrs):
            coords=' '.join(f'{point(x,y)[0]:.2f},{point(x,y)[1]:.2f}' for x,y in points)
            out.append(f'<polygon points="{coords}" {attrs}/>')
        def line(a,b,attrs):
            x1,y1=point(*a); x2,y2=point(*b)
            out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {attrs}/>')
        polygon(outline, 'fill="#173b3b" stroke="#80d3be" stroke-width="2"')
        for ref in ('U1','U2','U3'):
            poly=audit.courtyard_polygon(parts[ref])
            polygon(poly, 'fill="#294751" fill-opacity="0.7" stroke="#91abbc" stroke-dasharray="4 4"')
            cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
            x,y=point(cx,cy)
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="label">{ref} front</text>')
        wiz=audit.transformed_rectangle(parts['U4'],[-1.34,-6.4,21.66,18.6],canonical=True)
        polygon(wiz, 'fill="#1d426c" fill-opacity="0.6" stroke="#73b5ff" stroke-width="2" stroke-dasharray="6 3"')
        face=audit.transform_points(parts['U4'],[(2.11,9.1),(18.21,9.1)])
        line(face[0],face[1],'stroke="#73b5ff" stroke-width="5"')
        cx=sum(p[0] for p in face)/2;fy=sum(p[1] for p in face)/2
        x,y=point(cx,60)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="label">WIZ / rear</text>')
        supports={r:p['at'][:2] for r,p in parts.items() if r not in audit.PIN_SETS}
        for ref,(sx,sy) in sorted(supports.items()):
            x,y=point(sx,sy)
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2.5*scale}" fill="#112532" stroke="#f6c765" stroke-width="1.5"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{1.35*scale}" fill="#0d1926" stroke="#f6c765"/>')
            anchor='end' if ref=='H4' else 'start'
            tx=x-19 if anchor=='end' else x+19
            out.append(f'<text x="{tx:.1f}" y="{y-6:.1f}" text-anchor="{anchor}" class="small">{ref} ({sx:g}, {sy:g})</text>')
        if 'H4' in supports:
            line(supports['H3'],supports['H4'],'stroke="#f6c765" stroke-dasharray="5 4"')
            x,y=point(38,69)
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="small">lower support row</text>')
            line((57.8,72),(57.8,77),'stroke="#8ddacb"')
            for dy in (72,77): line((56.8,dy),(58.8,dy),'stroke="#8ddacb"')
            x,y=point(59,75)
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" class="dim">5</text>')
            x,y=point(60,51)
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" class="dim">6 × 27 ear</text>')
        line((cx,91),(cx,fy+1),'stroke="#f6c765" stroke-width="2" marker-end="url(#arrow)"')
        x,y=point(cx+2,86)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" class="warn">insertion force</text>')
        line((0,-7),(bounds[2],-7),'stroke="#8ddacb"')
        for dx in (0,bounds[2]):line((dx,-8),(dx,-6),'stroke="#8ddacb"')
        x,y=point(bounds[2]/2,-9)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="dim">{bounds[2]:g}</text>')
        line((-4,0),(-4,75),'stroke="#8ddacb"')
        for dy in (0,75): line((-5,dy),(-3,dy),'stroke="#8ddacb"')
        x,y=point(-6,39)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="end" class="dim">75</text>')
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        out.append(f'<text x="{ox-12}" y="778" class="small">Native PCB SHA-256 {sha[:16]}…</text>')
    out.extend(['''<text x="42" y="817" class="warn">Four carrier supports do not bypass the WIZ header solder joints.</text>
<text x="42" y="845" class="subtitle">For repeated plugging: fit an insulating enclosure cradle / stop against a robust jack or module body surface.</text>
<text x="42" y="870" class="subtitle">Add cable strain relief. Cradle contact faces, height and tolerances require actual-module measurements.</text>
<text x="42" y="898" class="subtitle">Ø2.7 mounting holes · Ø5 maximum nylon support/head · no calculated stiffness or load rating claimed.</text>
</svg>'''])
    return '\n'.join(out)+'\n'

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,default=CARRIER/'cad/mc1.kicad_pcb')
    args=parser.parse_args()
    (HERE/'mounting.svg').write_text(render(args.board))
