"""Run the actual Zigbee TCP worker against loopback sockets and a UART model.

This checks session isolation/backpressure, not ESP-IDF timing or physical CTS.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ZigbeeTcpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="zigbee-tcp-contract-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / "test"
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required")
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([
            compiler, *flags,
            "-I", str(ROOT / "tests/native/zigbee_stubs"),
            "-I", str(ROOT / "firmware/low-power/components/zigbee_tcp"),
            str(ROOT / "tests/native/zigbee_tcp_harness.cpp"),
            "-o", str(cls.binary),
        ], check=True, timeout=60)

    def run_scenario(self, scenario):
        subprocess.run([str(self.binary), scenario], check=True, timeout=15)

    def test_duplex_partial_io_and_backpressure(self):
        self.run_scenario("duplex")

    def test_only_one_client_owns_uart(self):
        self.run_scenario("exclusive")

    def test_disconnect_clears_old_tx_fifo(self):
        self.run_scenario("session_fifo")

    def test_blocked_software_buffer_releases_client(self):
        self.run_scenario("software_timeout")

    def test_blocked_hardware_fifo_releases_client(self):
        self.run_scenario("fifo_timeout")

    def test_timeout_survives_millis_wraparound(self):
        self.run_scenario("wraparound")

    def test_idle_healthy_connection_is_not_timed_out(self):
        self.run_scenario("idle")

    def test_uart_reinstall_failure_stops_server(self):
        self.run_scenario("reset_failure")


if __name__ == "__main__":
    unittest.main()
