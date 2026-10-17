"""Disposable regression fixtures for the concept geometry and export guard."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('low_power_cad',ROOT/'build.py')
cad=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cad)


class LayoutChecks(unittest.TestCase):
    def setUp(self):
        self.p=json.loads((ROOT/'parameters.json').read_text())

    def test_default_allocations_have_no_volume_collisions(self):
        result=cad.validate_layout(self.p,cad.models(self.p))
        self.assertEqual(result['checked_component_count'],11)
        self.assertTrue(all(v==0 for v in result['printed_part_intersections_mm3'].values()))
        self.assertEqual(result['physical_fit'],'NOT TESTED')

    def test_component_overlap_is_rejected(self):
        self.p['components'][1]['origin']=self.p['components'][0]['origin'][:]
        with self.assertRaisesRegex(ValueError,'volume interference'):
            cad.validate_layout(self.p,cad.models(self.p))

    def test_connector_exit_must_match_reserved_straight_route(self):
        self.p['case']['poe_opening'][0]=50
        with self.assertRaisesRegex(ValueError,'ethernet_plug.*blocked'):
            cad.validate_layout(self.p,cad.models(self.p))

    def test_fastener_heads_are_not_ignored(self):
        # A conventional fourth corner hole would put its head inside the jack.
        self.p['carrier']['mount_centres'][-1]=[155,95]
        with self.assertRaisesRegex(ValueError,'RJ45.*fastener head'):
            cad.validate_layout(self.p,cad.models(self.p))

    def test_antenna_reservations_reject_other_components(self):
        self.p['antenna_reservations'][0]['size'][0]=155
        with self.assertRaisesRegex(ValueError,'antenna reservation intersects'):
            cad.validate_layout(self.p,cad.models(self.p))

    def test_antenna_reservations_also_exclude_fastener_heads(self):
        self.p['carrier']['mount_centres'][0][1]=5
        with self.assertRaisesRegex(ValueError,'antenna reservation intersects a fastener'):
            cad.validate_layout(self.p,cad.models(self.p))

    def test_radars_support_plane_must_meet_its_bosses(self):
        self.p['radar_holder']['origin'][2]+=1
        with self.assertRaisesRegex(AssertionError,'meet lid bosses'):
            cad.models(self.p)

    def test_exported_assets_are_checked_and_stale_scad_is_rejected(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as e:
            actual,expected=Path(a),Path(e)
            cad.generate(self.p,actual);cad.generate(self.p,expected)
            cad.check(actual,expected)
            path=actual/'carrier_fit_blank.scad'
            path.write_text(path.read_text()+'// changed\n')
            with self.assertRaisesRegex(ValueError,'content differs'):
                cad.check(actual,expected)

    def test_mesh_change_with_updated_checksum_is_rejected(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as e:
            actual,expected=Path(a),Path(e)
            cad.generate(self.p,actual);cad.generate(self.p,expected)
            path=actual/'carrier_fit_blank.stl'
            mesh=cad.trimesh.load_mesh(path,process=True);mesh.apply_scale([1,1,.9]);mesh.export(path)
            report=json.loads((actual/'mesh-report.json').read_text())
            report['artifacts'][path.name]=cad.sha(path)
            report['parts']['carrier_fit_blank']['sha256']=cad.sha(path)
            (actual/'mesh-report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'stale geometry'):
                cad.check(actual,expected)


if __name__=='__main__':unittest.main()
