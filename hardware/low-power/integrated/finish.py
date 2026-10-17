#!/usr/bin/env python3
"""Import a real Specctra session and generate prototype review exports after ERC/DRC."""
import argparse,json,shutil,subprocess,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as pcb
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'.build';BUILD.mkdir(exist_ok=True)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',required=True,type=Path);p.add_argument('--kicad-cli',default='kicad-cli');p.add_argument('--prepare-only',action='store_true',help='Write an intermediate board/report for the documented completion pass; do not export');p.add_argument('--seed-board',type=Path,default=BUILD/'integrated-unrouted.kicad_pcb');args=p.parse_args()
board=pcb.LoadBoard(str(args.seed_board))
if not pcb.ImportSpecctraSES(board,str(args.session.resolve())):raise SystemExit('Specctra import failed; no routed PCB was written')
# Native parity names no-connect nets explicitly. Obtain exact names from KiCad rather than guessing.
netlist=BUILD/'netlist-native.xml'
subprocess.run([args.kicad_cli,'sch','export','netlist','--format','kicadxml','-o',str(netlist),str(ROOT/'integrated.kicad_sch')],check=True)
fps={f.GetReference():f for f in board.GetFootprints()}
fps['U3'].Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(139),pcb.FromMM(16.5)))
for n in ET.parse(netlist).findall('./nets/net'):
    name=n.attrib['name']
    if not name.startswith('unconnected-'):continue
    ni=next((x for x in board.GetNetInfo().NetsByNetcode().values() if x.GetNetname()==name),None)
    if ni is None:ni=pcb.NETINFO_ITEM(board,name);board.Add(ni)
    for node in n.findall('node'):
        fp=fps.get(node.attrib['ref'])
        if fp:
            for pad in fp.Pads():
                if pad.GetNumber()==node.attrib['pin']:pad.SetNet(ni)
from tocap_escape import restore_ground_return
restore_ground_return(board)
# Surface ground returns connect the SMD pads to the reserved stitching vias;
# In1 remains the continuous internal reference layer.
for layer in (pcb.F_Cu,pcb.B_Cu):
 z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='gnd'));z.SetLocalClearance(pcb.FromMM(.25));z.SetMinThickness(pcb.FromMM(.2));z.SetPadConnection(pcb.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(0)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(1,.25),(159,.25),(159,141),(73,141),(73,117),(1,117)]:poly.Append(pcb.FromMM(x),pcb.FromMM(y))
 board.Add(z)
board.BuildListOfNets();board.BuildConnectivity()
pcb.ZONE_FILLER(board).Fill(board.Zones())
from complete_route import ground_stitch
ground_stitch(board)
pcb.ZONE_FILLER(board).Fill(board.Zones())
pcb.SaveBoard(str(ROOT/'integrated.kicad_pcb'),board)
# Retain the actual routing session without workstation-specific source paths.
(BUILD/'integrated.ses').write_text(args.session.read_text().replace(str(ROOT/'integrated.dsn'),'integrated.dsn'))
netlist.unlink()
for ref in ('H1','H2','H3','H4'):
 fp=next(f for f in board.GetFootprints() if f.GetReference()==ref);fp.SetAttributes(fp.GetAttributes() | pcb.FP_BOARD_ONLY | pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES)
 if ref=='H2':fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(155),pcb.FromMM(23)))
pcb.SaveBoard(str(ROOT/'integrated.kicad_pcb'),board)
# Let the native project-aware engine refill under the checked-in custom rules.
subprocess.run([args.kicad_cli,'pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--output',str(BUILD/'routing-check.json'),str(ROOT/'integrated.kicad_pcb')],check=True)
# Remove only copper identified by native DRC as a dangling track. A fresh
# native check after each pass still detects every open pad or broken net.
for _ in range(12):
 report=json.loads((BUILD/'routing-check.json').read_text())
 ids={item['uuid'] for v in report['violations'] if v['type']=='track_dangling' for item in v['items']}
 if not ids:break
 subprocess.run([sys.executable,str(ROOT/'trim_stubs.py'),str(ROOT/'integrated.kicad_pcb'),str(BUILD/'routing-check.json')],check=True)
 subprocess.run([args.kicad_cli,'pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--output',str(BUILD/'routing-check.json'),str(ROOT/'integrated.kicad_pcb')],check=True)
if args.prepare_only:
 print('Intermediate route imported; no fabrication exports generated. Complete the remaining route and validate.');raise SystemExit(0)
subprocess.run(['python3',str(ROOT/'validate.py'),'--kicad-cli',args.kicad_cli,'--design-only'],check=True)
out=ROOT/'fabrication';out.mkdir(exist_ok=True)
def run(arguments):subprocess.run([args.kicad_cli,*arguments],cwd=ROOT,check=True)
run(['sch','export','pdf','-o',str(out/'schematic.pdf'),'integrated.kicad_sch'])
run(['sch','erc','--format','json','--output',str(out/'erc.json'),'integrated.kicad_sch'])
run(['pcb','drc','--schematic-parity','--format','json','--output',str(out/'drc.json'),'integrated.kicad_pcb'])
run(['pcb','export','gerbers','--no-protel-ext','--subtract-soldermask','--check-zones','-o',str(out/'gerbers')+'/','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','integrated.kicad_pcb'])
run(['pcb','export','drill','-o',str(out/'drill')+'/','integrated.kicad_pcb'])
run(['pcb','export','pos','--format','csv','--units','mm','-o',str(out/'positions.csv'),'integrated.kicad_pcb'])
shutil.copyfile(ROOT/'assembly-bom.csv',out/'assembly-bom.csv')
(out/'README.txt').write_text('LP-I0 ENGINEERING REVIEW EXPORTS. NOT RELEASED FOR FABRICATION.\nSee ../release-status.json and ../README.md. No hardware qualification has been performed.\n')
run(['pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers','F.Cu,F.Silkscreen,Edge.Cuts','-o',str(out/'board-top.svg'),'integrated.kicad_pcb'])
run(['pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--black-and-white','--sketch-pads-on-fab-layers','--layers','F.Fab,F.SilkS,Edge.Cuts','-o',str(out/'assembly-top.svg'),'integrated.kicad_pcb'])
with zipfile.ZipFile(out/'prototype-gerbers.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
 for folder in ('gerbers','drill'):
  for f in sorted((out/folder).rglob('*')):
   if f.is_file():archive.write(f,str(f.relative_to(out)))
 archive.write(out/'README.txt','README.txt')
import validate
from routing_metrics import measure
metrics=measure(validate.parse_sexpr((ROOT/'integrated.kicad_pcb').read_text()),validate.child,validate.children,validate.net_name)
(out/'routing-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
manifest={'revision':'LP-I0','kicad':'10.0.6','fabrication_released':False,'source_sha256':validate.hashes(validate.source_paths()),'export_sha256':validate.hashes(sorted(p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'))}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(BUILD/'routing-check.json').unlink(missing_ok=True)
subprocess.run(['python3',str(ROOT/'validate.py'),'--kicad-cli',args.kicad_cli],check=True)
print('Prototype review exports generated; fabrication remains blocked by release-status.json')
