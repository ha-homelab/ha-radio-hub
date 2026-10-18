#!/usr/bin/env python3
"""Finish the remaining ZB_RX route, then refill ground. Native DRC is mandatory.
manual-route.json stores centerline vertices in mm, layer0=F.Cu, layer1=B.Cu.
The path was solved around the fixed candidate and is not reusable on a new layout.
"""
import json
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parent;b=p.LoadBoard(str(R/'mc1.kicad_pcb'));net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='/ZB_RX')
if any(t.GetNetCode()==net.GetNetCode() for t in b.GetTracks()):raise SystemExit('ZB_RX already routed; refusing duplicate route')
a=json.loads((R/'manual-route.json').read_text());a[0][:2]=[44,25.86];a[-1][:2]=[127.76,2.76]
for v,w in zip(a,a[1:]):
 if v[2]!=w[2]:
  t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1])));t.SetWidth(p.FromMM(.8));t.SetDrill(p.FromMM(.4));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
 else:
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1])));t.SetEnd(p.VECTOR2I(p.FromMM(w[0]),p.FromMM(w[1])));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu if v[2]==0 else p.B_Cu)
 t.SetNet(net);b.Add(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'mc1.kicad_pcb'),b)
print('Added',len(a)-1,'route items; run native DRC')
