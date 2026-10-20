"""MC2 digital geometry regressions, not mechanical or RF qualification."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mc2_enclosure_build',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class MC2Enclosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((HERE/'parameters.json').read_text())
        cls.s=b.source(cls.p)
        cls.g=b.geometry(cls.s,cls.p)

    def test_measurements_remain_unknown(self):
        self.assertTrue(all(v is None for v in self.p['measured'].values()))

    def test_native_mounting_holes_not_invented(self):
        self.assertGreaterEqual(len(self.s['holes']),3)
        for ref,xy in self.s['holes'].items():
            self.assertEqual(tuple(v+a for v,a in zip(xy,self.p['case']['board_origin_xy'])),self.g['pcb_holes'][ref])

    def test_native_module_reservations_follow_current_host(self):
        bx,by=self.p['case']['board_origin_xy']
        source={part['ref']:part for part in self.s['design']['parts']}
        self.assertEqual({part['ref'] for part in self.g['modules']},{'U1','U2','U3','U4'})
        for module in self.g['modules']:
            part=source[module['ref']]
            self.assertEqual(module['model'],part['model'])
            x0,y0,x1,y1=part['body_bounds_global_mm']
            self.assertEqual(module['bounds_case_mm'],[bx+x0,by+y0,bx+x1,by+y1])
        bad=copy.deepcopy(self.s)
        next(part for part in bad['design']['parts'] if part['ref']=='U1')['body_bounds_global_mm'][0]=-100
        with self.assertRaisesRegex(AssertionError,'module XY reservation'):
            b.geometry(bad,self.p)

    def test_rf_endpoints_follow_native_connectors(self):
        bx,by=self.p['case']['board_origin_xy']
        for route in self.g['routes']:
            x,y=self.s['design']['mechanics']['rf_ports'][route['module_ref']]['estimated_xy_mm']
            self.assertEqual(route['points_mm'][-1],[bx+x,by+y,self.p['rf']['module_connector_z_trial']])

    def test_three_labeled_independent_ports(self):
        ports=self.p['rf']['ports']
        self.assertEqual({p['label'] for p in ports},{'ZIGBEE','THREAD','BLE'})
        self.assertEqual(len({tuple(p['center']) for p in ports}),3)
        self.assertGreaterEqual(min(self.g['distances']),65)

    def test_close_ports_rejected(self):
        p=copy.deepcopy(self.p);p['rf']['ports'][1]['center'][0]=35;p['rf']['ports'][1]['strap_xy'][0]=35
        with self.assertRaisesRegex(AssertionError,'spacing'):
            b.geometry(self.s,p)

    def test_case_halves_nonintersecting(self):
        self.assertAlmostEqual(float((self.g['assembled']['base'].solid^self.g['assembled']['cover'].solid).volume()),0,places=5)

    def test_nominal_pcb_does_not_intersect_plastic(self):
        q=self.p['case'];bx,by=q['board_origin_xy'];z=q['board_seat_z']
        pcb=b.c.box(self.s['width'],self.s['length'],q['board_thickness']).move((bx,by,z))
        for name in ['base','cover']:
            self.assertAlmostEqual(float((pcb.solid^self.g['assembled'][name].solid).volume()),0,places=5)

    def test_bulkhead_core_and_tool_access_are_open(self):
        # A complete 1/4 inch barrel must pass; an inherited D-flat fails this.
        q=self.p['case']
        for port in self.p['rf']['ports']:
            x,y,z=port['center']
            core=b.c.cylinder(6.35,q['wall']+.4).rotate((90,0,0)).move((x,q['wall']+.2,z))
            tool=b.c.cylinder(self.p['rf']['tool_clearance_diameter'],12).rotate((90,0,0)).move((x,q['wall']+12.1,z))
            self.assertAlmostEqual(float((core.solid^self.g['nodes']['base'].solid).volume()),0,places=5)
            self.assertAlmostEqual(float((tool.solid^self.g['nodes']['base'].solid).volume()),0,places=5)

    def test_ceiling_mounting_holes_match_frame(self):
        q=self.p['case']
        for x,y in self.g['ceiling']:
            probe=b.c.cylinder(q['mounting_screw_hole']-.2,q['floor']+q['ceiling_spacing']).move((x,y,-q['ceiling_spacing']))
            for name in ['base','ceiling-spacing-frame']:
                self.assertAlmostEqual(float((probe.solid^self.g['assembled'][name].solid).volume()),0,places=5)

    def test_native_jack_corridor_is_open(self):
        q=self.p['case'];bx,by=q['board_origin_xy']
        x0,y0,x1,y1=self.s['design']['mechanics']['rj45']['service_corridor_global_mm']
        probe=b.c.box(x1-x0,y1-y0,24).move((bx+x0,by+y0,20))
        self.assertAlmostEqual(float((probe.solid^self.g['assembled']['base'].solid).volume()),0,places=5)

    def test_route_guides_allow_connector_and_service_slack(self):
        self.assertEqual(len(self.g['routes']),3)
        for route in self.g['routes']:
            self.assertGreaterEqual(route['cable_length_minimum_budget_mm']-route['polyline_guide_length_mm'],30)
            self.assertEqual(route['cable_length_minimum_budget_mm'],144)
            self.assertGreaterEqual(route['straight_bulkhead_lead_mm'],21)
            self.assertIn('unmeasured',route['status'])

    def test_coupon_wall_and_short_cable(self):
        self.assertAlmostEqual(b.c.mesh_of(self.g['nodes']['bulkhead-fit-coupon']).extents[2],self.p['case']['wall'])
        p=copy.deepcopy(self.p)
        p['rf'].update(cable_length_trial=100,cable_length_minimum_budget=94)
        with self.assertRaisesRegex(AssertionError,'slack allowance'):
            b.geometry(self.s,p)

    def test_bulkhead_lead_in_keeps_declared_straight_reservation(self):
        for route in self.g['routes']:
            start,support,_=route['points_mm']
            self.assertEqual(start[0],support[0])
            self.assertEqual(start[2],support[2])
            self.assertGreaterEqual(support[1]-start[1],self.p['rf']['internal_straight_reservation'])
        p=copy.deepcopy(self.p);p['rf']['ports'][0]['strap_xy'][1]=20
        with self.assertRaisesRegex(AssertionError,'straight lead-in'):
            b.geometry(self.s,p)

    def test_floor_hardware_clearance_inside_spacing_frame(self):
        q=self.p['case'];self.assertGreaterEqual(q['ceiling_spacing'],4)
        xy=list(self.g['pcb_holes'].values())+[(self.g['rearcenter']+dx,q['length']-12) for dx in [-19,19]]
        for x,y in xy:
            screw=b.c.cylinder(6,3).move((x,y,-3))
            self.assertAlmostEqual(float((screw.solid^self.g['assembled']['ceiling-spacing-frame'].solid).volume()),0,places=5)

    def test_all_prints_closed_connected_and_on_bed(self):
        for name,node in self.g['nodes'].items():
            with self.subTest(name=name):
                mesh=b.c.mesh_of(node)
                self.assertTrue(mesh.is_watertight)
                self.assertTrue(mesh.is_winding_consistent)
                self.assertEqual(len(mesh.split()),1)
                self.assertGreater(mesh.volume,0)
                self.assertAlmostEqual(mesh.bounds[0,2],0,places=5)

if __name__=='__main__':unittest.main()
