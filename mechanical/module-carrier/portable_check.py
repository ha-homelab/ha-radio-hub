"""Cross-platform generated-artifact checks for the MC1 mechanical packages.

Meshes are compared as solids; PNGs retain recorded-byte integrity and decoded
size checks, but are not compared pixel-for-pixel across renderer platforms.
Source contracts, textual drawings and CSG remain exact.
"""
import hashlib
import json
import math


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_metadata(actual, expected, path='report'):
    """Allow exporter rounding only; preserve source contracts and structure."""
    if isinstance(expected, dict):
        # These digest fields describe local export bytes, checked separately.
        ignored={'generated_sha256','sha256'}
        a={k:v for k,v in actual.items() if k not in ignored}
        e={k:v for k,v in expected.items() if k not in ignored}
        if set(a)!=set(e):raise ValueError(f'{path}: metadata keys differ')
        for key in e:compare_metadata(a[key],e[key],f'{path}.{key}')
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected):raise ValueError(f'{path}: metadata list differs')
        for i,(a,e) in enumerate(zip(actual,expected)):compare_metadata(a,e,f'{path}[{i}]')
    elif isinstance(expected,float):
        if not isinstance(actual,(int,float)) or not math.isclose(actual,expected,rel_tol=1e-6,abs_tol=1e-4):
            raise ValueError(f'{path}: numerical metadata differs')
    elif actual!=expected:
        raise ValueError(f'{path}: metadata differs')


def check_outputs(actual, expected, csg, exact=False):
    """Validate source freshness, recorded integrity and geometric equivalence."""
    files={p.name for p in expected.iterdir() if p.is_file()}
    for name in files:
        p=actual/name
        if not p.is_file() or p.is_symlink():raise ValueError(f'{name}: missing regular generated file')
    if exact:
        for name in files:
            if (actual/name).read_bytes()!=(expected/name).read_bytes():raise ValueError(f'{name}: exact export differs')
        return
    have=json.loads((actual/'verification.json').read_text())
    want=json.loads((expected/'verification.json').read_text())
    have_hashes=have['generated_sha256'];want_hashes=want['generated_sha256']
    if set(have_hashes)!=set(want_hashes):raise ValueError('Reported artifact inventory differs')
    for name,digest in have_hashes.items():
        if sha(actual/name)!=digest:raise ValueError(f'{name}: bytes differ from recorded export hash')
    for name in sorted(files):
        a=actual/name;e=expected/name
        if name.endswith('.stl'):
            if a.read_bytes()!=e.read_bytes():
                csg.compare_mesh(csg.trimesh.load_mesh(a,process=True),csg.trimesh.load_mesh(e,process=True),name)
        elif name.endswith('.png'):
            # FreeType/Matplotlib/platform rasterization may change valid pixels.
            # The checked-in image must still be intact and the expected size.
            from PIL import Image
            with Image.open(a) as ai,Image.open(e) as ei:
                if ai.size!=ei.size or ai.mode!=ei.mode:raise ValueError(f'{name}: preview size/mode differs')
                ai.verify()
        elif name in ['verification.json','mesh-report.json']:
            av=json.loads(a.read_text());ev=json.loads(e.read_text());compare_metadata(av,ev,name)
            for stem,part in av.get('parts',{}).items():
                if part.get('sha256')!=sha(actual/(stem+'.stl')):raise ValueError(f'{name}: inconsistent mesh hash for {stem}')
        elif a.read_bytes()!=e.read_bytes():
            raise ValueError(f'{name}: source-derived text differs')
