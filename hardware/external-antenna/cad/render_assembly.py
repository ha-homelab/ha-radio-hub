#!/usr/bin/env python3
"""Draw factual module bounds, pads and connector directions from MC2 ledger."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parent; D=json.loads((R/'design.json').read_text())
S=7;OX=45;OY=100
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="970" viewBox="0 0 1160 970">','<rect width="100%" height="100%" fill="#0b1420"/><style>text{font-family:Arial,sans-serif}</style>']
def t(x,y,text,size=16,color='#e6edf4',anchor='start'):out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(text)}</text>')
def rect(b,fill,stroke='#76899d',dash=False):out.append(f'<rect x="{OX+b[0]*S}" y="{OY+b[1]*S}" width="{(b[2]-b[0])*S}" height="{(b[3]-b[1])*S}" fill="{fill}" stroke="{stroke}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
t(45,40,'MC2-D · CLASSIC ESP32 + THREE ANTENNAS',28);t(45,72,'100 × 100 mm · front view · all components on this side · prototype',16,'#b8c6d8')
rect([0,0,100,100],'#164845','#80bbac')
for x,y in D['mechanics']['mounting_holes_mm']:out.append(f'<circle cx="{OX+x*S}" cy="{OY+y*S}" r="{1.35*S}" fill="#0b1420" stroke="#d2e1d9"/>')
labels={'U1':['ESP32 DevKitC-VIE','8 MB / 8 MB','BLE4.2 host'],'U2':['XIAO ESP32C6','Thread RCP'],'U3':['XIAO MG24','Zigbee NCP'],'U4':['WIZ850io','Ethernet']}
for p in D['parts']:
 b=p['body_bounds_global_mm'];pads=p['pad_centers_mm'];ref=p['ref']
 if b:
  rect(b,'#d5e7df','#d5e7df');cx=OX+(b[0]+b[2])*S/2;cy=OY+(b[1]+b[3])*S/2
  for i,label in enumerate(labels[ref]):t(cx,cy+16*i,label,12,'#143d39','middle')
 else:
  xs=[q['x'] for q in pads];ys=[q['y'] for q in pads];rect([min(xs)-1.2,min(ys)-1.2,max(xs)+1.2,max(ys)+1.2],'#243247')
  t(OX+min(xs)*S,OY+min(ys)*S-12,ref+(' WIRE / NO DIODE' if ref=='D1' else ' DNP' if not p['fitted'] else ''),11)
 for q in pads:
  x=OX+q['x']*S;y=OY+q['y']*S
  out.append(f'<circle cx="{x}" cy="{y}" r="4.8" fill="#d1b45c"/><circle cx="{x}" cy="{y}" r="2.6" fill="#142525"/>')
rect(D['mechanics']['service_cutout']['bounds_mm'],'#0b1420','#f1a27a',True)
for ref,b in D['mechanics']['physical_usb_shells_mm'].items():rect(b,'none','#6db8f2',True)
for ref,p in D['mechanics']['rf_ports'].items():
 x,y=p['estimated_xy_mm'];cx=OX+x*S;cy=OY+y*S
 out.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#e0a847" stroke="#29200b"/>')
 t(cx,cy-13,p['radio']+' U.FL*',12,'#ffc96a','middle')
a,b=D['mechanics']['rj45']['face_global_mm'];rect([min(a[0],b[0]),99.3,max(a[0],b[0]),102],'#aab4be')
t(OX+(a[0]+b[0])*S/2,OY+110*S,'RJ45 cable ↓',16,'#80e2bf','middle')
notes=[('THREE SEPARATE RF PATHS','BLE, Thread and Zigbee: no splitter.'),('MATCHED 50 Ω PIGTAILS','U.FL / MHF1 to SMA female bulkhead.'),('EXTERNAL ANTENNA REQUIRED','Connect before radio operation.'),('C6 FACTORY HEADERS + 2 LEADS','J10.1 → TP8 EN; J10.2 → TP2 BOOT.'),('C6 EXTERNAL ANTENNA SELECTION','MC2-D firmware: GPIO3 LOW /14 HIGH.'),('HOST BOOT STRAPS','R4 / R5: GPIO12 / GPIO2 LOW at reset.'),('CASE & RF CHECK STILL REQUIRED','No measured coverage or fit claim.'),('* RF SOCKET LOCATIONS','C6: vendor KiCad; others: estimates.')]
for i,(a,b) in enumerate(notes):t(775,120+75*i,a,15,'#8ce0c2');t(775,145+75*i,b,12)
t(45,932,'Blue: physical USB shell bounds. Gold: C6 vendor KiCad center; other RF positions approximate. All dimensions require sample fit verification.',13,'#c6d0df')
out.append('</svg>');(R/'assembly-top.svg').write_text('\n'.join(out)+'\n')
