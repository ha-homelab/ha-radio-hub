"""Keep portable export checks tolerant of rendering, strict about geometry."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image, PngImagePlugin

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('portable_test_build',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class PortableExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.a=root/'actual';self.e=root/'expected'
        for d in [self.a,self.e]:
            d.mkdir();self.mesh(d,2)
            Image.new('RGB',(8,8),'blue').save(d/'preview.png')
            (d/'drawing.svg').write_text('<svg/>\n')
            self.record(d)
    def mesh(self,d,x):
        solid=b.csg.subtract(b.csg.box(10,10,2),b.csg.cylinder(1,3).move((x,5,-.5)))
        (d/'part.stl').write_text(b.csg.trimesh.exchange.stl.export_stl_ascii(b.csg.mesh_of(solid)))
    def record(self,d):
        record={'generator_sha256':'same-source','parts':{'part':{'sha256':b.sha(d/'part.stl')}},
                'generated_sha256':{n:b.sha(d/n) for n in ['part.stl','drawing.svg','preview.png']}}
        (d/'verification.json').write_text(json.dumps(record))
    def check(self,exact=False):b.portable.check_outputs(self.a,self.e,b.csg,exact=exact)
    def test_equivalent_mesh_export_and_png_metadata_are_portable(self):
        mesh=b.csg.trimesh.load_mesh(self.a/'part.stl',process=True)
        mesh.faces=mesh.faces[::-1]
        (self.a/'part.stl').write_text(b.csg.trimesh.exchange.stl.export_stl_ascii(mesh))
        info=PngImagePlugin.PngInfo();info.add_text('renderer','another supported platform')
        Image.new('RGB',(8,8),'blue').save(self.a/'preview.png',pnginfo=info)
        self.record(self.a);self.check()
        with self.assertRaisesRegex(ValueError,'exact export'):self.check(exact=True)
    def test_same_bounds_changed_feature_is_rejected(self):
        self.mesh(self.a,8);self.record(self.a)
        with self.assertRaisesRegex(ValueError,'stale geometry'):self.check()
    def test_unrecorded_png_change_is_rejected(self):
        Image.new('RGB',(8,8),'red').save(self.a/'preview.png')
        with self.assertRaisesRegex(ValueError,'recorded export hash'):self.check()
    def test_stale_source_contract_is_rejected(self):
        p=self.a/'verification.json';r=json.loads(p.read_text());r['generator_sha256']='old-source';p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'metadata differs'):self.check()

if __name__=='__main__':unittest.main()
