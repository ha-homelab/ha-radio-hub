"""Fault-injection tests for the offboard regulator's electrical boundaries."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mc2_power_design', HERE / 'power_design.py')
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class PowerContractTests(unittest.TestCase):
    def setUp(self):
        self.data = power.read_json(HERE / 'power-design.json')
        self.parts = power.read_json(HERE / 'cad/design.json')['parts']
        self.connectors = power.read_json(HERE / 'cad/connectors.json')['connectors']
        self.harnesses = power.read_json(HERE / 'harnesses.json')['harnesses']

    def validate(self):
        return power.validate(self.data, self.parts, self.connectors, self.harnesses)

    def test_present_power_contract_and_peripheral_reserve(self):
        self.assertEqual(self.validate(), {'reserve_ma': 400, 'rated_ma': 1000, 'hardware_measured': False})
        power.validate_companions(self.data, power.read_json(HERE.parents[1] / 'mechanical/full-hub/components.json'), power.read_json(HERE / 'procurement.json'))

    def test_reversed_sip_pinout_is_rejected(self):
        self.data['regulator']['pin_map']['1'] = 'VOUT'
        with self.assertRaisesRegex(ValueError, 'SIP pin map'):
            self.validate()

    def test_physical_pad_or_harness_voltage_swap_is_rejected(self):
        j2 = next(p for p in self.connectors if p['ref'] == 'J2')
        j2['pad_centers_mm'][0]['net'] = '+3V3'
        with self.assertRaisesRegex(ValueError, 'physical pad'):
            self.validate()
        self.setUp()
        j2 = next(p for p in self.harnesses if p['ref'] == 'J2')
        j2['pins'][0]['device_pin'] = '3'
        with self.assertRaisesRegex(ValueError, 'public harness'):
            self.validate()

    def test_radio_regulator_join_and_new_unbudgeted_load_are_rejected(self):
        next(p for p in self.parts if p['ref'] == 'U2')['pins']['4'] = '+3V3'
        with self.assertRaisesRegex(ValueError, 'local regulator'):
            self.validate()
        self.setUp()
        self.parts.append({'ref': 'EXTRA', 'pins': {'1': '+3V3'}})
        with self.assertRaisesRegex(ValueError, 'consumers changed'):
            self.validate()

    def test_after_diode_input_and_reduced_voltage_limit_are_rejected(self):
        self.data['input_connection']['before_radio_isolation_diodes'] = False
        with self.assertRaisesRegex(ValueError, 'before radio diodes'):
            self.validate()
        self.setUp()
        self.data['acceptance']['input_min_v'] = 4.0
        with self.assertRaisesRegex(ValueError, 'undervoltage'):
            self.validate()

    def test_missing_input_capacitor_or_reversed_polarity_is_rejected(self):
        self.data['input_capacitor']['capacitance_uf'] = 0
        with self.assertRaisesRegex(ValueError, 'capacitor missing'):
            self.validate()
        self.setUp()
        self.data['input_capacitor']['positive_regulator_pin'] = '2'
        with self.assertRaisesRegex(ValueError, 'polarity'):
            self.validate()

    def test_budget_overload_and_false_qualification_are_rejected(self):
        self.data['rail_loads'][0]['engineering_reserve_ma'] = 900
        with self.assertRaisesRegex(ValueError, 'reserve total'):
            self.validate()
        self.setUp()
        self.data['hardware_measured'] = True
        with self.assertRaisesRegex(ValueError, 'measured qualification'):
            self.validate()

    def test_insulated_link_short_and_missing_ground_link_are_rejected(self):
        self.data['perfboard']['links'][0]['to'] = 'C3'
        with self.assertRaisesRegex(ValueError, 'shorts power nets'):
            self.validate()
        self.setUp()
        self.data['perfboard']['links'].pop(3)
        with self.assertRaisesRegex(ValueError, 'disconnected pads'):
            self.validate()

    def test_regenerated_svg_is_current_and_has_two_views(self):
        rendered = power.render_perfboard(self.data)
        self.assertEqual(rendered, (HERE / 'power-perfboard.svg').read_text())
        parsed = ET.fromstring(rendered)
        texts = [p.text for p in parsed.iter('{http://www.w3.org/2000/svg}text')]
        self.assertTrue(any('COMPONENT SIDE' in text for text in texts))
        self.assertTrue(any('SOLDER SIDE' in text for text in texts))
        self.assertTrue(any('Crossing wires do NOT join' in text for text in texts))


if __name__ == '__main__':
    unittest.main()
