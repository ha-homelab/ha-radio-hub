"""Exercise production guard decisions and real HDLC/probe parser under faults."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = ["fresh_without_ethernet", "normal_power_cycles", "uncommissioned", "terminal_persists",
         "generic_sdk_abort", "unrelated_unarmed_abort", "normal_ota_reboot", "repeat_explicit_retry",
         "corrupt_guard", "missing_rcp", "stale_protocol", "not_radio", "missing_raw", "stale_api",
         "too_new_host_requirement", "missing_radio_feature", "rcp_dies_during_probe", "good_rcp",
         "malformed_varints", "hdlc_roundtrip", "hdlc_corrupt_and_resync", "hdlc_overflow",
         "persistence_failures", "saturating_counters", "maintenance_pause", "refuse_unstored_maintenance_or_retry",
         "old_session_does_not_arm_waiting_boot"]

class ThreadGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="thread-guard-tests-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / "guard"
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([shutil.which("c++"), *flags, "-I", str(ROOT.parent / "low-power/components/low_power_otbr"),
                        str(ROOT / "tests/thread_guard_test.cpp"), "-o", str(cls.binary)], check=True)

def make_test(name):
    def test(self):
        subprocess.run([str(self.binary), name], check=True)
    return test

for case in CASES:
    setattr(ThreadGuardTests, "test_" + case, make_test(case))

if __name__ == "__main__":
    unittest.main()
