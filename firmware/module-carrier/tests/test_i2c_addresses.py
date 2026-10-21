"""Exercise the manufacturer's decoded I2C block, not only the UART1 address."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

COMPONENT = Path(__file__).resolve().parents[1] / "components/wk2132_uart"
SPEC = importlib.util.spec_from_file_location("wk2132_address_plan", COMPONENT / "address_plan.py")
ADDRESS_PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADDRESS_PLAN)


class AddressPlanTests(unittest.TestCase):
    def validate(self, address, device_addresses=(), other_bus=False):
        bridge = {"id": "bridge", "i2c_id": "expansion", "address": address}
        sensors = [{"id": f"sensor_{i}", "i2c_id": "other" if other_bus else "expansion", "address": value}
                   for i, value in enumerate(device_addresses)]
        full = {"wk2132_uart": bridge, "sensor": sensors}
        ADDRESS_PLAN.validate_address_plan(bridge, full)

    def test_previous_bme_defaults_collide_even_when_uart2_disabled(self):
        for address in (0x76, 0x77):
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, "overlaps"):
                self.validate(0x70, [address])

    def test_selected_dip_positions_leave_both_bme_addresses_free(self):
        self.validate((1 << 6) | (0 << 5) | 0x10, [0x76, 0x77])

    def test_every_decoded_channel_and_fifo_address_is_reserved(self):
        for base in (0x10, 0x30, 0x50, 0x70):
            for suffix in range(8):
                with self.subTest(base=base, suffix=suffix), self.assertRaisesRegex(ValueError, "overlaps"):
                    self.validate(base, [base + suffix])

    def test_block_boundaries_do_not_reject_adjacent_addresses(self):
        for base in (0x10, 0x30, 0x50, 0x70):
            self.validate(base, [base - 1, base + 8])

    def test_separate_bus_is_not_an_electrical_collision(self):
        self.validate(0x70, [0x76, 0x77], other_bus=True)

    def test_uart1_register_address_must_match_dip_encoding(self):
        for base in (0x11, 0x51, 0x52, 0x57, 0x60, 0x76):
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, "UART1 register"):
                self.validate(base)

    def test_standalone_historical_base_is_still_supported(self):
        self.validate(0x70)

    def test_real_final_validator_applies_address_check(self):
        # Execute the production final validator with only framework context
        # replaced: the address plan must actually be invoked during validation.
        path = COMPONENT / "__init__.py"
        function = next(node for node in ast.parse(path.read_text()).body
                        if isinstance(node, ast.FunctionDef) and node.name == "final_validate")
        bridge = {"id": "bridge", "i2c_id": "expansion", "address": 0x70}
        full = {"wk2132_uart": bridge, "sensor": [
            {"id": "bme", "i2c_id": "expansion", "address": 0x77}]}
        frequencies = []
        namespace = {
            "cv": SimpleNamespace(Invalid=ValueError),
            "fv": SimpleNamespace(full_config=SimpleNamespace(get=lambda: full)),
            "i2c": SimpleNamespace(final_validate_device_schema=lambda *a, **kw:
                                   lambda c: frequencies.append(kw)),
            "validate_address_plan": ADDRESS_PLAN.validate_address_plan,
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
        with self.assertRaisesRegex(ValueError, "overlaps"):
            namespace["final_validate"](bridge)
        bridge["address"] = 0x50
        self.assertIs(namespace["final_validate"](bridge), bridge)
        self.assertEqual(frequencies, [{"min_frequency": "400kHz", "max_frequency": "400kHz"}])


if __name__ == "__main__":
    unittest.main()
