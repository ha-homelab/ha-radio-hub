#!/usr/bin/env python3
"""Prepare the complete MC1 profile with disposable credentials; never flash."""
import argparse
import importlib.util
from pathlib import Path
import shutil

def load_legacy(name):
    path=Path(__file__).resolve().parents[1]/"low-power"/(name+".py")
    spec=importlib.util.spec_from_file_location("legacy_"+name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def prepare(output: Path, upstream: Path | None=None) -> Path:
    legacy=load_legacy("prepare")
    original=legacy.prepare(output,upstream)
    profile=original.parent.parent/"module-carrier/hub.yaml"
    secrets=profile.parent/"secrets.yaml"
    shutil.copyfile(original.parent/"secrets.yaml",secrets)
    secrets.chmod(0o600)
    return profile

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--upstream",type=Path)
    args=parser.parse_args()
    print(prepare(args.output,args.upstream))
