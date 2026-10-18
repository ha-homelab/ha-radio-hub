"""Independent dimension/pin-order checks for transcribed manufacturer drawings."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class MechanicalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "mechanics.json").read_text())

    def test_h2_pin_order_and_grid(self):
        h = self.data["modules"]["Waveshare_ESP32_H2_Zero_M"]
        self.assertEqual(h["row_spacing"], 15.24)
        self.assertEqual(h["pitch"], 2.54)
        self.assertEqual(h["left_top_to_bottom"], [str(n) for n in range(1, 10)])
        self.assertEqual(h["right_top_to_bottom"], [str(n) for n in range(18, 9, -1)])
        self.assertEqual(h["pin_names"]["17"], "GPIO23_RX")
        self.assertEqual(h["pin_names"]["18"], "GPIO24_TX")
        self.assertEqual(len(set(h["left_top_to_bottom"] + h["right_top_to_bottom"])), 18)

    def test_wiz_power_and_nc(self):
        w = self.data["modules"]["WIZnet_WIZ850io"]
        self.assertEqual(w["row_spacing"], 20.32)
        self.assertEqual(w["pin_names"]["J2.1"], "GND")
        self.assertEqual(w["pin_names"]["J2.2"], "3V3")
        self.assertEqual(w["pin_names"]["J2.3"], "3V3")
        self.assertEqual(w["pin_names"]["J2.4"], "NC")
        self.assertEqual(w["pin_names"]["J2.5"], "RESET_N")
        self.assertEqual(w["pin_names"]["J2.6"], "MISO")


if __name__ == "__main__":
    unittest.main()
