"""Prevent stale or mixed fabrication uploads, without modifying source files."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("mc2_fabrication", Path(__file__).with_name("package.py"))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class FabricationGuards(unittest.TestCase):
    def test_checked_in_archive_and_sources_match(self):
        package.check()

    def test_firmware_pin_plan_drift_is_rejected(self):
        changed = package.ROOT / "firmware/external-antenna/pin-plan.json"
        original_read = Path.read_bytes
        def read(path):
            return b"changed firmware plan" if path == changed else original_read(path)
        with patch.object(Path, "read_bytes", read):
            with self.assertRaisesRegex(ValueError, "Firmware pin plan differs"):
                package.current_sources()

    def test_mechanical_parameters_changed_after_verification_are_rejected(self):
        changed = package.ROOT / "mechanical/full-hub/parameters.json"
        original_read = Path.read_bytes
        def read(path):
            return b"changed dimensions" if path == changed else original_read(path)
        with patch.object(Path, "read_bytes", read):
            with self.assertRaisesRegex(ValueError, "Stale mechanical evidence"):
                package.current_sources()

    def test_missing_drill_file_is_rejected(self):
        with zipfile.ZipFile(package.HERE / package.ARCHIVE) as archive:
            files = {n: archive.read(n) for n in archive.namelist() if n != "mc2-NPTH.drl"}
        with self.assertRaisesRegex(ValueError, "exactly"):
            package.inspect_files(files)

    def test_mixed_old_revision_is_rejected(self):
        with zipfile.ZipFile(package.HERE / package.ARCHIVE) as archive:
            files = {n: archive.read(n) for n in archive.namelist()}
        job = json.loads(files["mc2-job.gbrjob"])
        job["GeneralSpecs"]["ProjectId"]["Revision"] = "MC2-B"
        files["mc2-job.gbrjob"] = json.dumps(job).encode()
        with self.assertRaisesRegex(ValueError, "wrong revision"):
            package.inspect_files(files)

    def test_stale_source_and_changed_archive_are_rejected(self):
        original = package.HERE
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = json.loads((original / "manifest.json").read_text())
            (root / "manifest.json").write_text(json.dumps(manifest))
            (root / package.ARCHIVE).write_bytes((original / package.ARCHIVE).read_bytes() + b"tampered")
            with patch.object(package, "HERE", root):
                with patch.object(package, "current_sources", return_value={"stale": "source"}):
                    with self.assertRaisesRegex(ValueError, "stale"):
                        package.check()
                with patch.object(package, "current_sources", return_value=manifest["source_sha256"]):
                    with self.assertRaisesRegex(ValueError, "Archive hash"):
                        package.check()


if __name__ == "__main__":
    unittest.main()
