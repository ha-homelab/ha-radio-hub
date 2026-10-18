#!/usr/bin/env python3
"""Apply explicit remaining centerlines, then refill ground. Native DRC is required.
Each route's points are in millimetres, layer0=F.Cu/layer1=B.Cu. Stored routes
are specific to the frozen placement and router session, not new layouts.
"""
import json,argparse
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--routes',type=Path,default=R/'manual-route.json');args=ap.parse_args()
b=p.LoadBoard(str(R/'mc1.kicad_pcb'));data=json.loads(args.routes.read_text());count=0
for route in data['routes']:
 net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()==route['net'])
 if any(t.GetNetCode()==net.GetNetCode() for t in b.GetTracks()):raise SystemExit(route['net']+' already routed; refusing duplicate route')
 a=route['points'];a[0][:2]=route['start'];a[-1][:2]=route['end']
 for v,w in zip(a,a[1:]):
  if v[2]!=w[2]:
   t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1])));t.SetWidth(p.FromMM(.8));t.SetDrill(p.FromMM(.4));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
  else:
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1])));t.SetEnd(p.VECTOR2I(p.FromMM(w[0]),p.FromMM(w[1])));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu if v[2]==0 else p.B_Cu)
  t.SetNet(net);b.Add(t);count+=1
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'mc1.kicad_pcb'),b)
print('Added',count,'route items; run native DRC')
