"""Negative controls for electrical and pin-namespace mistakes in the atlas."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('atlas_validation',HERE/'validate.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((HERE/'connections.json').read_text())
    def pin(self,cid,pid):
        return next(p for c in self.data['components'] if c['id']==cid for p in c['pins'] if p['id']==pid)
    def net(self,nid):
        return next(n for n in self.data['nets'] if n['id']==nid)
    def bad(self):
        with self.assertRaises(ValueError): module.validate(self.data)
    def test_model_and_firmware_match(self):
        self.assertEqual(module.validate(self.data)['firmware_roles'],26)
    def firmware_fixture(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root=Path(directory.name)
        for name in ['hardware/low-power/pinmap.json','firmware/low-power/proof.yaml',
                     'firmware/low-power/hub.yaml','firmware/packages/rf-airbridge.yaml',
                     'firmware/low-power/mg24/config.json']:
            path=root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(module.ROOT/name,path)
        return root
    def test_changed_rf_default_substitutions_are_rejected(self):
        for name, pin, error in [('rf_cs_pin',15,'RF CS mismatch'),
                                 ('rf_rx_pin',5,'RF RX mismatch'),
                                 ('rf_tx_pin',4,'RF transmitter drive contract changed')]:
            with self.subTest(pin=name):
                root=self.firmware_fixture()
                path=root/'firmware/packages/rf-airbridge.yaml'
                source=path.read_text()
                self.assertIn(f'{name}: GPIO{pin}',source)
                path.write_text(source.replace(f'{name}: GPIO{pin}',f'{name}: GPIO6'))
                with self.assertRaisesRegex(ValueError,error):
                    module.validate(self.data,root=root)
    def test_target_rf_overrides_take_precedence_over_package_defaults(self):
        for name, pin, error in [('rf_cs_pin',15,'RF CS mismatch'),
                                 ('rf_rx_pin',5,'RF RX mismatch'),
                                 ('rf_tx_pin',4,'RF transmitter drive contract changed')]:
            with self.subTest(pin=name):
                root=self.firmware_fixture()
                package=root/'firmware/packages/rf-airbridge.yaml'
                package.write_text(package.read_text().replace(f'{name}: GPIO{pin}',f'{name}: GPIO6'))
                proof=root/'firmware/low-power/proof.yaml'
                proof.write_text(proof.read_text().replace('substitutions:\n',f'substitutions:\n  {name}: GPIO{pin}\n',1))
                self.assertEqual(module.validate(self.data,root=root)['firmware_roles'],26)
                hub=root/'firmware/low-power/hub.yaml'
                hub.write_text(f'substitutions:\n  {name}: GPIO7\n\n'+hub.read_text())
                with self.assertRaisesRegex(ValueError,error):
                    module.validate(self.data,root=root)
    def test_invented_module_header_is_rejected(self):
        self.pin('cc1101','GDO2')['physical']['position']='7'
        self.bad()
    def test_gpio_is_not_physical_pad(self):
        self.pin('s3','GPIO43')['physical']['position']='43'
        self.bad()
    def test_5v_on_logic_is_rejected(self):
        self.net('3v3')['nominal_voltage_v']=5
        self.bad()
    def test_pushpull_on_shared_rf_line_is_rejected(self):
        self.pin('s3','GPIO4')['direction']='output'
        self.bad()
    def test_rts_cts_swap_is_rejected(self):
        for nid in ('mg24_rts','mg24_cts'):
            member=next(m for m in self.net(nid)['members'] if m['component']=='mg24')
            member['pin']='RTS' if member['pin']=='CTS' else 'CTS'
        self.bad()
    def test_h2_missing_ground_pad_is_rejected(self):
        comp=next(c for c in self.data['components'] if c['id']=='h2')
        comp['pins']=[p for p in comp['pins'] if p['id']!='GND53']
        self.net('gnd')['members']=[m for m in self.net('gnd')['members'] if m!={'component':'h2','pin':'GND53'}]
        self.bad()
    def test_mg24_external_reset_pullup_is_rejected(self):
        self.data['support_parts'].append({'id':'BAD','kind':'resistor','value':10000,'unit':'ohm','between':['mg24_reset','3v3']})
        self.bad()
    def test_primary_ground_connection_is_rejected(self):
        self.net('gnd')['members'].append({'component':'pd','pin':'VINB'})
        self.bad()
    def test_wrong_irq_pullup_is_rejected(self):
        next(p for p in self.data['support_parts'] if p['id']=='R_sc16_irq')['value']=10000
        self.bad()
    def test_two_nets_on_one_pin_are_rejected(self):
        self.net('5v_fused')['members'].append({'component':'s3','pin':'3V3'})
        self.bad()

if __name__=='__main__':unittest.main()
