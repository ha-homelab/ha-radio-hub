"""Artwork-only guard must catch electrical/mechanical changes, not just traces."""
import json
from pathlib import Path
import tempfile
import unittest
from silkscreen_check import ROOT, fingerprint, verify


class SilkscreenGuard(unittest.TestCase):
    def test_committed_revision_and_preview_bindings(self):
        verify()

    def test_same_pad_drill_change_is_not_artwork(self):
        text = (ROOT / 'mc2.kicad_pcb').read_text()
        changed = text.replace('(drill 1.1)', '(drill 1.2)', 1)
        self.assertNotEqual(text, changed)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'changed.kicad_pcb'
            path.write_text(changed)
            self.assertNotEqual(fingerprint(path, True), fingerprint(ROOT/'mc2.kicad_pcb', True))

    def test_net_reassignment_is_not_artwork(self):
        text = (ROOT / 'mc2.kicad_pcb').read_text()
        changed = text.replace('(net "/+3V3")', '(net "/+5V")', 1)
        self.assertNotEqual(text, changed)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'changed.kicad_pcb'
            path.write_text(changed)
            self.assertNotEqual(fingerprint(path, True), fingerprint(ROOT/'mc2.kicad_pcb', True))

    def test_artwork_text_does_not_change_electrical_fingerprint(self):
        text = (ROOT / 'mc2.kicad_pcb').read_text()
        changed = text.replace('(gr_text "HA RADIO HUB"', '(gr_text "CHANGED LEGEND"', 1)
        self.assertNotEqual(text, changed)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'changed.kicad_pcb'
            path.write_text(changed)
            self.assertEqual(fingerprint(path, True), fingerprint(ROOT/'mc2.kicad_pcb', True))


if __name__ == '__main__':
    unittest.main()
