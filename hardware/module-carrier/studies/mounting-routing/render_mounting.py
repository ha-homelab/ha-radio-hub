#!/usr/bin/env python3
"""Compare the immutable ear layout with the current native carrier geometry."""
from pathlib import Path
import argparse
import hashlib
import html
import importlib.util
import math

HERE = Path(__file__).resolve().parent
CARRIER = HERE.parents[1]
spec = importlib.util.spec_from_file_location('independent_carrier_audit', CARRIER / 'audit_carrier.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def snapshot(path):
    parts = audit.read_board(path)
    outline = audit.board_outline(path)
    bounds = audit.board_bounds(path)
    area = abs(sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(outline, outline[1:]+outline[:1])))/2
    wiz = audit.transformed_rectangle(parts['U4'], [-1.34,-6.4,21.66,18.6], canonical=True)
    local_face = [(2.11,-9.1),(18.21,-9.1)]
    if parts['U4']['layer'] == 'B.Cu':
        local_face = [(x,-y) for x,y in local_face]
    face = audit.transform_points(parts['U4'], local_face)
    mouth = tuple(sum(p[i] for p in face)/2 for i in (0,1))
    tangent = (face[1][0]-face[0][0], face[1][1]-face[0][1])
    normal = (-tangent[1],tangent[0])
    norm = math.hypot(*normal)
    normal = tuple(x/norm for x in normal)
    center = tuple(sum(p[i] for p in wiz)/len(wiz) for i in (0,1))
    if sum((mouth[i]-center[i])*normal[i] for i in (0,1)) < 0:
        normal = tuple(-x for x in normal)
    supports = {r:tuple(p['at'][:2]) for r,p in parts.items() if r.startswith('H')}
    if not supports or 'H3' not in supports or 'H4' not in supports:
        raise ValueError('Expected native H3/H4 supports for this comparison')
    return dict(parts=parts, outline=outline, bounds=bounds, area=area, wiz=wiz,
                face=face, mouth=mouth, normal=normal, supports=supports,
                sha=hashlib.sha256(path.read_bytes()).hexdigest())


def render(board):
    previous = snapshot(HERE / 'ear-baseline/mc1.kicad_pcb')
    current = snapshot(board)
    out = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1060" viewBox="0 0 1400 1060" role="img" aria-label="Historical mounting ear and current rectangular carrier support geometry">
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7Z" fill="#f6c765"/></marker></defs>
<style>text{font-family:Arial,sans-serif;fill:#dce8f2}.title{font-size:28px;font-weight:bold}.panel{font-size:23px;font-weight:bold}.subtitle{font-size:16px;fill:#b5c9d9}.label{font-size:14px}.small{font-size:12px}.dim{font-size:15px;fill:#8ddacb}.warn{font-size:17px;fill:#f6c765}.strong{font-weight:bold}</style>
<rect width="1400" height="1060" fill="#0d1926"/>
<text x="36" y="44" class="title">Remove the mounting ear. Preserve a buildable assembly order.</text>
<text x="36" y="76" class="subtitle">Equal scale · front view · dashed bodies are front modules; blue WIZ is projected from the rear · dimensions in mm</text>
<path d="M700 110V792" stroke="#385064"/>
''']
    scale, oy = 5.8, 191
    for number, data in enumerate((previous, current)):
        panel_x = 34 + number*700
        ox = panel_x+40
        title = 'Historical: local mounting ear' if number == 0 else 'Current: no mounting ear'
        out.append(f'<text x="{panel_x}" y="118" class="panel">{title}</text>')
        def point(p): return (ox+p[0]*scale, oy+p[1]*scale)
        def text(x,y,value,css='label',anchor='start'):
            out.append(f'<text x="{x:.2f}" y="{y:.2f}" class="{css}" text-anchor="{anchor}">{html.escape(str(value))}</text>')
        def polygon(points,attrs):
            coords=' '.join(f'{point(p)[0]:.2f},{point(p)[1]:.2f}' for p in points)
            out.append(f'<polygon points="{coords}" {attrs}/>')
        def line(a,b,attrs):
            x1,y1=point(a);x2,y2=point(b)
            out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {attrs}/>')
        bounds=data['bounds']; width=bounds[2]-bounds[0];height=bounds[3]-bounds[1]
        text(panel_x,148,f'{width:g} × {height:g} bounding box · {data["area"]:g} mm² laminate','subtitle')
        polygon(data['outline'],'fill="#173b3b" stroke="#80d3be" stroke-width="2"')
        for ref,name in [('U1','Nano'),('U2','H2'),('U3','XIAO')]:
            poly=audit.courtyard_polygon(data['parts'][ref])
            polygon(poly,'fill="#294751" fill-opacity="0.7" stroke="#91abbc" stroke-dasharray="4 4"')
            center=tuple(sum(p[i] for p in poly)/len(poly) for i in (0,1))
            text(*point(center),f'{ref} {name}','label','middle')
        polygon(data['wiz'],'fill="#1d426c" fill-opacity="0.6" stroke="#73b5ff" stroke-width="2" stroke-dasharray="6 3"')
        center=tuple(sum(p[i] for p in data['wiz'])/len(data['wiz']) for i in (0,1))
        text(*point(center),'WIZ / rear','label','middle')
        line(*data['face'],'stroke="#73b5ff" stroke-width="5"')
        for ref, p in sorted(data['supports'].items()):
            x,y=point(p)
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{2.5*scale}" fill="#112532" stroke="#f6c765" stroke-width="1.7"/>')
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{1.35*scale}" fill="#0d1926" stroke="#f6c765"/>')
            # Keep labels outside the mounting body without obscuring the hole.
            text(x,y-18,ref,'small strong','middle')
        mouth=data['mouth']
        for ref in ('H3','H4'):
            line(data['supports'][ref],mouth,'stroke="#f6c765" stroke-opacity="0.7" stroke-dasharray="3 4"')
        if math.isclose(data['supports']['H3'][1],data['supports']['H4'][1],abs_tol=1e-4):
            line(data['supports']['H3'],data['supports']['H4'],'stroke="#8ddacb" stroke-dasharray="6 3"')
        arrow_tail=tuple(mouth[i]+data['normal'][i]*14 for i in (0,1))
        arrow_tip=tuple(mouth[i]+data['normal'][i]*1.5 for i in (0,1))
        line(arrow_tail,arrow_tip,'stroke="#f6c765" stroke-width="2" marker-end="url(#arrow)"')
        x,y=point(arrow_tail)
        text(x,y+22,'Example plug-in direction','small','middle')
        right_x=panel_x+410
        text(right_x,218,'Mounting coordinates','label strong')
        for i,(ref,p) in enumerate(sorted(data['supports'].items())):
            text(right_x,246+i*25,f'{ref}  ({p[0]:g}, {p[1]:g})')
        text(right_x,367,f'Mouth ({mouth[0]:g}, {mouth[1]:g})','label strong')
        for i,ref in enumerate(('H3','H4')):
            support=data['supports'][ref]
            distance=math.dist(mouth,support)
            setback=sum((mouth[j]-support[j])*data['normal'][j] for j in (0,1))
            text(right_x,404+i*68,f'{ref}: distance {distance:.2f}','dim')
            text(right_x,429+i*68,f'axial setback {setback:.2f}','small')
        if number == 0:
            text(right_x,567,'Both lower supports','subtitle')
            text(right_x,592,'lie on one 5 mm row.','subtitle')
        else:
            text(right_x,567,'H3 occupies the gap','subtitle')
            text(right_x,592,'between H2 and XIAO.','subtitle')
            text(right_x,632,'The support geometry','warn')
            text(right_x,657,'is now staggered.','warn')
        text(panel_x,753,f'Native PCB SHA-256 {data["sha"][:20]}…','small')
        text(panel_x,778,'Historical geometry, not current assembly.' if number == 0 else 'All 13 rear parts first → then 3 front modules.','subtitle')
    old_bbox=(previous['bounds'][2]-previous['bounds'][0])*(previous['bounds'][3]-previous['bounds'][1])
    new_bbox=(current['bounds'][2]-current['bounds'][0])*(current['bounds'][3]-current['bounds'][1])
    bbox_change=100*(new_bbox/old_bbox-1)
    area_change=100*(current['area']/previous['area']-1)
    out += [f'<text x="36" y="826" class="dim">Bounding rectangle {bbox_change:+.2f}% · actual laminate {area_change:+.2f}% · same two copper layers</text>',
'''<text x="36" y="861" class="warn">A smaller outline does not establish equal stiffness or a connector load rating.</text>
<text x="36" y="897" class="subtitle">Dashed mouth-to-support lines are distances, not measured load paths. The former symmetric support row is gone.</text>
<text x="36" y="927" class="subtitle">Use all four supports. An enclosure cradle / stop and cable strain relief must separately protect the WIZ header joints.</text>
<text x="36" y="957" class="subtitle">Ø2.7 mounting holes · Ø5 maximum nylon support/head · actual vertical clearance and enclosure fit still require measurement.</text>
<text x="36" y="994" class="small">Earlier 51 × 75 mm three-support layout remains in baseline/. Ear-layout source is preserved in ear-baseline/.</text>
<text x="36" y="1022" class="small">These are reproducible plan-view drawings from native CAD, not photographs or hardware test results.</text>
</svg>''']
    return '\n'.join(out)+'\n'


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,default=CARRIER/'cad/mc1.kicad_pcb')
    parser.add_argument('--output',type=Path,default=HERE/'mounting.svg')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    generated=render(args.board)
    if args.check:
        if not args.output.exists() or args.output.read_text()!=generated:
            raise SystemExit('Mounting comparison is stale; run render_mounting.py')
        print('Mounting comparison matches native sources.')
    else:
        args.output.write_text(generated)
