#!/usr/bin/env python3
"""Import local router result, retain exact schematic net names, export final PCB."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as pcb
ROOT=Path(__file__).resolve().parent
board=pcb.LoadBoard(str(ROOT/'.build/mg24-adapter-unrouted.kicad_pcb'))
ses=ROOT/'.build/mg24-adapter.ses'
ses.write_text(ses.read_text().replace('(component \n','(component ""\n'))
if not pcb.ImportSpecctraSES(board,str(ses)):raise SystemExit('SES import failed')
# KiCad local labels have absolute sheet paths in the native netlist.
for net in board.GetNetInfo().NetsByNetcode().values():
    if net.GetNetname():net.SetNetname('/'+net.GetNetname().lstrip('/'))
nettree=ET.parse(ROOT/'.build/mg24-adapter.xml')
for n in nettree.findall('./nets/net'):
    if not n.get('name').startswith('unconnected-'):continue
    info=pcb.NETINFO_ITEM(board,n.get('name'));board.Add(info)
    for node in n.findall('node'):
        f=next(f for f in board.GetFootprints() if f.GetReference()==node.get('ref'))
        for pad in f.Pads():
            if pad.GetNumber()==node.get('pin'):
                pad.SetNet(info);pad.SetPinFunction('NC');pad.SetPinType('no_connect')
for f in board.GetFootprints():
    if f.GetReference().startswith('H'):f.SetAttributes(pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES)
for name,layer in [('/GND',pcb.B_Cu),('/GND',pcb.F_Cu)]:
    z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()==name));z.SetLocalClearance(pcb.FromMM(0.25));z.SetMinThickness(pcb.FromMM(0.20));z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(pcb.FromMM(0.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(0.30));z.SetIslandRemovalMode(0)
    poly=z.Outline();poly.NewOutline()
    for x,y in [(0.25,0.25),(59.75,0.25),(59.75,39.75),(0.25,39.75)]:poly.Append(pcb.FromMM(x),pcb.FromMM(y))
    board.Add(z)
# The module ground lands have direct connections and nearby stitching vias.
u=next(f for f in board.GetFootprints() if f.GetReference()=='U1')
for p in u.Pads():
    if p.GetNetname()=='/GND':p.SetLocalZoneConnection(pcb.ZONE_CONNECTION_FULL)
board.BuildListOfNets();board.BuildConnectivity()
pcb.ZONE_FILLER(board).Fill(board.Zones())
pcb.SaveBoard(str(ROOT/'mg24-adapter.kicad_pcb'),board)
print('Imported final routing:',len(list(board.GetTracks())),'track/via items')
