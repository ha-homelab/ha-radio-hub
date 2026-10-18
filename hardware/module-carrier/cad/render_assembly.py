#!/usr/bin/env python3
"""Scaled assembly drawing from the same placement/pad ledger as native KiCad."""
import json,html,math
from pathlib import Path
R=Path(__file__).resolve().parent;d=json.loads((R/'design.json').read_text());e=html.escape
W=d['board']['width_mm'];H=d['board']['height_mm'];S=7;OX=100;OY=170;CW=1330;CH=1160
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">','<rect width="100%" height="100%" fill="#0c1423"/>','<style>text{font-family:Arial,sans-serif}</style>','<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#71e5bc"/></marker></defs>']
def text(x,y,t,size=15,color='#e8f0fb',anchor='start'):
 svg.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{color}" font-size="{size}" text-anchor="{anchor}">{e(t)}</text>')
def xy(x,y):return OX+S*x,OY+S*y
def box(b,fill,stroke='#c0d1dd',dash=False):
 x,y=xy(*b[:2]);svg.append(f'<rect x="{x}" y="{y}" width="{S*(b[2]-b[0])}" height="{S*(b[3]-b[1])}" fill="{fill}" stroke="{stroke}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
def tr(p,x,y):
 a=math.radians(p['rotation']);return p['xy'][0]+x*math.cos(a)+y*math.sin(a),p['xy'][1]-x*math.sin(a)+y*math.cos(a)
def bounds(p,b):
 q=[tr(p,*b[:2]),tr(p,*b[2:])];return[min(x[0] for x in q),min(x[1] for x in q),max(x[0] for x in q),max(x[1] for x in q)]
text(55,48,'MC1 Nano · actual carrier assembly',31)
text(55,83,f'{W} × {H} mm · 2 copper layers · factory male pins soldered directly · no module sockets',18,'#b4c7d9')
text(55,111,'ENGINEERING DRAWING — actual placement and pad numbers; not a product photograph',13,'#71e5bc')
box([0,0,W,H],'#16484a','#93b5b8')
for b in d['mechanics']['rf_copper_keepouts_mm']:box(b,'#704735','#f4b073')
for b in d['mechanics'].get('rf_pour_only_keepouts_mm',[]):box(b,'#926644','#f4b073',True)
for ref,b in d['mechanics']['physical_usb_shells_mm'].items():
 box(b,'#153d50','#73b5dc',True)
for ref,b in d['mechanics']['header_mating_envelopes_mm'].items():box(b,'none','#b8c2c5',True)
for i,(x,y) in enumerate(d['mechanics']['mounting_holes_mm'],1):
 xx,yy=xy(x,y);svg.append(f'<circle cx="{xx}" cy="{yy}" r="17.5" fill="none" stroke="#c4d3df" stroke-dasharray="3 3"/><circle cx="{xx}" cy="{yy}" r="9.45" fill="#0c1423" stroke="#e8f0fb"/>');text(xx+20,yy+5,'H'+str(i),10)
labels={'U1':['U1 · NANO','S3 · 16M / 8M','ANT ↑ USB ↓'],'U2':['U2 · ESP32-H2','Thread RCP','ANT ↑   USB ↓'],'U3':['U3 · XIAO MG24','Zigbee NCP','ANT ←   USB →'],'U4':['U4 · WIZ850io','3.3 V / shared SPI','RJ45 ↓']}
for p in d['parts']:
 ref=p['ref'];pads=p['pad_centers_mm']
 if p.get('body_bounds_local_mm'):
  b=bounds(p,p['body_bounds_local_mm']);box(b,'#d7e8dd','#f8faf8')
  if ref=='U4':box(bounds(p,[2.11,-9.1,18.21,16]),'#bfcad2','#f5fafc')
  if ref=='U2':box(bounds(p,[4.83,-6.975,18.03,-1.575]),'#987c4f','#e6c989')
  if ref=='U1':box(bounds(p,[5.3,37,10.4,39.37]),'#987c4f','#e6c989')
  if ref=='U3':box(bounds(p,[8.7,16.034,13.9,18.034]),'#987c4f','#e6c989')
  cx,cy=xy((b[0]+b[2])/2,(b[1]+b[3])/2)
  for i,t in enumerate(labels[ref]):text(cx,cy+(i-1)*17,t,12 if ref!='U3' else 11,'#173b47','middle')
 elif ref.startswith('J') and p['fitted']:
  b=[min(q['x'] for q in pads)-1.27,min(q['y'] for q in pads)-1.27,max(q['x'] for q in pads)+1.27,max(q['y'] for q in pads)+1.27];box(b,'#273548','#a4bac4');text(*xy(b[0],b[1]-1.05),ref,10)
 elif not p['fitted']:
  text(*xy(p['xy'][0],p['xy'][1]-2.2),ref+' pads',10)
 else:
  a,b=pads;xx,yy=xy((a['x']+b['x'])/2,(a['y']+b['y'])/2);x1,y1=xy(a['x'],a['y']);x2,y2=xy(b['x'],b['y']);vertical=abs(a['x']-b['x'])<.01
  bw,bh=(16,32) if vertical else (32,16)
  svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#d0d7dc" stroke-width="3"/><rect x="{xx-bw/2}" y="{yy-bh/2}" width="{bw}" height="{bh}" rx="2" fill="'+('#51565e' if ref.startswith('D') else '#c8ad75')+'" stroke="#e7ddd0"/>')
  if ref.startswith('D'):
   if vertical:svg.append(f'<line x1="{xx-7}" y1="{yy-10}" x2="{xx+7}" y2="{yy-10}" stroke="#f5ebd4" stroke-width="3"/>')
   else:svg.append(f'<line x1="{xx-10}" y1="{yy-7}" x2="{xx-10}" y2="{yy+7}" stroke="#f5ebd4" stroke-width="3"/>')
  text(xx,yy-bh/2-15,ref,10,'#e8f0fb','middle')
 for q in pads:
  x,y=xy(q['x'],q['y']);n=q['number'];svg.append(f'<circle cx="{x}" cy="{y}" r="4.7" fill="#d4ad58" stroke="#f1d797"/><circle cx="{x}" cy="{y}" r="2.2" fill="#12212c"/>')
  if ref in ('U1','U2','U3'):
   b=bounds(p,p['body_bounds_local_mm'])
   if p['rotation']%180==0:
    left=q['x']<(b[0]+b[2])/2;text(x+(8 if left else -8),y+3,n.split('.')[-1],8,'#173b47','start' if left else 'end')
   else:
    up=q['y']<(b[1]+b[3])/2;text(x,y+(14 if up else -9),n.split('.')[-1],8,'#173b47','middle')
  elif ref=='U4':text(x+(9 if n.startswith('J2') else -9),y+3,n.split('.')[-1],8,'#173b47','start' if n.startswith('J2') else 'end')
  elif ref.startswith('J'):
   if p['rotation']%180==0:text(x+8,y+3,n,8,'#e3eff4')
   else:text(x,y+16,n,8,'#e3eff4','middle')
r=d['mechanics']['rj45'];box(r['service_corridor_global_mm'],'none','#71e5bc',True)
a,b=[xy(*v) for v in r['face_global_mm']];svg.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#111b22" stroke-width="7"/>');cx=sum(v[0] for v in r['face_global_mm'])/2
x1,y1=xy(cx,H+4);x2,y2=xy(cx,H+25);svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#71e5bc" stroke-width="4" marker-end="url(#arrow)"/>')
text(*xy(cx,H+32),'RJ45 OUT · 2 mm past PCB',12,'#71e5bc','middle')
text(770,165,'Placement and service',24)
notes=[('65 × 75 mm','32.3% less area than previous 80 × 90 mm.'),('16 fitted items / 133 pads','J8 and J9 are unpopulated recovery pads.'),('All mounted components on top','Three axial diodes, two axial resistors.'),('Blue dashed outlines','Physical USB shells only; no cable gaps.'),('Grey dashed outlines','5.5 mm narrow header housing allowance.'),('Orange regions','RF exclusions; dashed strip permits RX trace.'),('H1 / H2 / H3','Nylon M2.5 supports, max 5 mm head/body.'),('H2 application + ROM UART','GPIO23 RX / GPIO24 TX; remove R7 first.'),('J1 isolated 5 V · J2 external 3.3 V buck','J3 WK2132 · J4 ZAC93 · J5 CC1101'),('J6 LD2450 · J7 BME680','J8 XIAO boot · J9 Nano GPIO0 boot'),('Shared SPI','W5500 + CC1101: SCK / MOSI / MISO.'),('USB ports physically retained','Initial flash before assembly; later host/OTA.')]
for i,(title,desc) in enumerate(notes):
 y=209+i*61;text(770,y,title,16);text(770,y+22,desc,13,'#abc2d3')
text(55,1100,'Prototype: check exact module fit, plugs, antenna enclosure clearance, power behavior and RF coexistence before fabrication release.',15,'#f0c38b')
text(55,1129,'The geometry is reviewed; hardware performance and assembled service procedures remain unmeasured.',14,'#abc2d3')
svg.append('</svg>');(R/'assembly-top.svg').write_text('\n'.join(svg)+'\n')
