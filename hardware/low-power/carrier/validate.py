#!/usr/bin/env python3
"""Independent connector checks + native KiCad ERC/DRC/parity/netlist verification."""
import argparse, copy, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ALIASES={'+5V_IN':'5v_pd','+5V':'5v_fused','+3V3':'3v3','GND':'gnd','zac93_tx':'zwave_tx','zac93_rx':'zwave_rx'}
def assert_remote_map(catalog,visual):
    components={c['id']:{p['id']:p for p in c['pins']} for c in visual['components']}
    nets={n['id']:{(m['component'],m['pin']) for m in n['members']} for n in visual['nets']}
    for c in catalog['connectors']:
        for p in c['pins']:
            net=ALIASES.get(p['net'],p['net'])
            for remote in p['remote_endpoints']:
                identity=(remote['component'],remote['pin'])
                assert identity in nets[net],f'{c["ref"]}.{p["number"]}: {identity} is not on verified net {net}'
                v=components[identity[0]][identity[1]]
                if remote['position'] is not None:
                    assert remote['position']==v['physical']['position'],f'{c["ref"]}.{p["number"]}: physical position mismatch for {identity}'
    # Independent, explicit regression for the previously dangerous WIZ power mistake.
    w=components['w5500']
    assert {k:w[k]['physical']['position'] for k in ['GND3','3V3A','3V3B','NC']}=={'GND3':'J2.1','3V3A':'J2.2','3V3B':'J2.3','NC':'J2.4'}
    assert not any(r['component']=='w5500' and r['position']=='J2.4' for c in catalog['connectors'] for p in c['pins'] for r in p['remote_endpoints'])

def normalize(name):
    if not name or name.startswith('unconnected-'):return None
    return name.lstrip('/')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli',default='kicad-cli');ap.add_argument('--out',type=Path,default=ROOT/'.build/validation');ap.add_argument('--contract-only',action='store_true');ap.add_argument('--check-hashes',action='store_true');a=ap.parse_args();a.out=a.out.resolve()
    if a.check_hashes:
        manifest=json.loads((ROOT/'outputs/sha256.json').read_text())
        required={'carrier.kicad_pcb','carrier.kicad_sch','carrier.kicad_pro','assembly-bom.csv','connectors.json','netlist.json','outputs/prototype-gerbers.zip'}
        assert required<=set(manifest), 'Incomplete source/fabrication hash manifest'
        for name,sha in manifest.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,'Stale artifact or source: '+name
    catalog=json.loads((ROOT/'connectors.json').read_text());visual=json.loads((ROOT.parent/'visual/connections.json').read_text());assert_remote_map(catalog,visual)
    import design
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
    run('sch','erc','carrier.kicad_sch','--format','json','-o',erc,'--exit-code-violations')
    run('pcb','drc','carrier.kicad_pcb','--format','json','--schematic-parity','-o',drc,'--exit-code-violations')
    # Do not trust exit code alone: some CLI builds print violations but exit zero.
    e=json.loads(erc.read_text());d=json.loads(drc.read_text())
    assert not [v for s in e.get('sheets',[]) for v in s.get('violations',[])],e
    assert not d.get('violations'),d.get('violations')
    assert not d.get('unconnected_items'),d.get('unconnected_items')
    assert not d.get('schematic_parity'),d.get('schematic_parity')
    run('sch','export','netlist','carrier.kicad_sch','--format','kicadxml','-o',xml)
    actual={}
    for n in ET.parse(xml).findall('./nets/net'):
        for p in n.findall('node'):
            if not p.get('ref').startswith('#'):actual[p.get('ref'),p.get('pin')]=normalize(n.get('name'))
    assert expected==actual,{'missing':set(expected.items())-set(actual.items()),'extra':set(actual.items())-set(expected.items())}
    board=pcb.LoadBoard(str(ROOT/'carrier.kicad_pcb'))
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
    tracks=list(board.GetTracks());assert tracks,'unrouted PCB'
    report=dict(status='PASS',tool=version,erc_violations=0,drc_violations=0,unconnected=0,schematic_parity=0,checked_component_pins=len(expected),keyed_connectors=len(catalog['connectors']),copper_items=len(tracks),hardware_validated=False)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
