"""Independent manufacturer-derived adapter pin coordinates; no network or KiCad dependency."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parent
REFERENCE=json.loads((ROOT/'reference/adapter-contacts.json').read_text())


def footprint_contacts(text):
    """Read the named TH pads in these simple native KiCad adapter footprints."""
    found=re.findall(r'\(pad\s+"([^"]+)"\s+thru_hole\s+\w+\s+\(at\s+([-+.\d]+)\s+([-+.\d]+)',text)
    assert len(found)==len(re.findall(r'\(pad\s',text)), 'unparsed or non-through-hole pad'
    assert len({p for p,_,_ in found})==len(found), 'duplicate pad number'
    return {p:(float(x),float(y)) for p,x,y in found}


def assert_contacts(testcase, expected, actual):
    testcase.assertEqual(set(expected),set(actual))
    for pin,xy in expected.items():
        testcase.assertAlmostEqual(xy[0],actual[pin][0],places=5,msg='pin '+pin+' X')
        testcase.assertAlmostEqual(xy[1],actual[pin][1],places=5,msg='pin '+pin+' Y')


class AdapterReferenceTests(unittest.TestCase):
    def test_source_provenance_and_complete_34_contacts(self):
        self.assertEqual(sum(len(a['contacts']) for a in REFERENCE['adapters']),34)
        for adapter,count in zip(REFERENCE['adapters'],[28,6]):
            self.assertEqual(adapter['source']['commit'],'dbd7a1928c2b668a9edf3d53277063eac4c3e938')
            self.assertRegex(adapter['source']['sha256'],r'^[a-f0-9]{64}$')
            self.assertEqual({p['ic_pin'] for p in adapter['contacts']},{str(n) for n in range(1,count+1)})

    def test_all_native_adapter_contacts(self):
        for adapter in REFERENCE['adapters']:
            expected={p['ic_pin']:p['position_mm'] for p in adapter['contacts']}
            actual=footprint_contacts((ROOT/'DIY.pretty'/(adapter['footprint']+'.kicad_mod')).read_text())
            assert_contacts(self,expected,actual)

    def test_independent_orientation_anchors(self):
        tssop,sot=REFERENCE['adapters']
        t={p['ic_pin']:p for p in tssop['contacts']}
        self.assertEqual((t['1']['source_header'],t['1']['source_header_pin']),('JP2','1'))
        self.assertEqual(t['1']['position_mm'],[0,0])
        self.assertEqual(t['14']['position_mm'],[0,33.02])
        self.assertEqual(t['28']['position_mm'],[15.24,0])
        s={p['ic_pin']:p for p in sot['contacts']}
        self.assertEqual((s['1']['source_header'],s['1']['source_header_pin']),('JP2','1'))
        self.assertEqual(s['3']['position_mm'],[0,5.08])
        self.assertEqual(s['6']['position_mm'],[7.62,0])

    def test_mirrored_or_swapped_adapter_fails(self):
        for adapter in REFERENCE['adapters']:
            expected={p['ic_pin']:p['position_mm'] for p in adapter['contacts']}
            actual=copy.deepcopy(expected)
            last=str(len(expected));actual['1'],actual[last]=actual[last],actual['1']
            with self.assertRaises(AssertionError):assert_contacts(self,expected,actual)


if __name__=='__main__':unittest.main()
