"""Real ESPHome codegen and native execution of the ESP-NOW freshness policy.

No radio, broker, Home Assistant, installation secret or hardware is accessed.
"""
import importlib.metadata
import importlib.util
import base64
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "firmware/espnow"
SPEC = importlib.util.spec_from_file_location("espnow_validate", SOURCE / "validate.py")
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)


class TaggedLoader(yaml.SafeLoader):
    pass


TaggedLoader.add_constructor("!secret", lambda loader, node: loader.construct_scalar(node))


class EspnowEvidenceTests(unittest.TestCase):
    def test_final_wifi_and_coexistence_flags_are_both_required(self):
        required = VALIDATE.REQUIRED_RADIO_SDKCONFIG
        VALIDATE.require_options(dict(required), required)
        for key in required:
            for replacement in (None, "n"):
                broken = dict(required)
                if replacement is None:
                    del broken[key]
                else:
                    broken[key] = replacement
                with self.subTest(key=key, replacement=replacement):
                    with self.assertRaisesRegex(RuntimeError, key):
                        VALIDATE.require_options(broken, required)

    def test_build_recipe_hashes_reject_changed_prepared_inputs(self):
        with tempfile.TemporaryDirectory(prefix="espnow-recipe-") as directory:
            prepared = Path(directory) / "espnow"
            shutil.copytree(SOURCE, prepared, ignore=shutil.ignore_patterns(
                ".esphome", "__pycache__", "secrets.yaml"))
            hashes = VALIDATE.verify_recipe(prepared)
            self.assertIn("hub-radio.yaml", hashes)
            self.assertIn("hub-sensors.yaml", hashes)
            self.assertIn("prepare.py", hashes)
            self.assertIn("validate.py", hashes)
            self.assertNotIn("secrets.yaml", hashes)
            path = prepared / "hub-radio.yaml"
            path.write_text(path.read_text() + "\n# changed after preparation\n")
            with self.assertRaisesRegex(RuntimeError, "hub-radio.yaml"):
                VALIDATE.verify_recipe(prepared)

    def test_real_freshness_lambdas_start_offline_and_never_revive_without_a_heartbeat(self):
        config = yaml.load((SOURCE / "hub-sensors.yaml").read_text(), Loader=TaggedLoader)
        compiler = shutil.which(os.environ.get("CXX", "c++"))
        self.assertIsNotNone(compiler, "A native C++ compiler is required")
        functions = []
        for provider in ("climate", "probe", "contact"):
            heartbeat = next(sensor for sensor in config["sensor"]
                             if sensor.get("id") == f"espnow_{provider}_uptime")
            on_value = heartbeat["on_value"]["then"][0]["lambda"]
            online = next(sensor["lambda"] for sensor in config["binary_sensor"]
                          if sensor.get("name") == f"ESP-NOW {provider.title()} Online")
            age = next(sensor["lambda"] for sensor in config["sensor"]
                       if sensor.get("name") == f"ESP-NOW {provider.title()} Last Seen Age")
            seen = f"espnow_{provider}_seen"
            last = f"espnow_{provider}_last_ms"
            globals_by_id = {item["id"]: item for item in config["globals"]}
            for state_id in (seen, last):
                self.assertFalse(globals_by_id[state_id]["restore_value"])
            seen_initial = globals_by_id[seen]["initial_value"]
            last_initial = globals_by_id[last]["initial_value"]
            body = f"""
bool {seen} = {seen_initial};
{globals_by_id[last]['type']} {last} = {last_initial};
void receive_{provider}(float x) {{ {on_value} }}
bool online_{provider}() {{ {online} }}
float age_{provider}() {{ {age} }}
void test_{provider}() {{
  clock_ms = 0;
  assert(!online_{provider}());
  assert(std::isnan(age_{provider}()));
  receive_{provider}(NAN);
  assert(!online_{provider}());
  receive_{provider}(INFINITY);
  assert(!online_{provider}());
  clock_ms = 1234;
  receive_{provider}(1.0f);
  assert(online_{provider}());
  assert(age_{provider}() == 0.0f);
  clock_ms = 1234 + 89999;
  assert(online_{provider}());
  clock_ms = 1234 + 90000;
  assert(!online_{provider}());
  receive_{provider}(NAN);
  assert(!online_{provider}());
  clock_ms = uint64_t{{1}} + UINT32_MAX + 1234;
  assert(!online_{provider}());
  assert(age_{provider}() > 4294967.0f);
  receive_{provider}(2.0f);
  assert(online_{provider}());
  clock_ms = UINT32_MAX - 999;
  receive_{provider}(3.0f);
  clock_ms = uint64_t{{1}} + UINT32_MAX + 1000;
  assert(online_{provider}());
  assert(age_{provider}() == 2.0f);
  clock_ms = uint64_t{{1}} + UINT32_MAX + 90000;
  assert(!online_{provider}());
}}
"""
            functions.append(re.sub(r"\bid\((\w+)\)", r"\1", body))
        source = """#include <cassert>
#include <cmath>
#include <cstdint>
uint64_t clock_ms = 0;
uint64_t millis_64() { return clock_ms; }
""" + "\n".join(functions) + "\nint main() { test_climate(); test_probe(); test_contact(); }\n"
        with tempfile.TemporaryDirectory(prefix="espnow-freshness-") as directory:
            path = Path(directory)
            (path / "test.cpp").write_text(source)
            command = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror"]
            if os.environ.get("RF_CPP_SANITIZERS") == "1":
                command.extend(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])
            subprocess.run(command + [str(path / "test.cpp"), "-o", str(path / "test")], check=True)
            subprocess.run([str(path / "test")], check=True)


class EspnowCodegenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.metadata.version("esphome") != VALIDATE.ESPHOME_VERSION:
            raise AssertionError(f"Install firmware/requirements.txt: ESPHome {VALIDATE.ESPHOME_VERSION} is required")
        cls.temporary = tempfile.TemporaryDirectory(prefix="espnow-codegen-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.firmware = Path(cls.temporary.name) / "firmware"
        shutil.copytree(ROOT / "firmware", cls.firmware, ignore=shutil.ignore_patterns(
            ".esphome", "__pycache__", "secrets.yaml", "*.pyc"))
        # --only-generate needs a declared component path, not the actual OTBR
        # server implementation. The full compile runner uses pinned preparation.
        server = cls.firmware / "low-power/generated/esp_ot_br_server"
        server.mkdir(parents=True, exist_ok=True)
        (server / "CMakeLists.txt").write_text("idf_component_register()\n")
        cls.directory = cls.firmware / "espnow"
        example = yaml.safe_load((SOURCE / "secrets.example.yaml").read_text())
        example.update({
            "api_encryption_key": base64.b64encode(bytes(range(32))).decode(),
            "ota_password": "codegen-only-no-device",
            "mqtt_username": "codegen-only",
            "mqtt_password": "codegen-only-no-broker",
        })
        for name in ("climate", "probe", "contact"):
            example[f"espnow_{name}_key"] = f"public-codegen-fixture-{name}-not-installation-key"
        (cls.directory / "secrets.yaml").write_text(yaml.safe_dump(example))
        cls.results = {}
        for kind, (filename, name) in VALIDATE.PROFILES.items():
            result = subprocess.run(
                [sys.executable, "-m", "esphome", "compile", "--only-generate", str(cls.directory / filename)],
                capture_output=True, text=True,
            )
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.results[kind] = VALIDATE.verify_codegen(cls.directory, kind)

    def test_opt_in_hub_retains_entire_mc2d_pin_and_bus_contract(self):
        result = self.results["hub"]
        self.assertTrue(result["generated_pin_checks"]["all_assigned_gpio_verified"])
        self.assertEqual(result["generated_pin_checks"]["ble_slots"], 3)
        self.assertTrue(result["generated_pin_checks"]["shared_spi"])
        self.assertFalse(result["compiled"])
        self.assertFalse(result["hardware_tested"])

    def test_every_satellite_and_receiver_use_matching_encrypted_provider_ids(self):
        def generated(kind):
            return (self.directory / ".esphome/build" / VALIDATE.PROFILES[kind][1] / "src/main.cpp").read_text()

        hub = generated("hub")
        self.assertIn("espnow_sensors->set_ping_pong_enable(true);", hub)
        self.assertIn("espnow_sensors->set_ping_pong_recycle_time(60);", hub)
        for kind in ("climate", "probe", "contact"):
            main = generated(kind)
            self.assertIn("satellite_transport->set_rolling_code_enable(true);", main)
            self.assertIn("satellite_transport->set_encryption_key(", main)
            self.assertIn(f'espnow_sensors->set_provider_encryption("espnow-{kind}",', hub)
            self.assertIn('satellite_transport->add_sensor("node_uptime", satellite_uptime);', main)
            self.assertFalse(self.results[kind]["compiled"])


if __name__ == "__main__":
    unittest.main()
