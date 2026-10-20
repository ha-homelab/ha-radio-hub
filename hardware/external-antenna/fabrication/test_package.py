"""Prevent stale or mixed fabrication uploads, without modifying source files."""
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("mc2_fabrication", Path(__file__).with_name("package.py"))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


@contextmanager
def isolated_package():
    """Exercise manifest mutations without touching the published package."""
    original = package.HERE
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name in ("manifest.json", package.ARCHIVE):
            (root / name).write_bytes((original / name).read_bytes())
        manifest = json.loads((root / "manifest.json").read_text())
        with patch.object(package, "HERE", root):
            yield root, manifest


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

    def test_native_pcb_changed_after_verification_is_rejected(self):
        changed = package.CAD / "mc2.kicad_pcb"
        original_read = Path.read_bytes
        def read(path):
            return b"changed native PCB" if path == changed else original_read(path)
        with patch.object(Path, "read_bytes", read):
            with self.assertRaisesRegex(ValueError, "Stale native evidence"):
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

    def test_assembly_refresh_keeps_native_export_bytes_and_bindings(self):
        with isolated_package() as (root, manifest):
            sources = dict(manifest["source_sha256"])
            changed = [
                "hardware/external-antenna/rf-bom.json",
                "mechanical/full-hub/components.json",
                "mechanical/full-hub/verification.json",
                "mechanical/module-carrier/external-antenna-prototype/build.py",
            ]
            for name in changed:
                sources[name] = "a" * 64
            archive_before = (root / package.ARCHIVE).read_bytes()
            with patch.object(package, "current_sources", return_value=sources):
                with self.assertRaisesRegex(ValueError, "stale"):
                    package.check()
                package.refresh_assembly_evidence()
                package.check()
            refreshed = json.loads((root / "manifest.json").read_text())
            self.assertEqual(refreshed["source_sha256"], sources)
            self.assertEqual(refreshed["archive_sha256"], manifest["archive_sha256"])
            self.assertEqual(refreshed["files_sha256"], manifest["files_sha256"])
            self.assertEqual((root / package.ARCHIVE).read_bytes(), archive_before)
            refresh = refreshed["assembly_evidence_refresh"]
            self.assertEqual(refresh["changed_sources"], sorted(changed))
            self.assertFalse(refresh["archive_reexported"])
            self.assertFalse(refresh["native_checks_rerun"])
            self.assertIn("No fresh native KiCad export", refresh["note"])

    def test_assembly_refresh_rejects_changed_added_and_removed_immutable_sources(self):
        cases = [
            ("change", "hardware/external-antenna/cad/mc2.kicad_pcb"),
            ("change", "firmware/external-antenna/build-evidence.json"),
            ("remove", "hardware/external-antenna/cad/mc2.kicad_pcb"),
            ("add", "firmware/external-antenna/new-native-input.c"),
            ("add", "mechanical/full-hub/../../native-input"),
            ("add", "mechanical/full-hub-other/components.json"),
            ("add", "mechanical/module-carrier/external-antenna-prototype/other.py"),
        ]
        for operation, name in cases:
            with self.subTest(operation=operation, name=name), isolated_package() as (root, manifest):
                sources = dict(manifest["source_sha256"])
                if operation == "remove":
                    sources.pop(name)
                else:
                    sources[name] = "a" * 64
                manifest_before = (root / "manifest.json").read_bytes()
                with patch.object(package, "current_sources", return_value=sources):
                    with self.assertRaisesRegex(ValueError, "fresh native export"):
                        package.refresh_assembly_evidence()
                self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)

    def test_assembly_refresh_rejects_changed_archive_without_writing_manifest(self):
        with isolated_package() as (root, manifest):
            archive = root / package.ARCHIVE
            archive.write_bytes(archive.read_bytes() + b"tampered")
            manifest_before = (root / "manifest.json").read_bytes()
            with patch.object(package, "current_sources", return_value=manifest["source_sha256"]):
                with self.assertRaisesRegex(ValueError, "Archive hash"):
                    package.refresh_assembly_evidence()
            self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)

    def test_assembly_refresh_rejects_bad_members_even_if_archive_hash_is_updated(self):
        with isolated_package() as (root, manifest):
            archive_path = root / package.ARCHIVE
            with zipfile.ZipFile(archive_path) as archive:
                files = {n: archive.read(n) for n in archive.namelist()}
            files["mc2-PTH.drl"] += b"\n; unexpected drill mutation\n"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for name, data in files.items():
                    archive.writestr(name, data)
            manifest["archive_sha256"] = package.sha(archive_path.read_bytes())
            (root / "manifest.json").write_text(json.dumps(manifest))
            manifest_before = (root / "manifest.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "Fabrication file hash"):
                package.refresh_assembly_evidence()
            self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)

    def test_assembly_refresh_requires_current_evidence_guards(self):
        with isolated_package() as (root, _):
            manifest_before = (root / "manifest.json").read_bytes()
            with patch.object(package, "current_sources", side_effect=ValueError("Stale mechanical evidence")):
                with self.assertRaisesRegex(ValueError, "Stale mechanical evidence"):
                    package.refresh_assembly_evidence()
            self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)

    def test_assembly_refresh_is_noop_when_nothing_changed(self):
        with isolated_package() as (root, manifest):
            manifest_before = (root / "manifest.json").read_bytes()
            with patch.object(package, "current_sources", return_value=manifest["source_sha256"]):
                package.refresh_assembly_evidence()
            self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)


if __name__ == "__main__":
    unittest.main()
