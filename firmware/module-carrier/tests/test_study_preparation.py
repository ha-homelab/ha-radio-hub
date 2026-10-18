"""Historical CLI entrypoints must fail closed before staging the active profile."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

STUDY = Path(__file__).resolve().parents[3] / "hardware/module-carrier/studies/compact-s3/firmware"


class StudyPreparationTests(unittest.TestCase):
    def test_both_entrypoints_and_board_selections_preserve_baseline_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "must-not-be-created"
            for script, options in [("prepare_nano.py", []), ("prepare.py", ["--board", "nano"]),
                                    ("prepare.py", ["--board", "mini"])]:
                with self.subTest(script=script, options=options):
                    result = subprocess.run([sys.executable, str(STUDY / script), str(output), *options],
                                            capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Historical study helper", result.stderr)
                    self.assertNotIn("ImportError", result.stderr)
                    self.assertFalse(output.exists())
