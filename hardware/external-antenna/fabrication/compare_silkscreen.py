#!/usr/bin/env python3
"""Require the original MC2-D manufacturing geometry, allowing only S1 ink."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent


def normalized(data, name):
    if name.endswith('gbrjob'):
        obj = json.loads(data)
        obj['Header'].pop('CreationDate', None)
        return json.dumps(obj, sort_keys=True).encode()
    text = data.decode()
    text = re.sub(r'^%TF.CreationDate,[^*]+\*%$', '%TF.CreationDate,<timestamp>*%', text, flags=re.M)
    text = re.sub(r'^(G04 Created by KiCad \(PCBNEW [^)]+\) date )[^*]+(\*)$', r'\1<timestamp>\2', text, flags=re.M)
    text = re.sub(r'^; #@! TF.CreationDate,.+$', '; #@! TF.CreationDate,<timestamp>', text, flags=re.M)
    text = re.sub(r'^(; DRILL file KiCad [^\n]+? date ).+$', r'\1<timestamp>', text, flags=re.M)
    return text.encode()


def compare():
    old = ROOT / 'history/MC2-D-original-gerbers.zip'
    new = ROOT / 'MC2-D-S1-prototype-gerbers.zip'
    baseline_sha = hashlib.sha256(old.read_bytes()).hexdigest()
    assert baseline_sha == '5898031673d14b154e9d25f597b3b8dc522e52fdb28e6391236c0a5b4490a7fe'
    with zipfile.ZipFile(old) as before, zipfile.ZipFile(new) as after:
        assert len(before.namelist()) == len(after.namelist()) == 10
        assert set(before.namelist()) == set(after.namelist())
        same = {name: normalized(before.read(name), name) == normalized(after.read(name), name)
                for name in sorted(before.namelist())}
    changed = [name for name, equal in same.items() if not equal]
    assert changed == ['mc2-B_Silkscreen.gbo', 'mc2-F_Silkscreen.gto'], changed
    return {'artwork_revision': 'S1', 'baseline_archive_sha256': baseline_sha,
            'current_archive_sha256': hashlib.sha256(new.read_bytes()).hexdigest(),
            'comparison': 'Exact native export contents with creation timestamps removed; job JSON keys sorted. No geometric normalization.',
            'unchanged_members': [name for name, equal in same.items() if equal],
            'changed_members': changed}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    report = json.dumps(compare(), indent=2) + '\n'
    path = ROOT / 'silkscreen-comparison.json'
    if args.check:
        assert path.read_text() == report, 'Stale silkscreen comparison'
    else:
        path.write_text(report)
    print('Only F/B silkscreen changed; all 8 other manufacturing members match')
