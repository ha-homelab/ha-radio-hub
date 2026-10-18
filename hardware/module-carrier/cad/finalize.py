#!/usr/bin/env python3
"""Import validated routing candidate, preserve schematic NCs, and add ground plane."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as pcb
from design import BOARD_W, BOARD_H
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
# Five crowded GND pads use their routed 0.8mm return rather than a starved
# thermal island. Keep the pad-to-plane clearance; the GND traces join the plane.
for f in board.GetFootprints():
    for pd in f.Pads():
        if (f.GetReference(),pd.GetNumber()) in [('U1','JP1.14'),('U3','13'),('J1','2'),('J2','4'),('J2','2')]:
            pd.SetLocalZoneConnection(pcb.ZONE_CONNECTION_NONE)
# Two ground pours, no plane under the RF exclusion strips.
for layer in [pcb.F_Cu,pcb.B_Cu]:
    z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='/GND'));z.SetLocalClearance(pcb.FromMM(.25));z.SetMinThickness(pcb.FromMM(.2));z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.35));z.SetIslandRemovalMode(0)
    po=z.Outline();po.NewOutline()
    for x,y in [(1,1.8),(BOARD_W-1,1.8),(BOARD_W-1,BOARD_H-1),(1,BOARD_H-1)]:po.Append(pcb.FromMM(x),pcb.FromMM(y))
    board.Add(z)
board.BuildListOfNets();board.BuildConnectivity();pcb.ZONE_FILLER(board).Fill(board.Zones());pcb.SaveBoard(str(ROOT/'mc1.kicad_pcb'),board)
print('Imported final routing:',len(list(board.GetTracks())),'track/via items')

from project_rules import restore_project_rules
restore_project_rules()
