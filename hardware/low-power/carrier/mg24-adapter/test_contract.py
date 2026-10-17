"""Independent negative controls for the adapter's externally defined interfaces."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('adapter_validation', ROOT/'validate.py')
validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)
spec=importlib.util.spec_from_file_location('adapter_design', ROOT/'design.py')
design=importlib.util.module_from_spec(spec);spec.loader.exec_module(design)
class ContractTest(unittest.TestCase):
    def setUp(self):
        self.parts=copy.deepcopy(design.parts)
        self.catalog=json.loads((ROOT/'connectors.json').read_text())
        self.visual=json.loads((ROOT.parent.parent/'visual/connections.json').read_text())
        self.carrier=json.loads((ROOT.parent/'connectors.json').read_text())
    def check(self):validation.assert_contract(self.parts,self.catalog,self.visual,self.carrier)
    def reject(self):
        with self.assertRaises(AssertionError):self.check()
    def test_valid(self):self.check()
    def test_uart_reversal(self):
        self.parts[0]['pins']['12'],self.parts[0]['pins']['13']=self.parts[0]['pins']['13'],self.parts[0]['pins']['12'];self.reject()
    def test_flow_control_reversal(self):
        self.parts[0]['pins']['5'],self.parts[0]['pins']['6']=self.parts[0]['pins']['6'],self.parts[0]['pins']['5'];self.reject()
    def test_missing_ground(self):self.parts[0]['pins']['34']=None;self.reject()
    def test_missing_nc(self):del self.parts[0]['pins']['33'];self.reject()
    def test_rfout_grounded(self):self.parts[0]['pins']['33']='GND';self.reject()
    def test_other_module_variant(self):self.parts[0]['model']='MGM240PB22VNA3';self.reject()
    def test_reset_external_high(self):self.catalog['connectors'][1]['pins'][4]['voltage_v']=3.3;self.reject()
    def test_reversed_cable_power(self):self.catalog['connectors'][0]['pins'][0]['net']='GND';self.reject()
    def test_boot_pulldown(self):next(p for p in self.parts if p['ref']=='R1')['pins']['1']='GND';self.reject()
if __name__=='__main__':unittest.main()
