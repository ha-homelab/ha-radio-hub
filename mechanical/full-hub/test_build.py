#!/usr/bin/env python3
"""Regression checks for real enclosure integration errors, not fit claims."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('full_hub_build',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class FullHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((HERE/'parameters.json').read_text())
        cls.m=b.manifest();cls.s=b.source();cls.g=b.geometry(cls.p,cls.m,cls.s)
        cls.checks=b.validate(cls.p,cls.m,cls.s,cls.g)

    def test_every_module_and_power_accessory_is_mounted(self):
        expected={'carrier','poe_splitter','buck','wk2132','zwave','cc1101','ld2450','bme680','dc_adapter','fuse_holder'}
        self.assertEqual(set(self.g['bounds']),expected)
        self.assertEqual(set(self.g['mounting']),expected)

    def test_all_native_carrier_holes_are_used(self):
        x,y,z=self.p['placements']['carrier']
        expected=sorted((x+h[0],y+h[1])for h in self.s['holes'].values())
        self.assertEqual(sorted(self.g['carrier_holes']),expected)
        self.assertEqual(len(expected),4)
        self.assertEqual(self.g['bounds']['carrier'][4]-y,102)

    def test_real_component_collision_is_rejected(self):
        bad=copy.copy(self.g);bad['bounds']=copy.deepcopy(self.g['bounds'])
        bad['bounds']['poe_splitter']=bad['bounds']['carrier'].copy()
        with self.assertRaisesRegex(AssertionError,'Component overlap'):
            b.validate(self.p,self.m,self.s,bad)

    def test_replacement_radio_must_fit_populated_carrier_reservation(self):
        bad=copy.deepcopy(self.s)
        radio=next(p for p in bad['design']['parts'] if p['ref']=='U2')
        radio['body_bounds_global_mm'][2]=101
        with self.assertRaisesRegex(AssertionError,'U2 module exceeds'):
            b.validate(self.p,self.m,bad,self.g)

    def test_taller_radio_or_usb_shell_cannot_escape_fit_checks(self):
        bad=copy.deepcopy(self.s)
        bad['design']['mechanics']['module_geometry']['U2']['model_height_mm']=9
        with self.assertRaisesRegex(AssertionError,'U2 nominal model exceeds'):
            b.validate(self.p,self.m,bad,self.g)
        bad=copy.deepcopy(self.s)
        bad['design']['mechanics']['physical_usb_shells_mm']['U2'][1]=-1
        with self.assertRaisesRegex(AssertionError,'U2 module exceeds'):
            b.validate(self.p,self.m,bad,self.g)

    def test_zac93_has_socket_and_underneath_header_clearance(self):
        z=self.checks['detailed_component_solids_mm']['zwave']
        header=self.checks['mated_connector_boxes_mm']['zac93-underside-mating-header']
        self.assertAlmostEqual(z[0][2],26.4)
        self.assertAlmostEqual(z[1][5],z[0][2])
        self.assertAlmostEqual(header[5],z[1][2])
        self.assertLess(header[2],header[5])
        self.assertEqual(self.g['mounting']['zwave']['socket_envelope_mm'],z[1])

    def test_filling_zac93_socket_bay_is_rejected(self):
        bad=copy.copy(self.g);bad['assembled']=dict(self.g['assembled'])
        x,y,z=self.p['placements']['zwave']
        bad['assembled']['zwave-tray']=b.c.union(bad['assembled']['zwave-tray'],b.c.box(12,15,10).move((x+1,y+1,14)))
        with self.assertRaisesRegex(AssertionError,'clashes|collides|interference|reservation|collision'):
            b.validate(self.p,self.m,self.s,bad)

    def test_stock_zac93_antenna_is_clear_and_not_below_radar(self):
        z=self.g['bounds']['zwave'];r=self.g['bounds']['ld2450']
        self.assertFalse(z[0]<r[3] and r[0]<z[3] and z[1]<r[4] and r[1]<z[4])
        for name,box in self.g['bounds'].items():
            self.assertFalse(b.overlap(box,self.checks['keepouts_mm']['zac93-outboard-antenna-air-reservation']),name)

    def test_regulator_board_support_and_solder_clearance(self):
        mount=self.g['mounting']['buck'];details=self.checks['regulator_subassembly_mm']
        self.assertEqual(mount['local_hole_centres_mm'],[])
        self.assertEqual(details['perfboard'][2],12)
        self.assertAlmostEqual(details['underside_solder'][2]-8.4,1.6)
        self.assertEqual(self.m['buck']['mount']['perfboard_mm'],[24,24,1.6])
        for box in details.values():self.assertTrue(b.contains(self.g['bounds']['buck'],box))
        self.assertGreater(self.m['buck']['mount']['strap_band_local_y_mm'][0],
                           self.m['buck']['mount']['capacitor_local_body_origin_mm'][1]+5.5)

    def test_untrimmed_regulator_leads_are_rejected(self):
        bad=copy.deepcopy(self.m)
        bad['buck']['mount']['maximum_tail_below_board_mm']=5
        with self.assertRaisesRegex(AssertionError,'Regulator underside_solder escapes'):
            b.validate(self.p,bad,self.s,self.g)

    def test_oversize_replacement_input_capacitor_is_rejected(self):
        bad=copy.deepcopy(self.m)
        bad['buck']['mount']['capacitor_max_body_mm'][2]=25
        with self.assertRaisesRegex(AssertionError,'Regulator input_capacitor escapes'):
            b.validate(self.p,bad,self.s,self.g)

    def test_all_power_and_data_branches_have_routes(self):
        ids={v['id']for v in self.checks['routes']}
        self.assertNotIn('wk2132-zac93-uart',ids)
        self.assertNotIn('fuse-buck-input',ids)
        self.assertLessEqual({'j3-wk2132','j4-zac93','j5-cc1101','j2-buck','poe-dc-adapter','dc-adapter-fuse','fuse-j1','ambient-harness','radar-service-loop','ethernet'},ids)
        for route in self.checks['routes']:
            self.assertGreater(route['length_mm'],0)
            self.assertEqual(len(route['segment_envelopes_mm']),len(route['points_mm'])-1)

    def test_rf_bulkheads_are_in_fixed_base(self):
        self.assertEqual(len(self.p['rf_ports']),3)
        for port in self.p['rf_ports']:
            x,y,z=port['center'];self.assertEqual(y,0)
            pin=b.c.cylinder(2,4).rotate((90,0,0)).move((x,3,z))
            self.assertLess((pin.solid^self.g['nodes']['base'].solid).volume(),.1)
        self.assertEqual(self.g['poses']['base'],((0,0,0),(0,0,0)))

    def test_full_round_sma_barrel_fits_and_coupon_matches_wall(self):
        wall=self.p['case']['wall']
        for port in self.p['rf_ports']:
            x,y,z=port['center']
            barrel=b.c.cylinder(6.35,wall+.2).rotate((90,0,0)).move((x,wall+.1,z))
            self.assertLess((barrel.solid^self.g['nodes']['base'].solid).volume(),.01)
        self.assertAlmostEqual(b.c.mesh_of(self.g['nodes']['fit-coupon']).extents[2],wall)

    def test_coax_shortfall_and_service_slack_are_both_reserved(self):
        rf=self.p['rf_harness']
        self.assertEqual(rf['minimum_length_budget_mm'],144)
        for route in self.checks['routes']:
            if 'coax' not in route['id']:continue
            self.assertLessEqual(route['guide_length_upper_bound_mm']+25,144)
            self.assertGreaterEqual(route['straight_bulkhead_lead_mm'],21)
            self.assertTrue(route['bend_arcs'])
            self.assertTrue(all(arc['radius_mm']>=6.8 for arc in route['bend_arcs']))
        bad=copy.deepcopy(self.p)
        bad['rf_harness']['minimum_length_budget_mm']=150
        with self.assertRaisesRegex(AssertionError,'shortfall allowance'):
            b.validate(bad,self.m,self.s,self.g)
        bad=copy.deepcopy(self.p)
        bad['rf_harness'].update(nominal_length_mm=130,minimum_length_budget_mm=124)
        with self.assertRaisesRegex(AssertionError,'insufficient coax length'):
            b.validate(bad,self.m,self.s,self.g)

    def test_coax_bend_radius_is_geometric_not_only_a_label(self):
        points,arcs,lead=b.rounded_coax_path([[0,0,0],[30,0,0],[30,30,0]],6.8,17)
        self.assertAlmostEqual(lead,23.2)
        self.assertAlmostEqual(arcs[0]['center_mm'][0],23.2)
        self.assertAlmostEqual(arcs[0]['center_mm'][1],6.8)
        for point in points[1:-1]:
            self.assertAlmostEqual(b.math.dist(point,arcs[0]['center_mm']),6.8)
        with self.assertRaisesRegex(AssertionError,'bend radius'):
            b.rounded_coax_path([[0,0,0],[5,0,0],[5,5,0]],6.8,0)
        with self.assertRaisesRegex(AssertionError,'heatshrink'):
            b.rounded_coax_path([[0,0,0],[20,0,0],[20,30,0]],6.8,17)

    def test_radar_window_has_solid_skin_and_nominal_gap(self):
        p=self.p;mount=self.g['mounting']['ld2450']
        self.assertAlmostEqual(p['radar']['inner_window_z_mm']-p['radar']['antenna_plane_z_mm'],12.4)
        self.assertEqual(mount['radome_skin_mm'],.8)
        x,y,z=p['placements']['ld2450'];test=b.c.box(2,2,.4).move((x+10,y+5,77.4))
        self.assertGreater((test.solid^self.g['assembled']['lid'].solid).volume(),1.5)

    def test_radar_restraints_cross_board_ends_not_empty_air(self):
        x,y,z=self.p['placements']['ld2450'];width=self.m['ld2450']['design_envelope_mm'][0]
        strips=self.g['mounting']['ld2450']['board_end_strap_x_ranges_mm']
        for low,high in strips:
            self.assertGreaterEqual(low,x)
            self.assertLessEqual(high,x+width)
        self.assertLessEqual(strips[0][1],x+3)
        self.assertGreaterEqual(strips[1][0],x+width-4)

    def test_bme_pod_is_attached_with_two_arms(self):
        self.assertIn('pod-arm-2',self.g['assembled'])
        self.assertEqual(self.g['mounting']['bme680']['arm_quantity'],2)
        self.assertEqual(self.g['mounting']['bme680']['air_gap_mm'],17)
        for name in ['pod-arm','pod-arm-2']:
            bounds=b.c.mesh_of(self.g['assembled'][name]).bounds
            self.assertAlmostEqual(bounds[0][0],self.p['case']['width'])
            self.assertGreater(bounds[1][0],self.p['pod']['origin'][0])

    def test_all_print_parts_connected_watertight_and_fit_with_brim(self):
        for key,node in self.g['nodes'].items():
            mesh=b.c.mesh_of(node)
            with self.subTest(part=key):
                self.assertTrue(mesh.is_watertight);self.assertTrue(mesh.is_winding_consistent)
                self.assertEqual(len(mesh.split()),1)
                self.assertAlmostEqual(mesh.bounds[0][2],0,places=4)
                self.assertLessEqual(mesh.extents[0]+4,220)
                self.assertLessEqual(mesh.extents[1]+4,220)

    def test_native_header_collision_is_rejected(self):
        bad=copy.copy(self.g);bad['assembled']=dict(self.g['assembled'])
        bad['assembled']['bad_header_obstacle']=b.c.box(1,1,2).move((52.5,110.5,33))
        with self.assertRaisesRegex(AssertionError,'Native J2 header'):
            b.validate(self.p,self.m,self.s,bad)

    def test_cable_sweep_rejects_real_plastic_obstacle(self):
        bad=copy.copy(self.g);bad['assembled']=dict(self.g['assembled'])
        bad['assembled']['bad_harness_obstacle']=b.c.box(2,2,2).move((121,119,49))
        with self.assertRaisesRegex(AssertionError,'Cable sweep collides'):
            b.validate(self.p,self.m,self.s,bad)

    def test_j2_diagonal_through_wiznet_is_rejected(self):
        routes=copy.deepcopy(b.cable_routes(self.p,self.s))
        route=next(r for r in routes if r['id']=='j2-buck')
        del route['points_mm'][1] # remove the vertical rise above the jack
        with patch.object(b,'cable_routes',return_value=routes):
            with self.assertRaisesRegex(AssertionError,"obstacle.*U4"):
                b.validate(self.p,self.m,self.s,self.g)

    def test_j1_diagonal_through_wiznet_is_rejected(self):
        routes=copy.deepcopy(b.cable_routes(self.p,self.s))
        route=next(r for r in routes if r['id']=='fuse-j1')
        del route['points_mm'][-2] # remove the vertical drop outside the jack
        with patch.object(b,'cable_routes',return_value=routes):
            with self.assertRaisesRegex(AssertionError,"obstacle.*U4"):
                b.validate(self.p,self.m,self.s,self.g)

    def test_physical_fit_is_never_promoted_by_digital_checks(self):
        self.assertFalse(self.checks['physical_fit_verified'])
        self.assertIn('prototype',self.p['status'])
        for component in self.m.values():
            self.assertFalse(component.get('fit_verified',False))

if __name__=='__main__':unittest.main(verbosity=2)
