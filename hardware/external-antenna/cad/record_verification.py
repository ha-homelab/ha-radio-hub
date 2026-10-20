#!/usr/bin/env python3
"""Record exact design inputs and saved copper; run using KiCad's Python."""
import json,hashlib
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parent
INPUTS=['c6d-evidence.json','design.py','generate.py','finalize.py','project_rules.py','routing/mc2.ses','pin-plan.json','mc2.kicad_pcb','mc2.kicad_sch','mc2.kicad_pro','design.json','connectors.json','BOM.csv','test_design.py']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def topology(board):
 b=p.LoadBoard(str(board)); tracks=[];pads=[]
 for t in b.GetTracks():
  v=isinstance(t,p.PCB_VIA);a=t.GetStart();z=t.GetEnd()
  tracks.append([t.GetClass(),t.GetNetname(),t.GetLayer(),round(p.ToMM(a.x),6),round(p.ToMM(a.y),6),round(p.ToMM(z.x),6),round(p.ToMM(z.y),6),round(p.ToMM(t.GetWidth(p.F_Cu) if v else t.GetWidth()),6)])
 for f in b.GetFootprints():
  for q in f.Pads():pads.append([f.GetReference(),q.GetNumber(),q.GetNetname(),round(p.ToMM(q.GetPosition().x),6),round(p.ToMM(q.GetPosition().y),6)])
 return {'tracks':sorted(tracks),'pads':sorted(pads)}
if __name__=='__main__':
 drc=json.loads((R/'checks/drc.json').read_text());erc=json.loads((R/'checks/erc.json').read_text())
 assert all(drc[k]==[] for k in ['violations','unconnected_items','schematic_parity'])
 assert all(s['violations']==[] for s in erc['sheets'])
 t=topology(R/'mc2.kicad_pcb');d=json.loads((R/'design.json').read_text())
 connected={'tracks':t['tracks'],'pads':[q for q in t['pads'] if not q[2].startswith('unconnected-')]}
 connected_digest=hashlib.sha256(json.dumps(connected,sort_keys=True).encode()).hexdigest()
 v={'status':'native_checks_passed_physical_prototype_unqualified','kicad_version':p.GetBuildVersion(),'checks':{'erc':0,'drc':0,'unconnected':0,'schematic_parity':0},'fitted_parts':sum(q['fitted'] for q in d['parts']),'footprint_positions':len(d['parts']),'plated_module_and_component_holes':sum(len(q['pins']) for q in d['parts']),'connected_nets':len({n for q in d['parts'] for n in q['pins'].values() if n}),'tracks_and_vias':len(t['tracks']),'via_count':sum(x[0]=='PCB_VIA' for x in t['tracks']),'connected_topology_sha256':connected_digest,'topology_sha256':hashlib.sha256(json.dumps(t,sort_keys=True).encode()).hexdigest(),'source_sha256':{n:digest(R/n) for n in INPUTS},'physical_rf_coverage_verified':False,'physical_assembly_fit_verified':False}
 (R/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ['checks','fitted_parts','footprint_positions','plated_module_and_component_holes','connected_nets','via_count']}))
