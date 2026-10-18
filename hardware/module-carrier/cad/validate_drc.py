#!/usr/bin/env python3
"""Strictly classify the 41 intentional opposite-side PTH/body projections.

This is NOT a KiCad suppression and NOT a physical clearance approval. The raw
report remains unchanged. Every other native violation, missing/extra pair,
wrong native side/position, unrouted item or schematic mismatch fails.
"""
import argparse,json,math,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Reviewed flanged carrier placement contract. Values are native final anchors/rotations.
BACK={
 'J1':(20,41,180,2,'U2'), 'J2':(20,29,180,4,'U2'),
 'J3':(13.5,17,180,6,'U2'), 'J4':(13.5,34,180,5,'U2'),
 'J5':(7,17,180,8,'U2'), 'J6':(7,39,180,4,'U2'),
 'J7':(20,17,180,4,'U2'),
 'D1':(45,16,250,2,'U1'),
 'D3':(17,67,180,2,'U3'), 'R1':(38.5,30,10,2,'U1'),
 'R2':(38,23.5,90,2,'U1')}
FRONT={'U1':(49.5,39,180),'U2':(2,1.5,0),'U3':(18,56.5,270)}
def parse(text):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   else:root=n
   stack.append(n)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 return root
def get(n,key,default=None):return next((v[1:] for v in n if isinstance(v,list) and v and v[0]==key),default)
def close(a,b):return len(a)==len(b) and all(abs(float(x)-float(y))<1e-4 for x,y in zip(a,b))
def classify(report,board_text):
 root=parse(board_text);fps={};identities={};errors=[]
 for key in ('violations','unconnected_items','schematic_parity'):
  if key not in report or not isinstance(report[key],list):errors.append('Missing or invalid required report list: '+key)
 if errors:return dict(result='fail',errors=errors,physical_z_qualified=False)
 for f in root:
  if not isinstance(f,list) or not f or f[0]!='footprint':continue
  ref=next(v[2] for v in f if isinstance(v,list) and v[:2]==['property','Reference']);fps[ref]=f
  at=get(f,'at');xy=list(map(float,at[:2]));rotation=float(at[2]) if len(at)>2 else 0
  identities[get(f,'uuid')[0]]=('footprint',ref,None,xy)
  for p in f:
   if not isinstance(p,list) or not p or p[0]!='pad':continue
   pos=list(map(float,get(p,'at')[:2]));a=math.radians(rotation)
   absolute=[xy[0]+pos[0]*math.cos(a)+pos[1]*math.sin(a),xy[1]-pos[0]*math.sin(a)+pos[1]*math.cos(a)]
   identities[get(p,'uuid')[0]]=('pad',ref,p[1],absolute)
 for ref,v in {**FRONT,**BACK}.items():
  f=fps.get(ref)
  if f is None:errors.append('Missing reviewed footprint '+ref);continue
  at=get(f,'at');actual=[float(at[0]),float(at[1]),(float(at[2]) if len(at)>2 else 0)%360]
  if not close(actual,v[:3]):errors.append('Reviewed position changed: '+ref)
  if get(f,'layer')!=['B.Cu' if ref in BACK else 'F.Cu']:errors.append('Reviewed side changed: '+ref)
 expected={(ref,str(i),v[4]) for ref,v in BACK.items() for i in range(1,v[3]+1)}
 actual=set();classified=[];unclassified=[]
 for violation in report.get('violations',[]):
  items=violation.get('items',[]);found=[identities.get(v.get('uuid')) for v in items]
  reason=None
  if violation.get('type')!='pth_inside_courtyard' or len(items)!=2 or any(v is None for v in found):reason='Not an exact known PTH/body pair'
  else:
   p=next((v for v in found if v[0]=='pad'),None);f=next((v for v in found if v[0]=='footprint'),None)
   if not p or not f or (p[1],p[2],f[1]) not in expected:reason='Unreviewed pad/body pair'
   elif (p[1],p[2],f[1]) in actual:reason='Duplicate pair'
   elif any(not close([v['pos']['x'],v['pos']['y']],identity[3]) for v,identity in zip(items,found)):reason='Report position differs from native object'
   else:
    # Check every local plated pad position as well as anchors.
    fp=fps[p[1]];pd=next(v for v in fp if isinstance(v,list) and v[:2]==['pad',p[2]])
    n=int(p[2]);local=[0,-(n-1)*2.54] if p[1].startswith('J') else [(n-1)*7.62,0]
    if pd[2]!='thru_hole' or not close(get(pd,'at')[:2],local):reason='Reviewed plated-pad geometry changed'
    else:
     actual.add((p[1],p[2],f[1]));classified.append({'pad_ref':p[1],'pad_number':p[2],'front_body_ref':f[1],'position_mm':[round(x,4) for x in p[3]]})
  if reason:unclassified.append({'reason':reason,'violation':violation})
 missing=sorted(expected-actual)
 if missing:errors.append('Missing reviewed projections: '+repr(missing))
 if report.get('unconnected_items'):errors.append('Unconnected native items remain')
 if report.get('schematic_parity'):errors.append('Schematic parity issues remain')
 if unclassified:errors.append('Unclassified native violations remain')
 return dict(result='pass_with_conditional_mechanical_findings' if not errors else 'fail',native_drc_violations=len(report.get('violations',[])),classified_mechanical_overlaps=len(classified),unclassified_violations=len(unclassified),unconnected_items=len(report.get('unconnected_items',[])),schematic_parity_issues=len(report.get('schematic_parity',[])),physical_z_qualified=False,acceptance='Only electrical/routing and exact intended 2D projection classification; measured Z clearance and solderability remain pending',errors=errors,classified=sorted(classified,key=lambda v:(v['pad_ref'],v['pad_number'])),unclassified=unclassified)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,default=ROOT/'checks/drc.json');ap.add_argument('--board',type=Path,default=ROOT/'mc1.kicad_pcb');ap.add_argument('--output',type=Path,default=ROOT/'checks/drc-classification.json');ap.add_argument('--cli',help='If supplied, generate the raw report using this kicad-cli first');a=ap.parse_args()
 if a.cli:
  a.report.parent.mkdir(parents=True,exist_ok=True)
  subprocess.run([a.cli,'pcb','drc','--severity-all','--schematic-parity','--format','json','--output',str(a.report),str(a.board)],check=True)
 result=classify(json.loads(a.report.read_text()),a.board.read_text());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('classified','unclassified')}));raise SystemExit(bool(result['errors']))
if __name__=='__main__':main()
