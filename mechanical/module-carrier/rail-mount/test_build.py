"""Meaningful fit-coupon geometry checks; no hardware-fit claim."""
import importlib.util
import json
import copy
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rail_study_build',HERE/'build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
PARAMETERS=json.loads((HERE/'parameters.json').read_text())

class RailCouponTests(unittest.TestCase):
    @staticmethod
    def source():
        return {'lands':[{'id':'left','bounds_mm':[0,15,.85,54.5]},
                         {'id':'right','bounds_mm':[46.3,8,47.5,74]}]}

    def test_nominal_lips_reserve_pointwise_motion_at_all_boundaries(self):
        source=self.source();bands=build.nominal_contact_bands(source,PARAMETERS)
        dx=PARAMETERS['interface']['trial_edge_displacement_budget_mm']['x']
        dy=PARAMETERS['interface']['trial_edge_displacement_budget_mm']['y']
        for band,land in zip(bands,source['lands']):
            bound=land['bounds_mm']
            for x_shift in [-dx,0,dx]:
                for y_shift in [-dy,0,dy]:
                    # Clip the actual bearing to the board edge. Outer material
                    # is the case wall, not a contact on the board surface.
                    inner_left=max(band[0]+x_shift,0)
                    inner_right=min(band[2]+x_shift,47.5)
                    self.assertGreaterEqual(inner_left+1e-9,bound[0])
                    self.assertLessEqual(inner_right-1e-9,bound[2])
                    self.assertGreaterEqual(band[1]+y_shift+1e-9,bound[1])
                    self.assertLessEqual(band[3]+y_shift-1e-9,bound[3])
            nominal_depth=band[2]-band[0]
            expected_min=.45 if land['id']=='left' else .8
            self.assertAlmostEqual(nominal_depth-dx,expected_min)

    def test_budget_cannot_leave_no_guaranteed_engagement(self):
        p=copy.deepcopy(PARAMETERS);p['interface']['trial_edge_displacement_budget_mm']['x']=.43
        with self.assertRaises(AssertionError):build.nominal_contact_bands(self.source(),p)

    def test_side_clearance_cannot_exceed_motion_allowance(self):
        p=copy.deepcopy(PARAMETERS);p['interface']['trial_side_clearance_per_edge_mm']=.21
        with self.assertRaises(AssertionError):build.nominal_contact_bands(self.source(),p)

    def test_unknown_dimensions_are_not_filled_by_nominal_values(self):
        for name in ['pcb_actual_thickness_mm','pcb_actual_width_mm','selected_slot_height_mm',
                     'front_component_projection_measured_mm','rear_component_projection_measured_mm',
                     'case_internal_height_mm','case_attachment_coordinates_mm',
                     'actual_side_clearance_per_edge_mm','actual_max_edge_excursion_mm']:
            self.assertIsNone(PARAMETERS[name],name)

    def test_coupon_gap_and_bearing_faces(self):
        q=PARAMETERS['coupon'];csg=build.csg
        for i,gap in enumerate(PARAMETERS['trial_slot_heights_mm'],1):
            with self.subTest(gap=gap):
                node=build.coupon_node(gap,PARAMETERS,i)
                # Undo the rigid print orientation to test the intended slot.
                height=q['base_mm']+gap+q['upper_lip_mm']
                solid=node.solid.translate((-height,0,0)).rotate((0,90,0))
                x=q['wall_mm']+q['engagement_mm']/2;y=q['length_mm']/2
                probe=lambda z:csg.box(.1,.1,.1).move((x,y,z)).solid
                self.assertAlmostEqual(float((solid^probe(q['base_mm']+gap/2)).volume()),0,places=8)
                self.assertGreater(float((solid^probe(q['base_mm']-.15)).volume()),.0009)
                self.assertGreater(float((solid^probe(q['base_mm']+gap+.05)).volume()),.0009)
                mesh=csg.mesh_of(node)
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(len(mesh.split(only_watertight=False)),1)
                self.assertGreater(mesh.volume,0)
                self.assertAlmostEqual(mesh.bounds[0][2],0,places=5)
                self.assertAlmostEqual(mesh.bounds[1][2],q['handling_base_width_mm'],places=5)

    def test_larger_gaps_do_not_change_bearing_engagement(self):
        # The wall grows with gap; lower and upper bearing depth is constant.
        q=PARAMETERS['coupon'];csg=build.csg
        for gap in PARAMETERS['trial_slot_heights_mm']:
            node=build.coupon_node(gap,PARAMETERS,1)
            height=q['base_mm']+gap+q['upper_lip_mm']
            solid=node.solid.translate((-height,0,0)).rotate((0,90,0))
            beyond=csg.box(.1,.1,.1).move((q['wall_mm']+q['engagement_mm']+.05,5,q['base_mm']+gap+.1))
            self.assertAlmostEqual(float((solid^beyond.solid).volume()),0,places=8)

    def test_invalid_gap_is_rejected(self):
        with self.assertRaises(AssertionError):build.coupon_node(0,PARAMETERS,1)

    def test_nominal_pcb_tolerance_is_not_zero(self):
        p=PARAMETERS;t=p['pcb_nominal_thickness_mm'];tol=p['pcb_fabrication_thickness_tolerance_fraction']
        self.assertAlmostEqual(t*(1-tol),1.44)
        self.assertAlmostEqual(t*(1+tol),1.76)
        self.assertAlmostEqual(min(p['trial_slot_heights_mm'])-t*(1+tol),.04)

if __name__=='__main__':unittest.main()
