"""Behavioral regression controls for actual bottom-copper + wire connectivity."""
import copy,unittest
from continuity import verify,separation
import design

def fixture():
 c=[dict(id='J1.1',net='signal__1',a=[0,0],b=[0,0],radius=1),dict(id='T1.1',net='signal__1',a=[3,0],b=[3,0],radius=1),dict(id='trace1',net='signal__1',a=[0,0],b=[3,0],radius=.3),dict(id='J2.1',net='signal__2',a=[13,0],b=[13,0],radius=1),dict(id='T2.1',net='signal__2',a=[10,0],b=[10,0],radius=1),dict(id='trace2',net='signal__2',a=[10,0],b=[13,0],radius=.3)]
 w=[dict(ref='W1',logical_net='signal',from_terminal='T1',to_terminal='T2',from_net='signal__1',to_net='signal__2',awg=26,route_mm=[[3,0],[10,0]],route_length_mm=7,cut_length_mm=21,strip_each_end_mm=5)]
 return c,{'J1.1':'signal','J2.1':'signal'},w
class ContinuityTests(unittest.TestCase):
 def test_real_wire_completes_separate_copper_islands(self):self.assertEqual(verify(*fixture())['wire_links'],1)
 def test_missing_wire_is_open(self):
  c,p,w=fixture()
  with self.assertRaisesRegex(AssertionError,'OPEN ASSEMBLY'):verify(c,p,[])
 def test_cut_bottom_track_is_open(self):
  c,p,w=fixture();c=[x for x in c if x['id']!='trace1']
  with self.assertRaisesRegex(AssertionError,'disconnected bottom island'):verify(c,p,w)
 def test_wrong_logical_signal_detected(self):
  c,p,w=fixture();p['J2.1']='other'
  with self.assertRaisesRegex(AssertionError,'SHORT ASSEMBLY'):verify(c,p,w)
 def test_wire_metadata_cannot_disguise_power(self):
  c,p,w=fixture();w[0]['logical_net']='+3V3'
  with self.assertRaisesRegex(AssertionError,'logical net label'):verify(c,p,w)
 def test_undersized_power_wire(self):
  c,p,w=fixture()
  for x in c:x['net']=x['net'].replace('signal','+3V3')
  p={k:'+3V3' for k in p}
  for k in ['logical_net','from_net','to_net']:w[0][k]=w[0][k].replace('signal','+3V3')
  with self.assertRaisesRegex(AssertionError,'undersized'):verify(c,p,w)
 def test_duplicate_wire_reference(self):
  c,p,w=fixture();w+=copy.deepcopy(w)
  with self.assertRaisesRegex(AssertionError,'duplicate wire'):verify(c,p,w)
 def test_wrong_endpoint_coordinates(self):
  c,p,w=fixture();w[0]['route_mm']=[[4,0],[11,0]]
  with self.assertRaisesRegex(AssertionError,'endpoints'):verify(c,p,w)
 def test_short_wire_cut(self):
  c,p,w=fixture();w[0]['cut_length_mm']=10
  with self.assertRaisesRegex(AssertionError,'too short'):verify(c,p,w)
 def test_diagonal_crossing_is_short(self):
  c,p,w=fixture();c+=[dict(id='cross',net='other__1',a=[1,-2],b=[1,2],radius=.3)]
  with self.assertRaisesRegex(AssertionError,'clearance/short'):verify(c,p,w)
 def test_reversed_supply_connector_is_detected(self):
  c,p,w=fixture()
  for x in c:x['net']=x['net'].replace('signal','+3V3')
  p={k:'+3V3' for k in p}
  for k in ['logical_net','from_net','to_net']:w[0][k]=w[0][k].replace('signal','+3V3')
  w[0]['awg']=24
  c += [dict(id='J1.2',net='GND__1',a=[0,10],b=[0,10],radius=1),dict(id='J2.2',net='GND__1',a=[13,10],b=[13,10],radius=1),dict(id='ground',net='GND__1',a=[0,10],b=[13,10],radius=.6)]
  p.update({'J1.2':'GND','J2.2':'GND'})
  verify(c,p,w)
  p['J2.1'],p['J2.2']=p['J2.2'],p['J2.1']
  with self.assertRaisesRegex(AssertionError,'SHORT ASSEMBLY|OPEN ASSEMBLY'):verify(c,p,w)
 def test_more_than_two_wire_ends_rejected(self):
  c,p,w=fixture();w += [dict(w[0],ref='W2'),dict(w[0],ref='W3')]
  with self.assertRaisesRegex(AssertionError,'more than 2 ends'):verify(c,p,w)
 def test_assembly_length_must_follow_physical_path(self):
  c,p,w=fixture();w[0]['route_length_mm']=6
  with self.assertRaisesRegex(AssertionError,'incorrect wire length'):verify(c,p,w)
 def test_changed_stripping_length_requires_review(self):
  c,p,w=fixture();w[0]['strip_each_end_mm']=10
  with self.assertRaisesRegex(AssertionError,'strip length'):verify(c,p,w)
 def raised_fixture(self):
  c,p,w=fixture();c[1]['id']='U1.11'
  w[0].update(from_terminal='E1',from_pin='U1.11',to_pin='T2.1',from_height_mm=4,to_height_mm=0,height_allowance_mm=4,cut_length_mm=25)
  return c,p,w
 def test_real_raised_pin_replaces_no_drilled_hole(self):
  self.assertEqual(verify(*self.raised_fixture())['wire_links'],1)
 def test_raised_joint_cannot_move_to_unapproved_header(self):
  c,p,w=self.raised_fixture();c[1]['id']='J3.11';w[0]['from_pin']='J3.11'
  with self.assertRaisesRegex(AssertionError,'unapproved component'):verify(c,p,w)
 def test_raised_joint_height_is_part_of_contract(self):
  c,p,w=self.raised_fixture();w[0].update(from_height_mm=3,height_allowance_mm=3,cut_length_mm=24)
  with self.assertRaisesRegex(AssertionError,'incorrect joint height'):verify(c,p,w)
 def test_raised_joint_needs_cut_length_allowance(self):
  c,p,w=self.raised_fixture();w[0]['height_allowance_mm']=0
  with self.assertRaisesRegex(AssertionError,'incorrect height allowance'):verify(c,p,w)
 def test_only_one_wire_on_raised_pin(self):
  c,p,w=self.raised_fixture();w += [dict(w[0],ref='W2')]
  with self.assertRaisesRegex(AssertionError,'1 on adapter pin'):verify(c,p,w)
 def test_circle_square_clearance(self):
  self.assertAlmostEqual(separation(dict(rect=[0,0,2,2]),dict(a=[4,1],b=[4,1],radius=1)),1)
 def test_original_pin_contract(self):
  original={(o['ref'],p):n for o in design.c0.parts for p,n in o['pins'].items() if not o['ref'].startswith('#') and p not in ['MP1','MP2']}
  current={(o['ref'],p):n for o in design.parts for p,n in o['pins'].items() if not o['ref'].startswith('#')}
  self.assertEqual(original,current)
 def test_no_spi_or_uart_pin_reassignment(self):
  parts={p['ref']:p for p in design.parts}
  self.assertEqual(parts['J4']['pins']['1'],'+3V3');self.assertEqual(parts['J4']['pins']['9'],'GND')
  self.assertEqual(parts['J8']['pins'],{'1':'+3V3','2':'GND','3':'zac93_tx','4':'zac93_rx','5':'GND'})
  self.assertEqual(parts['U1']['pins']['13'],'shared_spi_sclk');self.assertEqual(parts['U1']['pins']['22'],'GND')
if __name__=='__main__':unittest.main()
