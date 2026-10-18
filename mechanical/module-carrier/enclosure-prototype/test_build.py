"""Geometry checks of the prototype, not a fit or load certification."""
import copy, importlib.util, json, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('enclosure_build',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class EnclosureGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((HERE/'parameters.json').read_text())
        cls.s=b.rail.native_source(b.ROOT/'hardware/module-carrier/cad')
        cls.g=b.geometry(cls.s,cls.p)
    def test_only_native_h3_is_used_for_pcb(self):
        self.assertEqual(set(self.s['supports']),{'H3'})
        self.assertEqual(self.s['supports']['H3'],[18.0,52.03])
    def test_no_unknown_measurements_presented_as_measured(self):
        self.assertTrue(all(v is None for v in self.p['measured'].values()))
    def test_case_halves_do_not_intersect(self):
        self.assertAlmostEqual(float((self.g['assembled']['base'].solid ^ self.g['assembled']['cover'].solid).volume()),0,places=5)
    def test_rail_reach_respects_legal_native_lands(self):
        for band,land in zip(self.g['bands'],sorted(self.s['lands'],key=lambda x:x['id'])):
            a=land['bounds_mm'];self.assertGreaterEqual(band[0],a[0]);self.assertGreaterEqual(band[1],a[1]);self.assertLessEqual(band[2],a[2]);self.assertLessEqual(band[3],a[3])
    def test_nominal_board_does_not_intersect_case(self):
        seat=self.g['seat'];hx,hy=self.s['supports']['H3']
        pcb=b.c.subtract(b.c.box(self.s['width'],self.s['height'],1.6).move((0,0,seat)),b.c.cylinder(2.7,2).move((hx,hy,seat-.1)))
        for name in ['base','cover']:
            self.assertAlmostEqual(float((pcb.solid ^ self.g['assembled'][name].solid).volume()),0,places=5)
    def test_jack_service_tunnel_open(self):
        # Within the modeled port only; the actual boot/latch Z envelope is unknown.
        probe=b.c.box(29.8,19,20).move((18.1,77,4))
        for name in ['base','cover']:
            self.assertAlmostEqual(float((probe.solid ^ self.g['assembled'][name].solid).volume()),0,places=5)
    def test_ceiling_screw_driver_access_in_open_base(self):
        ix,iy,ix1,iy1=self.g['inner']
        for x in [ix+6,ix1-6]:
            probe=b.c.cylinder(8.8,self.g['roof']).move((x,39,2.5))
            self.assertAlmostEqual(float((probe.solid ^ self.g['assembled']['base'].solid).volume()),0,places=5)
    def test_h2_antenna_end_wall_clearance(self):
        self.assertAlmostEqual(min(p[1] for p in self.g['antenna']),-5.475)
        self.assertAlmostEqual(self.g['h2_top_wall_gap'],15.525)
        invalid=copy.deepcopy(self.p);invalid['nominal']['end_margin']=18
        with self.assertRaisesRegex(AssertionError,'end-wall'):
            b.geometry(self.s,invalid)
    def test_floor_hardware_is_clear_of_ceiling_frame(self):
        frame=self.g['assembled']['ceiling-spacing-frame'].solid
        n=self.p['nominal'];projection=n['floor_hardware_max_projection']
        self.assertGreaterEqual(n['ceiling_spacing']-projection,1)
        self.assertAlmostEqual(self.g['installed_height'],61.4)
        for x in [25,41]:
            head=b.c.cylinder(6,projection).move((x,n['jack_stop_contact_y']-6.5,-projection))
            self.assertAlmostEqual(float((head.solid ^ frame).volume()),0,places=5)
        # Entire spacing frame ends at the original floor underside.
        self.assertAlmostEqual(b.c.mesh_of(self.g['assembled']['ceiling-spacing-frame']).bounds[1,2],0)
    def test_spacing_frame_and_base_mounting_holes_align(self):
        x0,y0,x1,y1=self.g['inner'];spacing=self.p['nominal']['ceiling_spacing']
        for x in [x0+6,x1-6]:
            shaft=b.c.cylinder(4.2,spacing+2.4).move((x,39,-spacing))
            for name in ['base','ceiling-spacing-frame']:
                self.assertAlmostEqual(float((shaft.solid ^ self.g['assembled'][name].solid).volume()),0,places=5)
    def test_all_prints_are_connected_and_on_bed(self):
        for name,node in self.g['nodes'].items():
            with self.subTest(name=name):
                mesh=b.c.mesh_of(node);self.assertTrue(mesh.is_watertight);self.assertEqual(len(mesh.split()),1);self.assertGreater(mesh.volume,0);self.assertAlmostEqual(mesh.bounds[0,2],0,places=4)
if __name__=='__main__':unittest.main()
