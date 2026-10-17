#!/usr/bin/env python3
"""Regenerate the final single-copper D0 board from the reviewed routing plan.
Run with KiCad10's bundled Python; no autorouter or network is needed.
"""
import csv,copy,json,uuid,re
import pcbnew as pcb
from design import ROOT,parts,connectors,SOURCES,WIDTH,HEIGHT
from schematic import write_schematic
U=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://ha-homelab/LP-D0/'+s))
Q=lambda s:json.dumps(str(s))
def stamp_footprint(fp,prefix):
 fp.SetUuid(pcb.KIID(U(prefix)))
 for field in fp.GetFields():field.SetUuid(pcb.KIID(U(prefix+'/field/'+field.GetName())))
 for pad in fp.Pads():pad.SetUuid(pcb.KIID(U(prefix+'/pad/'+pad.GetNumber())))
 for item in fp.GraphicalItems():
  box=item.GetBoundingBox()
  key='/'.join(map(str,[item.GetClass(),item.GetLayer(),box.GetX(),box.GetY(),box.GetWidth(),box.GetHeight()]))
  item.SetUuid(pcb.KIID(U(prefix+'/graphic/'+key)))
plan=json.loads((ROOT/'routing-plan.json').read_text());L=ROOT/'DIY.pretty'
P={o['id']:o for o in plan['pads']}
# Use distinct nets for isolated copper. Wires are real off-board 2-terminal
# assembly components, not a fiction that top copper exists on home-etched FR4.
assembly=[]
for o in parts:
 if o['ref'].startswith('#'):continue
 o=copy.deepcopy(o);o['footprint']='DIY:'+o['footprint'].split(':')[-1]
 o['pins']={p:P[o['ref']+'.'+p]['physical_net'] for p in o['pins']};assembly.append(o)
for o in plan['terminals']:
 if o.get('kind')=='adapter_pin':continue
 assembly.append(dict(ref=o['ref'],model='Insulated wire terminal hole',footprint='DIY:WireTerminal',pins={'1':o['physical_net']},xy=o['xy'],rotation=0,source=None,notes='1.1mm manually drilled, NOT plated; max2 stripped wire ends, solder underside.',types={}))
for o in plan['wires']:
 assembly.append(dict(ref=o['ref'],model='INSULATED WIRE '+str(o['cut_length_mm'])+'mm AWG'+str(o['awg']),footprint='',pins={'1':o['from_net'],'2':o['to_net']},xy=[0,0],rotation=0,source=None,notes=o['from_terminal']+' to '+o['to_terminal']+'; not fabricated copper',types={},off_board=True))
for i,n in enumerate(sorted({n for o in assembly for n in o['pins'].values() if n and any(n.startswith(x+'__') for x in ['+5V_IN','+5V','+3V3','GND'])}),1):
 assembly.append(dict(ref='#FLG'+str(i),model='Assembly power through verified wires',footprint='',pins={'1':n},xy=[0,0],rotation=0,source=None,notes='Power flag follows independently verified assembly wire graph.',types={'1':'power_out'}))
write_schematic(ROOT,assembly,U,Q)
(ROOT/'assembly-netlist.json').write_text(json.dumps(dict(revision='LP-D0',parts=assembly),indent=2)+'\n')
term='''(footprint "WireTerminal" (version 20260206) (generator "pcbnew") (layer "F.Cu") (attr through_hole)
(property "Reference" "T?" (at 0 -1.7) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))
(property "Value" "Wire terminal" (at 0 1.7) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))
(pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 1.1) (layers "*.Cu" "*.Mask")))
'''
(L/'WireTerminal.kicad_mod').write_text(term)
for path in L.glob('*.kicad_mod'):
 fp=pcb.FootprintLoad(str(L),path.stem)
 if path.stem in ['Adafruit1208_TSSOP28','Adafruit1230_SOT23_6']:
  # The body is elevated 6mm. At D0 level only the two header strips obstruct
  # wire holes; the full daughterboard outline remains on assembly layers.
  for graphic in fp.GraphicalItems():
   if graphic.GetLayer()==pcb.F_CrtYd and pcb.ToMM(graphic.GetBoundingBox().GetWidth())>5:graphic.SetLayer(pcb.Dwgs_User)
  if not any(g.GetLayer()==pcb.F_CrtYd for g in fp.GraphicalItems()):
   span,height=(15.24,33.02) if '1208' in path.stem else (7.62,5.08)
   for x in [0,span]:
    g=pcb.PCB_SHAPE(fp);g.SetShape(pcb.SHAPE_T_RECT);g.SetStart(pcb.VECTOR2I(pcb.FromMM(x-1.5),pcb.FromMM(-1.5)));g.SetEnd(pcb.VECTOR2I(pcb.FromMM(x+1.5),pcb.FromMM(height+1.5)));g.SetLayer(pcb.F_CrtYd);g.SetWidth(pcb.FromMM(.05));fp.Add(g)
 for pad in fp.Pads():
  pad.SetSize(pcb.VECTOR2I(pcb.FromMM(2),pcb.FromMM(2)))
  ls=pcb.LSET.AllCuMask();ls.AddLayer(pcb.F_Mask);ls.AddLayer(pcb.B_Mask);pad.SetLayerSet(ls)
 stamp_footprint(fp,'library/'+path.stem)
 pcb.FootprintSave(str(L),fp)
 # KiCad regenerates field UUIDs on library save; normalize only those IDs.
 counter=iter(range(10000))
 path.write_text(re.sub(r'\(uuid \"[^\"]+\"\)',lambda m:'(uuid '+Q(U('library-text/'+path.stem+'/'+str(next(counter))))+')',path.read_text()))
b=pcb.BOARD();b.SetCopperLayerCount(2);s=b.GetDesignSettings();s.m_TrackMinWidth=pcb.FromMM(.6);s.m_MinClearance=pcb.FromMM(.5);s.m_MinThroughDrill=pcb.FromMM(.8)
nets={}
for o in assembly:
 for p,n in o['pins'].items():
  if n is None:n='unconnected-('+o['ref']+'-NC-Pad'+p+')'
  else:n='/'+n
  if n not in nets:nets[n]=pcb.NETINFO_ITEM(b,n);b.Add(nets[n])
for o in assembly:
 if not o['footprint']:continue
 fp=pcb.FootprintLoad(str(L),o['footprint'].split(':')[-1]);fp.SetReference(o['ref']);fp.SetValue(o['model']);fp.SetFPID(pcb.LIB_ID('DIY',o['footprint'].split(':')[-1]));fp.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(v) for v in o['xy']]));fp.SetOrientationDegrees(o['rotation']);fp.SetPath(pcb.KIID_PATH('/'+U('schematic')+'/'+U('symbol/'+o['ref'])))
 fp.Value().SetVisible(False)
 for pad in fp.Pads():
  pad.SetSize(pcb.VECTOR2I(pcb.FromMM(2),pcb.FromMM(2)));ls=pcb.LSET.AllCuMask();ls.AddLayer(pcb.F_Mask);ls.AddLayer(pcb.B_Mask);pad.SetLayerSet(ls)
  n=o['pins'][pad.GetNumber()];pad.SetNet(nets['/'+n if n else 'unconnected-('+o['ref']+'-NC-Pad'+pad.GetNumber()+')'])
  if n is None:pad.SetPinFunction('NC');pad.SetPinType('no_connect')
 b.Add(fp)
for o in plan['bottom_tracks']:
 t=pcb.PCB_TRACK(b);t.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in o['a']]));t.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in o['b']]));t.SetWidth(pcb.FromMM(o['width']));t.SetLayer(pcb.B_Cu);t.SetNet(nets['/'+o['physical_net']]);b.Add(t)
for a,c in [((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,HEIGHT)),((WIDTH,HEIGHT),(0,HEIGHT)),((0,HEIGHT),(0,0))]:
 line=pcb.PCB_SHAPE();line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));line.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in c]));line.SetLayer(pcb.Edge_Cuts);line.SetWidth(pcb.FromMM(.05));b.Add(line)
for i,(x,y) in enumerate([(5,5),(185,5),(5,140),(185,140)],1):
 fp=pcb.FOOTPRINT(b);fp.SetReference('H'+str(i));fp.SetValue('M3 manually drilled');fp.SetAttributes(pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES);fp.Reference().SetVisible(False);fp.Value().SetVisible(False);fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)))
 p=pcb.PAD(fp);p.SetAttribute(pcb.PAD_ATTRIB_NPTH);p.SetShape(pcb.PAD_SHAPE_CIRCLE);p.SetSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));p.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));p.SetLayerSet(pcb.LSET.AllCuMask());fp.Add(p);b.Add(fp)
for w in plan['wires']:
 for a,c in zip(w['route_mm'],w['route_mm'][1:]):
  line=pcb.PCB_SHAPE();line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));line.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in c]));line.SetLayer(pcb.Dwgs_User);line.SetWidth(pcb.FromMM(.18));b.Add(line)
for text,xy in [('LP-D0 / B.Cu ONLY / INSULATED LINKS REQUIRED',(90,5)),('ISOLATED 5V ONLY / NO PoE VOLTAGE',(110,140))]:
 t=pcb.PCB_TEXT(b);t.SetText(text);t.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(v) for v in xy]));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(1.2),pcb.FromMM(1.2)));t.SetTextThickness(pcb.FromMM(.18));t.SetLayer(pcb.F_SilkS);b.Add(t)
for fp in b.GetFootprints():stamp_footprint(fp,'footprint/'+fp.GetReference())
for index,item in enumerate(b.GetTracks()):item.SetUuid(pcb.KIID(U('track/'+str(index))))
for index,item in enumerate(b.GetDrawings()):item.SetUuid(pcb.KIID(U('drawing/'+str(index))))
b.BuildListOfNets();b.BuildConnectivity();pcb.SaveBoard(str(ROOT/'diy.kicad_pcb'),b)
# Normalize generated native IDs after serialization, preserving symbol path IDs.
pth=ROOT/'diy.kicad_pcb';text=pth.read_text();counter=[0]
def stable(match):
 counter[0]+=1;return '(uuid '+Q(U('native/'+str(counter[0])))+')'
text=re.sub(r'\(uuid \"[^\"]+\"\)',stable,text);pth.write_text(text)
for c in connectors:
 f=next(f for f in b.GetFootprints() if f.GetReference()==c['ref'])
 c['board_position_mm']=[round(pcb.ToMM(v),6) for v in [f.GetPosition().x,f.GetPosition().y]];c['rotation_deg']=f.GetOrientationDegrees()
 c['pad_centers_mm']=[dict(number=p.GetNumber(),x=round(pcb.ToMM(p.GetPosition().x),6),y=round(pcb.ToMM(p.GetPosition().y),6)) for p in f.Pads()]
(ROOT/'connectors.json').write_text(json.dumps(dict(schema_version=1,revision='LP-D0',status='prototype_not_hardware_validated',sources=SOURCES,connectors=connectors),indent=2)+'\n')
(ROOT/'jumpers.json').write_text(json.dumps(dict(schema_version=1,revision='LP-D0',fabricated_copper=False,view='component/top view; wire ABOVE board',terminals=plan['terminals'],wires=plan['wires']),indent=2)+'\n')
with (ROOT/'jumpers.csv').open('w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['Reference','Logical net','From terminal','To terminal','AWG','Route length mm','Cut length mm','Strip each end mm','From physical pad','To physical pad','From height mm','To height mm','Height allowance mm','Assembly notes'])
 for w in plan['wires']:wr.writerow([w['ref'],w['logical_net'],w['from_terminal'],w['to_terminal'],w['awg'],w['route_length_mm'],w['cut_length_mm'],w['strip_each_end_mm'],w.get('from_pin',w['from_terminal']+'.1'),w.get('to_pin',w['to_terminal']+'.1'),w.get('from_height_mm',0),w.get('to_height_mm',0),w.get('height_allowance_mm',0),w.get('notes','')])
with (ROOT/'assembly-bom.csv').open('w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['Reference','Quantity','Manufacturer part / value','Footprint','Note','Source'])
 for o in parts:
  if not o['ref'].startswith('#'):wr.writerow([o['ref'],1,o['model'],o['footprint'],o['notes'],SOURCES.get(o['source'],'')])
with (ROOT/'drill.csv').open('w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['Reference','Pad','X top-view mm','Y top-view mm','Drill mm','Plated'])
 for fp in b.GetFootprints():
  for p in fp.Pads():wr.writerow([fp.GetReference(),p.GetNumber(),round(pcb.ToMM(p.GetPosition().x),6),round(pcb.ToMM(p.GetPosition().y),6),round(pcb.ToMM(p.GetDrillSize().x),3),'NO - manual drilling'])
from bom import write_bom
write_bom()
(ROOT/'logical-netlist.json').write_text(json.dumps(dict(revision='LP-D0',parts=parts),indent=2)+'\n')
print('Generated final board:',len(plan['bottom_tracks']),'bottom tracks;',len(plan['wires']),'physical insulated links')
