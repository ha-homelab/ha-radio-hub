#!/usr/bin/env python3
"""Validate first, then regenerate prototype fabrication and review outputs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli',default='kicad-cli');a=ap.parse_args()
out=ROOT/'outputs';fab=out/'gerbers';out.mkdir(exist_ok=True);fab.mkdir(exist_ok=True)
for old in fab.iterdir():
    if old.is_file():old.unlink()
subprocess.run([sys.executable,str(ROOT/'validate.py'),'--kicad-cli',a.kicad_cli,'--out',str(out/'validation')],check=True)
def run(*args):subprocess.run([a.kicad_cli,*map(str,args)],cwd=ROOT,check=True)
run('pcb','export','gerbers','mg24-adapter.kicad_pcb','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','--no-protel-ext','--check-zones','-o',fab)
run('pcb','export','drill','mg24-adapter.kicad_pcb','--format','excellon','--excellon-separate-th','--generate-map','--map-format','pdf','-o',fab)
run('pcb','export','pos','mg24-adapter.kicad_pcb','--format','csv','--units','mm','--side','both','-o',out/'placement.csv')
run('pcb','export','svg','mg24-adapter.kicad_pcb','-l','F.Cu,F.SilkS,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',out/'board-top.svg')
run('pcb','export','svg','mg24-adapter.kicad_pcb','-l','F.Fab,F.SilkS,Edge.Cuts','--sketch-pads-on-fab-layers','--black-and-white','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',out/'assembly-top.svg')
run('sch','export','pdf','mg24-adapter.kicad_sch','-o',out/'schematic.pdf')
# Strip workstation paths only from text reports; never edit PCB, Gerber or drill geometry.
for p in (out/'validation').glob('*'):
    if p.suffix in {'.json','.xml'}:p.write_text(p.read_text().replace(str(ROOT),'hardware/low-power/carrier/mg24-adapter'))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name not in {'sha256.json','prototype-gerbers.zip'}}
for p in [ROOT/('mg24-adapter'+ext) for ext in ['.kicad_pcb','.kicad_sch','.kicad_pro']]+[ROOT/'Carrier.kicad_sym']+list(ROOT.glob('*-bom.csv'))+[ROOT/n for n in ['design.py','generate.py','finalize.py','connectors.json','netlist.json','fp-lib-table','sym-lib-table','validate.py','export.py','test_contract.py','README.md','NOTICE.md']]+list((ROOT/'Carrier.pretty').glob('*.kicad_mod')):
    if p.is_file() and p.suffix!='.kicad_prl':manifest[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(out/'prototype-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(fab.iterdir()):z.write(p,p.name)
manifest['outputs/prototype-gerbers.zip']=hashlib.sha256((out/'prototype-gerbers.zip').read_bytes()).hexdigest()
(out/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prototype outputs generated; fabrication release still requires physical and assembly review.')
