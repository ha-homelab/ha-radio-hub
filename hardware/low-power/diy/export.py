#!/usr/bin/env python3
"""Export bottom-only fabrication reference and high-contrast assembly documents."""
import argparse,csv,hashlib,json,subprocess,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli',default='kicad-cli');ap.add_argument('--hashes-only',action='store_true');a=ap.parse_args()
 out=ROOT/'outputs';out.mkdir(exist_ok=True)
 def run(*argv):subprocess.run([a.kicad_cli,*map(str,argv)],cwd=ROOT,check=True)
 if not a.hashes_only:
  run('pcb','export','svg','diy.kicad_pcb','--layers','F.Fab,F.SilkS,Dwgs.User,Edge.Cuts','--black-and-white','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--sketch-pads-on-fab-layers','-o',out/'assembly-top.svg')
  run('pcb','export','gerbers','diy.kicad_pcb','--layers','B.Cu,Edge.Cuts','--no-protel-ext','--subtract-soldermask','--check-zones','-o',str(out/'bottom-gerbers')+'/')
  run('sch','export','pdf','diy.kicad_sch','-o',out/'assembly-schematic.pdf')
  holes=list(csv.DictReader((ROOT/'drill.csv').open()));sizes=sorted({float(h['Drill mm']) for h in holes});tools={v:i+1 for i,v in enumerate(sizes)}
  lines=['M48','; D0 ALL HOLES UNPLATED - manual drilling reference','METRIC,TZ']+[f'T{tools[d]:02}C{d:.3f}' for d in sizes]+['%','G90','G05']
  for d in sizes:
   lines.append(f'T{tools[d]:02}')
   for h in holes:
    if float(h['Drill mm'])==d:lines.append(f'X{float(h["X top-view mm"]):.6f}Y{-float(h["Y top-view mm"]):.6f}')
  lines.append('M30');(out/'all-holes-unplated.drl').write_text('\n'.join(lines)+'\n')
  (out/'README.txt').write_text('LP-D0 PROTOTYPE: bottom copper only. No top copper or plated holes are required.\nUse the separately checked print PDFs for toner transfer.\nThe drill file and CSV specify every hole as unplated. Do not import top wire overlays as copper.\nBOM, jumper schedule, and measured assembly acceptance remain mandatory.\n')
  with zipfile.ZipFile(out/'d0-bottom-reference.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
   for p in sorted([*list((out/'bottom-gerbers').glob('*.gbr')),out/'all-holes-unplated.drl',out/'README.txt']):
    info=zipfile.ZipInfo(p.relative_to(out).as_posix(),date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
 # Keep native netlist diagnostics publishable without reserializing their XML.
 netlist=out/'validation/schematic.xml'
 source=ET.parse(netlist).findtext('./design/source')
 schematic=ROOT/'diy.kicad_sch'
 relative_source=schematic.relative_to(ROOT.parents[2]).as_posix()
 assert source in [str(schematic),relative_source],'unexpected native schematic source'
 xml=netlist.read_text();old='<source>'+escape(source)+'</source>'
 assert xml.count(old)==1,'ambiguous native schematic source'
 netlist.write_text(xml.replace(old,'<source>'+relative_source+'</source>'))
 included=[]
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if not p.is_file() or any(x in ['.build','__pycache__','print'] for x in rel.parts):continue
  if p.name in ['sha256.json'] or p.suffix in ['.pyc','.kicad_prl']:continue
  included.append(p)
 included += [ROOT.parent/'carrier/design.py',ROOT.parent/'pinmap.json',ROOT.parent/'visual/connections.json']
 manifest={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(included)}
 (out/'sha256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print('Bound',len(manifest),'source/export files')
if __name__=='__main__':main()
