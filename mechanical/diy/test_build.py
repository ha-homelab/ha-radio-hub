"""Dimension/orientation regressions for the actual print exporter."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location('diy_print', Path(__file__).with_name('build.py'))
build=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(build)

BOARD='''(kicad_pcb
(gr_rect (start 0 0) (end 160 100) (layer "Edge.Cuts"))
(footprint "THT" (layer "F.Cu") (at 20 30 90)
(property "Reference" "J1") (property "Value" "Header")
(pad "1" thru_hole rect (at 0 0) (size 2 2) (drill 1) (net "+3V3"))
(pad "2" thru_hole circle (at 2.54 0) (size 2 2) (drill 1) (net "GND")))
(segment (start 20 30) (end 20 27.46) (width .8) (layer "B.Cu")))'''

class TestPrint(unittest.TestCase):
    def geometry(self, source=BOARD):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.kicad_pcb'; p.write_text(source)
            return build.board_geometry(p)

    def test_rotation_and_native_drill_contract(self):
        g=self.geometry()
        self.assertEqual([g['width_mm'],g['height_mm']],[160,100])
        self.assertEqual([(h['x_mm'],h['y_mm']) for h in g['holes']],[(20,30),(20,27.46)])
        self.assertEqual([h['net'] for h in g['holes']],['+3V3','GND'])
        self.assertEqual(g['minimum_track_mm'],.8)

    def test_rejects_unprintable_top_copper_smd_vias_zones(self):
        bad=[BOARD.replace('(layer "B.Cu")','(layer "F.Cu")'),
             BOARD.replace('thru_hole rect','smd rect'),
             BOARD[:-1]+'(via (at 10 10)))', BOARD[:-1]+'(zone (net "GND")))']
        for source in bad:
            with self.subTest(source=source):
                with self.assertRaises(ValueError): self.geometry(source)

    def test_rejects_nonzero_crop_origin(self):
        with self.assertRaises(ValueError): self.geometry(BOARD.replace('(start 0 0)','(start 1 0)'))

    def test_svg_preserves_unit_scale_and_checks_every_pad(self):
        g=self.geometry()
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="159.99mm" height="100mm" viewBox="0 0 159.99 100"><title>time</title><circle cx="20" cy="30" r=".2"/><circle cx="20" cy="27.46" r=".2"/></svg>'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'native.svg'; p.write_text(svg)
            result=build.normalize_native_svg(p,g).decode()
            self.assertIn('width="160.0mm"',result)
            self.assertNotIn('scale(',result)
            self.assertNotIn('time',result)
            p.write_text(svg.replace('cx="20"','cx="140"'))
            with self.assertRaisesRegex(ValueError,'unmirrored pilot'):
                build.normalize_native_svg(p,g)
            p.write_text(svg.replace('0 0 159.99 100','0 0 155 100'))
            with self.assertRaisesRegex(ValueError,'crop'):
                build.normalize_native_svg(p,g)

    def test_calibration_has_true_metric_vectors(self):
        from pypdf import PdfReader
        from pypdf.generic import ContentStream
        for paper,wh in [('a4',(210,297)),('letter',(215.9,279.4))]:
            with self.subTest(paper=paper):
                reader=PdfReader(io.BytesIO(build.calibration(paper)))
                page=reader.pages[0]
                self.assertAlmostEqual(float(page.mediabox.width)/build.MM,wh[0],places=3)
                self.assertAlmostEqual(float(page.mediabox.height)/build.MM,wh[1],places=3)
                ops=ContentStream(page.get_contents(),reader).operations
                self.assertTrue(any(op==b're' and abs(float(a[2])/build.MM-50)<.001 and
                                    abs(float(a[3])/build.MM-50)<.001 for a,op in ops))
                # Both 100 mm ruler baselines must exist independently.
                moves=[]; lengths=[]
                for a,op in ops:
                    if op==b'm': moves=[float(x) for x in a]
                    if op==b'l' and moves:
                        dx=(float(a[0])-moves[0])/build.MM; dy=(float(a[1])-moves[1])/build.MM
                        if abs(abs(dx)+abs(dy)-100)<.001: lengths.append((round(dx),round(dy)))
                self.assertIn((100,0),lengths); self.assertIn((0,100),lengths)

    def test_wire_schedule_must_match_native_terminal_positions(self):
        from pypdf import PdfReader
        geometry={'holes':[{'ref':'T1','id':'T1.1','x_mm':10,'y_mm':20},
                           {'ref':'T2','id':'T2.1','x_mm':40,'y_mm':20}]}
        plan={'terminals':[{'ref':'T1','xy':[10,20]},{'ref':'T2','xy':[40,20]}],
              'wires':[{'ref':'W1','logical_net':'GND','from_terminal':'T1',
                        'to_terminal':'T2','cut_length_mm':44,'awg':24}]}
        output=build.wire_schedule_pdf(plan,geometry,'a4')
        extracted=PdfReader(io.BytesIO(output)).pages[0].extract_text()
        self.assertIn('T1 (10,20)',extracted);self.assertIn('T2 (40,20)',extracted)
        plan['terminals'][1]['xy'][0]=41
        with self.assertRaisesRegex(ValueError,'differs from native PCB'):
            build.wire_schedule_pdf(plan,geometry,'a4')

    def test_adapter_joint_uses_real_pin_without_a_fictitious_hole(self):
        from pypdf import PdfReader
        geometry={'holes':[{'ref':'U1','id':'U1.11','x_mm':85,'y_mm':85.4},
                           {'ref':'U1','id':'U1.28','x_mm':100,'y_mm':60},
                           {'ref':'T2','id':'T2.1','x_mm':40,'y_mm':20}]}
        plan={'terminals':[{'ref':'E1','kind':'adapter_pin','physical_pin':'U1.11',
                           'connection_height_mm':4,'xy':[85,85.4]},
                          {'ref':'T2','xy':[40,20]}],
              'wires':[{'ref':'W1','logical_net':'MOSI','from_terminal':'E1',
                        'to_terminal':'T2','cut_length_mm':84,'awg':26}]}
        pdf=PdfReader(io.BytesIO(build.wire_schedule_pdf(plan,geometry,'a4')))
        self.assertEqual(len(pdf.pages),2)
        self.assertIn('E1: U1.11 @4mm',pdf.pages[0].extract_text())
        self.assertIn('not extra drill holes',pdf.pages[1].extract_text())
        self.assertEqual(len(geometry['holes']),3)
        plan['terminals'][0]['physical_pin']='U1.12'
        with self.assertRaisesRegex(ValueError,'absent from native PCB'):
            build.wire_schedule_pdf(plan,geometry,'a4')

    def test_bottom_drill_is_mirrored_once(self):
        from pypdf import PdfReader
        g=self.geometry(); reader=PdfReader(io.BytesIO(build.drill_sheet(g,'a4')))
        content=reader.pages[0].get_contents().get_data().decode()
        self.assertIn('bottom copper view',reader.pages[0].extract_text())
        # Bottom view of source J1.x=20 lands at (210-160)/2+160-20=165 mm.
        # The first circle begins at x + radius =165.5 mm (PDF's Bezier path).
        self.assertIn(f'{165.5*build.MM:.4f}'[:7],content)

if __name__=='__main__': unittest.main()
