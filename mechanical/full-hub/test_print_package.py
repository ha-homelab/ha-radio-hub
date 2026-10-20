#!/usr/bin/env python3
"""Protect print quantities and reject stale, missing or unrelated package files."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('full_hub_print_package', HERE/'print_package.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


class PrintPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.report = {'revision': p.REVISION, 'units': 'mm', 'parts': {}, 'generated_sha256': {}}
        for _, stem, _, quantity, _, _ in p.PARTS:
            data = f'solid {stem}\nendsolid {stem}\n'.encode()
            (self.directory/(stem+'.stl')).write_bytes(data)
            self.report['parts'][stem] = {'quantity': quantity, 'sha256': p.sha(data)}
            self.report['generated_sha256'][stem+'.stl'] = p.sha(data)
        self.save_report()

    def save_report(self):
        (self.directory/'verification.json').write_text(json.dumps(self.report))

    def test_archive_is_allowlisted_deterministic_and_hashes_match(self):
        (self.directory/'unrelated-private.stl').write_text('exclude me')
        (self.directory/'assembly.scad').write_text('exclude this too')
        a = p.payload(self.directory)
        self.assertEqual(a, p.payload(self.directory))
        with zipfile.ZipFile(io.BytesIO(a[p.ARCHIVE])) as archive:
            expected = sorted([row[1]+'.stl' for row in p.PARTS] + ['PRINT-FIRST.txt', 'print-manifest.json'])
            self.assertEqual(archive.namelist(), expected)
            manifest = json.loads(archive.read('print-manifest.json'))
            for row in manifest['parts']:
                self.assertEqual(p.sha(archive.read(row['file'])), row['sha256'])
            for item in archive.infolist():
                self.assertEqual(item.date_time, (1980,1,1,0,0,0))
                self.assertEqual(item.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(item.external_attr >> 16, 0o100644)

    def test_two_arms_and_trial_optional_counts(self):
        m = p.make_manifest(self.directory, self.report)
        self.assertEqual(next(row for row in m['parts'] if row['file']=='pod-arm.stl')['quantity'], 2)
        self.assertEqual((m['unique_stl_files'], m['installed_pieces'], m['pieces_including_trial_and_optional']), (14,13,15))
        self.assertEqual([r['file'] for r in m['parts'] if r['stage']==1], ['fit-coupon.stl','zwave-tray.stl'])
        self.assertEqual([r['file'] for r in m['parts'] if r['role']=='optional'], ['cc1101-port-blank.stl'])
        self.assertFalse(m['physical_fit_verified'])

    def test_incorrect_arm_quantity_is_rejected(self):
        self.report['parts']['pod-arm']['quantity'] = 1
        with self.assertRaisesRegex(ValueError, 'incorrect quantity'):
            p.make_manifest(self.directory, self.report)

    def test_missing_or_unexpected_report_part_is_rejected(self):
        for operation in ('missing', 'unexpected'):
            report = copy.deepcopy(self.report)
            if operation == 'missing': del report['parts']['lid']
            else: report['parts']['old-case'] = {'quantity': 1}
            with self.subTest(operation=operation), self.assertRaisesRegex(ValueError, 'allowlist'):
                p.make_manifest(self.directory, report)

    def test_missing_mesh_is_rejected(self):
        (self.directory/'base.stl').unlink()
        with self.assertRaisesRegex(ValueError, 'missing regular file'):
            p.payload(self.directory)

    def test_stale_mesh_or_inconsistent_report_hash_is_rejected(self):
        (self.directory/'base.stl').write_text('changed mesh')
        with self.assertRaisesRegex(ValueError, 'verification hashes'):
            p.payload(self.directory)
        self.report['parts']['base']['sha256'] = p.sha(b'changed mesh')
        self.save_report()
        with self.assertRaisesRegex(ValueError, 'verification hashes'):
            p.payload(self.directory)

    def test_symlink_mesh_cannot_exfiltrate_another_file(self):
        (self.directory/'base.stl').unlink()
        (self.directory/'base.stl').symlink_to(self.directory/'lid.stl')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            p.payload(self.directory)

    def test_check_rejects_corrupt_archive_or_manifest(self):
        p.publish(self.directory)
        p.publish(self.directory, check=True)
        for name in [p.ARCHIVE, 'print-manifest.json', 'PRINT-FIRST.txt']:
            with self.subTest(file=name):
                (self.directory/name).write_bytes(b'corrupt')
                with self.assertRaisesRegex(ValueError, 'stale or corrupted'):
                    p.publish(self.directory, check=True)
                p.publish(self.directory)

    def test_wrong_revision_or_units_cannot_be_packaged(self):
        for key, value in [('revision', 'old'), ('units', 'inch')]:
            report = dict(self.report); report[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'current FH1'):
                p.make_manifest(self.directory, report)


if __name__ == '__main__':
    unittest.main()
