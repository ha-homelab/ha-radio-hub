#!/usr/bin/env python3
"""Independent assertions for mechanical coordinates, power boundaries and pin map."""
import unittest,json,math
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text());P={p['ref']:p for p in D['parts']}
def pad(r,n):return next(p for p in P[r]['pad_centers_mm'] if p['number']==n)
class CarrierTests(unittest.TestCase):
 def test_dimensions(self):
  self.assertEqual((D['board']['width_mm'],D['board']['height_mm'],D['board']['copper_layers']),(160,100,2))
 def test_module_row_centers(self):
  for ref,left,right,spacing in [('U1','J1.1','J3.1',22.86),('U2','J1.1','J3.1',22.86),('U3','1','14',15.24),('U4','J1.1','J2.1',20.32)]:
   a,b=pad(ref,left),pad(ref,right);self.assertAlmostEqual(math.dist((a['x'],a['y']),(b['x'],b['y'])),spacing,places=4)
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
if __name__=='__main__':unittest.main(verbosity=2)
