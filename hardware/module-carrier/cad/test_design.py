#!/usr/bin/env python3
"""Independent assertions for mechanical coordinates, power boundaries and pin map."""
import unittest,json,math,re
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text());P={p['ref']:p for p in D['parts']}
def pad(r,n):return next(p for p in P[r]['pad_centers_mm'] if p['number']==n)
def native_tree():
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
 return root
def native_footprints():return [x for x in native_tree() if isinstance(x,list) and x and x[0]=='footprint']
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
  self.assertEqual((D['board']['width_mm'],D['board']['height_mm'],D['board']['copper_layers']),(47.5,75,2))
 def test_native_routing_metrics(self):
  metrics=json.loads((R/'routing-metrics.json').read_text());total=0;vias=0
  for obj in native_tree():
   if not isinstance(obj,list):continue
   if obj[0]=='via':vias+=1
   if obj[0]=='segment':
    fields={x[0]:x[1:] for x in obj[1:] if isinstance(x,list)}
    total+=math.dist(list(map(float,fields['start'])),list(map(float,fields['end'])))
  self.assertAlmostEqual(total,metrics['current']['total_track_length_mm'],places=2)
  self.assertEqual(vias,metrics['current']['total_vias'])
  self.assertEqual(metrics['current']['total_segments'],sum(isinstance(o,list) and o[0]=='segment' for o in native_tree()))
 def test_rectangle_rails_and_single_retainer(self):
  self.assertEqual(D['board']['outline_mm'],[[0,0],[47.5,0],[47.5,75],[0,75]])
  self.assertEqual(D['board']['area_mm2'],3562.5)
  self.assertEqual(D['mechanics']['mounting_holes_mm'],[[18,52.03]])
  mouth=D['mechanics']['rj45']['face_global_mm'];center=[sum(p[i] for p in mouth)/2 for i in (0,1)]
  self.assertEqual(center,[33.0,77.0]);self.assertEqual(D['mechanics']['mounting_hole_refs'],['H3'])
 def test_module_row_centers(self):
  for ref,left,right,spacing in [('U1','JP1.1','JP2.15',15.24),('U2','J1.1','J3.1',22.86),('U3','1','14',15.24),('U4','J1.1','J2.1',20.32)]:
   a,b=pad(ref,left),pad(ref,right);self.assertAlmostEqual(math.dist((a['x'],a['y']),(b['x'],b['y'])),spacing,places=4)
 def test_rj45_faces_out_of_bottom_edge(self):
  p=P['U4'];self.assertEqual(p['rotation'],0);self.assertEqual(p['xy'],[22.84,67.9])
  g=D['mechanics']['rj45'];self.assertEqual(g['outward_normal_global'],[0.0,1.0])
  self.assertEqual(g['face_global_mm'],[[24.95,77.0],[41.05,77.0]])
  self.assertAlmostEqual(g['mouth_beyond_bottom_edge_mm'],2.0)
  self.assertTrue(all(0<q['x']<47.5 and 0<q['y']<75 for q in p['pad_centers_mm']))
  x1,y1,x2,y2=g['service_corridor_global_mm']
  for r in P.values():
   if r['ref']=='U4':continue
   self.assertFalse(any(x1<=q['x']<=x2 and y1<=q['y']<=y2 for q in r['pad_centers_mm']))
 def test_native_rj45_footprint_matches_edge_contract(self):
  f=next(f for f in native_footprints() if any(isinstance(p,list) and p[:3]==['property','Reference','U4'] for p in f))
  at=next(x for x in f if isinstance(x,list) and x[0]=='at')
  self.assertEqual([float(at[1]),float(at[2]),(float(at[3]) if len(at)>3 else 0)%360],[22.84,67.9,0.0])
  face_found=False
  for x in f:
   if not isinstance(x,list) or x[0]!='fp_line':continue
   fields={y[0]:y[1:] for y in x[1:] if isinstance(y,list)}
   if fields.get('layer')==['B.Fab'] and fields.get('start')==['2.11','9.1'] and fields.get('end')==['18.21','9.1']:face_found=True
  self.assertTrue(face_found,'Native footprint must mark the verified RJ45 face')
 def test_carrier_holes_stay_inside_outline(self):
  for p in P.values():
   for q in p['pad_centers_mm']:
    self.assertTrue(.5 < q['x'] < 47 and .5 < q['y'] < 74.5,(p['ref'],q['number']))
 def test_no_connected_pad_is_trapped_by_rf_track_exclusion(self):
  for p in P.values():
   for q in p['pad_centers_mm']:
    if not q['net']:continue
    for x1,y1,x2,y2 in D['mechanics']['rf_copper_keepouts_mm']:
     self.assertFalse(x1<q['x']<x2 and y1<q['y']<y2,(p['ref'],q['number'],'inside track exclusion'))
 def test_xiao_rf_escape_only_routes_rx(self):
  pocket=D['mechanics']['rf_pour_only_keepouts_mm'];self.assertEqual(pocket,[[16.48,72.5,17.5,73.8]])
  native_pocket=False
  for obj in native_tree():
   if not isinstance(obj,list) or obj[0]!='zone':continue
   fields={x[0]:x[1:] for x in obj[1:] if isinstance(x,list)}
   if 'polygon' not in fields or 'keepout' not in fields:continue
   pts=next(x[1:] for x in fields['polygon'] if x[0]=='pts')
   coords=[[float(p[1]),float(p[2])] for p in pts]
   if coords==[[16.48,72.5],[17.5,72.5],[17.5,73.8],[16.48,73.8]]:
    k={x[0]:x[1] for x in fields['keepout']};self.assertEqual(k['tracks'],'allowed');self.assertEqual(k['vias'],'not_allowed');self.assertEqual(k['copperpour'],'not_allowed');self.assertEqual(fields['layers'],['F.Cu','B.Cu']);native_pocket=True
  self.assertTrue(native_pocket)
  # Check the actual native copper objects, not only the intended netlist.
  touched=0
  for obj in native_tree():
   if not isinstance(obj,list) or obj[0] not in ('segment','via'):continue
   fields={x[0]:x[1:] for x in obj[1:] if isinstance(x,list)}
   if obj[0]=='via':
    x,y=map(float,fields['at']);radius=float(fields['size'][0])/2
    self.assertFalse(x+radius>16.48 and x-radius<17.5 and y+radius>72.5 and y-radius<73.8,'Via in antenna RX pocket')
   else:
    x1,y1=map(float,fields['start']);x2,y2=map(float,fields['end']);radius=float(fields['width'][0])/2
    if max(x1,x2)+radius>16.48 and min(x1,x2)-radius<17.5 and max(y1,y2)+radius>72.5 and min(y1,y2)-radius<73.8:
     self.assertEqual(fields['net'],['/ZB_RX']);self.assertEqual(float(fields['width'][0]),.25);touched+=1
  self.assertGreater(touched,0)
 def test_h2_antenna_beyond_board_edge(self):
  p=P['U2'];self.assertEqual(p['xy'],[2.57,1.5]);self.assertEqual(p['rotation'],0)
  ant_max_y=p['xy'][1]-1.575;ant_min_y=p['xy'][1]-6.975
  self.assertLess(ant_max_y,0);self.assertAlmostEqual(ant_min_y,-5.475)
  self.assertGreaterEqual(min(q['y'] for q in p['pad_centers_mm'])-.9,.5)
 def test_pitch(self):
  for ref,a,b in [('U1','JP1.1','JP1.2'),('U2','J1.1','J1.2'),('U3','1','2'),('U4','J1.1','J1.2')]:
   x,y=pad(ref,a),pad(ref,b);self.assertAlmostEqual(math.dist((x['x'],x['y']),(y['x'],y['y'])),2.54,places=4)
 def test_native_pad_nets_match_complete_ledger(self):
  count=0
  for f in native_footprints():
   ref=next(x[2] for x in f if isinstance(x,list) and x[:2]==['property','Reference'])
   if ref not in P:continue
   seen={}
   for pd in f:
    if not isinstance(pd,list) or pd[0]!='pad':continue
    self.assertEqual(pd[2],'thru_hole')
    net=next((x for x in pd if isinstance(x,list) and x[0]=='net'),None)
    name=net[-1] if net else ''
    seen[pd[1]]=name
   self.assertEqual(set(seen),set(P[ref]['pins']))
   for n,wanted in P[ref]['pins'].items():
    if wanted:self.assertEqual(seen[n].lstrip('/'),wanted,(ref,n))
    else:self.assertTrue(not seen[n] or seen[n].startswith('unconnected-'),(ref,n))
   count+=len(seen)
  self.assertEqual(count,133)
 def test_uart_crossovers(self):
  for r,n,r2,n2,net in [('U1','JP2.1','U2','J3.3','THREAD_RX'),('U1','JP2.2','U2','J3.2','THREAD_TX'),('U1','JP2.11','U3','8','ZB_RX'),('U1','JP2.12','U3','7','ZB_TX'),('U1','JP2.7','U3','5','ZB_CTS'),('U1','JP2.13','U3','6','ZB_RTS')]:
   self.assertEqual(P[r]['pins'][n],net);self.assertEqual(P[r2]['pins'][n2],net)
 def test_no_joined_mcu_regulators(self):
  for r,ns in [('U1',['JP1.2','JP1.12']),('U2',['J1.1']),('U3',['12'])]:
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
  self.assertEqual(len(P),18)
 def test_nano_firmware_and_shared_spi_contract(self):
  plan=json.loads((R/'nano-pin-plan.json').read_text())
  names={'ethernet_sck':'SPI_SCK','ethernet_mosi':'SPI_MOSI','ethernet_miso':'SPI_MISO','ethernet_cs':'ETH_CS','ethernet_irq':'ETH_INT','ethernet_reset':'ETH_RESET','cc1101_sck':'SPI_SCK','cc1101_mosi':'SPI_MOSI','cc1101_miso':'SPI_MISO','cc1101_cs':'RF_CS','cc1101_gdo0_tx':'RF_GDO0','cc1101_gdo2_rx':'RF_GDO2','zigbee_tx':'ZB_RX','zigbee_rx':'ZB_TX','zigbee_rts':'ZB_CTS','zigbee_cts':'ZB_RTS','i2c_sda':'I2C_SDA','i2c_scl':'I2C_SCL','thread_tx':'THREAD_RX','thread_rx':'THREAD_TX','thread_reset':'THREAD_EN','thread_boot':'THREAD_BOOT','radar_tx':'RADAR_RX','radar_rx':'RADAR_TX'}
  for key,net in names.items():self.assertEqual(P['U1']['pins'][plan['assignments'][key]['header_pin']],net,key)
  self.assertEqual(len({v['gpio'] for v in plan['assignments'].values()}),21)
  for sig,u4,j5 in [('MOSI','J1.3','4'),('MISO','J2.6','5'),('SCK','J1.4','3')]:
   self.assertEqual(P['U4']['pins'][u4],'SPI_'+sig);self.assertEqual(P['J5']['pins'][j5],'SPI_'+sig)
  self.assertEqual(P['U1']['pins']['JP1.15'],'+5V_S3')
  self.assertEqual(P['U1']['pins']['JP1.13'],'S3_BOOT_SERVICE')
  self.assertEqual(P['J9']['pins'],{'1':'S3_BOOT_SERVICE','2':'GND'})
  self.assertEqual(sum(len(p['pins']) for p in P.values()),133)
 def test_nano_footprint_pin_direction(self):
  # JP1 increments USB->antenna, JP2 numbering reverses on opposite row.
  a,b,c=pad('U1','JP1.1'),pad('U1','JP1.15'),pad('U1','JP2.15')
  self.assertEqual((a['x'],a['y']),(44.57,39));self.assertEqual((b['x'],b['y']),(44.57,3.44));self.assertEqual((c['x'],c['y']),(29.33,39))
 def test_no_usb_cable_gaps_but_physical_shells_retained(self):
  self.assertEqual(D['mechanics']['usb_service_envelopes_mm'],{})
  self.assertEqual(set(D['mechanics']['physical_usb_shells_mm']),{'U1','U2','U3'})
  self.assertEqual(D['mechanics']['physical_usb_shells_mm']['U1'],[31.33,42.81,42.57,44.81])
  self.assertEqual(D['mechanics']['physical_usb_shells_mm']['U2'],[1.3,48.185,26.7,49.185])
  self.assertEqual(D['mechanics']['physical_usb_shells_mm']['U3'],[4.62,52.379,13.62,55.379])
 def test_unpopulated_recovery_pads_and_rom_uart(self):
  self.assertEqual({r for r,p in P.items() if not p['fitted']},{'J8','J9'})
  self.assertEqual(sum(p['fitted'] for p in P.values()),16)
  self.assertEqual(P['U2']['pins']['J3.3'],'THREAD_RX');self.assertEqual(P['U2']['pins']['J3.2'],'THREAD_TX')
  self.assertIsNone(P['U2']['pins']['J1.9']);self.assertIsNone(P['U2']['pins']['J1.10'])
  for f in native_footprints():
   ref=next(x[2] for x in f if isinstance(x,list) and x[:2]==['property','Reference'])
   if ref not in P:continue
   attr=next((x[1:] for x in f if isinstance(x,list) and x[0]=='attr'),[])
   self.assertEqual('dnp' in attr,ref in ('J8','J9'))
 def test_service_clearances(self):
  def poly(a):return [(a[0],a[1]),(a[2],a[1]),(a[2],a[3]),(a[0],a[3])] if isinstance(a[0],(int,float)) else a
  def overlap(a,b):
   a,b=poly(a),poly(b)
   for p in (a,b):
    for v,w in zip(p,p[1:]+p[:1]):
     axis=(v[1]-w[1],w[0]-v[0]);aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
     if min(max(aa),max(bb))<=max(min(aa),min(bb))+1e-9:return False
   return True
  def native_boxes():
   out={}
   for f in native_footprints():
    ref=next(x[2] for x in f if isinstance(x,list) and x[:2]==['property','Reference'])
    if ref not in P:continue
    pp=P[ref];th=math.radians(pp['rotation']);boxes=[]
    for x in f:
     if not isinstance(x,list) or x[0]!='fp_rect':continue
     fields={q[0]:q[1:] for q in x[1:] if isinstance(q,list)}
     if fields.get('layer') not in (['F.CrtYd'],['B.CrtYd']):continue
     coords=[]
     a0,b0=map(float,fields['start']);a1,b1=map(float,fields['end'])
     for a,b in [(a0,b0),(a1,b0),(a1,b1),(a0,b1)]:coords.append((pp['xy'][0]+a*math.cos(th)+b*math.sin(th),pp['xy'][1]-a*math.sin(th)+b*math.cos(th)))
     boxes.append(coords)
    out[ref]=boxes
   return out
  boxes=native_boxes();mechanics=D['mechanics']
  for ref,bs in boxes.items():
   for ref2,cs in boxes.items():
    if ref>=ref2 or P[ref]['side']!=P[ref2]['side']:continue
    for b in bs:
     for c in cs:self.assertFalse(overlap(b,c),f'{ref} courtyard hits {ref2}')
  # If B would hide A's solder lands, A must be soldered before B.
  edges={r:set() for r,p in P.items() if p['fitted']}
  for a in edges:
   for b in edges:
    if P[a]['side']==P[b]['side']:continue
    for q in P[a]['pad_centers_mm']:
     halo=[q['x']-2,q['y']-2,q['x']+2,q['y']+2]
     if any(overlap(halo,bb) for bb in boxes[b]):edges[a].add(b)
  for a,ee in edges.items():
   for b in ee:self.assertFalse(P[a]['side']=='front' and P[b]['side']=='back',f'Front {a} would have to be soldered before rear {b}')
  pending={r:set(e) for r,e in edges.items()};order=[]
  while pending:
   ready=[r for r in pending if not any(r in e for e in pending.values())]
   self.assertTrue(ready,'Circular opposite-side solder obstruction')
   order.extend(ready)
   for r in ready:pending.pop(r)
  self.assertLess(order.index('J5'),order.index('U2'))
  self.assertLess(order.index('D1'),order.index('U1'))
  for ref,a in mechanics['header_mating_envelopes_mm'].items():
   for ref2,bs in boxes.items():
    if ref==ref2 or P[ref]['side']!=P[ref2]['side']:continue
    for b in bs:self.assertFalse(overlap(a,b),f'{ref} mating shell hits {ref2}')
   for ref2,b in mechanics['header_mating_envelopes_mm'].items():
    if ref!=ref2:self.assertFalse(overlap(a,b),f'{ref} shell hits {ref2} shell')
  for ref,a in mechanics['physical_usb_shells_mm'].items():
   for ref2,bs in boxes.items():
    if ref==ref2 or P[ref]['side']!=P[ref2]['side']:continue
    for b in bs:self.assertFalse(overlap(a,b),f'{ref} USB hits {ref2}')
   for ref2,b in mechanics['header_mating_envelopes_mm'].items():
    if P[ref]['side']==P[ref2]['side']:self.assertFalse(overlap(a,b),f'{ref} USB hits {ref2} shell')
   for x,y in mechanics['mounting_holes_mm']:self.assertFalse(overlap(a,[x-2.5,y-2.5,x+2.5,y+2.5]),f'{ref} USB hits support')
  for x,y in mechanics['mounting_holes_mm']:
   a=[x-2.5,y-2.5,x+2.5,y+2.5]
   for ref,bs in boxes.items():
    for b in bs:self.assertFalse(overlap(a,b),f'support hits {ref}')
   for ref,b in mechanics['header_mating_envelopes_mm'].items():self.assertFalse(overlap(a,b),f'support hits {ref} shell')
 def test_native_flat_rail_lands(self):
  expected=[[0,14.7,1.3,54.8],[46,7.7,47.5,74.3]]
  self.assertEqual(D['mechanics']['rail_copper_keepouts_mm'],expected)
  self.assertEqual(D['mechanics']['enclosure_rail_lands'],[{'id':'left','bounds_mm':[0,15,.85,54.5]},{'id':'right','bounds_mm':[46.3,8,47.5,74]}])
  found=[]
  for obj in native_tree():
   if not isinstance(obj,list) or obj[0]!='zone':continue
   fields={x[0]:x[1:] for x in obj[1:] if isinstance(x,list)}
   if 'polygon' not in fields or 'keepout' not in fields:continue
   pts=next(x[1:] for x in fields['polygon'] if x[0]=='pts');coords=[[float(p[1]),float(p[2])] for p in pts]
   xs=[p[0] for p in coords];ys=[p[1] for p in coords];bb=[min(xs),min(ys),max(xs),max(ys)]
   if bb in expected:
    k={x[0]:x[1] for x in fields['keepout']}
    for key in ['tracks','vias','pads','copperpour']:self.assertEqual(k[key],'not_allowed')
    self.assertEqual(fields['layers'],['F.Cu','B.Cu']);found.append(bb)
  self.assertEqual(sorted(found),sorted(expected))
  holes=[f for f in native_footprints() if any(isinstance(p,list) and p[:2]==['property','Reference'] and p[2].startswith('H') for p in f)]
  self.assertEqual(len(holes),1)
  self.assertTrue(any(isinstance(p,list) and p[:3]==['property','Reference','H3'] for p in holes[0]))
 def test_two_sided_placement_and_stack(self):
  for r,p in P.items():
   expected='front' if r in ('U1','U2','U3','J8','J9') else 'back'
   self.assertEqual(p['side'],expected)
   f=next(f for f in native_footprints() if any(isinstance(q,list) and q[:3]==['property','Reference',r] for q in f))
   self.assertIn(['layer','F.Cu' if expected=='front' else 'B.Cu'],f)
  stack=D['mechanics']['stack']
  self.assertEqual(stack['opposing_metal_clearance_min_mm'],1)
  self.assertEqual(stack['trimmed_tail_and_solder_max_mm'],1)
  self.assertIsNone(stack['front_module_gap_measured_mm'])
  self.assertTrue(stack['all_rear_parts_before_front'])
 def test_exact_drc_classification_and_mutations(self):
  from validate_drc import classify
  import copy
  report=json.loads((R/'checks/drc.json').read_text());native=(R/'mc1.kicad_pcb').read_text()
  self.assertEqual(classify(report,native)['result'],'pass_with_conditional_mechanical_findings')
  mutations=[]
  x=copy.deepcopy(report);x['violations'].pop();mutations.append(x)
  x=copy.deepcopy(report);x['violations'].append(copy.deepcopy(x['violations'][0]));mutations.append(x)
  x=copy.deepcopy(report);x['violations'][0]['type']='clearance';mutations.append(x)
  x=copy.deepcopy(report);x['violations'][0]['items'][0]['pos']['x']+=.1;mutations.append(x)
  x=copy.deepcopy(report);x['unconnected_items']=[{}];mutations.append(x)
  x=copy.deepcopy(report);x['schematic_parity']=[{}];mutations.append(x)
  for key in ('violations','unconnected_items','schematic_parity'):
   x=copy.deepcopy(report);del x[key];mutations.append(x)
  for x in mutations:self.assertEqual(classify(x,native)['result'],'fail')
if __name__=='__main__':unittest.main(verbosity=2)
