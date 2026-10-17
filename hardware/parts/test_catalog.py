import copy
import json
import html
import unittest
from build import HERE, ROOT, inventory, outputs, read_rows, image_for, dimensions, purchase_link, family
from validate import validate


class CatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((HERE/'catalog.json').read_text())
        cls.data=inventory(cls.config)

    def test_full_canonical_coverage(self):
        self.assertTrue(validate(self.config,self.data))
        # Every discoverable assembly/harness source must be registered; duplicate
        # fabrication exports are intentionally excluded.
        configured={s['path'] for s in self.config['sources']}
        for glob in ['assembly-bom.csv','harness-bom.csv']:
            for path in (ROOT/'hardware/low-power').rglob(glob):
                if 'fabrication' not in path.parts:
                    self.assertIn(str(path.relative_to(ROOT)),configured)

    def test_missing_row_fails(self):
        data=copy.deepcopy(self.data);data['cards'][0]['rows'].pop()
        with self.assertRaisesRegex(ValueError,'coverage'):validate(self.config,data)

    def test_duplicate_row_fails(self):
        data=copy.deepcopy(self.data);data['cards'][0]['rows']*=2
        with self.assertRaisesRegex(ValueError,'coverage'):validate(self.config,data)

    def test_changed_value_fails(self):
        data=copy.deepcopy(self.data);data['cards'][0]['rows'][0]['qty']='999'
        with self.assertRaisesRegex(ValueError,'canonical'):validate(self.config,data)

    def test_no_verified_listing_claim(self):
        data=copy.deepcopy(self.data);data['cards'][0]['ali']['kind']='verified_listing'
        with self.assertRaisesRegex(ValueError,'Purchase claim'):validate(self.config,data)

    def test_no_unreviewed_manufacturer_image(self):
        data=copy.deepcopy(self.data)
        card=next(c for c in data['cards'] if c['image']['kind']=='manufacturer_photo')
        card['image']['url']='https://example.com/invented.jpg'
        with self.assertRaisesRegex(ValueError,'reviewed source'):validate(self.config,data)

    def test_both_views_cover_every_card_and_row(self):
        generated=outputs(self.config)
        web=generated['index.html'];markdown=generated['../../docs/parts-gallery.md']
        for card in self.data['cards']:
            self.assertEqual(web.count('id="'+card['id']+'"'),1)
            self.assertEqual(markdown.count('id="'+card['id']+'"'),1)
            for row in card['rows']:
                self.assertIn('<b>'+html.escape(row['key'])+'</b>',web)
                self.assertIn('**'+row['key']+':**',markdown)

    def test_generated_fresh(self):
        for name,text in outputs(self.config).items():
            self.assertEqual((HERE/name).read_text(),text,name)

    def test_local_image_links_exist(self):
        for c in self.data['cards']:
            path=c['image']['url']
            if not path.startswith('https://'):self.assertTrue((HERE/path).is_file(),path)

    def test_product_names_in_accessories_do_not_select_photo(self):
        for name in ['Vented removable BME680 pod', 'WIZ850io cable', 'ZAC93 adapter cable', 'LD2450 4-pin cable', 'D24V22F3 cable', 'I0 external modules: ZAC93, CC1101, HLK-LD2450, Adafruit 3660']:
            row=dict(model=name,package='',source_id='accessory',ref='negative')
            self.assertEqual(image_for(row,self.config)['kind'],'original_illustration',name)

    def test_dimensions_are_readable(self):
        self.assertEqual(dimensions([25.4,17.78,None]),'25.4 × 17.78 mm; height unspecified')

    def test_custom_parts_link_project(self):
        for name in ['Vented removable BME680 pod','LP-M0 populated with MGM240PA22VNA3','Single-host PCB option: LP-C0 backplane or LP-I0 integrated board']:
            row=dict(model=name,package='',source_id='accessory',ref='negative')
            self.assertEqual(purchase_link(row)['kind'],'project_source')

    def test_diy_packages_have_through_hole_illustrations(self):
        rows={r['key']:r for r in read_rows(self.config)}
        for ref,profile in [('R1','resistor-axial'),('C8','capacitor-electrolytic'),('C10','capacitor-radial'),('Y1','crystal-through-hole')]:
            self.assertTrue(image_for(rows['d0:'+ref],self.config)['url'].endswith(profile+'.svg'))
        for ref in ['SC16 adapter','Supervisor adapter']:
            self.assertEqual(image_for(rows['d0-harness:'+ref],self.config)['kind'],'manufacturer_photo')
        for key, category in [('d0:Y1','crystal'), ('d0:F1','fuse'),
                              ('d0-harness:U1 adapter pins','connector'),
                              ('d0-harness:U2 adapter pins','connector')]:
            self.assertEqual(family(rows[key]),category,key)

    def test_sensitive_specs_preserved(self):
        rows={r['key']:r for r in read_rows(self.config)}
        self.assertIn('100V',rows['i0:C37']['model'])
        self.assertIn('2kV',rows['i0:C50']['model'])
        self.assertIn('0603',rows['i0:C11']['package'])
        self.assertIn('MGM240PA22VNA3',rows['m0:U1']['model'])


if __name__=='__main__':unittest.main()
