"""Negative controls check independently sourced external endpoint/power mappings."""
import json,unittest
from validate import assert_remote_map,ROOT
class ConnectorContract(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/'connectors.json').read_text());self.v=json.loads((ROOT.parent/'visual/connections.json').read_text())
    def pin(self,j,p):return next(pn for c in self.c['connectors'] if c['ref']==j for pn in c['pins'] if pn['number']==p)
    def test_valid(self):assert_remote_map(self.c,self.v)
    def test_wiz_wrong_j2_power_pad(self):
        self.pin('J4',1)['remote_endpoints'][0]['position']='J2.1'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_wiz_ground_instead_of_3v3(self):
        self.pin('J4',1)['remote_endpoints'][0]['pin']='GND3'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_zac_tx_rx_swap(self):
        self.pin('J8',3)['remote_endpoints'][0]['pin']='TX'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_no_5v_to_cc1101(self):
        self.pin('J7',1)['net']='+5V'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_no_poe_primary_input(self):
        self.pin('J1',1)['remote_endpoints'][0]['pin']='VINA'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_mg24_flow_control_not_swd(self):
        self.pin('J6',5)['remote_endpoints'][0]['pin']='SWCLK'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_h2_en_not_boot(self):
        self.pin('J5',5)['remote_endpoints'][0]['pin']='GPIO9'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
    def test_radar_tx_rx_swap(self):
        self.pin('J9',3)['remote_endpoints'][0]['pin']='RX'
        with self.assertRaises(AssertionError):assert_remote_map(self.c,self.v)
if __name__=='__main__':unittest.main()
