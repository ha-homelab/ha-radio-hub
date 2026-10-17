#!/usr/bin/env python3
"""Import the optional autorouter workspace into a portable routing candidate."""
import argparse,json
from pathlib import Path
import pcbnew as pcb
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,default=ROOT/'.build/routing.kicad_pcb');ap.add_argument('--session',type=Path,default=ROOT/'.build/routing.ses');args=ap.parse_args()
b=pcb.LoadBoard(str(args.board))
ses=ROOT/'.build/import.ses';ses.write_text(args.session.read_text().replace('(component \n','(component ""\n'))
assert pcb.ImportSpecctraSES(b,str(ses))
def xy(p):return [round(pcb.ToMM(p.x),6),round(pcb.ToMM(p.y),6)]
pads=[];tracks=[]
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNumber():pads.append(dict(id=f.GetReference()+'.'+p.GetNumber(),xy=xy(p.GetPosition()),net=p.GetNetname(),shape='rect' if p.GetShape()==pcb.PAD_SHAPE_RECT else 'circle',size=xy(p.GetSize())))
seen=set()
for t in b.GetTracks():
 key=(isinstance(t,pcb.PCB_VIA),t.GetNetname(),t.GetLayer(),tuple(sorted([tuple(xy(t.GetStart())),tuple(xy(t.GetEnd()))])))
 if key in seen:continue
 seen.add(key)
 tracks.append(dict(id='t'+str(len(tracks)),via=isinstance(t,pcb.PCB_VIA),net=t.GetNetname(),a=xy(t.GetStart()),b=xy(t.GetEnd()),width=round(pcb.ToMM(t.GetWidth(pcb.B_Cu) if isinstance(t,pcb.PCB_VIA) else t.GetWidth()),6),layer='B.Cu' if t.GetLayer()==pcb.B_Cu else 'F.Cu'))
(ROOT/'.build/candidate.json').write_text(json.dumps(dict(pads=pads,tracks=tracks),indent=2)+'\n')
pcb.SaveBoard(str(ROOT/'.build/candidate.kicad_pcb'),b)
print('Captured',len(pads),'pads',len(tracks),'track/via records')
