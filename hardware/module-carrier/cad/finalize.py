#!/usr/bin/env python3
"""Import validated routing candidate, preserve schematic NCs, and add ground plane."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as pcb
ROOT=Path(__file__).resolve().parent
board=pcb.LoadBoard(str(ROOT/'.build/mc1-unrouted.kicad_pcb'))
ses=ROOT/'.build/mc1.ses'
if not ses.exists():ses.write_text((ROOT/'routing/mc1.ses').read_text())
ses.write_text(ses.read_text().replace('(component \n','(component ""\n'))
if not pcb.ImportSpecctraSES(board,str(ses)):raise SystemExit('SES import failed')
for net in board.GetNetInfo().NetsByNetcode().values():
    if net.GetNetname():net.SetNetname('/'+net.GetNetname().lstrip('/'))
nettree=ET.parse(ROOT/'.build/mc1.xml')
for n in nettree.findall('./nets/net'):
    name=n.get('name')
    if name.startswith('unconnected-'):
        info=pcb.NETINFO_ITEM(board,name);board.Add(info)
    else:info=next(i for i in board.GetNetInfo().NetsByNetcode().values() if i.GetNetname()==name)
    for node in n.findall('node'):
        f=next(f for f in board.GetFootprints() if f.GetReference()==node.get('ref'))
        pd=next(pd for pd in f.Pads() if pd.GetNumber()==node.get('pin'));pd.SetNet(info);pd.SetPinFunction(node.get('pinfunction',''));pd.SetPinType(node.get('pintype','passive'))
for f in board.GetFootprints():
    if f.GetReference().startswith('H'):f.SetAttributes(pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES)
# Direct ground connection on WIZ header pins avoids starved thermal islands.
for f in board.GetFootprints():
    if f.GetReference()=='U4':
        for pd in f.Pads():
            if pd.GetNetname()=='/GND':pd.SetLocalZoneConnection(pcb.ZONE_CONNECTION_FULL)
# Two ground pours, no plane under the top RF exclusion strip.
for layer in [pcb.F_Cu,pcb.B_Cu]:
    z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='/GND'));z.SetLocalClearance(pcb.FromMM(.25));z.SetMinThickness(pcb.FromMM(.2));z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.35));z.SetIslandRemovalMode(0)
    po=z.Outline();po.NewOutline()
    for x,y in [(1,1.5),(159,1.5),(159,99),(1,99)]:po.Append(pcb.FromMM(x),pcb.FromMM(y))
    board.Add(z)
board.BuildListOfNets();board.BuildConnectivity();pcb.ZONE_FILLER(board).Fill(board.Zones());pcb.SaveBoard(str(ROOT/'mc1.kicad_pcb'),board)
print('Imported final routing:',len(list(board.GetTracks())),'track/via items')
