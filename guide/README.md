# Readable build guide

From the repository root, run:

```sh
python3 tools/preview.py
```

The command opens the current MC2-D guide in your browser. It uses only Python's
standard library. Stop it with Ctrl+C. Use `--no-open` to print the URL without
opening a browser, or `--port 0` to choose a free port if 8780 is occupied.
You can also open [index.html](index.html) directly: no server or Internet is
needed for the included guides, diagrams and print downloads. Links to vendor
pages, source Markdown and less-used references open the Internet.

The guide includes readable instructions, topic search, section links, printable
pages, code-copy buttons and direct wiring/print downloads. The navigation
follows loose-board programming before permanent assembly. Source Markdown
remains authoritative; the guide does not flash hardware or configure HA.

## Update the generated pages

Builders do not need these dependencies. Maintainers install the pinned
[markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html)
renderer to regenerate the committed HTML after documentation changes:

```sh
python3 -m venv .venv-guide
.venv-guide/bin/pip install -r guide/requirements.txt
.venv-guide/bin/python guide/build.py
.venv-guide/bin/python -m unittest discover -s guide -p 'test_*.py'
.venv-guide/bin/python guide/build.py --check
python3 -m unittest discover -s tests -p 'test_preview.py'
```

`pages.json` maps the included sources to their HTML names. Relative links
between those documents are rewritten to the readable pages, while other
Markdown references point to GitHub's rendered view. Raw HTML in Markdown is
escaped. `public-files.json` is a generated inventory for the read-only preview;
the server refuses unlisted/private files, path traversal and symlinks, and
binds only to 127.0.0.1. Regenerate after adding public files.
