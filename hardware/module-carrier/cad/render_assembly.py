#!/usr/bin/env python3
"""Front/back assembly drawings from native-placement ledger; rear view mirrored."""
import json,html,math
from pathlib import Path
R=Path(__file__).resolve().parent;D=json.loads((R/'design.json').read_text());P={p['ref']:p for p in D['parts']};W=D['board']['width_mm'];H=D['board']['height_mm'];S=8;OX=80;OY=160

def render(side):
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="1100" viewBox="0 0 1220 1100">','<rect width="100%" height="100%" fill="#0c1423"/>','<style>text{font-family:Arial,sans-serif}</style>','<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#71e5bc"/></marker></defs>']
 def text(x,y,t,size=15,color='#e8f0fb',anchor='start'):out.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{color}" font-size="{size}" text-anchor="{anchor}">{html.escape(t)}</text>')
 def xy(x,y):return OX+S*(W-x if side=='back' else x),OY+S*y
 def box(b,fill,stroke='#c0d1dd',dash=False):
  xa,ya=xy(*b[:2]);xb,yb=xy(*b[2:]);out.append(f'<rect x="{min(xa,xb)}" y="{min(ya,yb)}" width="{abs(xb-xa)}" height="{abs(yb-ya)}" fill="{fill}" stroke="{stroke}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
 def bounds(p,b):
  a=math.radians(p['rotation']);q=[]
  for x,y in [b[:2],b[2:]]:
   if p['side']=='back':y=-y
   q.append((p['xy'][0]+x*math.cos(a)+y*math.sin(a),p['xy'][1]-x*math.sin(a)+y*math.cos(a)))
  return [min(v[0] for v in q),min(v[1] for v in q),max(v[0] for v in q),max(v[1] for v in q)]
 text(45,43,'MC1 Nano · '+('FRONT / room-facing' if side=='front' else 'BACK / ceiling-facing · mirrored physical view'),27)
 text(45,79,'51 × 75 mm body + mounting ear · 57 × 75 mm bounds · no sockets',18,'#b4c7d9')
 text(45,109,'ENGINEERING PROTOTYPE — physical Z clearance remains unmeasured',15,'#f0c38b')
 points=' '.join(f'{xy(x,y)[0]},{xy(x,y)[1]}' for x,y in D['board']['outline_mm']);out.append(f'<polygon points="{points}" fill="#16484a" stroke="#93b5b8"/>')
 for b in D['mechanics']['rf_copper_keepouts_mm']:box(b,'#704735','#f4b073')
 for b in D['mechanics']['rf_pour_only_keepouts_mm']:box(b,'#926644','#f4b073',True)
 # Dashed reverse-side bodies explain occupied volume without pretending they are mounted here.
 for p in P.values():
  if p['side']!=side and p.get('body_bounds_global_mm'):
   b=p['body_bounds_global_mm'];box(b,'none','#688b98',True)
   cx,cy=xy((b[0]+b[2])/2,(b[1]+b[3])/2)
   if side=='front':text(cx,cy,'WIZ850io on reverse',11,'#8eaab5','middle')
 for ref,b in D['mechanics']['header_mating_envelopes_mm'].items():
  if P[ref]['side']==side:box(b,'none','#b8c2c5',True)
 for i,(x,y) in enumerate(D['mechanics']['mounting_holes_mm'],1):
  xx,yy=xy(x,y);out.append(f'<circle cx="{xx}" cy="{yy}" r="20" fill="none" stroke="#c4d3df" stroke-dasharray="3 3"/><circle cx="{xx}" cy="{yy}" r="10.8" fill="#0c1423" stroke="#e8f0fb"/>');text(xx+13,yy+4,'H'+str(i),9)
 labels={'U1':['U1 · NANO','S3 · 16M / 8M','ANT ↑  USB ↓'],'U2':['U2 · H2','Thread RCP','ANT ↑ USB ↓'],'U3':['U3 · MG24','Zigbee NCP','ANT ← USB →'],'U4':['U4 · WIZ850io','3.3 V / SPI','RJ45 ↓']}
 for p in P.values():
  if p['side']!=side:continue
  ref=p['ref'];pads=p['pad_centers_mm']
  if p.get('body_bounds_local_mm'):
   b=p['body_bounds_global_mm'];box(b,'#d7e8dd','#f8faf8')
   if ref=='U4':box(bounds(p,[2.11,-9.1,18.21,16]),'#bfcad2','#f5fafc')
   if ref=='U2':box(bounds(p,[4.83,-6.975,18.03,-1.575]),'#987c4f','#e6c989')
   if ref=='U1':box(bounds(p,[5.3,37,10.4,39.37]),'#987c4f','#e6c989')
   if ref=='U3':box(bounds(p,[8.7,16.034,13.9,18.034]),'#987c4f','#e6c989')
   cx,cy=xy((b[0]+b[2])/2,(b[1]+b[3])/2)
   for i,t in enumerate(labels[ref]):text(cx,cy+(i-1)*17,t,12 if ref!='U3' else 10,'#173b47','middle')
   if ref=='U4':
    for row in ['J1','J2']:
     rowpads=[q for q in pads if q['number'].startswith(row+'.')];xx,yy=xy(rowpads[0]['x'],min(q['y'] for q in rowpads)-2.0);text(xx,yy,row,9,'#173b47','middle')
  elif ref.startswith('J') and p['fitted']:
   b=[min(q['x'] for q in pads)-1.27,min(q['y'] for q in pads)-1.27,max(q['x'] for q in pads)+1.27,max(q['y'] for q in pads)+1.27];box(b,'#273548','#a4bac4');xx,yy=xy(p['xy'][0],p['xy'][1]);text(xx-10,yy+3,ref,10,anchor='end')
  elif not p['fitted']:text(*xy(p['xy'][0],p['xy'][1]-2),ref+' pads',10)
  else:
   a,b=pads;xx,yy=xy((a['x']+b['x'])/2,(a['y']+b['y'])/2);x1,y1=xy(a['x'],a['y']);x2,y2=xy(b['x'],b['y']);angle=math.degrees(math.atan2(y2-y1,x2-x1))
   out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#d0d7dc" stroke-width="3"/><g transform="rotate({angle} {xx} {yy})"><rect x="{xx-19}" y="{yy-8}" width="38" height="16" rx="2" fill="'+('#51565e' if ref.startswith('D') else '#c8ad75')+'" stroke="#e7ddd0"/>')
   if ref.startswith('D'):out.append(f'<line x1="{xx-11}" y1="{yy-7}" x2="{xx-11}" y2="{yy+7}" stroke="#f5ebd4" stroke-width="3"/>')
   out.append('</g>');text(xx,min(y1,y2)-11,ref,10,anchor='middle')
  for q in pads:
   x,y=xy(q['x'],q['y']);n=q['number'];out.append(f'<circle cx="{x}" cy="{y}" r="5.3" fill="#d4ad58" stroke="#f1d797"/><circle cx="{x}" cy="{y}" r="2.4" fill="#12212c"/>')
   if ref in ('U1','U2','U3','U4'):
    b=p['body_bounds_global_mm'];mx=(b[0]+b[2])/2
    if p['rotation']%180==0:
     left=(q['x']<mx) != (side=='back');text(x+(9 if left else -9),y+3,n.split('.')[-1],8,'#173b47','start' if left else 'end')
    else:text(x,y+(14 if q['y']<(b[1]+b[3])/2 else -9),n.split('.')[-1],8,'#173b47','middle')
   elif ref.startswith('J'):text(x+8,y+3,n,8,'#e3eff4')
 for ref,b in D['mechanics']['physical_usb_shells_mm'].items():
  if P[ref]['side']==side:box(b,'#153d50','#73b5dc',True)
 if side=='back':
  r=D['mechanics']['rj45'];box(r['service_corridor_global_mm'],'none','#71e5bc',True)
  a,b=[xy(*v) for v in r['face_global_mm']];out.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#111b22" stroke-width="7"/>');cx=sum(v[0] for v in r['face_global_mm'])/2
  x1,y1=xy(cx,H+4);x2,y2=xy(cx,H+23);out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#71e5bc" stroke-width="4" marker-end="url(#arrow)"/>');text(*xy(cx,H+29),'RJ45 OUT · 2 mm',12,'#71e5bc','middle')
 text(565,170,'Assembly and clearance contract',24)
 notes=[('16 fitted parts / 18 positions','J8/J9 are unpopulated pads, not fitted headers.'),('Front: three controller modules','Nano, H2 and XIAO retain factory male pins.'),('Back: Ethernet and all harness headers','WIZ850io, J1–J7 and all five axial parts.'),('Two-sided drawing convention','Back is mirrored; actual pad identities preserved.'),('41 intentional PTH/body projections','33 under H2; 6 under Nano; 2 under XIAO.'),('No measured Z approval yet','Gap − underside protrusion − tail/fillet ≥ 1 mm.'),('Tail/fillet target ≤ 1 mm, conditional','Do not compromise acceptable solder joints.'),('Seat factory pin spacers normally','Measure actual gap; no floating unsupported boards.'),('Assembly order is acyclic','Rear headers/axials → front modules → rear WIZ.'),('Blue outlines: retained USB sockets','No postassembly USB cable space is reserved.'),('Orange: prototype RF provisions','Keep rear parts, wires and ceiling metal clear.'),('Lower supports straddle the jack','5 mm behind mouth; enclosure cradle still needed.')]
 for i,(title,desc) in enumerate(notes):
  y=209+i*61;text(565,y,title,16);text(565,y+23,desc,13,'#abc2d3')
 text(45,1040,'Prototype only: verify actual module gaps, trimmed solder joints, enclosure load support and RF coexistence.',14,'#f0c38b')
 out.append('</svg>');(R/('assembly-top.svg' if side=='front' else 'assembly-bottom.svg')).write_text('\n'.join(out)+'\n')
for side in ['front','back']:render(side)
