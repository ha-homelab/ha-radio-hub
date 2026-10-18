#!/usr/bin/env python3
"""MC1 editable KiCad carrier generator. Run with KiCad Python; see README.md.
Creates unrouted source, schematic, exact-pad ledger and Specctra DSN.
Module footprints use manufacturer hole centers; external modules use harnesses.
"""
import argparse, csv, json, uuid, re
from pathlib import Path
import pcbnew as pcb
from design import ROOT, parts, connectors, SOURCES, s3names, h2names
ap=argparse.ArgumentParser(); ap.add_argument('--libraries', type=Path, required=True); a=ap.parse_args()
LIB=a.libraries; LOCAL=ROOT/'MC1.pretty'; LOCAL.mkdir(exist_ok=True); BUILD=ROOT/'.build'; BUILD.mkdir(exist_ok=True)
U=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://ha-radio-hub/MC1/'+s)); Q=lambda s:json.dumps(str(s))

def module_fp(name,pads,rect,description):
    x1,y1,x2,y2=rect
    lines=[f'(footprint {Q(name)} (version 20250108) (generator "pcbnew") (layer "F.Cu") (descr {Q(description)})',f'(property "Reference" "REF**" (at {(x1+x2)/2} {y2+2} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',f'(property "Value" {Q(name)} (at {(x1+x2)/2} {y2+3.5} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))','(attr through_hole)']
    for layer,d in [('F.Fab',0),('F.CrtYd',0.5)]:
        lines.append(f'(fp_rect (start {x1-d} {y1-d}) (end {x2+d} {y2+d}) (stroke (width 0.05) (type solid)) (fill none) (layer "{layer}"))')
    # Two thin longitudinal silkscreen guides do not cross any plated header holes.
    for xx in [x1,x2]:
        lines.append(f'(fp_line (start {xx} {max(1,y1)}) (end {xx} {y2-1}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    for num,x,y in pads:
        shape='rect' if num in ['J1.1','1'] else 'circle'
        lines.append(f'(pad {Q(num)} thru_hole {shape} (at {x} {y}) (size 1.9 1.9) (drill 1.1) (layers "*.Cu" "*.Mask"))')
    lines.append(')');(LOCAL/(name+'.kicad_mod')).write_text('\n'.join(lines)+'\n')
module_fp('S3_DevKitC1_v11',[(f'{r}.{i+1}',x,i*2.54) for r,x in [('J1',0),('J3',22.86)] for i in range(22)],(-1.27,-1.40,24.13,61.34),'Official Espressif v1.1 dimension PDF;22.86mm row spacing;2.54mm pitch;factory male headers;direct solder;1.1mm carrier finished hole is design allowance, not factory hole size')
module_fp('H2_DevKitM1',[(f'{r}.{i+1}',x,i*2.54) for r,x in [('J1',0),('J3',22.86)] for i in range(15)],(-1.27,-1.575,24.13,46.685),'Official Espressif v1.2 dimension PDF;22.86 rowspacing;2.54 pitch;antenna extends5.4mm beyond PCBtop;direct factory male headers')
module_fp('XIAO_MG24',[(str(i+1),0,i*2.54) for i in range(7)]+[(str(14-i),15.24,i*2.54) for i in range(7)],(-1.27,-2.921,16.51,18.034),'Seeed official XIAO MG24 260114 nativePCB inner headerhole centers;15.24rowspacing;2.54pitch;D0pad1upperleft USBup;presoldered102010690')
module_fp('WIZ850io',[(f'{r}.{i+1}',x,i*2.54) for r,x in [('J1',0),('J2',20.32)] for i in range(6)],(-1.34,-9.1,21.66,18.6),'WIZnet dimension and top-view pinmap;20.32rowspacing;2.54pitch;RJ45extends2.7mm beyond23x25PCB;direct pins')
for p in parts:
    fp=p['footprint']
    if fp.startswith('MC1:'):continue
    lib,name=fp.split(':'); src=LIB/'footprints'/(lib+'.pretty')/(name+'.kicad_mod'); txt=src.read_text(); at=txt.find('\n\t(model ')
    if at>=0:txt=txt[:at]+'\n)\n'
    (LOCAL/(name+'.kicad_mod')).write_text(txt);p['footprint']='MC1:'+name
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "MC1")(type "KiCad")(uri "${KIPRJMOD}/MC1.pretty")(options "")(descr "MC1 verified module centers and THT connectors")))\n')

# Generic module symbols explicitly show every factory header pin; passive terminal
# types avoid pretending this high-level interposer schematic models internal ICs.
symbols=[]; instances=[]; wires=[]; labels=[]; ncs=[]; rootid=U('schematic')
def geometry(p):
    count=len(p['pins']); left=(count+1)//2 if count>8 else count
    if count==2 and p['ref'][0] in 'RD':return [(n,net,-7.62 if i==0 else 7.62,0,0 if i==0 else 180,i==1) for i,(n,net) in enumerate(p['pins'].items())],1
    return [(n,net,20.32 if i>=left else -20.32,-(i-left if i>=left else i)*2.54,180 if i>=left else 0,i>=left) for i,(n,net) in enumerate(p['pins'].items())],left
for ix,p in enumerate(parts):
    ref=p['ref']; name='Module_'+ref; g,left=geometry(p); short=len(p['pins'])==2 and ref[0] in 'RD'
    sy=[f'(symbol {Q(name)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',f'(property "Reference" {Q(ref)} (at 0 5.08 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(p["model"])} (at 0 2.54 0) (effects (font (size 1.27 1.27))))']
    if short:
        if ref[0]=='D':
            body='(polyline (pts (xy -2.54 -2.54) (xy -2.54 2.54)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy -2.54 0) (xy 2.54 -2.54) (xy 2.54 2.54) (xy -2.54 0)) (stroke (width 0.254) (type default)) (fill (type none)))'
            body+='(polyline (pts (xy -3.81 0) (xy -2.54 0)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 2.54 0) (xy 3.81 0)) (stroke (width 0.254) (type default)) (fill (type none)))'
        else:body='(rectangle (start -3.81 -1.27) (end 3.81 1.27) (stroke (width 0.254) (type default)) (fill (type none)))'
    else:body=f'(rectangle (start -15.24 1.27) (end 15.24 {-max(1,left-1)*2.54-2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
    sy += [f'(symbol "{name}_0_1" {body})',f'(symbol "{name}_1_1"']
    for num,net,x,y,ang,right in g:
        pname=net or 'NC'
        if ref=='U1':row,n=num.split('.');pname='GPIO'+s3names[row][int(n)-1] if s3names[row][int(n)-1].isdigit() else s3names[row][int(n)-1]
        if ref=='U2':row,n=num.split('.');pname='GPIO'+h2names[row][int(n)-1] if h2names[row][int(n)-1].isdigit() else h2names[row][int(n)-1]
        sy.append(f'(pin passive line (at {x} {y} {ang}) (length {3.81 if short else 5.08}) (name {Q("~" if short else pname)} (effects (font (size 0.8 0.8)))) (number {Q(num)} (effects (font (size 1 1)))))')
    sy.append('))');symbols.append('\n'.join(sy))
    if ix<4:x,y=45.72+ix*101.6,30.48
    elif ix<11:x,y=45.72+((ix-4)%4)*101.6,111.76+((ix-4)//4)*45.72
    else:x,y=45.72+((ix-11)%4)*101.6,210.82+((ix-11)//4)*35.56
    iid=U('symbol/'+ref)
    ins=[f'(symbol (lib_id "MC1:{name}") (at {x:.4f} {y:.4f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{iid}")',f'(property "Reference" {Q(ref)} (at {x} {y-6.35} 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(p["model"])} (at {x} {y-3.81} 0) (effects (font (size 1 1))))',f'(property "Footprint" {Q(p["footprint"])} (at {x} {y} 0) (effects (font (size 1 1)) hide))']
    for num,net,px,py,ang,right in g:
        ins.append(f'(pin {Q(num)} (uuid "{U(ref+"/pin/"+num)}"))');xx=round(x+px,4);yy=round(y-py,4);end=round(xx+(5.08 if right else -5.08),4)
        if net is None:ncs.append(f'(no_connect (at {xx} {yy}) (uuid "{U(ref+"/NC/"+num)}"))')
        else:
            wires.append(f'(wire (pts (xy {xx} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{U(ref+"/wire/"+num)}"))')
            labels.append(f'(label {Q(net)} (at {end} {yy} {0 if right else 180}) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid "{U(ref+"/label/"+num)}"))')
    ins.append(f'(instances (project "mc1" (path "/{rootid}" (reference {Q(ref)}) (unit 1)))))'); instances.append('\n'.join(ins))
(ROOT/'MC1.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+'\n'.join(symbols)+'\n)\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "MC1")(type "KiCad")(uri "${KIPRJMOD}/MC1.kicad_sym")(options "")(descr "MC1 all physical module pins")))\n')
embed=[s.replace('(symbol "Module_', '(symbol "MC1:Module_',1) for s in symbols]
sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A3") (title_block (title "MC1 - ready-module carrier / engineering prototype") (date "2026-10-17") (rev "MC1") (comment 1 "Direct-solder factory male pins; no sockets; no carrier SMT components") (comment 2 "External isolated fused 5V; separate peripheral 3V3; module 3V3 outputs never joined"))\n(lib_symbols\n'+'\n'.join(embed)+')\n'+'\n'.join(wires+labels+ncs+instances)+'\n)\n';(ROOT/'mc1.kicad_sch').write_text(sch)

board=pcb.BOARD(); board.SetCopperLayerCount(2); st=board.GetDesignSettings(); st.m_TrackMinWidth=pcb.FromMM(.2);st.m_MinClearance=pcb.FromMM(.2);st.m_ViasMinSize=pcb.FromMM(.8);st.m_MinThroughDrill=pcb.FromMM(.4)
nets={}
for p in parts:
    for n in p['pins'].values():
        if n is not None and n not in nets:nets[n]=pcb.NETINFO_ITEM(board,n);board.Add(nets[n])
for p in parts:
    fp=pcb.FootprintLoad(str(LOCAL),p['footprint'].split(':')[1]);fp.SetReference(p['ref']);fp.SetValue(p['model']);fp.SetFPID(pcb.LIB_ID('MC1',p['footprint'].split(':')[1]));fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(p['xy'][0]),pcb.FromMM(p['xy'][1])));fp.SetOrientationDegrees(p['rotation']);fp.SetPath(pcb.KIID_PATH('/'+rootid+'/'+U('symbol/'+p['ref'])))
    assert {x.GetNumber() for x in fp.Pads()}==set(p['pins']),p['ref']
    for pad in fp.Pads():
        if p['pins'][pad.GetNumber()]:pad.SetNet(nets[p['pins'][pad.GetNumber()]])
    fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.9),pcb.FromMM(.9)));fp.Reference().SetTextThickness(pcb.FromMM(.15));fp.Value().SetVisible(False);board.Add(fp)
for p,q in [((0,0),(160,0)),((160,0),(160,100)),((160,100),(0,100)),((0,100),(0,0))]:
    s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(pcb.VECTOR2I(pcb.FromMM(p[0]),pcb.FromMM(p[1])));s.SetEnd(pcb.VECTOR2I(pcb.FromMM(q[0]),pcb.FromMM(q[1])));s.SetLayer(pcb.Edge_Cuts);s.SetWidth(pcb.FromMM(.05));board.Add(s)
for i,(x,y) in enumerate([(5,5),(155,5),(5,95),(155,95)],1):
    fp=pcb.FOOTPRINT(board);fp.SetReference('H'+str(i));fp.SetValue('M3 NPTH');fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));fp.Reference().SetVisible(False);fp.Value().SetVisible(False);fp.SetAttributes(pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES|pcb.FP_BOARD_ONLY)
    pd=pcb.PAD(fp);pd.SetAttribute(pcb.PAD_ATTRIB_NPTH);pd.SetShape(pcb.PAD_SHAPE_CIRCLE);pd.SetSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));pd.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)));pd.SetLayerSet(pcb.LSET.AllCuMask());fp.Add(pd);board.Add(fp)
for txt,x,y,size in [('MC1 / MODULE CARRIER',24,12,1),('ENGINEERING PROTOTYPE',24,15,.9),('160 x 100 / 2 LAYERS',24,18,.8),('NO SOCKETS / NO SMT',23,22,.9),('FUSED 5V ONLY',23,96,.8),('3V3 BUCK',44,96,.8),('WK2132',98,96,.8),('ZAC93',132,96,.8),('CC1101',66,81,.8),('RADAR',149,52,.8),('BME680',149,74,.8),('D0 / GND',141,38,.8),('PROGRAM BEFORE SOLDERING',107,73,.9),('POWERED SERVICE + VBUS BLOCKER',109,76,.8),('MCU 3V3 OUTPUTS ISOLATED',109,79,.8)]:
    t=pcb.PCB_TEXT(board);t.SetText(txt);t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(.13));t.SetLayer(pcb.F_SilkS);board.Add(t)
# No copper pours underneath/on top of antenna end. The antenna tips extend
# over the top edge; keep first 1.2mm of carrier copper-free. All pads start y>=2.76.
# Conservative RF keepouts between the factory header rows; no copper/tracks/vias.
# Rectangles stop short of the header pads and extend to the carrier edge.
for bounds in [(0,0,160,1.2),(47,0,64,12),(89,0,106,12),(128.8,0,141,5)]:
    zone=pcb.ZONE(board);zone.SetIsRuleArea(True);zone.SetLayerSet(pcb.LSET.AllCuMask());zone.SetDoNotAllowZoneFills(True);zone.SetDoNotAllowTracks(True);zone.SetDoNotAllowVias(True);zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False)
    outline=zone.Outline();outline.NewOutline();x1,y1,x2,y2=bounds
    for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:outline.Append(pcb.FromMM(x),pcb.FromMM(y))
    board.Add(zone)
board.BuildListOfNets();board.BuildConnectivity();pcb.SaveBoard(str(BUILD/'mc1-unrouted.kicad_pcb'),board);pcb.ExportSpecctraDSN(board,str(BUILD/'mc1.dsn'))
# All high-current supply nets get 0.8mm traces rather than default signal width.
dsn=BUILD/'mc1.dsn';s=dsn.read_text().replace('(width 200)','(width 250)').replace('(clearance 50 (type smd_smd))','(clearance 200 (type smd_smd))').replace('600:300','800:400').replace('(circle F.Cu 600)','(circle F.Cu 800)').replace('(circle B.Cu 600)','(circle B.Cu 800)')
power=[n for n in nets if n.startswith('+') or n=='GND']
match=re.search(r'\(class kicad_default(.*?)\(circuit',s,re.S)
if match:
    body=match.group(1)
    for n in power:body=re.sub(r'(?<!\S)'+re.escape(n)+r'(?!\S)','',body);body=body.replace('"'+n+'"','')
    s=s[:match.start(1)]+body+s[match.end(1):]
pos=s.rfind('\n  (wiring');end=s.rfind('\n  )',0,pos);s=s[:end]+'\n    (class power '+' '.join(Q(n) for n in power)+' (circuit (use_via "Via[0-1]_800:400_um")) (rule (width 800) (clearance 200)))\n'+s[end:];dsn.write_text(s)
ledger=[]
for p in parts:
    fp=next(f for f in board.GetFootprints() if f.GetReference()==p['ref']);r=dict(p);r['pad_centers_mm']=[dict(number=pd.GetNumber(),net=p['pins'][pd.GetNumber()],x=round(pcb.ToMM(pd.GetPosition().x),4),y=round(pcb.ToMM(pd.GetPosition().y),4),drill_mm=round(pcb.ToMM(pd.GetDrillSize().x),4)) for pd in fp.Pads()];ledger.append(r)
metadata=dict(schema_version=1,revision='MC1',status='engineering_prototype_not_fabrication_release',board=dict(width_mm=160,height_mm=100,copper_layers=2,assembly='Factory male pins directly soldered in PTH; no female sockets',signal_track_mm=.25,power_track_mm=.8,via_diameter_mm=.8,via_drill_mm=.4),sources=SOURCES,parts=ledger)
(ROOT/'design.json').write_text(json.dumps(metadata,indent=2)+'\n');(ROOT/'connectors.json').write_text(json.dumps(dict(schema_version=1,revision='MC1',connectors=[r for r in ledger if r['ref'].startswith(('U','J'))]),indent=2)+'\n')
with (ROOT/'BOM.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Quantity','Part / module','Carrier footprint','Assembly note','Source']);
    for p in parts:w.writerow([p['ref'],1,p['model'],p['footprint'],p['notes'],SOURCES.get(p['source'],'')])
project={'meta':{'filename':'mc1.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.8,'min_through_hole_diameter':.4,'min_copper_edge_clearance':.25}}},'net_settings':{'classes':[{'name':'Default','clearance':.2,'track_width':.25,'via_diameter':.8,'via_drill':.4},{'name':'Power','clearance':.2,'track_width':.8,'via_diameter':.8,'via_drill':.4}],'netclass_patterns':[{'netclass':'Power','pattern':'/'+n} for n in power]}}
(ROOT/'mc1.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
print(f'MC1 generated: {len(parts)} THT footprints, {len(nets)} connected nets; 160x100mm, 2 copper layers')
