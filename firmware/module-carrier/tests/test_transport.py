"""Host regression tests for the exact transport core used by MC1 firmware."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CASES=["init","large_tx","backpressure","full_rx","count_race","read_error",
       "write_error","line_errors","post_read_error","rx_overflow","tx_overflow",
       "busy","reg_error","peek_partial"]

class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="wk2132-tests-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary=Path(cls.tmp.name)/"transport"
        flags=["-std=c++17","-Wall","-Wextra","-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS")=="1":
            flags += ["-fsanitize=address,undefined","-fno-sanitize-recover=all"]
        subprocess.run([shutil.which("c++"),*flags,"-I",str(ROOT/"components/wk2132_uart"),
                        str(ROOT/"tests/transport_test.cpp"),"-o",str(cls.binary)],check=True)

def make_test(name):
    def test(self):
        subprocess.run([str(self.binary),name],check=True)
    return test

for case in CASES:
    setattr(TransportTests,"test_"+case,make_test(case))

if __name__=="__main__":
    unittest.main()
