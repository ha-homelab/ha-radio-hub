"""Public release boundaries: committed bytes, no installation material."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from tools.check import private_path, public_paths
from tools.package_release import build_package


class ReleasePackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Synthetic release fixture')
        (self.repo / '.gitignore').write_text('private/\n.build/\nsecrets.yaml\n')
        (self.repo / 'README.md').write_text('Committed public instructions\n')
        self.commit()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True).stdout

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture')

    def test_bundle_uses_committed_bytes_and_verifiable_manifest(self):
        (self.repo / 'README.md').write_text('Unpublished working draft\n')
        (self.repo / 'private').mkdir()
        (self.repo / 'private/device.yaml').write_text('synthetic installation material\n')
        first, checksum = build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'one')
        second, _ = build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'two')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(checksum.read_text().split()[0], hashlib.sha256(first.read_bytes()).hexdigest())
        with zipfile.ZipFile(first) as archive:
            prefix = 'ha-radio-hub-v0.2.0/'
            self.assertFalse(any('private/' in name for name in archive.namelist()))
            self.assertEqual(archive.read(prefix + 'README.md'), b'Committed public instructions\n')
            manifest = json.loads(archive.read(prefix + 'RELEASE-MANIFEST.json'))
            self.assertEqual(manifest['commit'], self.git('rev-parse', 'HEAD').decode().strip())
            for name, metadata in manifest['files'].items():
                self.assertEqual(metadata['sha256'], hashlib.sha256(archive.read(prefix + name)).hexdigest())

    def test_hygiene_ignores_local_private_files_but_exposes_tracked_ones(self):
        (self.repo / 'private').mkdir()
        fixture = self.repo / 'private/device.yaml'
        fixture.write_text('synthetic installation material\n')
        self.assertNotIn(fixture, public_paths(self.repo))
        # An untracked manifest must not hide files in a real checkout.
        (self.repo / 'RELEASE-MANIFEST.json').write_text(json.dumps({'files': {}}))
        self.git('add', '-f', 'private/device.yaml')
        self.assertIn(fixture, public_paths(self.repo))
        self.git('commit', '-qm', 'Accidentally tracked fixture')
        with self.assertRaisesRegex(ValueError, 'Non-public'):
            build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'out')

    def test_extracted_package_hygiene_uses_public_manifest(self):
        archive, _ = build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'out')
        extracted = self.root / 'extracted'
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extracted)
        root = extracted / 'ha-radio-hub-v0.2.0'
        (root / 'private').mkdir()
        (root / 'private/device.yaml').write_text('synthetic installation material\n')
        paths = public_paths(root)
        self.assertIn(root / 'README.md', paths)
        self.assertNotIn(root / 'private/device.yaml', paths)
        (root / 'RELEASE-MANIFEST.json').write_text(json.dumps({'files': {'../outside': {}}}))
        with self.assertRaisesRegex(ValueError, 'invalid path'):
            public_paths(root)

    def test_rejects_symlink_without_reading_target(self):
        (self.repo / 'linked-file').symlink_to(self.root / 'not-in-the-repository')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'regular committed files'):
            build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'out')

    def test_private_paths_are_rejected_on_case_insensitive_filesystems(self):
        for path in ('Private/device.yaml', 'Software/Runtime/hub.env', 'BACKUPS/state.json',
                     'firmware/SECRETS.YAML', 'Private\\device.yaml'):
            with self.subTest(path=path):
                self.assertTrue(private_path(path))
        (self.repo / 'Private').mkdir()
        (self.repo / 'Private/device.yaml').write_text('synthetic installation material\n')
        self.git('add', '-f', 'Private/device.yaml')
        self.git('commit', '-qm', 'Mixed-case private fixture')
        with self.assertRaisesRegex(ValueError, 'Non-public'):
            build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'out')

    def test_rejects_credential_pattern_without_echoing_value(self):
        synthetic = 'gh' + 'p_' + 'z' * 36
        (self.repo / 'accidental.txt').write_text(synthetic)
        self.commit()
        with self.assertRaisesRegex(ValueError, 'value suppressed') as caught:
            build_package(self.repo, 'HEAD', 'v0.2.0', self.root / 'out')
        self.assertNotIn(synthetic, str(caught.exception))


if __name__ == '__main__':
    unittest.main()
