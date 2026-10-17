"""CAD export freshness regressions; only disposable generated files are changed."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import numpy as np
import trimesh

from mechanical.build import (ROOT, StaleAssets, assembly_poses, check_assets,
                              generate, mesh_of, pose_matrix, solid_from_mesh, Node)
import manifold3d as mf


class GeneratedAssetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory(prefix='cad-test-reference-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.expected=Path(cls.directory.name)
        cls.parameters=json.loads((ROOT/'parameters.json').read_text())
        generate(cls.parameters,cls.expected)

    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='cad-test-copy-')
        self.addCleanup(self.directory.cleanup)
        self.actual=Path(self.directory.name)/'generated'
        shutil.copytree(self.expected,self.actual)

    def accept_new_checksum(self,name):
        """Simulate a coherent older export, not merely a corrupted file."""
        report_path=self.actual/'mesh-report.json'
        report=json.loads(report_path.read_text())
        checksum=hashlib.sha256((self.actual/name).read_bytes()).hexdigest()
        report['artifacts'][name]=checksum
        if name.endswith('.stl'):
            report['parts'][Path(name).stem]['sha256']=checksum
        report_path.write_text(json.dumps(report))

    def test_current_assets_and_reordered_stl_pass_without_rewriting(self):
        check_assets(self.actual,self.expected)
        path=self.actual/'fit_coupon.stl'
        mesh=trimesh.load_mesh(path)
        mesh.faces=mesh.faces[::-1]
        mesh.export(path)
        self.assertNotEqual(path.read_bytes(),(self.expected/path.name).read_bytes())
        self.accept_new_checksum(path.name)
        before={p.name:p.read_bytes() for p in self.actual.iterdir()}
        check_assets(self.actual,self.expected)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.actual.iterdir()})

    def test_hole_change_with_identical_bounds_is_rejected(self):
        path=self.actual/'fit_coupon.stl'
        mesh=trimesh.load_mesh(path)
        solid=solid_from_mesh(mesh,path.name)
        bore=mf.Manifold.cylinder(10,1,circular_segments=32).translate((35,10,-1))
        modified=mesh_of(Node(solid-bore,''))
        np.testing.assert_equal(mesh.bounds,modified.bounds)
        modified.export(path)
        self.accept_new_checksum(path.name)
        with self.assertRaisesRegex(StaleAssets,'symmetric difference'):
            check_assets(self.actual,self.expected)

    def test_stale_scad_is_rejected_even_with_matching_report_checksum(self):
        path=self.actual/'lid.scad'
        path.write_text(path.read_text()+'translate([1,0,0]) cube(1);\n')
        self.accept_new_checksum(path.name)
        with self.assertRaisesRegex(StaleAssets,'stale CSG'):
            check_assets(self.actual,self.expected)

    def test_missing_preview_is_rejected(self):
        (self.actual/'layout-plan.png').unlink()
        with self.assertRaisesRegex(StaleAssets,'inventory'):
            check_assets(self.actual,self.expected)

    def test_stale_generator_or_parameters_are_rejected(self):
        path=self.actual/'mesh-report.json'
        report=json.loads(path.read_text())
        report['inputs']['parameters']['radar_skin']=1.0
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(StaleAssets,'stale CAD source or parameters'):
            check_assets(self.actual,self.expected)

    def test_reflected_lid_in_assembly_is_rejected(self):
        path=self.actual/'assembly.glb'
        scene=trimesh.load(path,force='scene')
        reflection=np.eye(4)
        reflection[0,0]=-1
        reflection[0,3]=self.parameters['width']/1000
        scene.geometry['lid'].apply_transform(reflection)
        scene.export(path)
        self.accept_new_checksum(path.name)
        with self.assertRaisesRegex(StaleAssets,'assembly.glb/lid: stale geometry'):
            check_assets(self.actual,self.expected)

    def test_print_to_assembly_poses_preserve_handedness(self):
        poses=assembly_poses(self.parameters)
        for rotation,translation in poses.values():
            self.assertAlmostEqual(np.linalg.det(pose_matrix(rotation,translation)[:3,:3]),1)
        rotation,translation=poses['lid']
        corners=trimesh.transform_points([[0,0,0],[self.parameters['width'],0,0]],
                                        pose_matrix(rotation,translation))
        np.testing.assert_allclose(corners,[[240,0,80],[0,0,80]],atol=0.000001)


if __name__=='__main__':
    unittest.main()
