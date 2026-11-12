#!/usr/bin/env python3
"""Guard an artwork-only revision, including all non-silk native objects."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'mc2_sexpr', ROOT.parents[1] / 'module-carrier/audit_carrier.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
SILK = {'F.SilkS', 'B.SilkS'}


def clean(node, without_silk=False):
    if not isinstance(node, list):
        return node
    if node and node[0] in ('uuid', 'tstamp'):
        return None
    if without_silk and any(isinstance(x, list) and len(x) == 2
                            and x[0] == 'layer' and x[1] in SILK for x in node):
        return None
    result = [value for child in node if (value := clean(child, without_silk)) is not None]
    if node and node[0] == 'layer' and len(result) > 2:
        # KiCad reorders colour/thickness keys in stackup layer records.
        result = result[:2] + sorted(result[2:], key=lambda v: json.dumps(v))
    return result


def fingerprint(path, without_silk=False):
    tree = clean(reader.sexpr(path.read_text()), without_silk)
    # Root item order is not geometry. Polygon point order remains untouched.
    data = sorted(json.dumps(item, separators=(',', ':')) for item in tree[1:])
    return hashlib.sha256(json.dumps(data, separators=(',', ':')).encode()).hexdigest()


def artwork_fingerprint(path):
    tree = reader.sexpr(path.read_text())
    result = []
    def collect(node, ref='board'):
        if not isinstance(node, list):
            return
        if node and node[0] == 'footprint':
            ref = next(x[2] for x in node if isinstance(x, list) and x[:2] == ['property', 'Reference'])
        if any(isinstance(x, list) and len(x) == 2 and x[0] == 'layer' and x[1] in SILK for x in node):
            result.append([ref, clean(node)])
            return
        for child in node:
            collect(child, ref)
    collect(tree)
    return hashlib.sha256(json.dumps(sorted(json.dumps(x) for x in result)).encode()).hexdigest()


def verify():
    baseline = json.loads((ROOT / 'silkscreen-baseline.json').read_text())
    actual = fingerprint(ROOT / 'mc2.kicad_pcb', without_silk=True)
    assert actual == baseline['non_silk_native_sha256'], 'S1 must not change non-silkscreen native objects'
    qr = json.loads((ROOT / 'silkscreen-qr.json').read_text())
    matrix = qr['matrix']
    assert qr['url'] == 'https://ha-homelab.github.io/ha-radio-hub/'
    assert qr['quiet_zone_modules'] == 4 and qr['module_mm'] >= .4
    assert len(matrix) == 37 and all(len(row) == 37 and set(row) <= {'0', '1'} for row in matrix)
    assert all(set(row) == {'0'} for row in matrix[:4] + matrix[-4:])
    assert all(set(row[:4] + row[-4:]) == {'0'} for row in matrix)
    preview = json.loads((ROOT / 'silkscreen-preview-verification.json').read_text())
    for name, expected in preview['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, f'Stale preview: {name}'
    assert all(row['decoded_url'] == qr['url'] for row in preview['qr_decodes'])
    print('S1: every non-silkscreen native object matches the MC2-D baseline')


if __name__ == '__main__':
    verify()
