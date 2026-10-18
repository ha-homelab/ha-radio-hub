#!/usr/bin/env python3
"""Rebuild the committed routing in a temporary copy and check it with KiCad."""
import argparse,datetime,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--python',required=True,help='KiCad Python containing pcbnew');ap.add_argument('--cli',required=True,help='kicad-cli');ap.add_argument('--libraries',required=True);a=ap.parse_args()
with tempfile.TemporaryDirectory(prefix='mc1-reproduction-') as tmp:
 parent=Path(tmp)/'module-carrier';dst=parent/'cad'
 shutil.copytree(R,dst,ignore=shutil.ignore_patterns('.build','__pycache__','*.kicad_prl','logs','*.log'))
 commands=[[a.python,'generate.py','--libraries',a.libraries],[a.cli,'sch','export','netlist','--format','kicadxml','-o','.build/mc1.xml','mc1.kicad_sch'],[a.python,'finalize.py'],[a.python,'apply_manual_route.py'],[a.cli,'pcb','drc','--format','json','--output','checks/drc.json','--schematic-parity','mc1.kicad_pcb'],[a.cli,'sch','erc','--format','json','--output','checks/erc.json','mc1.kicad_sch'],[a.python,'validate_drc.py'],[a.python,'test_design.py']]
 for command in commands:
  r=subprocess.run(command,cwd=dst,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  if r.returncode:raise SystemExit('Reproduction failed: '+str(command)+'\n'+r.stdout)
 drc=json.loads((dst/'checks/drc.json').read_text());erc=json.loads((dst/'checks/erc.json').read_text())
 counts=dict(drc_violations=len(drc['violations']),unconnected_items=len(drc['unconnected_items']),schematic_parity_issues=len(drc['schematic_parity']),erc_violations=sum(len(x['violations']) for x in erc['sheets']))
 classification=json.loads((dst/'checks/drc-classification.json').read_text())
 counts.update(classified_mechanical_overlaps=classification['classified_mechanical_overlaps'],unclassified_violations=classification['unclassified_violations'])
 if any(counts[k] for k in ['unconnected_items','schematic_parity_issues','erc_violations','unclassified_violations']):raise SystemExit('Rebuilt native checks failed: '+str(counts))
 report=dict(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),result='pass_with_conditional_mechanical_findings',physical_z_qualified=False,method='Clean temporary copy; generator + committed SES + manual route; native DRC/parity/ERC and geometry/electrical tests',checks=counts,source_sha256={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['mc1.kicad_pcb','mc1.kicad_pro','project_rules.py','generate.py','finalize.py','apply_manual_route.py','validate_drc.py','routing/mc1.ses','manual-route.json']})
 (R/'checks/reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print('Clean reproduction passed:',counts)
