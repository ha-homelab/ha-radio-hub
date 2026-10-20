from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from tools.preview import GuideHandler, load_inventory, requested_file


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root / 'guide').mkdir()
        (cls.root / 'guide/index.html').write_text('<h1>Guide</h1>')
        (cls.root / 'unlisted.txt').write_text('not public')
        (cls.root / 'secrets.yaml').write_text('private')
        (cls.root / 'guide/alias.html').symlink_to(cls.root / 'unlisted.txt')
        (cls.root / 'guide/exposed.txt').write_text('ghp_' + 'A' * 36)
        cls.inventory = {'guide/index.html', 'guide/alias.html', 'guide/exposed.txt'}
        (cls.root / 'guide/public-files.json').write_text(json.dumps({'schema_version': 1, 'files': sorted(cls.inventory)}))
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(GuideHandler, root=cls.root, inventory=cls.inventory))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, method='GET', headers=None):
        connection = HTTPConnection('127.0.0.1', self.server.server_port)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_root_opens_guide_and_head_has_no_body(self):
        status, body, headers = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'<h1>Guide</h1>', body)
        self.assertIn('text/html', headers['Content-Type'])
        status, body, headers = self.request('/', 'HEAD')
        self.assertEqual(status, 200)
        self.assertEqual(body, b'')
        self.assertGreater(int(headers['Content-Length']), 0)

    def test_private_unlisted_and_symlink_files_are_not_served(self):
        for path in ['/unlisted.txt', '/secrets.yaml', '/guide/alias.html', '/.git/config']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_encoded_traversal_and_backslash_are_not_resolved(self):
        for path in ['/guide/../unlisted.txt', '/guide/%2e%2e/unlisted.txt', '/guide%5cindex.html', '/guide/%00index.html']:
            with self.subTest(path=path):
                self.assertIsNone(requested_file(self.root, self.inventory, path))

    def test_foreign_host_is_rejected(self):
        self.assertEqual(self.request('/', headers={'Host': 'attacker.example'})[0], 403)

    def test_credential_like_content_is_not_returned(self):
        status, body, _ = self.request('/guide/exposed.txt')
        self.assertEqual(status, 403)
        self.assertNotIn(b'ghp_', body)

    def test_inventory_rejects_private_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'guide').mkdir()
            for name in ['private/install.yaml', '../outside', 'secrets.yaml', '/etc/passwd', 'guide/../secret']:
                (root / 'guide/public-files.json').write_text(json.dumps({'schema_version': 1, 'files': [name]}))
                with self.subTest(name=name), self.assertRaises(ValueError):
                    load_inventory(root)


if __name__ == '__main__':
    unittest.main()
