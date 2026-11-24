"""Check the published editable print against its STL and source profile."""
from collections import Counter
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PROJECT = HERE / 'commissioning' / 'FH1-ZAC93-XY3-PLA.3mf'
PROFILE = PROJECT.with_name('xy3-zac93-pla.ini')


def faces(triangles):
    # The STL and 3MF exporters use different decimal precision and may order
    # faces differently. Keep winding and multiplicity in the comparison.
    result = Counter()
    for triangle in triangles:
        a, b, c = [tuple(round(n, 5) for n in vertex) for vertex in triangle]
        result[min((a, b, c), (b, c, a), (c, a, b))] += 1
    return result


class CommissioningProject(unittest.TestCase):
    def test_cradle_mesh_and_build_position(self):
        with ZipFile(PROJECT) as archive:
            model = ET.fromstring(archive.read('3D/3dmodel.model'))
        self.assertEqual(model.get('unit'), 'millimeter')
        obj, = model.findall('{*}resources/{*}object')
        item, = model.findall('{*}build/{*}item')
        self.assertEqual(item.get('objectid'), obj.get('id'))
        self.assertEqual(item.get('printable', '1'), '1')
        matrix = list(map(float, item.attrib['transform'].split()))
        self.assertEqual(matrix[:9], [1, 0, 0, 0, 1, 0, 0, 0, 1])
        vertices = [tuple(float(v.attrib[k]) for k in 'xyz')
                    for v in obj.findall('{*}mesh/{*}vertices/{*}vertex')]
        triangles = [tuple(vertices[int(t.attrib[k])] for k in ('v1', 'v2', 'v3'))
                     for t in obj.findall('{*}mesh/{*}triangles/{*}triangle')]
        points = [tuple(map(float, line.split()[1:]))
                  for line in (HERE / 'zwave-tray.stl').read_text().splitlines()
                  if line.lstrip().startswith('vertex ')]
        self.assertEqual(len(points), 3 * len(triangles))
        self.assertGreater(len(triangles), 0)
        self.assertTrue(faces(triangles) == faces(points[i:i + 3] for i in range(0, len(points), 3)),
                        'Rebuild the project from the current cradle STL')
        xs, ys, zs = zip(*vertices)
        for values, shift in zip((xs, ys), matrix[9:11]):
            self.assertAlmostEqual((min(values) + max(values)) / 2 + shift, 100, places=4)
        self.assertAlmostEqual(min(zs) + matrix[11], 0, places=4)

    def test_embedded_preset_matches_ini(self):
        def settings(text):
            pairs = {}
            for line in text.splitlines():
                key, sep, value = line.removeprefix('; ').partition('=')
                if sep and not key.startswith('#'):
                    pairs[key.strip()] = value.strip().strip('"')
            return pairs

        with ZipFile(PROJECT) as archive:
            embedded = settings(archive.read('Metadata/Slic3r_PE.config').decode())
        for key, value in settings(PROFILE.read_text()).items():
            with self.subTest(key=key):
                self.assertEqual(embedded.get(key), value)
