"""Exercise the real SC16 register core; no claim about timing on silicon."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Sc16RegisterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="sc16-contract-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / "test"
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required")
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([compiler, *flags, "-I", str(ROOT / "firmware/low-power/components/sc16is752_uart"),
                        str(ROOT / "tests/native/sc16is752_harness.cpp"), "-o", str(cls.binary)], check=True)

    def test_register_contract(self):
        for scenario in ["divisor","init","duplex","backpressure","rx_overflow","line_error","invalid_level"]:
            with self.subTest(scenario=scenario):
                subprocess.run([str(self.binary),scenario],check=True)

if __name__ == "__main__":
    unittest.main()
