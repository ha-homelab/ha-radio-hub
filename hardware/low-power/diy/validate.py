#!/usr/bin/env python3
"""Native ERC/DRC/parity plus independent bottom-copper/physical-wire union."""
import argparse,json,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from continuity import verify
ROOT=Path(__file__).resolve().parent

def native_geometry(board,pcb):
 copper=[]
 for f in board.GetFootprints():
  for p in f.Pads():
   if not p.GetNumber():assert p.GetAttribute()==pcb.PAD_ATTRIB_NPTH;continue
   assert p.IsOnLayer(pcb.B_Cu),'component pad has no bottom copper'
   assert p.GetAttribute()==pcb.PAD_ATTRIB_PTH,'not a manually drillable component hole'
   x,y=pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y);w,h=pcb.ToMM(p.GetSize().x),pcb.ToMM(p.GetSize().y)
   o=dict(id=f.GetReference()+'.'+p.GetNumber(),net=p.GetNetname().lstrip('/'))
   assert w>=1.999 and h>=1.999,'pad below2mm DIY rule'
   drill=pcb.ToMM(p.GetDrillSize().x)
   assert .799<=drill<=1.101,'unexpected hole size'
   assert (min(w,h)-drill)/2>=.449,'insufficient annular ring'
   if f.GetReference().startswith('T'):assert abs(drill-1.1)<.001,'wire hole must be1.1mm'
   if p.GetShape()==pcb.PAD_SHAPE_RECT:
    assert round(p.GetOrientationDegrees())%90==0
    if round(p.GetOrientationDegrees())%180:w,h=h,w
    o['rect']=[x-w/2,y-h/2,x+w/2,y+h/2]
   else:assert abs(w-h)<1e-6;o.update(a=[x,y],b=[x,y],radius=w/2)
   copper.append(o)
 for i,t in enumerate(board.GetTracks()):
  assert not isinstance(t,pcb.PCB_VIA),'D0 cannot require plated vias'
  assert t.GetLayer()==pcb.B_Cu,'top copper is not an insulated wire'
  width=pcb.ToMM(t.GetWidth());assert width>=.5999
  if t.GetNetname().lstrip('/').rsplit('__',1)[0] in ['GND','+3V3','+5V','+5V_IN']:assert width>=1.1999,'narrow power trace'
  copper.append(dict(id='track'+str(i),net=t.GetNetname().lstrip('/'),a=[pcb.ToMM(t.GetStart().x),pcb.ToMM(t.GetStart().y)],b=[pcb.ToMM(t.GetEnd().x),pcb.ToMM(t.GetEnd().y)],radius=width/2))
 assert not list(board.Zones()),'unreviewed copper/rule zones'
 return copper

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli',default='kicad-cli');ap.add_argument('--out',type=Path,default=ROOT/'.build/validation');ap.add_argument('--check-hashes',action='store_true');a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
 import pcbnew as pcb
 def run(*cmd):
  r=subprocess.run([a.kicad_cli,*map(str,cmd)],cwd=ROOT,capture_output=True,text=True)
  assert r.returncode==0,r.stdout+r.stderr
  return r.stdout
 assert run('version').startswith('10.')
 run('sch','erc','diy.kicad_sch','--format','json','-o',a.out/'erc.json')
 run('pcb','drc','diy.kicad_pcb','--format','json','--schematic-parity','-o',a.out/'drc.json')
 e=json.loads((a.out/'erc.json').read_text());d=json.loads((a.out/'drc.json').read_text())
 assert not [v for s in e['sheets'] for v in s['violations']],e
 assert not d['violations'],d['violations'];assert not d['unconnected_items'],d['unconnected_items'];assert not d['schematic_parity'],d['schematic_parity']
 b=pcb.LoadBoard(str(ROOT/'diy.kicad_pcb'));copper=native_geometry(b,pcb)
 logical=json.loads((ROOT/'logical-netlist.json').read_text())
 import design
 fresh={o['ref']+'.'+p:n for o in design.parts if o['footprint'] for p,n in o['pins'].items()}
 pins={o['ref']+'.'+p:n for o in logical['parts'] if o['footprint'] for p,n in o['pins'].items()}
 assert fresh==pins,'stale logical netlist compared with current C0/pin contract'
 manifest=json.loads((ROOT/'jumpers.json').read_text());wires=manifest['wires']
 terminals={t['ref']:t for t in manifest['terminals']};assert len(terminals)==len(manifest['terminals']),'duplicate terminal ref'
 physical={c['id']:c for c in copper}
 for wire in wires:
  for side in ['from','to']:
   term=terminals[wire[side+'_terminal']];pin=term.get('physical_pin',term['ref']+'.1')
   assert wire.get(side+'_pin',wire[side+'_terminal']+'.1')==pin,'terminal manifest does not match actual joint'
   assert physical[pin]['net']==term['physical_net'],'terminal physical net mismatch'
   if term.get('kind')=='adapter_pin':
    assert term['drill_mm'] is None and term['connection_height_mm']==4 and term['ref']+'.1' not in physical,'raised joint must not invent a drilled hole'
   else:assert abs(term['drill_mm']-1.1)<.001,'unexpected wire hole drill'
 report=verify(copper,pins,wires)
 # Compare logical connector/power/radio assignments with independently reviewed C0.
 import importlib.util
 spec=importlib.util.spec_from_file_location('c0_validation',ROOT.parent/'carrier/validate.py');c0=importlib.util.module_from_spec(spec);spec.loader.exec_module(c0)
 c0.assert_remote_map(json.loads((ROOT/'connectors.json').read_text()),json.loads((ROOT.parent/'visual/connections.json').read_text()))
 run('sch','export','netlist','diy.kicad_sch','--format','kicadxml','-o',a.out/'schematic.xml')
 actual={n.get('ref')+'.'+n.get('pin'):net.get('name').lstrip('/') for net in ET.parse(a.out/'schematic.xml').findall('./nets/net') for n in net.findall('node') if not n.get('ref').startswith('#')}
 for item in copper:
  if not item['id'].startswith('track'):assert actual[item['id']]==item['net'],('native netlist',item['id'])
 if a.check_hashes:
  manifest=json.loads((ROOT/'outputs/sha256.json').read_text())
  for name,value in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,'stale source/export: '+name
 report.update(status='PASS',erc_violations=0,drc_violations=0,unconnected=0,schematic_parity=0,bottom_only=True,plated_vias=0,physical_validation=False)
 (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
