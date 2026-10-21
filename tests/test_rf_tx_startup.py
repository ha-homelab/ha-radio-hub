"""Exercise actual RF startup wrapper against the pinned IDF pad-routing order."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RFStartupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required")
        temp = tempfile.TemporaryDirectory(prefix="rf-startup-")
        cls.addClassCleanup(temp.cleanup)
        root = Path(temp.name)
        for name in ("esphome/core/defines.h", "driver/gpio.h", "esp_private/gpio.h", "driver/rmt_tx.h", "esp_idf_version.h"):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#include "rf_tx_startup_stubs.h"\n')
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g", "-O1"]
        cls.binary = root / "startup"
        proc = subprocess.run([compiler, *flags, "-I", str(root), "-I", str(ROOT / "tests/native"),
                               "-I", str(ROOT / "firmware/components/rf_tx_startup"),
                               str(ROOT / "tests/native/rf_tx_startup_harness.cpp"), "-o", str(cls.binary)],
                              capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(proc.stdout + proc.stderr)

    def scenario(self, name):
        result = subprocess.run([str(self.binary), name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_old_allocator_reproduces_low_drive(self): self.scenario("unguarded")
    def test_init_level_alone_still_drives_pushpull_high(self): self.scenario("init_only")
    def test_guard_releases_before_routing_and_preserves_other_fields(self): self.scenario("safe")
    def test_other_gpio_is_unmodified(self): self.scenario("other_gpio")
    def test_pushpull_configuration_is_rejected_before_gpio_changes(self): self.scenario("reject_pushpull")
    def test_inverted_configuration_is_rejected_before_gpio_changes(self): self.scenario("reject_inverted")
    def test_null_handle_is_rejected_before_gpio_changes(self): self.scenario("null_handle")
    def test_null_config_preserves_original_error(self): self.scenario("null_config")
    def test_latch_failure_does_not_allocate(self): self.scenario("level_error")
    def test_open_drain_failure_does_not_allocate(self): self.scenario("od_error")
    def test_allocator_error_propagates_without_drive(self): self.scenario("allocation_error")


class RFStartupConfigTest(unittest.TestCase):
    def setUp(self):
        import ast
        import types
        from unittest.mock import Mock
        source = ROOT / "firmware/components/rf_tx_startup/__init__.py"
        tree = ast.parse(source.read_text())
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name in ("transmitter_config", "final_validate")]
        self.pin = {"number": 25, "inverted": False, "mode": {"open_drain": True}}
        self.full = {"esp32": {"framework": {"type": "esp-idf", "version": "5.5.5"}},
                     "remote_transmitter": [{"id": "rf", "pin": self.pin}], "cc1101": [{"id": "radio"}]}
        self.digest = Mock()
        self.digest.hexdigest.return_value = "reviewed-source"
        self.context = {"cv": types.SimpleNamespace(Invalid=ValueError),
                        "fv": types.SimpleNamespace(full_config=types.SimpleNamespace(get=lambda: self.full)),
                        "esp32": types.SimpleNamespace(get_esp32_variant=lambda: "ESP32", VARIANT_ESP32="ESP32", VARIANT_ESP32S3="ESP32S3"),
                        "__version__": "2026.9.1", "SOURCE_SHA256": "reviewed-source", "CC1101_SHA256": "reviewed-source",
                        "Path": Mock(), "remote_transmitter": types.SimpleNamespace(__file__="unused"),
                        "cc1101": types.SimpleNamespace(__file__="unused"),
                        "hashlib": types.SimpleNamespace(sha256=lambda _: self.digest)}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), self.context)

    def validate(self):
        return self.context["final_validate"]({"transmitter_id": "rf", "radio_id": "radio"})

    def test_selected_transmitter_is_accepted(self):
        self.assertEqual(self.validate(), {"transmitter_id": "rf", "radio_id": "radio"})

    def test_unreviewed_source_is_rejected(self):
        self.digest.hexdigest.return_value = "changed"
        with self.assertRaisesRegex(ValueError, "upstream RMT transmitter changed"):
            self.validate()

    def test_unreviewed_framework_is_rejected(self):
        self.full["esp32"]["framework"]["version"] = "5.5.6"
        with self.assertRaisesRegex(ValueError, "requires ESPHome"):
            self.validate()

    def test_unreviewed_esphome_is_rejected(self):
        self.context["__version__"] = "2026.10.0"
        with self.assertRaisesRegex(ValueError, "requires ESPHome"):
            self.validate()

    def test_pushpull_and_inverted_are_rejected(self):
        self.pin["mode"]["open_drain"] = False
        with self.assertRaisesRegex(ValueError, "non-inverted open-drain"):
            self.validate()
        self.pin["mode"]["open_drain"] = True
        self.pin["inverted"] = True
        with self.assertRaisesRegex(ValueError, "non-inverted open-drain"):
            self.validate()

    def test_cc1101_cannot_take_ownership_of_the_transmitter_pin(self):
        self.full["cc1101"][0]["gdo0_pin"] = {"number": 25}
        with self.assertRaisesRegex(ValueError, "separate GDO2"):
            self.validate()
        self.full["cc1101"][0].pop("gdo0_pin")
        self.full["cc1101"][0]["packet_mode"] = True
        with self.assertRaisesRegex(ValueError, "asynchronous mode"):
            self.validate()

    def test_wrong_transmitter_reference_is_rejected(self):
        self.full["remote_transmitter"][0]["id"] = "other"
        with self.assertRaisesRegex(ValueError, "exactly one transmitter"):
            self.validate()


if __name__ == "__main__": unittest.main()
