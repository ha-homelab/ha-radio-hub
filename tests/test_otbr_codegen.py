"""Verify custom OTBR requests the crypto removed by ESPHome's default trimming."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OtbrCodegenTest(unittest.TestCase):
    def test_thread_crypto_and_dtls_server_are_not_trimmed(self):
        with tempfile.TemporaryDirectory(prefix="otbr-codegen-") as directory:
            root = Path(directory)
            server = root / "server"
            server.mkdir()
            (server / "CMakeLists.txt").write_text("idf_component_register()\n")
            config = root / "fixture.yaml"
            config.write_text(f"""esphome:
  name: otbr-crypto-fixture
esp32:
  board: esp32-s3-devkitc-1
  framework:
    type: esp-idf
    version: 5.5.5
psram:
  mode: octal
ethernet:
  type: W5500
  clk_pin: GPIO13
  mosi_pin: GPIO11
  miso_pin: GPIO12
  cs_pin: GPIO14
  interrupt_pin: GPIO10
  reset_pin: GPIO9
network:
  enable_ipv6: true
uart:
  tx_pin: GPIO39
  rx_pin: GPIO40
  baud_rate: 256000
external_components:
  - source:
      type: local
      path: {json.dumps(str(ROOT / 'firmware/low-power/components'))}
    components: [low_power_otbr]
low_power_otbr:
  server_component_path: {json.dumps(str(server))}
  tx_pin: GPIO17
  rx_pin: GPIO18
  reset_pin: GPIO47
  boot_pin: GPIO48
""")
            result = subprocess.run([sys.executable, "-m", "esphome", "compile", "--only-generate", str(config)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            build = root / ".esphome/build/otbr-crypto-fixture"
            source = (build / "sdkconfig.otbr-crypto-fixture").read_text()
            options = dict(line.split("=", 1) for line in source.splitlines() if line.startswith("CONFIG_"))
            self.assertIn("# ESPHOME_IDF_VERSION=5.5.5\n", source)
            # Required features may retain IDF's enabled defaults. The actual
            # post-Kconfig values are also checked after every full CI build.
            for name in ("TLS_SERVER_AND_CLIENT", "ECP_C", "CCM_C", "ECDSA_DETERMINISTIC"):
                self.assertNotEqual(options.get("CONFIG_MBEDTLS_" + name), "n", name)
            self.assertNotEqual(options.get("CONFIG_MBEDTLS_TLS_CLIENT_ONLY"), "y")
            self.assertNotEqual(options.get("CONFIG_MBEDTLS_TLS_DISABLED"), "y")
            self.assertEqual(options["CONFIG_MBEDTLS_SSL_PROTO_DTLS"], "y")
            self.assertEqual(options["CONFIG_OPENTHREAD_COMMISSIONER"], "y")
            self.assertEqual(options["CONFIG_OPENTHREAD_JOINER"], "y")


if __name__ == "__main__":
    unittest.main()
