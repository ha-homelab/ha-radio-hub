#!/usr/bin/env python3
"""Draw the manufacturer-referenced XIAO bottom pads and actual carrier window."""
import html,json
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text());E=json.loads((R/'xiaoc6-evidence.json').read_text())
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850">','<rect width="1200" height="850" fill="#0b1420"/><style>text{font-family:Arial,sans-serif}</style>']
def text(x,y,s,size=18,color='#e4eef8',anchor='start'):
 out.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}">{html.escape(s)}</text>')
def rect(x,y,w,h,fill,stroke='#81b9a8',radius=0):out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
text(40,45,'MC2-D · XIAO ESP32C6 recovery wiring',30)
text(40,78,'Buy 102010636 with factory male headers. Add only these two underside signal leads.',18,'#afc9dd')
S=17;OY=205;OX=60;WIDTH=17.78*S
text(210,130,'BOTTOM VIEW',23,anchor='middle');text(210,159,'USB at top · mirrored left/right',16,'#afc9dd','middle')
rect(OX,OY,WIDTH,20.955*S,'#194740',radius=8);rect(OX+WIDTH/2-65,OY-28,130,60,'#a4afba')
def local(x,y):return OX+(16.51-x)*S,OY+(y+2.921)*S
for n,p in E['header']['pad_map'].items():
 x,y=local(*p['local_mm']);out.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#c7ad53" stroke="#1d2822"/>')
 text(x+(-18 if int(n)>7 else 18),y+4,n,12,'#dfeee5','end' if int(n)>7 else 'start')
for key,label,color in [('TP8','EN','#ffad69'),('TP2','BOOT','#c89bff')]:
 x,y=local(*E['mechanics']['service_pads'][key]['local_mm']);out.append(f'<circle cx="{x}" cy="{y}" r="{1.143*S/2}" fill="{color}"/>');text(x-18,y+5,key+' '+label,16,color,'end')
text(211,600,'Each pad is only Ø1.143 mm.',16,'#afc9dd','middle')
text(211,626,'Confirm printed EN / BOOT labels.',16,'#afc9dd','middle')
text(211,651,'Do not use the battery pads.',16,'#afc9dd','middle')
# Front section of the real carrier, scaled and cropped around U2/J10.
SX=610;SY=170;SC=15
def globalxy(x,y):return SX+(x-42)*SC,SY+(y-9)*SC
rect(SX,SY,375,530,'#214d40',radius=6)
u2=next(p for p in D['parts'] if p['ref']=='U2');b=u2['body_bounds_global_mm'];x,y=globalxy(*b[:2]);rect(x,y,(b[2]-b[0])*SC,(b[3]-b[1])*SC,'#66958b')
text(804,131,'CARRIER FRONT VIEW',23,anchor='middle')
b=D['mechanics']['service_cutout']['bounds_mm'];x,y=globalxy(*b[:2]);rect(x,y,(b[2]-b[0])*SC,(b[3]-b[1])*SC,'#0b1420','#f5ca93',SC*1.5)
for p in u2['pad_centers_mm']:
 x,y=globalxy(p['x'],p['y']);out.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#d3b85b"/>')
for key,label,color,pin in [('EN','TP8 EN','#ffad69',1),('BOOT','TP2 BOOT','#c89bff',2)]:
 x,y=globalxy(*D['mechanics']['bottom_service_pads_global_mm'][key]);j=next(p for p in D['parts'] if p['ref']=='J10')['pad_centers_mm'][pin-1];xx,yy=globalxy(j['x'],j['y']);bend=globalxy(50.4 if pin==1 else 53.1,34.8)[0]
 out.append(f'<path d="M {x} {y} L {bend} {y+15} L {bend} {yy-35} L {xx} {yy}" fill="none" stroke="{color}" stroke-width="4"/>');out.append(f'<circle cx="{xx}" cy="{yy}" r="9" fill="{color}"/>');text(xx,yy+30,str(pin),16,color,'middle')
text(807,681,'J10: 1 EN · 2 BOOT',18,'#e4eef8','middle')
text(1010,255,'Real window',16,'#f5ca93');text(1010,278,'6 × 10.9 mm',16,'#f5ca93');text(1010,301,'R1.5 corners',16,'#f5ca93')
text(420,720,'1  Solder / inspect with magnification before seating; use flux and short dwell.',17)
text(420,748,'2  Route 30 AWG leads above carrier, between rows; retain a small slack loop.',17)
text(420,776,'3  Keep ≥2.5 mm gap, wire OD ≤0.8 mm and joints ≤1.5 mm; strain-relieve.',17)
text(40,824,'Nominal manufacturer pad positions, not a sample fit approval. Window remains open from below; verify no shorts before power.',16,'#afc9dd')
out.append('</svg>');(R/'c6-recovery.svg').write_text('\n'.join(out)+'\n')
