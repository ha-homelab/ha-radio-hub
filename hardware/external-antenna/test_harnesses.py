"""Electrical meaning and physical orientation of the public harness lookup."""
import copy
import csv
import importlib.util
from io import StringIO
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mc2_harness_render', HERE / 'render.py')
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class HarnessContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((HERE / 'harnesses.json').read_text())
        self.connectors = json.loads((HERE / 'cad/connectors.json').read_text())['connectors']
        self.parts = json.loads((HERE / 'cad/design.json').read_text())['parts']
        self.harnesses = {h['ref']: h for h in self.data['harnesses']}

    def validate(self):
        render.validate_harnesses(self.data, self.connectors, self.parts)

    def test_all_33_connections_agree_with_native_schematic_and_board(self):
        self.validate()
        self.assertEqual(sum(len(h['pins']) for h in self.harnesses.values()), 33)

    def test_missing_duplicate_and_additional_connectors_are_rejected(self):
        original = copy.deepcopy(self.data['harnesses'])
        for harnesses in [original[:-1], original + [original[0]], original + [{**original[0], 'ref': 'J8'}]]:
            with self.subTest(refs=[h['ref'] for h in harnesses]):
                self.data['harnesses'] = harnesses
                with self.assertRaisesRegex(ValueError, 'exactly once'):
                    self.validate()

    def test_wrong_voltage_and_missing_or_duplicate_wire_are_rejected(self):
        for change in ['voltage', 'missing', 'duplicate']:
            with self.subTest(change=change):
                self.setUp()
                h = self.harnesses['J4']
                if change == 'voltage':
                    h['pins'][0]['net'] = '+5V'
                elif change == 'missing':
                    h['pins'].pop()
                else:
                    h['pins'].append(h['pins'][0])
                with self.assertRaisesRegex(ValueError, 'native connector/schematic'):
                    self.validate()

    def test_stale_schematic_or_physical_pad_map_is_rejected(self):
        next(p for p in self.parts if p['ref'] == 'J4')['pins']['1'] = '+5V'
        with self.assertRaisesRegex(ValueError, 'schematic'):
            self.validate()
        self.setUp()
        next(p for p in self.connectors if p['ref'] == 'J4')['pad_centers_mm'][0]['net'] = '+5V'
        with self.assertRaisesRegex(ValueError, 'physical pad'):
            self.validate()

    def test_zac93_uses_remapped_physical_pins_not_a_straight_ribbon(self):
        pins = self.harnesses['J4']['pins']
        self.assertEqual([p['device_pin'] for p in pins], ['1', '6', '9', '8', '10'])
        pins[3]['device_pin'] = '4'
        with self.assertRaisesRegex(ValueError, 'ZAC93 physical pin remap'):
            self.validate()

    def test_uart_receiver_names_match_direction_at_both_ends(self):
        j3 = self.harnesses['J3']['pins']
        j4 = self.harnesses['J4']['pins']
        self.assertEqual((j3[4]['net'], j4[3]['net']), ('ZWAVE_RX', 'ZWAVE_RX'))
        self.assertEqual((j3[4]['direction'], j4[3]['direction']), ('to_carrier', 'to_device'))
        self.assertEqual((j3[5]['net'], j4[4]['net']), ('ZWAVE_TX', 'ZWAVE_TX'))
        self.assertEqual((j3[5]['direction'], j4[4]['direction']), ('to_device', 'to_carrier'))
        self.assertEqual([p['direction'] for p in self.harnesses['J6']['pins'][2:]], ['to_device', 'to_carrier'])

    def test_regulator_input_and_output_flow_in_opposite_directions(self):
        pins = self.harnesses['J2']['pins']
        self.assertEqual((pins[0]['net'], pins[0]['direction']), ('+5V', 'to_device'))
        self.assertEqual((pins[2]['net'], pins[2]['direction']), ('+3V3', 'to_carrier'))
        self.assertIn('VIN', self.harnesses['J7']['pins'][1]['device_contact'])

    def test_documented_sections_exist(self):
        source = (HERE / self.data['source']).resolve()
        self.assertTrue(source.is_file())
        headings = re.findall(r'^#{1,6} (.+)$', source.read_text(), re.M)
        anchors = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
        for h in self.harnesses.values():
            self.assertIn(h['source_anchor'], anchors)

    def test_csv_preserves_all_endpoints_and_device_contacts(self):
        _, _, csv_text = render.render_harnesses(self.data, self.connectors)
        rows = list(csv.DictReader(StringIO(csv_text)))
        expected = [(h['ref'], p['carrier_pin'], p['net'], p['device_contact']) for h in self.data['harnesses'] for p in h['pins']]
        self.assertEqual([(r['Carrier connector'], r['Carrier pad'], r['Net'], r['Device contact']) for r in rows], expected)

    def test_connector_diagram_uses_physical_coordinates_even_if_list_is_reordered(self):
        connector = copy.deepcopy(next(p for p in self.connectors if p['ref'] == 'J4'))
        connector['pad_centers_mm'].reverse()
        svg = ET.fromstring(render.connector_diagram(connector))
        labels = {node.text: (float(node.attrib['x']), float(node.attrib['y'])) for node in svg.findall('text')}
        positions = {p['number']: (p['x'], p['y']) for p in connector['pad_centers_mm']}
        for pin, coords in positions.items():
            self.assertAlmostEqual(labels[pin][0] - labels['1'][0], (coords[0] - positions['1'][0]) * 14)
            self.assertAlmostEqual(labels[pin][1] - labels['1'][1], (coords[1] - positions['1'][1]) * 14)
        square = svg.find('rect')
        self.assertAlmostEqual(float(square.attrib['x']) + 9, labels['1'][0])
        connector['side'] = 'back'
        self.connectors = [connector if c['ref'] == 'J4' else c for c in self.connectors]
        with self.assertRaisesRegex(ValueError, 'front-view'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
