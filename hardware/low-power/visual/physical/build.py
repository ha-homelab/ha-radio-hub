#!/usr/bin/env python3
"""Draw checked contact geometry, without requiring KiCad or network access."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def sexpr(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack = [[]]
    for token in tokens:
        if token == '(':
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            if len(stack) == 1:
                raise ValueError('Unbalanced footprint')
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError('Invalid footprint')
    return stack[0][0]


def child(node, key):
    return next((x for x in node if isinstance(x, list) and x[0] == key), None)


def point(x, y):
    return [round(x, 6), round(y, 6)]


def pad(name, x, y, w, h, shape='rect', **extra):
    return dict(id=str(name), center_mm=point(x, y), size_mm=point(w, h), shape=shape, **extra)


def geometry(m):
    if m['kind'] == 'kicad':
        result = []
        ox, oy = m['offset']
        for n in sexpr((ROOT / m['source_file']).read_text()):
            if not isinstance(n, list) or n[0] != 'pad':
                continue
            layers = child(n, 'layers')[1:]
            if not ('F.Cu' in layers or '*.Cu' in layers):
                continue  # Stencil-only apertures are not electrical contacts.
            at = child(n, 'at')[1:]
            x, y = map(float, at[:2])
            angle = float(at[2]) if len(at) > 2 else 0
            w, h = map(float, child(n, 'size')[1:])
            p = pad(n[1], x + ox, y + oy, w, h, n[3], rotation_deg=-angle)
            drill = child(n, 'drill')
            if drill:
                p['drill_mm'] = float(drill[1])
            if n[3] == 'custom':
                primitives = child(n, 'primitives')
                poly = child(primitives, 'gr_poly') if primitives else None
                if not poly:
                    raise ValueError('Unsupported custom pad')
                p['polygon_local_mm'] = [list(map(float, v[1:])) for v in child(poly, 'pts')[1:]]
            result.append(p)
        return result
    if m['id'] == 'mg24':
        p = [pad(n, .8, .7+n-1, 2.4, .6, 'oval') for n in range(1,15)]
        p += [pad(n, 2.95+n-15, 14.2, .6, 2.4, 'oval') for n in range(15,23)]
        p += [pad(n, 12.1, 13.7-(n-23), 2.4, .6, 'oval') for n in range(23,37)]
        return p
    if m['id'] == 'wiz850io':
        names = [['GND','GND','MOSI','SCLK','SCNn','INTn'], ['GND','3V3D','3V3D','NC','RSTn','MISO']]
        return [pad(f'J{j+1}.{i+1}', 1.34+j*20.32, 6.4+i*2.54, 0, 0, 'contact_center', signal=s)
                for j,row in enumerate(names) for i,s in enumerate(row)]
    if m['id'] == 'pololu':
        p = [pad(s, 1.27+i*2.54, 16.53, 1.02, 1.02, 'module_hole', signal=s)
             for i,s in enumerate(['PG','EN','VIN','GND','VOUT'])]
        p += [pad('GND2',1.27,5.84,1.02,1.02,'module_hole',signal='GND')]
        p += [pad('MH1',2.3,2.3,2.18,2.18,'mount_hole'),pad('MH2',15.5,15.5,2.18,2.18,'mount_hole')]
        return p
    raise ValueError(m['id'])


def svg(m, pads):
    w, h = m['body']
    scale = min(27, 610 / max(w, h))
    x0, y0 = (1000-w*scale)/2, 240 if m['id']=='wiz850io' else 175
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1080" viewBox="0 0 1000 1080">',
           '<rect width="1000" height="1080" fill="#f8fafc"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#17263c}.title{font-size:29px;font-weight:bold}.label{font-size:14px}.note{font-size:16px}</style>']
    def text(x,y,t,cls='note',anchor='start',extra=''):
        out.append(f'<text x="{x:.3f}" y="{y:.3f}" class="{cls}" text-anchor="{anchor}" {extra}>{html.escape(str(t))}</text>')
    text(40,48,m['title'],'title')
    text(40,80,'PCB footprint top view; module view requires datasheet')
    text(40,108,'CONTACT REFERENCE ONLY - not a Gerber, drill template or fabrication release')
    text(500,145,f'Nominal body {w:g} x {h:g} mm | x right, y down','note','middle')
    out.append(f'<rect x="{x0}" y="{y0}" width="{w*scale}" height="{h*scale}" fill="#e6edf3" stroke="#496179" stroke-width="2"/>')
    if 'antenna' in m:
        ax,ay,aw,ah=m['antenna']
        out.append(f'<rect x="{x0+ax*scale}" y="{y0+ay*scale}" width="{aw*scale}" height="{ah*scale}" fill="#fef3c7" stroke="#a97b19" stroke-dasharray="6 4"/>')
        text(x0+(ax+aw/2)*scale,y0+(ay+ah/2)*scale,'ANTENNA REGION','label','middle')
    if m['id']=='wiz850io':
        text(500,y0-13,'RJ45 MOUTH / 2.7 mm beyond PCB','label','middle')
        out.append(f'<rect x="{x0+(w-16.1)/2*scale}" y="{y0-2.7*scale}" width="{16.1*scale}" height="{2.7*scale}" fill="none" stroke="#496179" stroke-dasharray="5 4"/>')
    counts={p['id']:sum(q['id']==p['id'] for q in pads) for p in pads}
    for p in sorted(pads, key=lambda p: p['shape']=='circle'):
        cx,cy=p['center_mm'];pw,ph=p['size_mm'];px=x0+cx*scale;py=y0+cy*scale
        shape=p['shape'];fill='#b56f16' if p['id'] not in ('1','J1.1','J2.1','PG') else '#d9483b'
        out.append(f'<g data-pad="{html.escape(p["id"])}"><title>{html.escape(p["id"]+" "+p.get("signal", "")+" "+str(p["center_mm"]))}</title>')
        if shape in ('contact_center','module_hole','mount_hole','circle'):
            radius=(pw*scale/2 if pw else 5)
            out.append(f'<circle cx="{px}" cy="{py}" r="{radius}" fill="{fill if shape=="circle" else "#ffffff"}" stroke="{fill}" stroke-width="2"/>')
            if shape=='contact_center':
                out.append(f'<path d="M {px-8} {py} h 16 M {px} {py-8} v 16" stroke="{fill}"/>')
        elif shape=='custom':
            pts=' '.join(f'{a*scale},{b*scale}' for a,b in p['polygon_local_mm'])
            out.append(f'<polygon points="{pts}" transform="translate({px},{py}) rotate({p.get("rotation_deg",0)})" fill="{fill}"/>')
        else:
            r=min(pw,ph)*scale/2 if shape=='oval' else 0
            out.append(f'<rect x="{-pw*scale/2}" y="{-ph*scale/2}" width="{pw*scale}" height="{ph*scale}" rx="{r}" transform="translate({px},{py}) rotate({p.get("rotation_deg",0)})" fill="{fill}"/>')
        if p.get('drill_mm'):
            out.append(f'<circle cx="{px}" cy="{py}" r="{p["drill_mm"]*scale/2}" fill="white"/>')
        out.append('</g>')
        if counts[p['id']]>1:
            continue
        label=p['id']+(' '+p['signal'] if m['id']=='wiz850io' else '')
        if m['id']=='pololu' and p['id'] not in ('GND2','MH1','MH2'):
            text(px,py+30,label,'label','start',f'transform="rotate(45 {px} {py+30})"')
        elif m['id']=='wiz850io':
            text(px+(-23 if cx<w/2 else 23),py+5,label,'label','end' if cx<w/2 else 'start')
        elif cx<1.5:
            text(px-45,py+5,label,'label','end')
        elif cx>w-1.5:
            text(px+45,py+5,label,'label')
        elif cy>h-2:
            text(px,py+48,label,'label','middle')
        elif m['id']=='h2' and cy<7:
            text(px,py-23,label,'label','middle')
        else:
            text(px+18,py+5,label,'label')
    if m['id'] in ('s3','h2'):
        ep='41' if m['id']=='s3' else '49'
        text(500,y0+h*scale*.63,ep+'  exposed ground','label','middle')
    text(40,883,m['check'])
    for i,note in enumerate(m['notes']):text(40,915+i*25,note)
    text(40,991,'Body/antenna outline is a reference, not a complete RF keep-out or case clearance.')
    text(40,1016,'Sources and source-derived coordinates: catalog.json, generated/contacts.json.')
    text(40,1041,'Red = first contact/orientation reference. Numbers identify pads, not ESP GPIOs.')
    out.append('</svg>')
    return '\n'.join(out)+'\n'


def products():
    c=json.loads((ROOT/'catalog.json').read_text())
    drawings={};contact_modules=[]
    for m in c['modules']:
        pads=geometry(m)
        for p in pads:
            if not all(math.isfinite(v) for v in p['center_mm']+p['size_mm']):raise ValueError('Nonfinite coordinate')
        ids={p['id'] for p in pads}
        expected={'s3':{str(i) for i in range(1,42)},'h2':{str(i) for i in range(1,54)},'mg24':{str(i) for i in range(1,37)}}
        if m['id'] in expected and ids!=expected[m['id']]:raise ValueError(f'Contact coverage: {m["id"]}: {ids}')
        drawing=svg(m,pads);ET.fromstring(drawing)
        drawings[m['id']+'-contacts.svg']=drawing
        contact_modules.append({'id':m['id'],'view':c['view'],'body_mm':m['body'],'pads':pads})
    drawings['contacts.json']=json.dumps({'units':'mm','coordinates':c['coordinates'],'modules':contact_modules},indent=2)+'\n'
    sources = [ROOT/'build.py', ROOT/'catalog.json', *sorted((ROOT/'source').glob('*'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    drawings['manifest.json']=json.dumps({'source_sha256':hashes,'generated_sha256':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in drawings.items()}},indent=2)+'\n'
    return drawings


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    out=ROOT/'generated';out.mkdir(exist_ok=True)
    generated=products()
    for name,data in generated.items():
        path=out/name
        if args.check:
            if not path.is_file() or path.read_text()!=data:raise SystemExit('STALE: '+str(path))
        else:path.write_text(data)
    actual={p.name for p in out.iterdir() if p.is_file()}
    if actual!=set(generated):raise SystemExit('Unexpected generated inventory: '+str(actual-set(generated)))
    print('PASS: five contact drawings, contact coverage, source hashes, XML and generated freshness')


if __name__=='__main__':main()
