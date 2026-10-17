import copy,importlib.util,unittest,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('integrated_validation',Path(__file__).with_name('validate.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ElectricalTests(unittest.TestCase):
 def setUp(self):self.parts=copy.deepcopy(v.source_parts())
 def p(self,ref):return next(p for p in self.parts if p['ref']==ref)
 def test_current_contract(self):self.assertEqual(len(v.electrical(self.parts)),113)
 def test_mg24_flow_control_swap(self):
  self.p('U3')['pins']['5']='mg24_cts'
  with self.assertRaisesRegex(ValueError,'U3.5'):v.electrical(self.parts)
 def test_5v_on_h2(self):
  self.p('U2')['pins']['3']='5v_fused'
  with self.assertRaises(ValueError):v.electrical(self.parts)
 def test_poe_primary_escape(self):
  self.p('R1')['pins']['1']='POE_12'
  with self.assertRaisesRegex(ValueError,'isolated domain'):v.electrical(self.parts)
 def test_w5500_reserved_pin_must_be_grounded(self):
  self.p('U4')['pins']['23']=None
  with self.assertRaisesRegex(ValueError,'U4.23'):v.electrical(self.parts)
 def test_usb_backfeed(self):
  self.p('U9')['pins']['2']='5v_fused'
  with self.assertRaisesRegex(ValueError,'backfeed'):v.electrical(self.parts)
 def test_1a_buck_substitution(self):
  self.p('U8')['model']='TSR 1-2433'
  with self.assertRaisesRegex(ValueError,'power review'):v.electrical(self.parts)
 def test_missing_rx_coupling(self):
  self.p('C34')['model']='0R'
  with self.assertRaisesRegex(ValueError,'support network'):v.electrical(self.parts)
 def test_s3_gpio_is_not_header_number(self):
  self.p('U1')['pins']['37']='ld2450_tx'
  with self.assertRaisesRegex(ValueError,'S3 role'):v.electrical(self.parts)
class NetFormatTests(unittest.TestCase):
 def test_kicad10_string_net(self):
  self.assertEqual(v.net_name(['net','gnd'],{}),'gnd')
 def test_legacy_numeric_net(self):
  self.assertEqual(v.net_name(['net','1'],{'1':'gnd'}),'gnd')
 def test_legacy_inline_net(self):
  self.assertEqual(v.net_name(['net','1','gnd'],{}),'gnd')
 def test_no_connect(self):
  self.assertTrue(v.disconnected(v.net_name(None,{})))
  self.assertTrue(v.disconnected('unconnected-(U1-NC-Pad2)'))
  self.assertFalse(v.disconnected('gnd'))
class BoardContractTests(unittest.TestCase):
 def setUp(self):
  self.parts=v.electrical(v.source_parts())
  self.board=v.parse_sexpr((v.ROOT/'integrated.kicad_pcb').read_text())
  self.board=[x for x in self.board if not isinstance(x,list) or x[0] not in ('segment','via')]
  # One synthetic track lets the net/coordinate checker run; these tests do not
  # claim that the fixture is electrically routed or DRC-clean.
  self.board.append(['segment',['start','80','80'],['end','81','80'],['width','0.2'],['layer','B.Cu'],['net','gnd']])
 def check(self):
  def emit(x):return '('+' '.join(emit(y) for y in x)+')' if isinstance(x,list) else json.dumps(x)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'fixture.kicad_pcb';path.write_text(emit(self.board));return v.pcb_connectivity(path,self.parts)
 def footprint(self,ref):
  return next(f for f in v.children(self.board,'footprint') if any(p[1:3]==['Reference',ref] for p in v.children(f,'property')))
 def test_current_physical_net_and_coordinate_contract(self):
  self.assertEqual(self.check()['segments'],1)
 def test_usb_shell_wrong_pad_name(self):
  self.parts['J2']['pins']['S1']=self.parts['J2']['pins'].pop('SH')
  with self.assertRaisesRegex(ValueError,'Unexpected/missing PCB pad'):self.check()
 def test_unused_buck_pin_accidentally_wired(self):
  pad=next(p for p in v.children(self.footprint('U8'),'pad') if p[1]=='PG')
  old=v.child(pad,'net')
  if old:pad.remove(old)
  pad.append(['net','3v3'])
  with self.assertRaisesRegex(ValueError,'NC unexpectedly wired'):self.check()
 def test_stale_connector_coordinate(self):
  at=v.child(self.footprint('J4'),'at');at[1]=str(float(at[1])+1)
  with self.assertRaisesRegex(ValueError,'coordinates differ|placement differs'):self.check()
 def test_signal_on_ground_reference_layer(self):
  v.child(self.board[-1],'layer')[1]='In1.Cu'
  with self.assertRaisesRegex(ValueError,'dedicated ground'):self.check()
if __name__=='__main__':unittest.main()
