#!/usr/bin/env python3
"""Independent assertions for mechanical coordinates, power boundaries and pin map."""
import unittest,json,math,re
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text());P={p['ref']:p for p in D['parts']}
def pad(r,n):return next(p for p in P[r]['pad_centers_mm'] if p['number']==n)
def native_footprints():
 tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',(R/'mc1.kicad_pcb').read_text())
 stack=[];root=None
 for t in tokens:
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   else:root=n
   stack.append(n)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 return [x for x in root if isinstance(x,list) and x and x[0]=='footprint']
class CarrierTests(unittest.TestCase):
 def test_project_routing_rules(self):
  project=json.loads((R/'mc1.kicad_pro').read_text());ns=project['net_settings'];classes={x['name']:x for x in ns['classes']}
  self.assertEqual(ns['meta']['version'],5)
  self.assertEqual(set(classes),{'Default','Power'})
  for name,width in [('Default',.25),('Power',.8)]:
   c=classes[name]
   self.assertEqual((c['clearance'],c['track_width'],c['via_diameter'],c['via_drill']),(.2,width,.8,.4))
  rules=project['board']['design_settings']['rules']
  self.assertEqual((rules['min_clearance'],rules['min_track_width'],rules['min_via_diameter'],rules['min_through_hole_diameter'],rules['min_copper_edge_clearance']),(.2,.2,.8,.4,.5))
  wanted={'/'+n for p in P.values() for n in p['pins'].values() if n and (n.startswith('+') or n=='GND')}
  self.assertEqual({x['pattern'] for x in ns['netclass_patterns'] if x['netclass']=='Power'},wanted)
  self.assertEqual(project['board']['design_settings'].get('drc_exclusions',[]),[])
 def test_dimensions(self):
  self.assertEqual((D['board']['width_mm'],D['board']['height_mm'],D['board']['copper_layers']),(100,90,2))
 def test_module_row_centers(self):
  for ref,left,right,spacing in [('U1','J1.1','J3.1',22.86),('U2','J1.1','J3.1',22.86),('U3','1','14',15.24),('U4','J1.1','J2.1',20.32)]:
   a,b=pad(ref,left),pad(ref,right);self.assertAlmostEqual(math.dist((a['x'],a['y']),(b['x'],b['y'])),spacing,places=4)
 def test_rj45_faces_out_of_right_edge(self):
  p=P['U4'];self.assertEqual(p['rotation'],270);self.assertEqual(p['xy'],[92.9,67])
  g=D['mechanics']['rj45'];self.assertEqual(g['outward_normal_global'],[1.0,0.0])
  self.assertEqual(g['face_global_mm'],[[102.0,69.11],[102.0,85.21]])
  self.assertAlmostEqual(g['mouth_beyond_right_edge_mm'],2.0)
  self.assertTrue(all(0<q['x']<100 and 0<q['y']<90 for q in p['pad_centers_mm']))
  self.assertGreater(g['service_corridor_global_mm'][0],max(q['x'] for q in p['pad_centers_mm']))
  # Empty access strip intersects no other module/connector pins inside the PCB.
  x1,y1,x2,y2=g['service_corridor_global_mm']
  for r in P.values():
   if r['ref']=='U4':continue
   self.assertFalse(any(x1<=q['x']<=x2 and y1<=q['y']<=y2 for q in r['pad_centers_mm']))
 def test_native_rj45_footprint_matches_edge_contract(self):
  f=next(f for f in native_footprints() if any(isinstance(p,list) and p[:3]==['property','Reference','U4'] for p in f))
  at=next(x for x in f if isinstance(x,list) and x[0]=='at')
  self.assertEqual([float(at[1]),float(at[2]),float(at[3])%360],[92.9,67.0,270.0])
  face_found=False
  for x in f:
   if not isinstance(x,list) or x[0]!='fp_line':continue
   fields={y[0]:y[1:] for y in x[1:] if isinstance(y,list)}
   if fields.get('layer')==['F.Fab'] and fields.get('start')==['2.11','-9.1'] and fields.get('end')==['18.21','-9.1']:face_found=True
  self.assertTrue(face_found,'Native footprint must mark the verified RJ45 face')
 def test_pitch(self):
  for ref,a,b in [('U1','J1.1','J1.2'),('U2','J1.1','J1.2'),('U3','1','2'),('U4','J1.1','J1.2')]:
   x,y=pad(ref,a),pad(ref,b);self.assertAlmostEqual(math.dist((x['x'],x['y']),(y['x'],y['y'])),2.54,places=4)
 def test_uart_crossovers(self):
  for r,n,r2,n2,net in [('U1','J3.7','U2','J1.9','THREAD_RX'),('U1','J3.6','U2','J1.10','THREAD_TX'),('U1','J1.10','U3','8','ZB_RX'),('U1','J1.11','U3','7','ZB_TX'),('U1','J1.9','U3','5','ZB_CTS'),('U1','J3.18','U3','6','ZB_RTS')]:
   self.assertEqual(P[r]['pins'][n],net);self.assertEqual(P[r2]['pins'][n2],net)
 def test_no_joined_mcu_regulators(self):
  for r,ns in [('U1',['J1.1','J1.2']),('U2',['J1.1']),('U3',['12'])]:
   for n in ns:self.assertIsNone(P[r]['pins'][n])
  self.assertEqual(P['J2']['pins']['3'],'+3V3')
  for ref,out in [('D1','+5V_S3'),('D2','+5V_H2'),('D3','+5V_ZB')]:self.assertEqual(P[ref]['pins'],{'1':out,'2':'+5V'})
 def test_peripheral_pin_mapping(self):
  self.assertEqual(P['J3']['pins']['5'],P['J4']['pins']['4']);self.assertEqual(P['J3']['pins']['6'],P['J4']['pins']['5'])
  self.assertEqual(P['U4']['pins']['J2.1'],'GND');self.assertEqual(P['U4']['pins']['J2.2'],'+3V3');self.assertEqual(P['U4']['pins']['J2.3'],'+3V3');self.assertIsNone(P['U4']['pins']['J2.4'])
  self.assertEqual(P['J8']['pins'],{'1':'ZB_BOOT_SERVICE','2':'GND'})
 def test_only_through_hole_assembly(self):
  for p in P.values():
   fp=(R/'MC1.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod')).read_text();self.assertIn('through_hole',fp);self.assertNotIn('(attr smd)',fp)
  self.assertEqual(len(P),17)
 def test_compact_preserves_electrical_contract(self):
  baseline=json.loads((R.parent/'layout-baseline.json').read_text())
  bp={p['ref']:p for p in baseline['parts']}
  self.assertEqual(set(P),set(bp))
  for ref,p in P.items():
   for key in ['model','footprint','pins']:self.assertEqual(p[key],bp[ref][key],f'{ref} {key}')
  self.assertEqual(sum(len(p['pins']) for p in P.values()),145)
  self.assertEqual(sum(v is not None for p in P.values() for v in p['pins'].values()),103)
 def test_service_clearances(self):
  def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
  def native_boxes():
   out={}
   for f in native_footprints():
    ref=next(x[2] for x in f if isinstance(x,list) and x[:2]==['property','Reference'])
    if ref not in P:continue
    pp=P[ref];th=math.radians(pp['rotation']);boxes=[]
    for x in f:
     if not isinstance(x,list) or x[0]!='fp_rect':continue
     fields={q[0]:q[1:] for q in x[1:] if isinstance(q,list)}
     if fields.get('layer')!=['F.CrtYd']:continue
     coords=[]
     for q in ['start','end']:
      a,b=map(float,fields[q]);coords.append((pp['xy'][0]+a*math.cos(th)+b*math.sin(th),pp['xy'][1]-a*math.sin(th)+b*math.cos(th)))
     boxes.append([min(v[0] for v in coords),min(v[1] for v in coords),max(v[0] for v in coords),max(v[1] for v in coords)])
    out[ref]=boxes
   return out
  boxes=native_boxes();mechanics=D['mechanics']
  for ref,a in mechanics['header_mating_envelopes_mm'].items():
   for ref2,bs in boxes.items():
    if ref==ref2:continue
    for b in bs:self.assertFalse(overlap(a,b),f'{ref} mating shell hits {ref2}')
   for ref2,b in mechanics['header_mating_envelopes_mm'].items():
    if ref!=ref2:self.assertFalse(overlap(a,b),f'{ref} shell hits {ref2} shell')
  for ref,a in mechanics['usb_service_envelopes_mm'].items():
   for ref2,bs in boxes.items():
    if ref==ref2:continue
    for b in bs:self.assertFalse(overlap(a,b),f'{ref} USB hits {ref2}')
   for ref2,b in mechanics['header_mating_envelopes_mm'].items():self.assertFalse(overlap(a,b),f'{ref} USB hits {ref2} shell')
   for x,y in mechanics['mounting_holes_mm']:self.assertFalse(overlap(a,[x-2.5,y-2.5,x+2.5,y+2.5]),f'{ref} USB hits support')
  for x,y in mechanics['mounting_holes_mm']:
   a=[x-2.5,y-2.5,x+2.5,y+2.5]
   for ref,bs in boxes.items():
    for b in bs:self.assertFalse(overlap(a,b),f'support hits {ref}')
   for ref,b in mechanics['header_mating_envelopes_mm'].items():self.assertFalse(overlap(a,b),f'support hits {ref} shell')
if __name__=='__main__':unittest.main(verbosity=2)
