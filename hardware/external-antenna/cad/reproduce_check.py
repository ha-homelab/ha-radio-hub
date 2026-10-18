#!/usr/bin/env python3
"""Regenerate MC2 in a clean directory and require exact ledger/copper equality."""
import argparse,json,subprocess,sys,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--python',required=True);ap.add_argument('--cli',required=True);ap.add_argument('--libraries',required=True);a=ap.parse_args()
def run(cmd,cwd):subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
with tempfile.TemporaryDirectory(prefix='mc2-reproduce-') as tmp:
 dest=Path(tmp)/'cad';shutil.copytree(R,dest,ignore=shutil.ignore_patterns('.build','__pycache__','checks','verification.json','*.kicad_prl'));(dest/'checks').mkdir()
 run([a.python,'generate.py','--libraries',a.libraries],dest)
 run([a.cli,'sch','export','netlist','--format','kicadxml','-o','.build/mc2.xml','mc2.kicad_sch'],dest)
 shutil.copy(dest/'routing/mc2.ses',dest/'.build/mc2.ses')
 run([a.python,'finalize.py'],dest)
 run([a.cli,'sch','erc','--severity-all','--exit-code-violations','--format','json','--output','checks/erc.json','mc2.kicad_sch'],dest)
 run([a.cli,'pcb','drc','--severity-all','--exit-code-violations','--schematic-parity','--format','json','--output','checks/drc.json','mc2.kicad_pcb'],dest)
 run([sys.executable,'test_design.py'],dest)
 run([a.python,'record_verification.py'],dest)
 baseline=json.loads((R/'verification.json').read_text());new=json.loads((dest/'verification.json').read_text())
 assert baseline['topology_sha256']==new['topology_sha256'],'Native copper/pad topology differs'
 for n in ['design.json','connectors.json','BOM.csv']:
  assert (R/n).read_bytes()==(dest/n).read_bytes(),f'{n} differs'
 result={'status':'pass','method':'Clean generate + frozen session; exact ledger and copper/pad topology; fresh native ERC/DRC/parity','native_checks':new['checks'],'topology_sha256':new['topology_sha256'],'source_sha256':baseline['source_sha256'],'byte_identical_pcb_required':False,'reason':'KiCad creates new object UUIDs; exact electrical/geometric topology is compared instead'}
 (R/'checks/reproduction.json').write_text(json.dumps(result,indent=2)+'\n');print('MC2 clean reproduction PASS')
