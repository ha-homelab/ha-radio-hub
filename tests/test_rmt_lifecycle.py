"""Compile the actual vendored ESP32 RMT driver against small IDF doubles.

Behavioral coverage: stale ring flush, pending/late ISR, fresh capture after TX,
idempotent ownership and fail-closed error paths. This cannot prove ESP-IDF's
interrupt synchronization on silicon; a hardware loopback test remains needed.
"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RmtLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required")
        directory = tempfile.TemporaryDirectory(prefix="rf-rmt-")
        cls.addClassCleanup(directory.cleanup)
        root = Path(directory.name)
        for name in ["esphome/components/remote_base/remote_base.h", "esphome/core/component.h",
                     "esphome/core/hal.h", "esphome/core/helpers.h", "soc/soc_caps.h",
                     "driver/gpio.h", "driver/rmt_rx.h", "esp_clk_tree.h",
                     "freertos/FreeRTOS.h", "freertos/portmacro.h"]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#include "rmt_stubs.h"\n')
        (root / "esphome/core/log.h").write_text(
            "\n".join(f"#define {name}(...)" for name in
                      ["ESP_LOGCONFIG", "ESP_LOGE", "ESP_LOGW", "ESP_LOGVV", "LOG_PIN"]))
        cls.binary = root / "rmt-test"
        flags = ["-std=c++17", "-DUSE_ESP32", "-Wall", "-Wextra", "-Wno-unused-variable"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                      "-fno-omit-frame-pointer", "-g", "-O1"]
        build = subprocess.run([
            compiler, *flags, "-I", str(root), "-I", str(ROOT / "tests/native"),
            "-I", str(ROOT / "firmware/components/remote_receiver"),
            str(ROOT / "tests/native/rmt_harness.cpp"), "-o", str(cls.binary)
        ], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)

    def scenario(self, name):
        process = subprocess.run([str(self.binary), name], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_flushes_pre_tx_capture_and_accepts_fresh_post_tx_capture(self):
        self.scenario("flush")

    def test_pending_isr_during_disable_cannot_rearm_or_publish(self):
        self.scenario("pending_isr")

    def test_repeated_suspend_resume_keeps_one_channel_buffer_and_callback(self):
        self.scenario("idempotent")

    def test_listener_starting_tx_invalidates_the_old_ring_snapshot(self):
        self.scenario("listener_flush")

    def test_enable_error_does_not_arm_failed_channel(self):
        self.scenario("enable_error")

    def test_receive_error_disables_failed_component(self):
        self.scenario("receive_error")

    def test_disable_error_fails_closed(self):
        self.scenario("disable_error")


if __name__ == "__main__":
    unittest.main()
