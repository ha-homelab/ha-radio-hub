"""MC2 board, shared validator and preparation regressions; no hardware access."""
import ast
import subprocess
import sys
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_mc2_validation_ignores_a_preloaded_mc1_contract(self):
        # Both revisions may be inspected in one process. MC1's generic module
        # name must not make MC2 call the older two-argument verifier.
        script = """
import importlib
from pathlib import Path
import sys
mc2 = Path(sys.argv[1])
sys.path.insert(0, str(mc2.parent / "module-carrier"))
legacy = importlib.import_module("contract")
sys.path.insert(0, str(mc2))
validator = importlib.import_module("validate")
contract = importlib.import_module("mc2_contract")
assert validator.verify_generated is contract.verify_generated
assert validator.verify_generated is not legacy.verify_generated
assert Path(contract.__file__).resolve() == mc2 / "mc2_contract.py"
"""
        subprocess.run([sys.executable, "-c", script, str(ROOT)], check=True)

    def test_hardware_and_firmware_use_identical_pins(self):
        firmware = json.loads((ROOT / 'pin-plan.json').read_text())
        hardware = json.loads((ROOT.parents[1] / 'hardware/external-antenna/cad/pin-plan.json').read_text())
        self.assertEqual({k: v for k, v in firmware.items() if k != 'status'},
                         {k: v for k, v in hardware.items() if k != 'status'})
        used = {v['gpio'] for v in firmware['assignments'].values()}
        for unavailable in ('onboard_usb_uart', 'flash', 'psram'):
            self.assertFalse(used.intersection(firmware['reserved'][unavailable]))
        self.assertNotIn(0, used)
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
        for tx, rx in ((8, 40), (8, 38), (39, 40), (23, 18)):
            full['uart'] = [{'tx_pin': {'number': tx}, 'rx_pin': {'number': rx}}]
            self.assertEqual(validate({'fixture': True}), {'fixture': True})
        for uarts in ([], [{'tx_pin': {'number': 15}, 'rx_pin': {'number': 16}}],
                      [{'tx_pin': {'number': 8}, 'rx_pin': {'number': 40}}] * 2):
            full['uart'] = uarts
            with self.assertRaisesRegex(ValueError, 'Only LD2450'):
                validate({})
        full['uart'] = [{'tx_pin': {'number': 23}, 'rx_pin': {'number': 18}}]
        full['logger'] = {'baud_rate': 115200}
        with self.assertRaisesRegex(ValueError, 'UART logging must be disabled'):
            validate({})

    def test_classic_image_header_rejects_wrong_chip_revision_and_flash(self):
        sys.path.insert(0, str(ROOT))
        from mc2_contract import verify_app_header
        import struct
        image = bytearray(24)
        image[0] = 0xE9
        image[3] = 0x30
        struct.pack_into('<H', image, 15, 300)
        self.assertEqual(verify_app_header(image)['soc'], 'ESP32')
        for offset, value, message in ((12, 9, 'classic ESP32'), (15, 0, 'ECO V3'), (3, 0x20, '8 MB')):
            broken = bytearray(image)
            broken[offset] = value
            with self.assertRaisesRegex(RuntimeError, message):
                verify_app_header(broken)


if __name__ == '__main__':
    unittest.main()
