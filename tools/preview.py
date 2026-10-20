#!/usr/bin/env python3
"""Open the static build guide on localhost. Python standard library only."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import unquote, urlsplit
import webbrowser

if __package__:
    from .check import private_path, public_file, SECRET_PATTERNS
else:
    from check import private_path, public_file, SECRET_PATTERNS

ROOT = Path(__file__).resolve().parents[1]


def load_inventory(root: Path) -> set[str]:
    path = root / 'guide/public-files.json'
    if not public_file(root, path):
        raise ValueError('Missing guide/public-files.json. Download a complete project copy.')
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('files'), list):
        raise ValueError('Invalid public file inventory')
    names = set()
    for name in data['files']:
        if not isinstance(name, str):
            raise ValueError('Invalid public file name')
        path = PurePosixPath(name)
        if not name or name.startswith('/') or '\\' in name or '..' in path.parts or path.as_posix() != name or private_path(name):
            raise ValueError('Non-public path in guide inventory')
        names.add(name)
    return names


def requested_file(root: Path, inventory: set[str], url: str) -> Path | None:
    raw = unquote(urlsplit(url).path)
    if not raw.startswith('/') or raw.startswith('//') or '\\' in raw or '\x00' in raw:
        return None
    name = raw[1:]
    if not name:
        name = 'guide/index.html'
    elif name.endswith('/'):
        name += 'index.html'
    path = PurePosixPath(name)
    if '..' in path.parts or path.as_posix() != name or name not in inventory or private_path(name):
        return None
    target = root / name
    return target if public_file(root, target) else None


class GuideHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, root: Path, inventory: set[str], **kwargs):
        self.root = root
        self.inventory = inventory
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_document(False)

    def do_HEAD(self):
        self.send_document(True)

    def send_document(self, head_only: bool):
        port = self.server.server_port
        if self.headers.get('Host') not in {f'127.0.0.1:{port}', f'localhost:{port}'}:
            self.send_error(403, 'Use the localhost URL printed by preview.py')
            return
        target = requested_file(self.root, self.inventory, self.path)
        if target is None:
            self.send_error(404, 'Not a public project file')
            return
        try:
            content = target.read_bytes()
        except OSError:
            self.send_error(404, 'File unavailable')
            return
        content_type = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if target.suffix in {'.html', '.css', '.js', '.json', '.md', '.py', '.txt', '.yaml', '.yml', '.csv'}:
            if any(pattern.search(content.decode('utf-8', errors='replace')) for pattern in SECRET_PATTERNS):
                self.send_error(403, 'Credential-like content is not served')
                return
        self.send_response(200)
        self.send_header('Content-Type', content_type + ('; charset=utf-8' if content_type.startswith('text/') else ''))
        self.send_header('Content-Length', str(len(content)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def log_message(self, format, *args):
        # Avoid writing browsing/query details or noisy asset requests to disk.
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8780, help='Local TCP port; 0 selects a free port (default: 8780)')
    parser.add_argument('--no-open', action='store_true', help='Print the URL without opening a browser')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        inventory = load_inventory(ROOT)
        handler = partial(GuideHandler, root=ROOT, inventory=inventory)
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot open guide: {error}\nTry --port 0 if the port is occupied.\n')
    url = f'http://127.0.0.1:{server.server_port}/guide/index.html'
    print(f'Build guide: {url}\nRead-only local files. Press Ctrl+C to stop.', flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nGuide closed.')
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
