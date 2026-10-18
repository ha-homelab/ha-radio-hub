#!/usr/bin/env python3
"""Scaled engineering assembly view from the native pad/placement ledger."""
import json, html, math
from pathlib import Path
R=Path(__file__).resolve().parent; d=json.loads((R/'design.json').read_text()); esc=html.escape
S=6.5; OX=100; OY=300; W=d['board']['width_mm']; H=d['board']['height_mm']; CW=1120; CH=1510
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">',f'<rect width="{CW}" height="{CH}" fill="#0b1424"/>','<style>text{font-family:Inter,Arial,sans-serif;fill:#e9f0fa}</style>','<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6ee7c8"/></marker></defs>']
def text(x,y,t,size=16,fill='#e9f0fa',anchor='start'):
 svg.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" style="fill:{fill}">{esc(t)}</text>')
def rect(x,y,w,h,fill,stroke='#bedde7',dash=False):
 svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}"'+(' stroke-dasharray="6 4"' if dash else '')+'/>')
def xy(x,y):return OX+S*x,OY+S*y
def box(b,fill,stroke,dash=False):rect(*xy(b[0],b[1]),(b[2]-b[0])*S,(b[3]-b[1])*S,fill,stroke,dash)
def trans(p,x,y):
 th=math.radians(p['rotation']);return p['xy'][0]+x*math.cos(th)+y*math.sin(th),p['xy'][1]-x*math.sin(th)+y*math.cos(th)
def bounds(p,b):
 co=[trans(p,*b[:2]),trans(p,*b[2:])];return [min(v[0] for v in co),min(v[1] for v in co),max(v[0] for v in co),max(v[1] for v in co)]
text(60,52,'MC1 · 100 × 100 mm geometry study',34)
text(60,89,f'{W} × {H} mm · two layers · all components on top · factory male headers soldered directly',19,'#a7b9cc')
text(60,121,'STUDY CANDIDATE · stock USB connectors retained · active 100 × 90 mm carrier unchanged',14,'#6adcc0')
box([0,0,W,H],'#154a4d','#7baeb2')
for b in d['mechanics']['rf_copper_keepouts_mm']:box(b,'#75503e','#eda86f')
for ref,b in d['mechanics']['usb_service_envelopes_mm'].items():
 box(b,'#113846','#55a4cb',True);text(*xy((b[0]+b[2])/2,b[1]+4),ref+' USB access',11,'#92c9e9','middle')
for ref,b in d['mechanics']['header_mating_envelopes_mm'].items():box(b,'#345258','#94afb2',True)
for i,(x,y) in enumerate(d['mechanics']['mounting_holes_mm'],1):
 xx,yy=xy(x,y);svg.append(f'<circle cx="{xx}" cy="{yy}" r="{2.5*S}" fill="none" stroke="#b8d4dc" stroke-dasharray="3 3"/><circle cx="{xx}" cy="{yy}" r="{1.35*S}" fill="#0b1424" stroke="#e6eef5"/>');text(xx,yy+32,'H'+str(i),11,'#c2d5e1','middle')
body={'U1':[-1.27,-1.4,24.13,61.34],'U2':[-1.27,-1.575,24.13,46.685],'U3':[-1.27,-2.921,16.51,18.034],'U4':[-1.34,-6.4,21.66,18.6]}
labels={'U1':['U1 · ESP32-S3','N8R8','Host / BLE / LAN'],'U2':['U2 · ESP32-H2','Thread RCP','Interior antenna'],'U3':['U3 · XIAO','MG24','Zigbee'],'U4':['U4 · WIZ850io','RJ45 below']}
for p in d['parts']:
 ref=p['ref'];pads=p['pad_centers_mm']
 if ref in body:
  b=bounds(p,body[ref]);box(b,'#d9e8dc' if ref!='U4' else '#b2d7ee','#f6fbfb')
  if ref=='U4':
   box(bounds(p,[2.11,-9.1,18.21,16]),'#c3cbd1','#f5f9fb')
   fa,fb=[xy(*v) for v in d['mechanics']['rj45']['face_global_mm']];svg.append(f'<line x1="{fa[0]}" y1="{fa[1]}" x2="{fb[0]}" y2="{fb[1]}" stroke="#101820" stroke-width="6"/>')
  cx,cy=xy((b[0]+b[2])/2,(b[1]+b[3])/2)
  for i,t in enumerate(labels[ref]):text(cx,cy+17*(i-(len(labels[ref])-1)/2),t,13 if ref!='U3' else 11,'#173c4d','middle')
  if ref=='U2':box(bounds(p,[4.83,-6.975,18.03,-1.575]),'#8d7650','#e2bf76')
 elif ref.startswith('J'):
  b=[min(v['x'] for v in pads)-1.27,min(v['y'] for v in pads)-1.27,max(v['x'] for v in pads)+1.27,max(v['y'] for v in pads)+1.27];box(b,'#273748','#7da2b1');text(*xy((b[0]+b[2])/2,b[1]-.6),ref,11,'#fff','middle')
 else:
  x1,y1=xy(pads[0]['x'],pads[0]['y']);x2,y2=xy(pads[1]['x'],pads[1]['y']);svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c8cbd1" stroke-width="3"/>');rect((x1+x2)/2-7,(y1+y2)/2-20,14,40,'#6d4750' if ref[0]=='D' else '#c9a771','#e7ddd0');text(x1,y1-13,ref,11,'#e9f5ff','middle')
 for pad in pads:
  x,y=xy(pad['x'],pad['y']);n=pad['number'];svg.append(f'<circle cx="{x}" cy="{y}" r="5.2" fill="#d8ac53" stroke="#eccb83"/><circle cx="{x}" cy="{y}" r="2.5" fill="#102530"/>')
  if ref in ['U1','U2']:
   left=pad['x']<p['xy'][0]+(0 if p['rotation']==180 else 1); direction=1 if left else -1
   text(x+direction*9,y+3,n,8,'#173c4d','start' if direction==1 else 'end')
  elif ref=='U4':text(x,y+(-9 if n.startswith('J2') else 14),n.split('.')[-1],9,'#173c4d','middle')
  elif ref=='U3':text(x,y+(-8 if pad['y']<65 else 13),n,8,'#173c4d','middle')
  elif ref.startswith('J'):text(x+12,y+3,n,8,'#e4f0f0')
r=d['mechanics']['rj45'];box(r['service_corridor_global_mm'],'none','#6ee7c8',True)
fx=sum(v[0] for v in r['face_global_mm'])/2;ax,ay=xy(fx,103);ex,ey=xy(fx,134)
svg.append(f'<line x1="{ax}" y1="{ay}" x2="{ex}" y2="{ey}" stroke="#6ee7c8" stroke-width="4" marker-end="url(#arrow)"/>')
text(*xy(72,114),'RJ45 CABLE OUT',15,'#6ee7c8');text(*xy(72,119),'Mouth: 2 mm past edge',13,'#c8e9df');text(*xy(72,124),'Keep boot + latch clear',12,'#c8e9df')
text(*xy(2,83),'All five axial parts on top',11,'#a7b9cc')
text(*xy(73,72),'Stock S3 USB',12,'#92c9e9');text(*xy(38,-12),'Stock H2 USB',12,'#92c9e9')
text(*xy(4,80),'XIAO USB kept intact',11,'#92c9e9')
svg.append(f'<path d="M{OX} {OY+S*H+25}v10m0 -5h{S*W}m0 -5v10" stroke="#a5bfd0" fill="none"/>');text(OX+S*15,OY+S*H+52,f'{W} mm',18,'#bcd0de','middle');text(OX-40,OY+S*H/2,f'{H} mm',15,'#bcd0de','middle')
text(60,1260,'Same 17 parts · same 145 pads · 11.1% more area than active 100 × 90 mm',22)
text(60,1294,'Blue dashed: full 30 mm USB service allowance. Grey dashed: narrow 5.5 mm header housing.',15,'#a7b9cc')
text(60,1324,'H2 antenna is internal: 15.325 mm to WIZ PCB, 15.56 mm laterally to the S3 board.',15,'#a7b9cc')
text(60,1354,'XIAO USB shell allowance: only 0.645 mm to H2 antenna and 0.680 mm to WIZ PCB.',15,'#f0c294')
text(60,1384,'No permanent USB cable in the H2 RF-clearance area. Lift the service cable vertically.',15,'#f0c294')
text(60,1424,'Study only: verify actual plug, vertical clearances, RF performance and enclosure before choosing this layout.',15,'#f0c294')
svg.append('</svg>');(R/'assembly-top.svg').write_text('\n'.join(svg)+'\n')
