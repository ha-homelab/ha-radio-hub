#!/usr/bin/env python3
"""Independent connector checks + native KiCad ERC/DRC/parity/netlist verification."""
import argparse, copy, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def assert_contract(parts,catalog,visual,carrier):
    byref={p['ref']:p for p in parts}
    module=byref['U1'];pins=module['pins']
    assert module['model']=='MGM240PA22VNA3', 'wrong firmware target'
    assert set(pins)=={str(i) for i in range(1,37)}, 'incomplete module pads, including NC'
    # Independently sourced atlas identifies actual module pads, not connector order.
    physical={p['id']:p for c in visual['components'] if c['id']=='mg24' for p in c['pins']}
    role={'RX':'mg24_tx','TX':'mg24_rx','CTS':'mg24_rts','RTS':'mg24_cts','BOOT':'BOOT','SWCLK':'SWCLK','SWDIO':'SWDIO','RESET':'RESET','VDD':'+3V3'}
    for i in [1,14,23,32,34,35,36]:role['GND'+str(i)]='GND'
    for name,net in role.items():
        assert pins[physical[name]['physical']['position']]==net, 'wrong module '+name
    used={physical[name]['physical']['position'] for name in role}
    assert all(value is None for pin,value in pins.items() if pin not in used), 'unused RF/GPIO pad wired'
    assert pins['33'] is None, 'RFOUT33 must remain NC with built-in antenna'
    j1=next(c for c in catalog['connectors'] if c['ref']=='J1')
    j6=next(c for c in carrier['connectors'] if c['ref']=='J6')
    assert {p['number']:p['net'] for p in j1['pins']}=={p['number']:p['net'] for p in j6['pins']}, 'carrier cable must be straight number-to-number'
    reset=next(p for c in catalog['connectors'] if c['ref']=='J2' for p in c['pins'] if p['net']=='RESET')
    assert reset['voltage_v'] is None and 'sink only' in reset['notes'], 'reset is internal DVDD, not 3.3V drive'
    assert byref['R1']['pins']=={'1':'+3V3','2':'BOOT'} and byref['R1']['model']=='10k', 'boot pull-up'
    for c in ['C1','C2','C3']:assert byref[c]['pins']=={'1':'+3V3','2':'GND'}, 'VDD bypass'

def normalize(name):
    if not name or name.startswith('unconnected-'):return None
    return name.lstrip('/')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli',default='kicad-cli');ap.add_argument('--out',type=Path,default=ROOT/'.build/validation');ap.add_argument('--contract-only',action='store_true');ap.add_argument('--check-hashes',action='store_true');a=ap.parse_args();a.out=a.out.resolve()
    if a.check_hashes:
        manifest=json.loads((ROOT/'outputs/sha256.json').read_text())
        required={'mg24-adapter.kicad_pcb','mg24-adapter.kicad_sch','mg24-adapter.kicad_pro','assembly-bom.csv','connectors.json','netlist.json','outputs/prototype-gerbers.zip'}
        assert required<=set(manifest), 'Incomplete source/fabrication hash manifest'
        for name,sha in manifest.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,'Stale artifact or source: '+name
    catalog=json.loads((ROOT/'connectors.json').read_text());visual=json.loads((ROOT.parent.parent/'visual/connections.json').read_text())
    carrier=json.loads((ROOT.parent/'connectors.json').read_text())
    import design
    assert_contract(design.parts,catalog,visual,carrier)
    expected={(c['ref'],p):n for c in design.parts if c['footprint'] for p,n in c['pins'].items()}
    saved=json.loads((ROOT/'netlist.json').read_text())
    assert expected=={(c['ref'],p):n for c in saved['parts'] if c['footprint'] for p,n in c['pins'].items()},'stale generated netlist'
    for c in catalog['connectors']:
        for p in c['pins']:assert expected[c['ref'],str(p['number'])]==p['net']
    if a.contract_only:print('PASS independent external endpoint/power/logic contract');return
    import pcbnew as pcb
    a.out.mkdir(parents=True,exist_ok=True)
    def run(*args):
        r=subprocess.run([a.kicad_cli,*map(str,args)],cwd=ROOT,text=True,capture_output=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        return r.stdout.strip()
    version=run('version');assert version.startswith('10.'),version
    erc=a.out/'erc.json';drc=a.out/'drc.json';xml=a.out/'schematic.xml'
    run('sch','erc','mg24-adapter.kicad_sch','--format','json','-o',erc,'--exit-code-violations')
    run('pcb','drc','mg24-adapter.kicad_pcb','--format','json','--schematic-parity','-o',drc,'--exit-code-violations')
    # Do not trust exit code alone: some CLI builds print violations but exit zero.
    e=json.loads(erc.read_text());d=json.loads(drc.read_text())
    assert not [v for s in e.get('sheets',[]) for v in s.get('violations',[])],e
    assert not d.get('violations'),d.get('violations')
    assert not d.get('unconnected_items'),d.get('unconnected_items')
    assert not d.get('schematic_parity'),d.get('schematic_parity')
    run('sch','export','netlist','mg24-adapter.kicad_sch','--format','kicadxml','-o',xml)
    actual={}
    for n in ET.parse(xml).findall('./nets/net'):
        for p in n.findall('node'):
            if not p.get('ref').startswith('#'):actual[p.get('ref'),p.get('pin')]=normalize(n.get('name'))
    assert expected==actual,{'missing':set(expected.items())-set(actual.items()),'extra':set(actual.items())-set(expected.items())}
    board=pcb.LoadBoard(str(ROOT/'mg24-adapter.kicad_pcb'))
    pads={(f.GetReference(),p.GetNumber()):normalize(p.GetNetname()) for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNumber():
                assert expected[f.GetReference(),p.GetNumber()]==normalize(p.GetNetname()),'individual physical pad mismatch'
                if expected[f.GetReference(),p.GetNumber()] is None:assert p.GetNetname().startswith('unconnected-'),'missing explicit NC pad'
            else:assert f.GetReference().startswith('H') and p.GetAttribute()==pcb.PAD_ATTRIB_NPTH,'unexpected unnamed physical pad'
    assert expected==pads,{'missing':set(expected.items())-set(pads.items()),'extra':set(pads.items())-set(expected.items())}
    for c in catalog['connectors']:
        f=next(f for f in board.GetFootprints() if f.GetReference()==c['ref'])
        real={p.GetNumber():(round(pcb.ToMM(p.GetPosition().x),4),round(pcb.ToMM(p.GetPosition().y),4)) for p in f.Pads() if p.GetNumber().isdigit()}
        assert real=={str(p['number']):(p['x'],p['y']) for p in c['pad_centers_mm']}
    for obj in design.parts:
        if not obj['footprint']:continue
        fp=next(f for f in board.GetFootprints() if f.GetReference()==obj['ref'])
        assert tuple(round(pcb.ToMM(v),4) for v in (fp.GetPosition().x,fp.GetPosition().y))==tuple(obj['xy']),obj['ref']+' position'
        assert round(fp.GetOrientationDegrees()%360,4)==obj['rotation']%360,obj['ref']+' rotation'
        assert fp.GetValue()==obj['model'],obj['ref']+' model'
        assert fp.GetFPID().GetLibItemName()==obj['footprint'].split(':')[1],obj['ref']+' footprint'
    assert board.GetCopperLayerCount()==2, 'adapter stack-up'
    # Datasheet Fig8.3, module-local coordinates in mm; catches a wrong land pattern.
    u=next(f for f in board.GetFootprints() if f.GetReference()=='U1')
    for pad in u.Pads():
        n=int(pad.GetNumber())
        if n<=14:xy=(0.8,0.7+(n-1))
        elif n<=22:xy=(2.95+(n-15),14.2)
        else:xy=(12.1,13.7-(n-23))
        actual=(pcb.ToMM(pad.GetPosition().x)-23.55,pcb.ToMM(pad.GetPosition().y))
        assert all(abs(a-b)<0.0001 for a,b in zip(actual,xy)), ('module land',n,actual,xy)
    keepouts=[z for z in board.Zones() if z.GetIsRuleArea()]
    assert len(keepouts)==1, 'antenna keepout missing'
    z=keepouts[0];poly=z.Outline()
    actual={(round(pcb.ToMM(poly.CVertex(i).x),4),round(pcb.ToMM(poly.CVertex(i).y),4)) for i in range(poly.VertexCount())}
    assert actual=={(25.6,0),(34.4,0),(34.4,4.8),(25.6,4.8)}, 'antenna box geometry'
    assert z.IsOnLayer(pcb.F_Cu) and z.IsOnLayer(pcb.B_Cu), 'antenna keepout must cover both copper layers'
    assert z.GetDoNotAllowTracks() and z.GetDoNotAllowVias() and z.GetDoNotAllowZoneFills(), 'antenna copper exclusion'
    # All other components are outside the antenna box; the module itself owns it.
    for f in board.GetFootprints():
        if f.GetReference()=='U1':continue
        box=f.GetBoundingBox(False,False)
        assert pcb.ToMM(box.GetRight())<=25.6 or pcb.ToMM(box.GetLeft())>=34.4 or pcb.ToMM(box.GetTop())>=4.8 or pcb.ToMM(box.GetBottom())<=0, 'component over antenna'
    ground_vias=[t for t in board.GetTracks() if isinstance(t,pcb.PCB_VIA) and normalize(t.GetNetname())=='GND']
    for pad in u.Pads():
        if normalize(pad.GetNetname())!='GND':continue
        assert pad.GetLocalZoneConnection()==pcb.ZONE_CONNECTION_FULL, 'module ground thermal relief is not allowed'
        assert min(((pcb.ToMM(v.GetPosition().x-pad.GetPosition().x))**2+(pcb.ToMM(v.GetPosition().y-pad.GetPosition().y))**2)**0.5 for v in ground_vias)<=2.0, 'module ground stitching too far'
    tracks=list(board.GetTracks());assert tracks,'unrouted PCB'
    report=dict(status='PASS',tool=version,erc_violations=0,drc_violations=0,unconnected=0,schematic_parity=0,checked_component_pins=len(expected),keyed_connectors=len(catalog['connectors']),copper_items=len(tracks),hardware_validated=False)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
