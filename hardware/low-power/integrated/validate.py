#!/usr/bin/env python3
"""Read-only validation of LP-I0 electrical contract and native KiCad files.
Exports and checks run in a disposable copy; source files and fabrication outputs are untouched.
"""
from __future__ import annotations
import argparse,collections,hashlib,importlib.util,json,re,shutil,subprocess,tempfile,math,sys
sys.dont_write_bytecode=True
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent

def require(ok,message):
 if not ok:raise ValueError(message)

def source_parts():
 spec=importlib.util.spec_from_file_location('integrated_design',ROOT/'design.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod.parts

def electrical(parts):
 p={p['ref']:p for p in parts};require(len(p)==len(parts),'Duplicate component reference')
 pins=lambda ref:p[ref]['pins']
 atlas=json.loads((ROOT.parent/'visual/connections.json').read_text())
 s3=next(c for c in atlas['components'] if c['id']=='s3')
 pad={p['gpio']:p['physical']['position'] for p in s3['pins'] if p.get('gpio') is not None}
 for role,gpio in atlas['firmware_roles'].items():require(pins('U1')[pad[gpio]]==role,'S3 role mismatch: '+role)
 checks={'U4':{'23':'gnd'},'U2':{'3':'3v3','8':'h2_reset','22':'h2_gpio8','23':'h2_boot','25':'h2_gpio25','30':'h2_tx','31':'h2_rx'},
 'U3':{'5':'mg24_rts','6':'mg24_cts','7':'mg24_boot','8':'mg24_swclk','9':'mg24_swdio','12':'mg24_tx','13':'mg24_rx','15':'3v3','31':'mg24_reset','33':None},
 'U5':{'2':'gnd','3':'zwave_tx','4':'zwave_rx','5':'sc16_reset','8':'3v3','9':'gnd','10':'sc16_cs','11':'shared_spi_mosi','12':'shared_spi_miso','13':'shared_spi_sclk','14':'gnd','15':'sc16_irq','16':'gnd','22':'gnd'},
 'U7':{'1':'POE_12','2':'POE_36','3':'POE_45','4':'POE_78','5':None,'6':None,'7':'gnd','8':'5v_pd','9':None,'10':None},
 'U8':{'PG':None,'EN':None,'VIN':'5v_fused','GND':'gnd','VOUT':'3v3','GND2':'gnd'},
 'J1':{'1':'mag_rxp','2':'eth_txp','5':'POE_12','6':'POE_45','7':'mag_ct','8':'mag_rxn','9':'eth_txn','10':'POE_36','11':'POE_78','S1':'chassis','S2':'chassis'}}
 for ref,expected in checks.items():
  for n,net in expected.items():require(pins(ref)[n]==net,f'{ref}.{n} has wrong net')
 require(p['U8']['model']=='D24V22F3','Buck substitution requires power review')
 for ref in ['U1','U2','U3','U4','U5','U6']:require(not any(n and (n.startswith('5v') or n.startswith('POE')) for n in pins(ref).values()),'High voltage on logic module '+ref)
 for obj in parts:
  if any(n and n.startswith('POE') for n in obj['pins'].values()):require(obj['ref'] in ['J1','U7','D1','D2','C37','C38'] or obj['ref'].startswith('#FLG'),'PoE primary escapes isolated domain')
 require(pins('F1')=={'1':'5v_pd','2':'5v_fused'},'Fuse bypass')
 require(pins('J5')['1']=='5v_fused','LD2450 must use fused5V')
 for obj in parts:
  if obj['ref'].startswith('R') and 'mg24_reset' in obj['pins'].values():raise ValueError('Forbidden MG24 reset external pull-up')
  if 'usb_vbus' in obj['pins'].values():require(not any(n and n.startswith('5v') for n in obj['pins'].values()),'USB/PoE backfeed connection')
 def two(value,a,b):return any(o['model']==value and set(o['pins'].values())=={a,b} for o in parts)
 for val,a,b in [('1k','sc16_irq','3v3'),('4.7k','cc1101_gdo0_tx','3v3'),('10k','h2_gpio8','3v3'),('10k','h2_gpio25','gnd'),('6.8nF','eth_rxp','mag_rxp'),('6.8nF','eth_rxn','mag_rxn'),('22','usb_dp','usb_dp_port'),('22','usb_dm','usb_dm_port')]:require(two(val,a,b),'Missing required support network '+a)
 require(p['Y1']['model']=='ABLS-3.6864MHZ-B2-T','Wrong SC16 crystal')
 return p

def parse_sexpr(text):
 tokens=re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',text);stack=[];root=None
 for t in tokens:
  if t=='(':v=[];stack[-1].append(v) if stack else None;stack.append(v)
  elif t==')':root=stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 return root

def child(tree,name):return next((x for x in tree if isinstance(x,list) and x and x[0]==name),None)
def children(tree,name):return [x for x in tree if isinstance(x,list) and x and x[0]==name]

def disconnected(net):return net is None or net.startswith('unconnected-')

def net_name(node,nets):
 # KiCad10 stores (net "name"); older files store (net id) or (net id "name").
 if not node:return None
 return node[2] if len(node)>2 else nets.get(node[1],node[1])

def pcb_connectivity(path,parts):
 b=parse_sexpr(path.read_text());coords={};nets={n[1]:n[2] for n in children(b,'net') if len(n)>2};actual={};tracks=collections.Counter();vias=collections.Counter()
 for f in children(b,'footprint'):
  props={x[1]:x[2] for x in children(f,'property')};ref=props.get('Reference');mapping={}
  fa=child(f,'at');fx,fy=map(float,fa[1:3]);angle=math.radians(float(fa[3]) if len(fa)>3 else 0);coords[ref]=[]
  for pad in children(f,'pad'):
   if not pad[1]:continue
   pa=child(pad,'at');px,py=map(float,pa[1:3]);coords[ref].append((pad[1],round(fx+px*math.cos(angle)+py*math.sin(angle),4),round(fy-px*math.sin(angle)+py*math.cos(angle),4)))
   n=child(pad,'net');net=net_name(n,nets)
   require(pad[1] not in mapping or mapping[pad[1]]==net,'Duplicate pad with conflicting nets');mapping[pad[1]]=net
  require(ref not in actual,'Duplicate PCB reference '+str(ref))
  actual[ref]=mapping
 for ref,xy in {'H1':(5,5),'H2':(155,23),'H3':(5,137),'H4':(155,137)}.items():
  f=next(f for f in children(b,'footprint') if any(p[1:3]==['Reference',ref] for p in children(f,'property')))
  require(tuple(map(float,child(f,'at')[1:3]))==xy,'Mounting hole position differs: '+ref)
 require(any(net_name(child(z,'net'),nets)=='gnd' and child(z,'layer')==['layer','In1.Cu'] for z in children(b,'zone')),'Dedicated ground plane missing')
 require(set(actual)=={r for r,o in parts.items() if o['footprint']}|{'H1','H2','H3','H4'},'Unexpected/missing PCB component')
 for ref,obj in parts.items():
  if not obj['footprint']:continue
  require(ref in actual,'PCB component missing '+ref)
  f=next(f for f in children(b,'footprint') if any(p[1:3]==['Reference',ref] for p in children(f,'property')))
  at=child(f,'at');actual_angle=float(at[3]) if len(at)>3 else 0
  require(tuple(map(float,at[1:3]))==tuple(obj['xy']) and (actual_angle-obj['rotation'])%360==0,'PCB placement differs from source: '+ref)
  require(set(actual[ref])==set(obj['pins']),'Unexpected/missing PCB pad on '+ref)
  for pin,net in obj['pins'].items():
   # Every named pad, including explicit mechanical tabs, must be present.
   if net is not None:require(actual[ref].get(pin)==net,f'PCB connectivity differs at{ref}.{pin}')
   else:require(disconnected(actual[ref].get(pin)),f'PCB NC unexpectedly wired: {ref}.{pin}')
 for c in json.loads((ROOT/'connectors.json').read_text())['connectors']:
  expected=sorted((str(p['number']),round(p['x'],4),round(p['y'],4)) for p in c['pad_centers_mm'])
  require(expected==sorted(coords[c['ref']]),'Connector physical coordinates differ: '+c['ref'])
 real_nets={n for p in parts.values() for n in p['pins'].values() if n is not None}
 for x in children(b,'segment'):
  n=child(x,'net');name=net_name(n,nets);require(name in real_nets,'Unexpected track net');tracks[name]+=1
  require(child(x,'layer')[1]!='In1.Cu','Signal track on dedicated ground reference layer')
 for x in children(b,'via'):
  n=child(x,'net');name=net_name(n,nets);require(name in real_nets,'Unexpected via net');vias[name]+=1
 require(sum(tracks.values())>0,'Board has no routed copper')
 return {'segments':sum(tracks.values()),'vias':sum(vias.values()),'mdi_vias':{n:vias[n] for n in ['eth_txp','eth_txn','eth_rxp','eth_rxn','mag_rxp','mag_rxn']},'usb_vias':{n:vias[n] for n in ['usb_dp','usb_dm','usb_dp_port','usb_dm_port']}}

def run(cli,args,cwd):
 proc=subprocess.run([cli,*args],cwd=cwd,text=True,capture_output=True)
 require(proc.returncode==0,'KiCad failed: '+proc.stdout+proc.stderr)

def source_paths():
 names=['design.py','generate.py','footprints.py','finish.py','validate.py','routing_metrics.py','preroute.py','complete_route.py','local_repairs.py','trim_stubs.py','tocap_escape.py','integrated.kicad_sch','integrated.kicad_pcb','integrated.kicad_pro','integrated.kicad_dru','Hub.kicad_sym','fp-lib-table','sym-lib-table','netlist.json','connectors.json','assembly-bom.csv','release-status.json']
 return [ROOT/n for n in names]+sorted((ROOT/'footprints').rglob('*.kicad_mod'))

def hashes(paths):return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def validate(kicad_cli='kicad-cli',native=True,check_exports=True):
 parts=electrical(source_parts());board=ROOT/'integrated.kicad_pcb';stats=pcb_connectivity(board,parts)
 from routing_metrics import measure
 metrics=measure(parse_sexpr(board.read_text()),child,children,net_name)
 require(all('track_mm' in p for p in metrics['paths'].values()),'Critical routing path could not be measured')
 for name,path in metrics['paths'].items():
  require(path['track_mm']<60,'Critical routing detour exceeds project sanity budget: '+name)
  if name.startswith(('eth_','mag_')):require(path['layers']==['F.Cu'] and path['total_net_vias']==0,'MDI must remain on F.Cu without vias: '+name)
 for pair,bound in [('ethernet_tx',2.5),('ethernet_rx',2.5),('usb',3.0)]:require(metrics['pairs'][pair]['track_skew_mm']<=bound,'Critical pair skew exceeds project sanity budget: '+pair)
 if native:
  with tempfile.TemporaryDirectory(prefix='lp-i0-check-') as tmp:
   snapshot=Path(tmp)/'project';shutil.copytree(ROOT,snapshot,ignore=shutil.ignore_patterns('__pycache__','fabrication','*.dsn','*.ses'))
   run(kicad_cli,['sch','erc','--format','json','--output','erc.json','integrated.kicad_sch'],snapshot)
   run(kicad_cli,['pcb','drc','--schematic-parity','--format','json','--output','drc.json','integrated.kicad_pcb'],snapshot)
   e=json.loads((snapshot/'erc.json').read_text());d=json.loads((snapshot/'drc.json').read_text())
   violations=[v for s in e['sheets'] for v in s['violations']]
   require(not violations,'ERC violations: '+str(len(violations)))
   require(not d['unconnected_items'],'Unconnected PCB items: '+str(len(d['unconnected_items'])))
   require(not d.get('schematic_parity',[]),'Schematic/PCB parity errors')
   require(not d['violations'],'PCB DRC violations: '+str(collections.Counter(x['type'] for x in d['violations'])))
   run(kicad_cli,['sch','export','netlist','--format','kicadxml','--output','netlist.xml','integrated.kicad_sch'],snapshot)
   xml=ET.parse(snapshot/'netlist.xml');actual={}
   require({c.attrib['ref'] for c in xml.findall('./components/comp')}=={r for r in parts if not r.startswith('#')},'Unexpected/missing schematic component')
   for net in xml.findall('./nets/net'):
    for node in net.findall('node'):actual[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name'].removeprefix('/')
   for ref,obj in parts.items():
    if not obj['footprint']:continue
    for pin,net in obj['pins'].items():
     if net is not None:require(actual.get((ref,pin))==net,f'Schematic connectivity mismatch {ref}.{pin}')
     else:require(disconnected(actual.get((ref,pin))),f'Schematic NC unexpectedly wired: {ref}.{pin}')
 for conn in json.loads((ROOT/'connectors.json').read_text())['connectors']:
  require({str(p['number']):p['net'] for p in conn['pins']}==parts[conn['ref']]['pins'],'Connector net metadata mismatch')
 if check_exports:
  manifest=json.loads((ROOT/'fabrication'/'manifest.json').read_text())
  require(json.loads((ROOT/'fabrication/routing-metrics.json').read_text())==metrics,'Routing metrics do not match native PCB')
  require(manifest['source_sha256']==hashes(source_paths()),'Fabrication exports are stale relative to native sources')
  files=sorted(p for p in (ROOT/'fabrication').rglob('*') if p.is_file() and p.name!='manifest.json')
  require(manifest['export_sha256']==hashes(files),'Fabrication export contents do not match manifest')
 status=json.loads((ROOT/'release-status.json').read_text());require(status['fabrication_released'] is False and status['blockers'],'Prototype release gates missing')
 return {'components':len([p for p in parts if not p.startswith('#')]),**stats,'native_checks':native,'fabrication_released':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kicad-cli',default='kicad-cli');p.add_argument('--electrical-only',action='store_true');p.add_argument('--design-only',action='store_true',help='For export generation: validate native design before export freshness checks');args=p.parse_args()
 if args.electrical_only:result={'electrical_contract':'PASS','components':len(electrical(source_parts()))}
 else:result=validate(args.kicad_cli,check_exports=not args.design_only)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
