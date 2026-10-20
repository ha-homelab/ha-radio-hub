#!/usr/bin/env python3
"""Render a portable, source-linked reading guide. No network calls."""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
from pathlib import Path
import sys
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'guide'
sys.path.insert(0, str(ROOT))
from tools.check import private_path, public_file, public_paths  # noqa: E402

GITHUB = 'https://github.com/ha-homelab/ha-radio-hub/blob/main/'


def slugify(text: str) -> str:
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def rewrite_url(url: str, source: str, routes: dict[str, str], root: Path = ROOT) -> str:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path:
        return url
    path = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parts.path)))
    if path == '..' or path.startswith('../') or path.startswith('/') or '\\' in path:
        raise ValueError(f'Local link escapes repository in {source}')
    if (root / path).is_dir() and (root / path / 'README.md').is_file():
        path = posixpath.join(path, 'README.md')
    if path in routes:
        target = routes[path] + '.html'
    elif path.endswith('.md'):
        target = GITHUB + quote(path, safe='/')
    else:
        target = '../' + quote(path, safe='/')
    return urlunsplit(('', '', target, parts.query, parts.fragment))


def render_markdown(text: str, source: str, routes: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    parser = MarkdownIt('commonmark', {'html': False}).enable(['table', 'strikethrough'])
    tokens = parser.parse(text)
    headings = []
    used = set()
    for i, token in enumerate(tokens):
        if token.type == 'heading_open':
            inline = tokens[i + 1]
            label = ''.join(t.content for t in inline.children or [] if t.type in {'text', 'code_inline'})
            base = slugify(label) or 'section'
            anchor = base
            suffix = 0
            while anchor in used:
                suffix += 1
                anchor = f'{base}-{suffix}'
            used.add(anchor)
            token.attrSet('id', anchor)
            if token.tag == 'h2':
                headings.append((anchor, label))
        for child in token.children or []:
            attribute = 'href' if child.type == 'link_open' else 'src' if child.type == 'image' else None
            if attribute:
                child.attrSet(attribute, rewrite_url(child.attrGet(attribute), source, routes))
    body = parser.renderer.render(tokens, parser.options, {})
    body = body.replace('<table>', '<div class="table-scroll"><table>').replace('</table>', '</table></div>')
    return body, headings


def shell(title: str, content: str, pages: list[dict], current: str = '') -> str:
    nav = ''.join(f'<a href="{p["slug"]}.html"' + (' aria-current="page"' if p['slug'] == current else '') + f'>{html.escape(p["label"])}</a>' for p in pages[:7])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · HA Radio Hub</title><link rel="stylesheet" href="style.css"><script src="guide.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="top"><a class="brand" href="index.html">HA Radio Hub</a><span class="badge">MC2-B / FH1 · PROTOTYPE</span>
<nav aria-label="Quick tools"><a href="../hardware/external-antenna/index.html#harness">Find a wire</a><a href="../mechanical/full-hub/index.html">Print files</a><a href="https://github.com/ha-homelab/ha-radio-hub">GitHub</a></nav></header>
<div class="shell"><aside class="side"><nav aria-label="Build guide">{nav}<span class="small">Reference</span><a href="documentation.html">All references</a><a href="history.html">Design history</a></nav></aside>
<main id="main">{content}<footer>MC2-B is the active classic ESP32 design. Physical fit, concurrent operation and coverage still require your measurements.
<br>This guide reads the repository documentation. Source links open GitHub; diagrams and downloads stay in this copy.</footer></main></div></body></html>
'''


def build() -> dict[str, str]:
    pages = json.loads((HERE / 'pages.json').read_text())
    if len({p['slug'] for p in pages}) != len(pages) or len({p['source'] for p in pages}) != len(pages):
        raise ValueError('Duplicate guide page or source')
    routes = {p['source']: p['slug'] for p in pages}
    output = {}
    cards = []
    for page in pages:
        source = ROOT / page['source']
        text = source.read_text()
        body, headings = render_markdown(text, page['source'], routes)
        toc = '<details class="toc"><summary>On this page</summary><ul>' + ''.join(f'<li><a href="#{anchor}">{html.escape(label)}</a></li>' for anchor, label in headings) + '</ul></details>' if headings else ''
        meta = f'<div class="page-meta"><a href="index.html">Guide home</a><a href="{GITHUB + quote(page["source"], safe="/")}">View Markdown source on GitHub</a><button type="button" data-print>Print this guide</button></div>'
        output[page['slug'] + '.html'] = shell(page['label'], meta + toc + '<article class="article">' + body + '</article>', pages, page['slug'])
        search = ' '.join((page['label'] + ' ' + page['description'] + ' ' + text).lower().split())
        cards.append(f'<article class="card" data-search="{html.escape(search, quote=True)}"><h2><a href="{page["slug"]}.html">{html.escape(page["label"])}</a></h2><p>{html.escape(page["description"])}</p></article>')
    home = '''<section class="hero"><div class="eyebrow">Build, wire, check</div><h1>One place to build<br>your radio hub.</h1><p>Start with the current MC2-B hardware, then work through programming, the FH1 enclosure and Home Assistant commissioning.</p><div class="actions"><a class="primary" href="start-here.html">Start the build</a><a href="../hardware/external-antenna/index.html#harness">Find a wire</a><a href="../mechanical/full-hub/FH1-MC2-B-print-package.zip" download>Download print package</a></div></section>
<section class="tools"><label for="guide-search">Find a guide by topic or part</label><input id="guide-search" type="search" placeholder="Try ZAC93, flash, antenna, BME680 or recovery"><p id="result-count" role="status"></p><button id="clear-search" type="button">Clear search</button></section>
<p class="empty" id="empty" hidden>No matching guides. Try a component name or clear the search.</p><section class="grid" aria-label="Guides">''' + ''.join(cards) + '</section>'
    output['index.html'] = shell('Build guide', home, pages)
    # This inventory makes the reader portable in a source archive, too. It is
    # consumed only by the read-only localhost server, never used for uploads.
    inventory = set()
    for path in public_paths(ROOT):
        relative = path.relative_to(ROOT).as_posix()
        if not private_path(relative) and public_file(ROOT, path):
            inventory.add(relative)
    inventory.update('guide/' + name for name in output)
    inventory.add('guide/public-files.json')
    output['public-files.json'] = json.dumps({'schema_version': 1, 'files': sorted(inventory)}, indent=2) + '\n'
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, content in build().items():
        path = HERE / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                stale.append(name)
        else:
            path.write_text(content)
    if stale:
        parser.exit(1, 'Stale reading guide: ' + ', '.join(stale) + '\n')
    print('Reading guide: sources, routes and public inventory match')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
