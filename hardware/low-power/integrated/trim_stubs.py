"""Trim only native-reported dangling track tails, preserving internal junctions."""
import json,math,sys
from pathlib import Path
import pcbnew as pcb
board=pcb.LoadBoard(sys.argv[1]);report=json.loads(Path(sys.argv[2]).read_text())
ids={x['uuid'] for v in report['violations'] if v['type']=='track_dangling' for x in v['items']}
tracks=list(board.GetTracks());pads=[p for f in board.GetFootprints() for p in f.Pads()];removed=[]
def xy(p):return p.x,p.y
for t in tracks:
 if isinstance(t,pcb.PCB_VIA) or t.m_Uuid.AsString() not in ids:continue
 a,b=xy(t.GetStart()),xy(t.GetEnd());dx,dy=b[0]-a[0],b[1]-a[1];length2=dx*dx+dy*dy
 if not length2:continue
 anchors=[]
 def add(p):
  k=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length2
  if -.00001<=k<=1.00001 and math.hypot(a[0]+k*dx-p[0],a[1]+k*dy-p[1])<=pcb.FromMM(.002):anchors.append(max(0,min(1,k)))
 for o in tracks:
  if o.m_Uuid.AsString()==t.m_Uuid.AsString() or o.GetNetname()!=t.GetNetname() or not o.IsOnLayer(t.GetLayer()):continue
  add(xy(o.GetStart()));add(xy(o.GetEnd()))
 for p in pads:
  if p.GetNetname()!=t.GetNetname() or not p.IsOnLayer(t.GetLayer()):continue
  shape=p.GetEffectiveShape(t.GetLayer())
  if shape.Collide(t.GetStart(),0):anchors.append(0)
  if shape.Collide(t.GetEnd(),0):anchors.append(1)
 if len(anchors)<2 or max(anchors)-min(anchors)<1e-8:
  removed.append(t);continue
 low,high=min(anchors),max(anchors)
 t.SetStart(pcb.VECTOR2I(round(a[0]+low*dx),round(a[1]+low*dy)));t.SetEnd(pcb.VECTOR2I(round(a[0]+high*dx),round(a[1]+high*dy)))
for t in removed:board.Remove(t)
pcb.SaveBoard(sys.argv[1],board)
print('Trimmed native-reported stubs:',len(ids))
