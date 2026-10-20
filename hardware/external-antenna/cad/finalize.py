#!/usr/bin/env python3
"""Import validated routing candidate, preserve schematic NCs, and add ground plane."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as pcb
from design import BOARD_W, BOARD_H
ROOT=Path(__file__).resolve().parent
board=pcb.LoadBoard(str(ROOT/'.build/mc2-unrouted.kicad_pcb'))
ses=ROOT/'.build/mc2.ses'
if not ses.exists():ses.write_text((ROOT/'routing/mc2.ses').read_text())
ses.write_text(ses.read_text().replace('(component \n','(component ""\n'))
if not pcb.ImportSpecctraSES(board,str(ses)):raise SystemExit('SES import failed')
for net in board.GetNetInfo().NetsByNetcode().values():
    if net.GetNetname():net.SetNetname('/'+net.GetNetname().lstrip('/'))
nettree=ET.parse(ROOT/'.build/mc2.xml')
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
# Two ground pours, no plane under the RF exclusion strips.
for layer in [pcb.F_Cu,pcb.B_Cu]:
    z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='/GND'));z.SetLocalClearance(pcb.FromMM(.25));z.SetMinThickness(pcb.FromMM(.2));z.SetPadConnection(pcb.ZONE_CONNECTION_FULL);z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.35));z.SetIslandRemovalMode(0)
    po=z.Outline();po.NewOutline()
    for x,y in [(1,1.8),(BOARD_W-1,1.8),(BOARD_W-1,BOARD_H-1),(1,BOARD_H-1)]:po.Append(pcb.FromMM(x),pcb.FromMM(y))
    board.Add(z)
board.BuildListOfNets();board.BuildConnectivity();pcb.ZONE_FILLER(board).Fill(board.Zones());pcb.SaveBoard(str(ROOT/'mc2.kicad_pcb'),board)
# KiCad 10's Python wrapper does not expose BOARD_STACKUP setters. Record the
# nominal order stackup in the native file, then require native parsing and DRC.
# 1.51 mm dielectric + 2*35 um copper + 2*10 um mask = nominal 1.60 mm.
path=ROOT/'mc2.kicad_pcb'
text=path.read_text()
assert '\t\t(stackup' not in text, 'Unexpected input stackup: review before replacing'
stackup='''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01) (color "Green"))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01) (color "Green"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
\t\t\t(copper_finish "HASL lead-free")
\t\t\t(dielectric_constraints no)
\t\t)
'''
assert text.count('\t(setup\n')==1
path.write_text(text.replace('\t(setup\n','\t(setup\n'+stackup,1))
# Parse immediately: malformed fabrication metadata must never leave a package.
pcb.LoadBoard(str(path))
print('Imported final routing:',len(list(board.GetTracks())),'track/via items')

from project_rules import restore_project_rules
restore_project_rules()
