"""Checks that the visual export does not drop physical pins or hide unknowns."""
from pathlib import Path
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('atlas_builder', ROOT / 'build.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'connections.json').read_text())

    def test_all_documented_pins_have_rows_including_nc(self):
        for component in self.data['components']:
            with self.subTest(component=component['id']):
                self.assertEqual({p['id'] for p in component['pins']},
                                 {r['pin']['id'] for r in builder.rows_for(component, self.data)})

    def test_unverified_pin_is_not_presented_as_verified(self):
        zac = next(c for c in self.data['components'] if c['id'] == 'zac93')
        self.assertIn('confirm exact board revision', builder.physical(zac['pins'][0]))
        cc = next(c for c in self.data['components'] if c['id'] == 'cc1101')
        self.assertIn('verify module markings', builder.physical(cc['pins'][0]))

    def test_all_diagrams_are_valid_accessible_svg(self):
        for component in self.data['components']:
            with self.subTest(component=component['id']):
                document = ET.fromstring(builder.diagram(component, self.data))
                self.assertEqual(document.attrib['role'], 'img')
                self.assertIsNotNone(document.find('{http://www.w3.org/2000/svg}title'))
                self.assertIsNotNone(document.find('{http://www.w3.org/2000/svg}desc'))

    def test_committed_exports_match_data_and_generator(self):
        for name, data in builder.generate().items():
            with self.subTest(name=name):
                self.assertEqual((ROOT / 'generated' / name).read_bytes(), data)

    def test_board_connector_data_survives_offline_packaging(self):
        output = builder.generate()
        match = re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>',
                          output['index.html'].decode(), re.S)
        packaged = json.loads(match.group(1))
        self.assertEqual({b['id'] for b in packaged['boards']}, {'carrier', 'integrated', 'mg24-adapter', 'diy'})
        for board in packaged['boards']:
            self.assertIn('overview_file', board, 'Every PCB needs its native assembly drawing')
            self.assertIn(board['overview_file'], output)
            directory = 'carrier/mg24-adapter' if board['id'] == 'mg24-adapter' else board['id']
            original = json.loads((ROOT.parent / directory / 'connectors.json').read_text())
            self.assertEqual(board['connectors'], original['connectors'])
            for connector in board['connectors']:
                self.assertTrue(connector['viewing_convention'])
                self.assertTrue(connector['pad_centers_mm'])
                self.assertTrue({str(p['number']) for p in connector['pins']}.issubset(
                    {str(p['number']) for p in connector['pad_centers_mm']}))

    def test_diy_xh_connector_and_common_net_roles(self):
        output=builder.generate()
        match=re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>',output['index.html'].decode(),re.S)
        boards={b['id']:b for b in json.loads(match.group(1))['boards']}
        diy={c['ref']:c for c in boards['diy']['connectors']}
        carrier={c['ref']:c for c in boards['carrier']['connectors']}
        self.assertEqual(set(diy),set(carrier))
        self.assertEqual(diy['J10']['model'],'B4B-XH-A')
        self.assertEqual(diy['J10']['mating_model'],'XHP-4')
        self.assertEqual(carrier['J10']['model'],'BM04B-SRSS-TB')
        self.assertIn('not the C0 JST SH/QT',boards['diy']['wiring_note'])
        for ref in diy:
            current={str(p['number']):p['net'] for p in diy[ref]['pins']}
            original={str(p['number']):p['net'] for p in carrier[ref]['pins']}
            self.assertEqual(current,original,ref)
        expected=sum(len(json.loads((ROOT.parent / directory / 'connectors.json').read_text())['connectors'])
                     for directory in ['carrier','carrier/mg24-adapter','integrated','diy'])
        self.assertEqual(sum(len(b['connectors']) for b in boards.values()),expected)

    def test_physical_reference_files_survive_offline_packaging(self):
        output = builder.generate()
        for name in ('s3', 'h2', 'mg24', 'wiz850io', 'pololu'):
            filename = name + '-contacts.svg'
            self.assertEqual(output[filename], (ROOT / 'physical' / 'generated' / filename).read_bytes())


if __name__ == '__main__':
    unittest.main()
