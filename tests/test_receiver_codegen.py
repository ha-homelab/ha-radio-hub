"""Generate real ESPHome sources to verify counted local receiver registrations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReceiverCodegenTest(unittest.TestCase):
    def test_listeners_and_dumpers_receive_storage_on_both_supported_targets(self):
        for board in ("esp32dev", "esp32-s3-devkitc-1"):
            with self.subTest(board=board), tempfile.TemporaryDirectory(prefix="rf-codegen-") as directory:
                root = Path(directory)
                config = root / "fixture.yaml"
                config.write_text(f"""esphome:
  name: receiver-count-fixture
esp32:
  board: {board}
  framework:
    type: esp-idf
    version: 5.5.5
external_components:
  - source:
      type: local
      path: {json.dumps(str(ROOT / 'firmware/components'))}
    components: [remote_receiver]
remote_receiver:
  id: receiver
  pin: GPIO5
  dump: [raw, rc_switch]
  on_raw:
    then:
      - lambda: '(void) x;'
  on_rc_switch:
    then:
      - lambda: '(void) x;'
binary_sensor:
  - platform: remote_receiver
    name: Counted sensor
    rc_switch_raw:
      code: '00000001'
      protocol: 1
""")
                result = subprocess.run([sys.executable, "-m", "esphome", "compile", "--only-generate", str(config)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                build = root / ".esphome/build/receiver-count-fixture"
                defines = (build / "src/esphome/core/defines.h").read_text()
                generated = (build / "src/main.cpp").read_text()
                sdkconfig = (build / "sdkconfig.receiver-count-fixture").read_text()
                self.assertIn("# ESPHOME_IDF_VERSION=5.5.5\n", sdkconfig)
                self.assertIn("#define REMOTE_BASE_LISTENER_COUNT 3\n", defines)
                self.assertIn("#define REMOTE_BASE_DUMPER_COUNT 2\n", defines)
                self.assertEqual(generated.count("->register_listener("), 3)
                self.assertEqual(generated.count("->register_dumper("), 2)
                # The compatibility port retains the patched runtime lifecycle.
                receiver = build / "src/esphome/components/remote_receiver"
                for name in ("remote_receiver.h", "remote_receiver_rmt.cpp"):
                    self.assertEqual((receiver / name).read_bytes(),
                                     (ROOT / "firmware/components/remote_receiver" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
