"""Orientation regression checks against the cited manufacturer drawings.

These are contact-reference checks, not a PCB DRC or physical fit test.
"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('physical_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
MODULES = {m['id']: m for m in json.loads((ROOT / 'catalog.json').read_text())['modules']}


class ContactOrientationTest(unittest.TestCase):
    def pads(self, name):
        return {p['id']: p for p in build.geometry(MODULES[name])}

    def test_s3_side_to_bottom_transitions_and_ground(self):
        # Fig 3-1 numbering: 14 left contacts, 12 bottom, 14 right.
        p = self.pads('s3')
        expected = {'1': [.25, 7.49], '14': [.25, 24],
                    '15': [2.015, 25.25], '26': [15.985, 25.25],
                    '27': [17.75, 24], '40': [17.75, 7.49]}
        for number, xy in expected.items():
            self.assertEqual(p[number]['center_mm'], xy)
        thermal = [p for p in build.geometry(MODULES['s3']) if p['id'] == '41']
        self.assertTrue(any(p['center_mm'] == [7.5, 15.21] and
                            p['size_mm'] == [3.9, 3.9] for p in thermal))
        self.assertTrue(any(p.get('drill_mm') == .2 for p in thermal))

    def test_h2_corner_numbers_and_inner_row_direction(self):
        p = self.pads('h2')
        expected = {'1': [.7, 7], '11': [.7, 15], '12': [1.8, 15.9],
                    '24': [11.4, 15.9], '25': [12.5, 15], '35': [12.5, 7],
                    '36': [11.4, 6.1], '48': [1.8, 6.1],
                    '50': [12.55, 6.05], '51': [12.55, 15.95],
                    '52': [.65, 15.95], '53': [.65, 6.05]}
        for number, xy in expected.items():
            self.assertEqual(p[number]['center_mm'], xy)
        self.assertEqual(sum(p['id'] == '49' for p in build.geometry(MODULES['h2'])), 9)

    def test_mgm_top_view_not_bottom_view(self):
        p = self.pads('mg24')
        self.assertEqual(p['1']['center_mm'], [.8, .7])
        self.assertEqual(p['36']['center_mm'], [12.1, .7])
        self.assertEqual(p['14']['center_mm'], [.8, 13.7])
        self.assertEqual(p['15']['center_mm'], [2.95, 14.2])
        self.assertEqual(p['22']['center_mm'], [9.95, 14.2])
        self.assertEqual(p['23']['center_mm'], [12.1, 13.7])
        self.assertEqual(p['1']['size_mm'], [2.4, .6])
        self.assertEqual(p['15']['size_mm'], [.6, 2.4])

    def test_wiz_j2_power_order_and_row_orientation(self):
        p = self.pads('wiz850io')
        self.assertEqual([p[f'J2.{i}']['signal'] for i in range(1, 7)],
                         ['GND', '3V3D', '3V3D', 'NC', 'RSTn', 'MISO'])
        self.assertEqual(p['J1.1']['center_mm'], [1.34, 6.4])
        self.assertEqual(p['J2.1']['center_mm'], [21.66, 6.4])
        self.assertEqual(p['J2.6']['center_mm'], [21.66, 19.1])
        self.assertTrue(all(v['size_mm'] == [0, 0] and v['shape'] == 'contact_center'
                            for v in p.values()))  # No invented carrier drills.

    def test_pololu_top_view_and_separate_module_holes(self):
        p = self.pads('pololu')
        for i, name in enumerate(['PG', 'EN', 'VIN', 'GND', 'VOUT']):
            self.assertEqual(p[name]['center_mm'], [round(1.27 + 2.54*i, 6), 16.53])
            self.assertEqual(p[name]['shape'], 'module_hole')
            self.assertEqual(p[name]['size_mm'], [1.02, 1.02])
        self.assertEqual(p['GND2']['center_mm'], [1.27, 5.84])
        self.assertEqual(p['MH1']['center_mm'], [2.3, 2.3])
        self.assertEqual(p['MH2']['center_mm'], [15.5, 15.5])
        self.assertEqual(p['MH1']['size_mm'], [2.18, 2.18])

    def test_published_outputs_are_current_and_sources_are_tracked(self):
        outputs = build.products()
        self.assertEqual(set(outputs), {p.name for p in (ROOT / 'generated').iterdir() if p.is_file()})
        for name, content in outputs.items():
            self.assertEqual((ROOT / 'generated' / name).read_text(), content, name)
        manifest = json.loads(outputs['manifest.json'])
        self.assertIn('catalog.json', manifest['source_sha256'])
        self.assertIn('build.py', manifest['source_sha256'])


if __name__ == '__main__':
    unittest.main()
