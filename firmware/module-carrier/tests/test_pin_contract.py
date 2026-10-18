"""Keep the active firmware pin manifest tied to the physical carrier."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT.parents[1] / "hardware/module-carrier/cad"
spec = importlib.util.spec_from_file_location("mc1_pin_contract", ROOT / "contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class PinContractTests(unittest.TestCase):
    def test_active_manifests_match_hardware_and_reject_old_h2_uart(self):
        firmware = json.loads((ROOT / "pin-plan.json").read_text())
        carrier = json.loads((CAD / "nano-pin-plan.json").read_text())
        # Only the human-readable status differs between the two manifests.
        self.assertEqual({k: v for k, v in firmware.items() if k != "status"},
                         {k: v for k, v in carrier.items() if k != "status"})
        self.assertEqual(contract.h2_pin_contract(),
                         {"rx": 23, "tx": 24, "baud": 460800, "reset": "EN", "boot": 9})
        parts = {p["ref"]: p for p in json.loads((CAD / "design.json").read_text())["parts"]}
        for host, radio, net in (("thread_tx", "J3.3", "THREAD_RX"),
                                  ("thread_rx", "J3.2", "THREAD_TX")):
            self.assertEqual(parts["U1"]["pins"][firmware["assignments"][host]["header_pin"]], net)
            self.assertEqual(parts["U2"]["pins"][radio], net)
        self.assertIsNone(parts["U2"]["pins"]["J1.9"])
        self.assertIsNone(parts["U2"]["pins"]["J1.10"])
        # A stale manifest must stop preparation/verification before any build
        # can be described as compatible with the assembled network updater.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for rx, tx in ((4, 5), (24, 23)):
                with self.subTest(rx=rx, tx=tx):
                    stale = json.loads(json.dumps(firmware))
                    stale["external_controller_contract"]["h2"].update(rx=rx, tx=tx)
                    (path / "pin-plan.json").write_text(json.dumps(stale))
                    with patch.object(contract, "STUDY", path), self.assertRaises(RuntimeError):
                        contract.h2_pin_contract()


if __name__ == "__main__":
    unittest.main()
