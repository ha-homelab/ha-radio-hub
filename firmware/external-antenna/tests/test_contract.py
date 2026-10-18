"""MC2 board, shared validator and preparation regressions; no hardware access."""
import ast
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_hardware_and_firmware_use_identical_pins(self):
        firmware = json.loads((ROOT / 'pin-plan.json').read_text())
        hardware = json.loads((ROOT.parents[1] / 'hardware/external-antenna/cad/pin-plan.json').read_text())
        self.assertEqual({k: v for k, v in firmware.items() if k != 'status'},
                         {k: v for k, v in hardware.items() if k != 'status'})
        used = {v['gpio'] for v in firmware['assignments'].values()}
        for unavailable in ('onboard_usb_uart', 'onboard_rgb_led_revision_dependent', 'octal_psram', 'unused_straps'):
            self.assertFalse(used.intersection(firmware['reserved'][unavailable]))
        self.assertEqual(firmware['flash_bytes'], 8 * 1024 * 1024)
        self.assertEqual(firmware['psram_bytes'], 8 * 1024 * 1024)

    def test_shared_uart_validator_accepts_mc2_and_rejects_extra_or_wrong_uart(self):
        # Execute the actual validation function with only ESPHome's schema context
        # stubbed, so this check also runs without a host ESPHome installation.
        path = ROOT.parent / 'low-power/components/low_power_otbr/__init__.py'
        function = next(node for node in ast.parse(path.read_text()).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'final_validate')
        module = ast.Module(body=[function], type_ignores=[])
        full = {'esp32': {'framework': {'type': 'esp-idf', 'version': '5.5.5'}},
                'network': {'enable_ipv6': True}}
        namespace = {'fv': SimpleNamespace(full_config=SimpleNamespace(get=lambda: full)),
                     'cv': SimpleNamespace(Invalid=ValueError), '__version__': '2026.9.1'}
        exec(compile(module, str(path), 'exec'), namespace)
        validate = namespace['final_validate']
        for tx, rx in ((8, 40), (8, 38), (39, 40)):
            full['uart'] = [{'tx_pin': {'number': tx}, 'rx_pin': {'number': rx}}]
            self.assertEqual(validate({'fixture': True}), {'fixture': True})
        for uarts in ([], [{'tx_pin': {'number': 15}, 'rx_pin': {'number': 16}}],
                      [{'tx_pin': {'number': 8}, 'rx_pin': {'number': 40}}] * 2):
            full['uart'] = uarts
            with self.assertRaisesRegex(ValueError, 'Only LD2450'):
                validate({})


if __name__ == '__main__':
    unittest.main()
