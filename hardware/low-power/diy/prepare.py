#!/usr/bin/env python3
"""Create the two-layer ROUTING WORKSPACE. F.Cu is temporary wire planning only."""
import argparse,json,uuid,re
from pathlib import Path
import pcbnew as pcb
from design import ROOT,parts,WIDTH,HEIGHT
from schematic import write_schematic
ap=argparse.ArgumentParser();ap.add_argument('--libraries',type=Path,required=True);args=ap.parse_args()
B=ROOT/'.build';B.mkdir(exist_ok=True);L=ROOT/'DIY.pretty';L.mkdir(exist_ok=True)
U=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://ha-homelab/LP-D0/'+s))
Q=lambda s:json.dumps(str(s))
def custom(name,pads,rect,drill=1):
 x1,y1,x2,y2=rect
 text=f'(footprint "{name}" (version 20260206) (generator "pcbnew") (layer "F.Cu") (attr through_hole)\n'
 text+=f'(property "Reference" "REF**" (at 0 {y1-1.6}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
 text+=f'(property "Value" "{name}" (at 0 {y2+1.6}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
 for layer,offset in [('F.Fab',0),('F.CrtYd',0.5)]:text+=f'(fp_rect (start {x1-offset} {y1-offset}) (end {x2+offset} {y2+offset}) (stroke (width 0.05) (type solid)) (fill none) (layer "{layer}"))\n'
 for n,x,y in pads:text+=f'(pad "{n}" thru_hole {"rect" if n==1 else "circle"} (at {x} {y}) (size 2 2) (drill {drill}) (layers "*.Cu" "*.Mask"))\n'
 text+=')\n';(L/(name+'.kicad_mod')).write_text(text)
custom('Wurth_61204021621',[(2*i+j+1,j*2.54,i*2.54) for i in range(20) for j in range(2)],(-3.28,-5.10,5.82,53.36),1.1)
custom('Adafruit1208_TSSOP28',[(i+1,0,i*2.54) for i in range(14)]+[(28-i,15.24,i*2.54) for i in range(14)],(-1.27,-1.27,16.51,34.29),1.1)
custom('Adafruit1230_SOT23_6',[(1,0,0),(2,0,2.54),(3,0,5.08),(4,7.62,5.08),(5,7.62,2.54),(6,7.62,0)],(-1.27,-1.27,8.89,6.35),1.1)
custom('Axial_R_P10.16',[(1,0,0),(2,10.16,0)],(1.5,-1.5,8.6,1.5),0.8)
custom('Radial_C_P2.54',[(1,0,0),(2,2.54,0)],(-1.3,-2.5,3.8,2.5),0.8)
custom('HC49U',[(1,0,0),(2,4.88,0)],(-3.31,-2.5,8.19,2.5),0.9)
custom('FuseHarness',[(1,0,0),(2,8,0)],(-1.2,-1.2,9.2,1.2),1.1)
for obj in parts:
 if obj['footprint'].startswith('Connector_JST:'):
  lib,name=obj['footprint'].split(':');s=(args.libraries/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')).read_text();i=s.find('\n\t(model ')
  if i>=0:s=s[:i]+'\n)\n'
  (L/(name+'.kicad_mod')).write_text(s)
 if obj['footprint']:obj['footprint']='DIY:'+obj['footprint'].split(':')[-1]
write_schematic(ROOT,parts,U,Q)
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "DIY")(type "KiCad")(uri "${KIPRJMOD}/DIY.pretty")(options "")(descr "LP-D0 enlarged through-hole footprints")))\n')
b=pcb.BOARD();b.SetCopperLayerCount(2)
s=b.GetDesignSettings();s.m_TrackMinWidth=pcb.FromMM(.6);s.m_MinClearance=pcb.FromMM(.5);s.m_ViasMinSize=pcb.FromMM(2);s.m_MinThroughDrill=pcb.FromMM(1)
nets={}
for p in parts:
 for net in p['pins'].values():
  if net and net not in nets:nets[net]=pcb.NETINFO_ITEM(b,net);b.Add(nets[net])
courtyard_records=[]
for obj in parts:
 if not obj['footprint']:continue
 fp=pcb.FootprintLoad(str(L),obj['footprint'].split(':')[-1]);fp.SetReference(obj['ref']);fp.SetValue(obj['model']);fp.SetFPID(pcb.LIB_ID('DIY',obj['footprint'].split(':')[-1]));fp.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(v) for v in obj['xy']]));fp.SetOrientationDegrees(obj['rotation']);fp.SetPath(pcb.KIID_PATH('/'+U('schematic')+'/'+U('symbol/'+obj['ref'])))
 for pad in fp.Pads():
  pad.SetSize(pcb.VECTOR2I(pcb.FromMM(2),pcb.FromMM(2)))
  net=obj['pins'].get(pad.GetNumber())
  if net:pad.SetNet(nets[net])
 fp.Value().SetVisible(False);b.Add(fp)
 # F.Cu is prohibited over ALL component courtyards. Later temporary vias become
 # dedicated wire endpoint holes, so no jumper competes for a component lead hole.
 boxes=[i.GetBoundingBox() for i in fp.GraphicalItems() if i.GetLayer()==pcb.F_CrtYd]
 if boxes and obj['ref'] not in ['U1','U2']:
  courtyard_records.append([pcb.ToMM(min(x.GetLeft() for x in boxes)),pcb.ToMM(min(x.GetTop() for x in boxes)),pcb.ToMM(max(x.GetRight() for x in boxes)),pcb.ToMM(max(x.GetBottom() for x in boxes))])
 if boxes:
  x1=min(x.GetLeft() for x in boxes)-pcb.FromMM(1.1);y1=min(x.GetTop() for x in boxes)-pcb.FromMM(1.1);x2=max(x.GetRight() for x in boxes)+pcb.FromMM(1.1);y2=max(x.GetBottom() for x in boxes)+pcb.FromMM(1.1)
  z=pcb.ZONE(b);z.SetLayer(pcb.F_Cu);z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True)
  poly=z.Outline();poly.NewOutline()
  for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:poly.Append(x,y)
  b.Add(z)
for a,c in [((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,HEIGHT)),((WIDTH,HEIGHT),(0,HEIGHT)),((0,HEIGHT),(0,0))]:
 line=pcb.PCB_SHAPE();line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));line.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in c]));line.SetLayer(pcb.Edge_Cuts);line.SetWidth(pcb.FromMM(.05));b.Add(line)
for i,(x,y) in enumerate([(5,5),(185,5),(5,140),(185,140)],1):
 fp=pcb.FOOTPRINT(b);fp.SetReference('H'+str(i));fp.SetAttributes(pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES);fp.Reference().SetVisible(False);fp.Value().SetVisible(False);fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)))
 p=pcb.PAD(fp);p.SetAttribute(pcb.PAD_ATTRIB_NPTH);p.SetShape(pcb.PAD_SHAPE_CIRCLE);p.SetSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));p.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));p.SetLayerSet(pcb.LSET.AllCuMask());fp.Add(p);b.Add(fp)
b.BuildConnectivity();pcb.SaveBoard(str(B/'routing.kicad_pcb'),b);pcb.ExportSpecctraDSN(b,str(B/'routing.dsn'))
s=(B/'routing.dsn').read_text().replace('(width 200)','(width 600)').replace('(clearance 200)','(clearance 500)').replace('(clearance 50 (type smd_smd))','(clearance 500 (type smd_smd))')
# Explicit router rules: 0.6mm signal /1.2mm power; 2mm endpoint landing pads.
s=re.sub(r'600:300','2000:1000',s);s=s.replace('(circle F.Cu 600)','(circle F.Cu 2000)').replace('(circle B.Cu 600)','(circle B.Cu 2000)')
s=s.replace('(class kicad_default +3V3 +5V +5V_IN ','(class kicad_default ')
pos=s.rfind('\n  (wiring');end=s.rfind('\n  )',0,pos)
s=s[:end]+'\n    (class power "+5V_IN" "+5V" "+3V3" "GND" (circuit (use_via "Via[0-1]_2000:1000_um")) (rule (width 1200) (clearance 500)))\n'+s[end:]
s=s.replace('(class kicad_default GND ','(class kicad_default ')
(B/'routing.dsn').write_text(s)
(B/'courtyards.json').write_text(json.dumps(courtyard_records,indent=2)+'\n')
(ROOT/'logical-netlist.json').write_text(json.dumps(dict(revision='LP-D0',parts=parts),indent=2)+'\n')
print('Prepared',len(parts),'parts',len(nets),'nets')
