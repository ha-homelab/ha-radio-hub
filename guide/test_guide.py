import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

SPEC = importlib.util.spec_from_file_location('reading_guide_build', Path(__file__).with_name('build.py'))
guide = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guide)


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.targets = []
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if attrs.get(name):
                self.targets.append(attrs[name])


class ReadingGuideTests(unittest.TestCase):
    def setUp(self):
        self.routes = {'docs/start-here.md': 'start-here', 'docs/full-hub-assembly.md': 'assembly'}

    def test_known_document_and_fragment_stay_readable(self):
        self.assertEqual(guide.rewrite_url('full-hub-assembly.md#install-the-zac93', 'docs/start-here.md', self.routes), 'assembly.html#install-the-zac93')
        self.assertEqual(guide.rewrite_url('#step-1', 'docs/start-here.md', self.routes), '#step-1')

    def test_assets_rebase_without_changing_external_urls(self):
        self.assertEqual(guide.rewrite_url('../hardware/a.svg', 'docs/start-here.md', self.routes), '../hardware/a.svg')
        url = 'https://example.com/a?query=1#part'
        self.assertEqual(guide.rewrite_url(url, 'docs/start-here.md', self.routes), url)

    def test_nonincluded_markdown_uses_rendered_github_view(self):
        self.assertEqual(guide.rewrite_url('other.md#details', 'docs/start-here.md', self.routes), guide.GITHUB + 'docs/other.md#details')

    def test_escaping_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            guide.rewrite_url('../../private.txt', 'docs/start-here.md', self.routes)

    def test_heading_ids_are_unique_and_tables_render(self):
        body, headings = guide.render_markdown('## Power & pins\n\n## Power & pins\n\nA | B\n--- | ---\n1 | 2\n', 'docs/start-here.md', self.routes)
        self.assertEqual([h[0] for h in headings], ['power--pins', 'power--pins-1'])
        self.assertIn('<div class="table-scroll"><table>', body)
        self.assertIn('id="power--pins-1"', body)

    def test_raw_html_is_escaped_and_code_is_preserved(self):
        body, _ = guide.render_markdown('<script>alert(1)</script>\n\n```sh\necho "$HOME"\n  next\n```', 'docs/start-here.md', self.routes)
        self.assertNotIn('<script>', body)
        self.assertIn('&lt;script&gt;', body)
        self.assertIn('echo &quot;$HOME&quot;\n  next\n', body)

    def test_navigation_flashes_loose_boards_before_mounting(self):
        pages = json.loads((guide.HERE / 'pages.json').read_text())
        order = [p['slug'] for p in pages]
        self.assertLess(order.index('firmware'), order.index('assembly'))

    def test_generated_local_links_and_section_targets_resolve(self):
        output = guide.build()
        documents = {(guide.HERE / name).resolve(): Links(text) for name, text in output.items() if name.endswith('.html')}
        for page, parsed in list(documents.items()):
            for url in parsed.targets:
                parts = urlsplit(url)
                if parts.scheme or parts.netloc:
                    continue
                target = (page.parent / unquote(parts.path)).resolve() if parts.path else page
                with self.subTest(page=page.name, url=url):
                    self.assertTrue(target in documents or target.exists(), f'Missing local link: {url}')
                    if parts.fragment and target.suffix == '.html':
                        if target not in documents:
                            documents[target] = Links(target.read_text())
                        self.assertIn(unquote(parts.fragment), documents[target].ids)


if __name__ == '__main__':
    unittest.main()
