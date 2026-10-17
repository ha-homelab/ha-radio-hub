"""Check rendering boundaries and protocol safety without hardware or Docker."""
import subprocess
import sys
import tempfile
import unittest
import json
import os
import shutil
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
                ("--thread-device", "/dev/serial/by-id/.."),
                ("--zigbee-device", "/dev/serial/by-path/."),
                ("--thread-device", "/dev/serial/by-id/usb-x\nINJECTED=1"),
            ):
                with self.subTest(extra=extra):
                    self.assertNotEqual(self.render(temp, *extra).returncode, 0)

    def test_rerender_replaces_files_privately_without_following_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "runtime"
            self.assertEqual(self.render(output).returncode, 0)
            for path in output.iterdir():
                path.chmod(0o644)
            self.assertEqual(self.render(output).returncode, 0)
            self.assertTrue(all(path.stat().st_mode & 0o777 == 0o600 for path in output.iterdir()))
            outside = root / "unrelated.yaml"
            outside.write_text("must remain unchanged")
            (output / "ser2net.yaml").unlink()
            (output / "ser2net.yaml").symlink_to(outside)
            before = (output / "hub.env").read_bytes()
            result = self.render(output, "--ha-ip", "192.0.2.30")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(outside.read_text(), "must remain unchanged")
            self.assertEqual((output / "hub.env").read_bytes(), before)

    @unittest.skipUnless(shutil.which("docker"), "Docker Compose CLI is not installed")
    def test_compose_uses_custom_output_without_creating_missing_bind_source(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "operator's custom runtime"
            result = self.render(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            environment = dict(os.environ)
            for name in ("HUB_LAN_IP", "HA_IP", "INFRA_IF", "THREAD_SERIAL_DEVICE",
                         "ZIGBEE_SERIAL_DEVICE", "SER2NET_CONFIG"):
                environment.pop(name, None)
            result = subprocess.run(
                ["docker", "compose", "--env-file", str(output / "hub.env"), "-f",
                 str(SCRIPT.with_name("compose.yaml")), "config", "--format", "json"],
                text=True, capture_output=True, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            mount = json.loads(result.stdout)["services"]["zigbee"]["volumes"][0]
            self.assertEqual(mount["source"], str((output / "ser2net.yaml").resolve()))
            self.assertTrue(mount["read_only"])
            self.assertFalse(mount.get("bind", {}).get("create_host_path", False))


if __name__ == "__main__":
    unittest.main()
