#!/usr/bin/env python3
"""Scaled assembly artwork generated from the same pad ledger as native KiCad."""
import json, html, math
from pathlib import Path
R=Path(__file__).resolve().parent; d=json.loads((R/'design.json').read_text()); esc=html.escape
S=7.;OX=320;OY=170
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1520" height="1130" viewBox="0 0 1520 1130">','<rect width="1520" height="1130" fill="#0b1424"/>','<style>text{font-family:Inter,Arial,sans-serif;fill:#e9f0fa}.muted{fill:#a7b9cc}.small{font-size:15px}.pin{font-size:10px;fill:#173c4d}.boardtext{font-size:12px;fill:#bddee2}</style>']
def text(x,y,t,size=18,fill=None,anchor='start'):
 svg.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"'+(f' style="fill:{fill}"' if fill else '')+'>'+esc(t)+'</text>')
def rect(x,y,w,h,fill,stroke='#bedde7',rx=0):svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
def trans(p,x,y):
 # KiCad uses positive counter-clockwise angle on a screen with y down.
 th=math.radians(p['rotation']); return p['xy'][0]+x*math.cos(th)+y*math.sin(th), p['xy'][1]-x*math.sin(th)+y*math.cos(th)
def xy(x,y):return OX+S*x,OY+S*y
text(76,64,'MC1 · one ready-module carrier',36);text(76,99,'160 × 100 mm · two copper layers · direct-solder factory male headers',21,'#a7b9cc')
text(76,131,'ASSEMBLY VIEW — verified hole centers; external harness modules shown below',15,'#6adcc0')
rect(OX,OY,160*S,100*S,'#154a4d','#7baeb2',10)
# Explicit cable access envelope; its size is an engineering reservation.
rx1,ry1,rx2,ry2=d['mechanics']['rj45']['service_corridor_global_mm'];rx,ry=xy(rx1,ry1)
svg.append(f'<rect x="{rx}" y="{ry}" width="{(rx2-rx1)*S}" height="{(ry2-ry1)*S}" fill="#123b3d" fill-opacity="0.45" stroke="#6ee7c8" stroke-width="1.5" stroke-dasharray="8 5"/>')
svg.append('<defs><marker id="out-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6ee7c8"/></marker></defs>')
for x,y in [(5,5),(155,5),(5,95),(155,95)]:
 xx,yy=xy(x,y);svg.append(f'<circle cx="{xx}" cy="{yy}" r="{1.6*S}" fill="#0b1424" stroke="#d2dee7"/>')
for x1,y1,x2,y2 in [(0,0,160,1.2),(47,0,64,12),(89,0,106,12),(128.8,0,141,5)]:
 xx,yy=xy(x1,y1);rect(xx,yy,(x2-x1)*S,(y2-y1)*S,'#75503e','#eda86f')
body={'U1':(-1.27,-1.4,24.13,61.34),'U2':(-1.27,-1.575,24.13,46.685),'U3':(-1.27,-2.921,16.51,18.034),'U4':(-1.34,-6.4,21.66,18.6)}
labels={'U1':['S3 N8R8','ESPHome host','BLE + LAN'],'U2':['ESP32-H2','Thread RCP'],'U3':['XIAO','MG24','Ember NCP'],'U4':['U4 · WIZ850io','RJ45 faces LEFT']}
for p in d['parts']:
 ref=p['ref']; pads=p['pad_centers_mm']
 if ref in body:
  x1,y1,x2,y2=body[ref];coords=[trans(p,x,y) for x,y in [(x1,y1),(x2,y2)]];xmin=min(a for a,b in coords);ymin=min(b for a,b in coords);xmax=max(a for a,b in coords);ymax=max(b for a,b in coords)
  xx,yy=xy(xmin,ymin);rect(xx,yy,(xmax-xmin)*S,(ymax-ymin)*S,'#d9e8dc' if ref!='U4' else '#b2d7ee','#f6fbfb',3)
  if ref=='U4':
   # Silver body depth is illustrative; aperture face/header geometry is authoritative.
   metal=[trans(p,2.11,-9.1),trans(p,18.21,16.0)]
   mx1=min(v[0] for v in metal);mx2=max(v[0] for v in metal);my1=min(v[1] for v in metal);my2=max(v[1] for v in metal)
   mx,my=xy(mx1,my1);rect(mx,my,(mx2-mx1)*S,(my2-my1)*S,'#c3cbd1','#f5f9fb',3)
   face=d['mechanics']['rj45']['face_global_mm'];fa=xy(*face[0]);fb=xy(*face[1])
   svg.append(f'<line x1="{fa[0]}" y1="{fa[1]}" x2="{fb[0]}" y2="{fb[1]}" stroke="#101820" stroke-width="6"/>')
  cx=OX+(xmin+xmax)*S/2;cy=OY+(ymin+ymax)*S/2
  for i,t in enumerate(labels[ref]):text(cx,cy+(i-(len(labels[ref])-1)/2)*17,t,14 if ref!='U3' else 12,'#173c4d','middle')
  if ref!='U4':text(cx,OY+ymax*S-8,ref,13,'#173c4d','middle')
 elif ref[0]=='J':
  xmin=min(a['x'] for a in pads)-1.27;xmax=max(a['x'] for a in pads)+1.27;ymin=min(a['y'] for a in pads)-1.27;ymax=max(a['y'] for a in pads)+1.27;xx,yy=xy(xmin,ymin);rect(xx,yy,(xmax-xmin)*S,(ymax-ymin)*S,'#273748','#7da2b1',2)
  text(OX+(xmin+xmax)*S/2,OY+ymin*S-6,ref,12,'#f2fcff','middle')
 else:
  x1,y1=pads[0]['x'],pads[0]['y'];x2,y2=pads[-1]['x'],pads[-1]['y'];xx,yy=xy(x1,y1);zz,ww=xy(x2,y2);svg.append(f'<line x1="{xx}" y1="{yy}" x2="{zz}" y2="{ww}" stroke="#b7bfca" stroke-width="3"/>');rect((xx+zz)/2-16,yy-6,32,12,'#5d464b' if ref[0]=='D' else '#c9a771','#e7ddd0',3);text((xx+zz)/2,yy-12,ref,12,'#def5ff','middle')
 for pad in pads:
  x,y=xy(pad['x'],pad['y']);n=pad['number'];svg.append(f'<circle cx="{x}" cy="{y}" r="5.2" fill="#d8ac53" stroke="#eccb83"/><circle cx="{x}" cy="{y}" r="2.5" fill="#102530"/>')
  if ref in ['U1','U2']:
   left=n.startswith('J1'); text(x+(8 if left else -8),y+3,n,9,'#173c4d','start' if left else 'end')
  elif ref=='U4':text(x,y+(-8 if n.startswith('J1') else 12),n.split('.')[-1],9,'#173c4d','middle')
  elif ref=='U3':text(x+(8 if int(n)>=8 else -8),y+3,n,9,'#173c4d','start' if int(n)>=8 else 'end')
  elif ref[0]=='J':text(x,y+15,n,9,'#cce4e4','middle')
for x,y,t in [(22,29,'No female sockets'),(22,33,'No carrier SMT'),(22,38,'4 mounted modules'),(22,42,'8 harness/service headers'),(107,60,'Factory pins through PTH'),(107,64,'Solder on underside'),(109,81,'MCU 3V3 outputs not joined')]:text(*xy(x,y),t,12,'#c9e5e6','middle')
text(*xy(4.5,65.1),'J2',9,'#173c4d','middle')
text(*xy(4.5,85.4),'J1',9,'#173c4d','middle')
# Aperture at x=-1 mm; the cable axis points out to negative X.
fy=(d['mechanics']['rj45']['face_global_mm'][0][1]+d['mechanics']['rj45']['face_global_mm'][1][1])/2
ax,ay=xy(-2,fy);ex,ey=xy(-31,fy)
svg.append(f'<line x1="{ax}" y1="{ay}" x2="{ex}" y2="{ey}" stroke="#6ee7c8" stroke-width="4" marker-end="url(#out-arrow)"/>')
text(OX-130,ay-24,'RJ45 CABLE OUT',16,'#6ee7c8','middle')
text(OX-130,ay+27,'Mouth: 1.0 mm past edge',14,'#c8e9df','middle')
text(OX-130,ay+60,'Keep plug / boot / latch clear',12,'#a7b9cc','middle')
svg.append(f'<line x1="{OX}" y1="{OY+S*59}" x2="{OX}" y2="{OY+S*90}" stroke="#f3bc79" stroke-dasharray="4 4"/>')
text(OX+5,OY+S*90,'PCB edge',11,'#f3bc79')
# Dimension lines, isolated from pad labels.
svg.append(f'<path d="M{OX} {OY+S*100+22}v10m0 -5h{S*160}m0 -5v10" stroke="#a5bfd0" fill="none"/>');text(OX+S*80,OY+S*100+50,'160 mm',17,'#bcd0de','middle')
text(76,956,'External ready modules — harness interfaces, not fabricated on MC1',22)
for x,w,title,line in [(76,267,'J1 · isolated PoE splitter','Fused regulated 5V + GND'),(358,267,'J2 · D24V22F3 buck','5V in / peripheral 3.3V out'),(640,267,'J3 · WK2132 DFR0627','3.3V · I²C · UART1'),(922,273,'J4–J8 · peripherals','ZAC93 · RF · radar · BME · boot')]:
 rect(x,982,w,73,'#17273d','#37506b',8);text(x+15,1012,title,16);text(x+15,1038,line,14,'#a7b9cc')
text(76,1095,'Prototype: jack face / holes are dimensioned; metal body sketch is illustrative. Verify cable boot, latch and enclosure clearance.',16,'#f0c294')
svg.append('</svg>');(R/'assembly-top.svg').write_text('\n'.join(svg)+'\n')
