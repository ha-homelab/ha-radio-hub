#!/usr/bin/env python3
"""Generate LP-C0 native KiCad source from design.py. Run with KiCad's Python.
The routed PCB is kept separately: regeneration produces carrier-unrouted.kicad_pcb.
"""
import argparse, csv, json, uuid
from pathlib import Path
import pcbnew as pcb
from design import ROOT, parts, connectors, SOURCES
p=argparse.ArgumentParser();p.add_argument('--libraries',type=Path,required=True);args=p.parse_args()
LIB=args.libraries
LOCAL=ROOT/'Carrier.pretty';LOCAL.mkdir(exist_ok=True)
BUILD=ROOT/'.build';BUILD.mkdir(exist_ok=True)
U=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://ha-homelab/LP-C0/'+s))
Q=lambda s:json.dumps(str(s))

def simple_fp(name,pads,rect,descr,th=False):
    x1,y1,x2,y2=rect
    lines=[f'(footprint {Q(name)} (version 20260206) (generator "pcbnew") (layer "F.Cu") (descr {Q(descr)})',
    f'(property "Reference" "REF**" (at 0 {y1-1.5} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
    f'(property "Value" {Q(name)} (at 0 {y2+1.5} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
    f'(attr {"through_hole" if th else "smd"})']
    for layer,d in [('F.Fab',0),('F.CrtYd',0.5)]:
        lines.append(f'(fp_rect (start {x1-d} {y1-d}) (end {x2+d} {y2+d}) (stroke (width 0.05) (type solid)) (fill none) (layer "{layer}"))')
    for n,x,y,w,h in pads:
        lines.append(f'(pad "{n}" {"thru_hole" if th else "smd"} {"rect" if n==1 or not th else "oval"} (at {x} {y}) (size {w} {h}) '+('(drill 1.1) (layers "*.Cu" "*.Mask")' if th else '(layers "F.Cu" "F.Paste" "F.Mask")')+')')
    lines.append(')');(LOCAL/(name+'.kicad_mod')).write_text('\n'.join(lines)+'\n')

# Manufacturer hole recommendation and dimensions, rather than generic IDC dimensions.
simple_fp('Wurth_61204021621',[(2*i+j+1,j*2.54,i*2.54,1.8,1.8) for i in range(20) for j in range(2)],(-3.28,-5.10,5.82,53.36),'Wurth61204021621 datasheet002.001:2.54grid;1.1drill;58.46x9.1body;pin1square',True)
simple_fp('Littelfuse_449',[(1,-2.45,0,1.96,3.15),(2,2.45,0,1.96,3.15)],(-3.15,-1.47,3.15,1.47),'Littelfuse449 datasheet2023-06-26 page3 recommended pads1.96x3.15 gap2.95 total6.86')
# Vendor only footprints actually used. Preserve source metadata and remove external3D references.
for obj in parts:
    fp=obj['footprint']
    if not fp or fp.startswith('Carrier:'):continue
    lib,name=fp.split(':');src=LIB/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')
    if not src.exists():raise FileNotFoundError(src)
    txt=src.read_text()
    # 3D paths are optional; no phantom local dependency in this portable package.
    at=txt.find('\n\t(model ')
    if at>=0:txt=txt[:at]+'\n)\n'
    if name=='JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical':
        # The two isolated hold-down tabs are distinct NC terminals, not one routed net.
        for number in ['MP1','MP2']:
            txt=txt.replace('(pad \"MP\"', '(pad \"'+number+'\"',1)
    (LOCAL/(name+'.kicad_mod')).write_text(txt)
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Carrier")(type "KiCad")(uri "${KIPRJMOD}/Carrier.pretty")(options "")(descr "Portable LP-C0 footprints")))\n')
for obj in parts:
    if obj['footprint']:obj['footprint']='Carrier:'+obj['footprint'].split(':')[1]

# Symbol bodies contain actual physical pin numbers; net labels are on real wire stubs.
symbols=[];instances=[];wires=[];labels=[];ncs=[]
rootid=U('schematic')
def geom(obj):
    count=len(obj['pins']);left=(count+1)//2 if count>8 else count
    if count==2 and obj['ref'][0] in 'RCYF':
        return [(num,net,(-7.62 if i==0 else 7.62),0,(0 if i==0 else 180),i==1) for i,(num,net) in enumerate(obj['pins'].items())],1
    r=[]
    for i,(num,net) in enumerate(obj['pins'].items()):
        right=i>=left;rank=i-left if right else i
        r.append((num,net,20.32 if right else -20.32, -rank*2.54,180 if right else 0,right))
    return r,left
for idx,obj in enumerate(parts):
    ref=obj['ref'];g,left=geom(obj);name='LP_'+ref.replace('#','')
    ymin=-max(1,left-1)*2.54-2.54
    sym=[f'(symbol {Q(name)} (pin_names (offset 0.508)) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"})',
    f'(property "Reference" {Q(ref)} (at 0 5.08 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(obj["model"])} (at 0 2.54 0) (effects (font (size 1.27 1.27))))',
    f'(symbol "{name}_0_1" (rectangle (start -15.24 1.27) (end 15.24 {ymin}) (stroke (width 0.254) (type default)) (fill (type background))))',f'(symbol "{name}_1_1"']
    for num,net,x,y,ang,right in g:
        typ=obj['types'].get(num,'passive');pinname=net or 'NC'
        short=len(obj['pins'])==2 and ref[0] in 'RCYF';pinlen=3.81 if short else 5.08;shown='~' if short else pinname
        sym.append(f'(pin {typ} line (at {x} {y} {ang}) (length {pinlen}) (name {Q(shown)} (effects (font (size 0.8 0.8)))) (number {Q(num)} (effects (font (size 1 1)))))')
    sym.append('))')
    if len(obj['pins'])==2 and ref[0] in 'RCYF':
        # Conventional IEC passives keep the schematic readable at useful zoom.
        body=f'(symbol "{name}_0_1" '
        if ref[0]=='C':
            body+=''.join(f'(polyline (pts (xy {xx} -2.54) (xy {xx} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))' for xx in [-1.27,1.27])
            body+=''.join(f'(polyline (pts (xy {a} 0) (xy {b} 0)) (stroke (width 0.254) (type default)) (fill (type none)))' for a,b in [(-3.81,-1.27),(1.27,3.81)])
        else:
            body+='(rectangle (start -3.81 -1.27) (end 3.81 1.27) (stroke (width 0.254) (type default)) (fill (type none)))'
        body+=')'
        sym[3]=body
    symbols.append('\n'.join(sym))
    row=idx//7
    x=43.18+(idx%7)*81.28;y=25.4+min(row,2)*68.58+max(0,row-2)*38.1
    iid=U('symbol/'+ref)
    inst=[f'(symbol (lib_id "Carrier:{name}") (at {x:.4f} {y:.4f} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{iid}")',f'(property "Reference" {Q(ref)} (at {x} {y-6.35} 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(obj["model"])} (at {x} {y-3.81} 0) (effects (font (size 1.0 1.0))))',f'(property "Footprint" {Q(obj["footprint"])} (at {x} {y} 0) (effects (font (size 1 1)) hide))']
    for num,net,px,py,ang,right in g:
        inst.append(f'(pin {Q(num)} (uuid "{U(ref+"/pin/"+num)}"))')
        xx=round(x+px,4);yy=round(y-py,4);end=round(xx+(5.08 if right else -5.08),4)
        if net is None:ncs.append(f'(no_connect (at {xx} {yy}) (uuid "{U(ref+"/NC/"+num)}"))')
        else:
            wires.append(f'(wire (pts (xy {xx} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{U(ref+"/wire/"+num)}"))')
            labels.append(f'(label {Q(net)} (at {end} {yy} {0 if right else 180}) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid "{U(ref+"/label/"+num)}"))')
    inst.append(f'(instances (project "carrier" (path "/{rootid}" (reference {Q(ref)}) (unit 1)))) )');instances.append('\n'.join(inst))
(ROOT/'Carrier.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+'\n'.join(symbols)+'\n)\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Carrier")(type "KiCad")(uri "${KIPRJMOD}/Carrier.kicad_sym")(options "")(descr "LP-C0 explicit physical pin symbols")))\n')
embedded=[s.replace('(symbol "LP_', '(symbol "Carrier:LP_',1) for s in symbols]
sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A2") (title_block (title "LP-C0 low-voltage module carrier - PROTOTYPE") (date "2026-10-17") (rev "C0") (comment 1 "3.3V logic; external isolated5V and buck; named harnesses, no unverified module footprints"))\n(lib_symbols\n'+'\n'.join(embedded)+')\n'+'\n'.join(wires+labels+ncs+instances)+'\n)\n'
(ROOT/'carrier.kicad_sch').write_text(sch)

# Board geometry and connectivity. Autorouter output becomes carrier.kicad_pcb only after verification.
board=pcb.BOARD();board.SetCopperLayerCount(2)
settings=board.GetDesignSettings();settings.m_TrackMinWidth=pcb.FromMM(0.2);settings.m_MinClearance=pcb.FromMM(0.2);settings.m_ViasMinSize=pcb.FromMM(0.7);settings.m_MinThroughDrill=pcb.FromMM(0.3)
nets={}
for obj in parts:
    for n in obj['pins'].values():
        if n is not None and n not in nets:
            ni=pcb.NETINFO_ITEM(board,n);board.Add(ni);nets[n]=ni
for obj in parts:
    if not obj['footprint']:continue
    fp=pcb.FootprintLoad(str(LOCAL),obj['footprint'].split(':')[1]);fp.SetReference(obj['ref']);fp.SetValue(obj['model']);fp.SetFPID(pcb.LIB_ID('Carrier',obj['footprint'].split(':')[1]));fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(obj['xy'][0]),pcb.FromMM(obj['xy'][1])));fp.SetOrientationDegrees(obj['rotation']);fp.SetPath(pcb.KIID_PATH('/'+rootid+'/'+U('symbol/'+obj['ref'])))
    physical_numbers={pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
    assert physical_numbers==set(obj['pins']), (obj['ref'], 'physical pad coverage',physical_numbers^set(obj['pins']))
    for pad in fp.Pads():
        net=obj['pins'].get(pad.GetNumber())
        if net:pad.SetNet(nets[net])
    fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.9),pcb.FromMM(0.9)));fp.Reference().SetTextThickness(pcb.FromMM(0.15));fp.Value().SetVisible(False)
    board.Add(fp)
for a,b in [((0,0),(160,0)),((160,0),(160,100)),((160,100),(0,100)),((0,100),(0,0))]:
    s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])));s.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]),pcb.FromMM(b[1])));s.SetLayer(pcb.Edge_Cuts);s.SetWidth(pcb.FromMM(0.05));board.Add(s)
for i,(x,y) in enumerate([(5,5),(155,5),(5,95),(155,95)],1):
    fp=pcb.FOOTPRINT(board);fp.SetReference('H'+str(i));fp.SetValue('M3 NPTH');fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
    pad=pcb.PAD(fp);pad.SetAttribute(pcb.PAD_ATTRIB_NPTH);pad.SetShape(pcb.PAD_SHAPE_CIRCLE);pad.SetSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));pad.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));pad.SetLayerSet(pcb.LSET.AllCuMask());fp.Add(pad);board.Add(fp)
for txt,x,y,size in [('LP-C0 MODULE CARRIER / PROTOTYPE',76,4,1.2),('5V DC ONLY',18,5,0.9),('J3: NOT RASPBERRY PI',28,82,0.9),('3V3 LOGIC / NO HOT PLUG',78,97,1.0),('1',19,25,1.0)]:
    t=pcb.PCB_TEXT(board);t.SetText(txt);t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(0.15));t.SetLayer(pcb.F_SilkS);board.Add(t)
# Local short crystal nets and VDD escape are routed before global routing.
def point(ref,num):
    f=next(f for f in board.GetFootprints() if f.GetReference()==ref)
    p=next(p for p in f.Pads() if p.GetNumber()==str(num)).GetPosition()
    return (pcb.ToMM(p.x),pcb.ToMM(p.y))
def route(net,coords,width=0.25):
    for a,b in zip(coords,coords[1:]):
        t=pcb.PCB_TRACK(board);t.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])));t.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]),pcb.FromMM(b[1])));t.SetWidth(pcb.FromMM(width));t.SetLayer(pcb.F_Cu);t.SetNet(nets[net]);t.SetLocked(True);board.Add(t)
route('xtal1',[point('U1',6),(82.8,56.025),(80.05,53.275),point('C1',1),point('Y1',1)])
route('xtal2',[point('U1',7),(83.1,56.675),(80.05,59.725),point('C2',1),point('Y1',2)])
route('+3V3',[point('U1',8),(83.8,57.325),(83.8,61)])
board.BuildListOfNets();board.BuildConnectivity();pcb.SaveBoard(str(BUILD/'carrier-unrouted.kicad_pcb'),board)
pcb.ExportSpecctraDSN(board,str(BUILD/'carrier.dsn'))
for c in connectors:
    f=next(f for f in board.GetFootprints() if f.GetReference()==c['ref'])
    c['board_position_mm']=[round(pcb.ToMM(f.GetPosition().x),4),round(pcb.ToMM(f.GetPosition().y),4)]
    c['rotation_deg']=f.GetOrientationDegrees()
    c['pad_centers_mm']=[dict(number=p.GetNumber(),x=round(pcb.ToMM(p.GetPosition().x),4),y=round(pcb.ToMM(p.GetPosition().y),4)) for p in f.Pads() if p.GetNumber().isdigit()]
(ROOT/'connectors.json').write_text(json.dumps(dict(schema_version=1,revision='LP-C0',status='prototype_not_hardware_validated',sources=SOURCES,connectors=connectors),indent=2)+'\n')
(ROOT/'netlist.json').write_text(json.dumps(dict(revision='LP-C0',parts=parts),indent=2)+'\n')
with (ROOT/'assembly-bom.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Quantity','Manufacturer part / value','Footprint','Note','Source'])
    for obj in parts:
        if not obj['ref'].startswith('#'):w.writerow([obj['ref'],1,obj['model'],obj['footprint'],obj['notes'],SOURCES.get(obj['source'],'')])
dsn=BUILD/'carrier.dsn'
s=dsn.read_text().replace('(width 200)','(width 250)').replace('(clearance 50 (type smd_smd))','(clearance 200 (type smd_smd))').replace('600:300','800:400').replace('(circle F.Cu 600)','(circle F.Cu 800)').replace('(circle B.Cu 600)','(circle B.Cu 800)')
s=s.replace('(class kicad_default +3V3 +5V +5V_IN ', '(class kicad_default ')
pos=s.rfind('\n  (wiring');network_end=s.rfind('\n  )',0,pos)
s=s[:network_end]+'\n    (class power "+5V_IN" "+5V" "+3V3" (circuit (use_via "Via[0-1]_800:400_um")) (rule (width 800) (clearance 200)))\n'+s[network_end:]
dsn.write_text(s)
print(f'Generated {len(parts)} symbols, {len(nets)} nets and {len(connectors)} keyed harness connectors')
