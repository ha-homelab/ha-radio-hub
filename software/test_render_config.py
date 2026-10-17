"""Check rendering boundaries and protocol safety without hardware or Docker."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("render_config.py")


class RenderConfigTests(unittest.TestCase):
    def render(self, output, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--hub-ip", "192.0.2.10", "--ha-ip", "192.0.2.20",
             "--thread-device", "/dev/serial/by-id/usb-Thread_TEST",
             "--zigbee-device", "/dev/serial/by-id/usb-Zigbee_TEST", "--output", str(output), *extra],
            text=True, capture_output=True,
        )

    def test_output_binds_one_radio_to_one_allowed_client(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.render(temp)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = (Path(temp) / "ser2net.yaml").read_text()
            self.assertIn("accepter: tcp,192.0.2.10,6638", config)
            self.assertIn('remaddr: "192.0.2.20,0"', config)
            self.assertIn("max-connections: 1", config)
            self.assertIn("115200n81,local,rtscts", config)
            self.assertNotIn("banner:", config)
            self.assertNotIn("telnet", config)
            self.assertEqual((Path(temp) / "hub.env").stat().st_mode & 0o777, 0o600)

    def test_rejects_same_radio_and_shell_injection(self):
        with tempfile.TemporaryDirectory() as temp:
            for extra in (
                ("--zigbee-device", "/dev/serial/by-id/usb-Thread_TEST"),
                ("--interface", "eth0;echo bad"),
                ("--hub-ip", "0.0.0.0"),
                ("--thread-device", "/dev/ttyACM0"),
                ("--thread-device", "/dev/serial/by-id/usb-x\nINJECTED=1"),
            ):
                with self.subTest(extra=extra):
                    self.assertNotEqual(self.render(temp, *extra).returncode, 0)


if __name__ == "__main__":
    unittest.main()
