#!/usr/bin/env python3
"""Rebuild MC1's English guide from the current CAD and review data."""
from pathlib import Path
import argparse, csv, hashlib, html, io, json, math, runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def h(x): return html.escape(str(x), quote=True)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def text(x,y,t,size=18,fill='#203748',weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}">{h(t)}</text>'
def box(x,y,w,hh,title,lines,fill='#eff5f8'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="8" fill="{fill}" stroke="#7894a4"/>'+text(x+18,y+32,title,21,weight=700)+''.join(text(x+18,y+65+i*25,t,17) for i,t in enumerate(lines))
def architecture():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="875" viewBox="0 0 1320 875" role="img" aria-label="MC1 one carrier architecture"><rect width="1320" height="875" fill="#fff"/><g font-family="Arial,sans-serif">'
    s+=text(36,47,'MC1 · one current module carrier',32,weight=700)+text(36,82,'One Ethernet uplink · local Thread BR · Ember Zigbee · direct-solder module pins',19)
    s+=box(36,122,1248,103,'Finished isolated power',['PoE splitter → fused 5 V → individual controller inputs; finished 3.3 V buck → peripheral rail'],'#f5f1e9')
    for points in ['318,360 425,360','805,344 948,344','805,458 865,458 865,536 948,536','318,552 369,552 369,460 425,460','600,550 600,666','425,515 405,515 405,735 385,735']:
        s+=f'<polyline points="{points}" fill="none" stroke="#2c698d" stroke-width="3"/>'
    s+=box(36,287,282,148,'WIZ850io',['Finished Ethernet module','Shared SPI · own CS','No raw PoE on its headers'])
    s+=box(425,278,380,272,'S3 · local host',['Waveshare ESP32-S3-Nano-M','16 MB flash + 8 MB PSRAM','Local Thread BR + 3 active BLE','Shared SPI, three native UARTs','Initial USB flash → later OTA'],'#e4eff7')
    s+=box(948,277,336,140,'H2 · Thread RCP',['ESP32-H2-DevKitM-1','Dedicated UART; EN + BOOT','Independent 802.15.4 radio'])
    s+=box(948,468,336,140,'XIAO MG24 · Zigbee',['Ember NCP, not ZBOSS','TX/RX + hardware RTS/CTS','Initial preflash → UART GBL'])
    s+=box(36,474,282,155,'CC1101 · existing RF',['433 MHz TX + RX','SPI + two GDO signals','Hardware-timed S3 I/O'])
    s+=box(425,666,400,130,'Finished WK2132 UART bridge',['DFR0627, I2C + checked forwarding','Existing ZAC93 Z-Wave UART'])
    s+=box(36,670,349,126,'LD2450 + BME680',['Radar: native UART, 5 V supply','Environment: I2C, external pod'])
    s+=box(948,666,336,130,'One custom board',['Modules + labeled harnesses','No female module sockets','No separate integrated variant'],'#edf3ed')
    s+=text(36,847,'Logical topology, not wire routing or measured performance. Use the native CAD for actual connector positions.',16)
    return s+'</g></svg>'

def assembly():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="450" viewBox="0 0 1320 450" role="img" aria-label="Direct solder through-hole assembly"><rect width="1320" height="450" fill="white"/><g font-family="Arial,sans-serif">'
    s+=text(36,48,'Factory male pins → plated carrier holes → underside solder',29,weight=700)
    s+=text(36,86,'Assembly principle; section not to scale. Actual heights and underside clearance require a dry fit.',18)
    s+='<rect x="115" y="146" width="500" height="22" fill="#2e6670"/>'
    for x in [165,515]:
        s+=f'<rect x="{x-5}" y="172" width="34" height="35" fill="#374750"/><rect x="{x+8}" y="155" width="7" height="159" fill="#b78e42"/>'
    s+='<rect x="100" y="274" width="540" height="18" fill="#41866c"/>'
    for x in [176,526]:
        s+=f'<ellipse cx="{x}" cy="294" rx="17" ry="7" fill="#aebbc2"/>'
    s+=text(700,166,'Ready module on its factory male pins',20)
    s+=text(700,205,'Existing male header and its plastic spacer',20)
    s+=text(700,284,'Carrier PCB with plated through-holes',20)
    s+=text(700,321,'Solder joints on the underside',20)
    s+=text(36,385,'No female socket. No castellated-side soldering. Module replacement requires desoldering.',20,weight=700)
    s+=text(36,421,'Program and verify all modules before soldering. No USB cable insertion space is reserved after assembly.',17)
    return s+'</g></svg>'

def layout_comparison(current):
    """Same-scale module bodies from the CAD ledgers; no invented copper."""
    previous=json.loads((HERE/'layout-usb-service.json').read_text())
    old=previous['board']; new=current['board']
    old_area=old['width_mm']*old['height_mm']; new_area=new['width_mm']*new['height_mm']
    reduction=100*(1-new_area/old_area)
    body={'U1':(-1.27,-1.4,24.13,61.34),'U2':(-1.27,-1.575,24.13,46.685),
          'U3':(-1.27,-2.921,16.51,18.034),'U4':(-1.34,-6.4,21.66,18.6)}
    names={'U1':'S3','U2':'H2','U3':'MG24','U4':'Ethernet'}
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="710" viewBox="0 0 1120 710" role="img" aria-label="Previous USB-service carrier and current compact carrier at equal scale"><rect width="1120" height="710" fill="#fff"/><g font-family="Arial,sans-serif">'
    s+=text(32,43,'Same modules. Less unused board.',29,weight=700)
    s+=text(32,78,f'{old_area/100:g} → {new_area/100:g} cm² of PCB · {reduction:.1f}% less area than the last carrier',19)
    scale=4.5
    for design,ox,label,color in [(previous,55,'Previous · USB cable clearance','#ecf0f3'),(current,625,'Current · network updates','#e2f0ec')]:
        oy=163; b=design['board']; w=b['width_mm']; height=b['height_mm']
        s+=text(ox,122,label,21,weight=700)
        s+=f'<rect x="{ox}" y="{oy}" width="{w*scale}" height="{height*scale}" fill="{color}" stroke="#688493" stroke-width="2"/>'
        if design is previous:
            for x1,y1,x2,y2 in design['mechanics']['usb_service_envelopes_mm'].values():
                s+=f'<rect x="{ox+x1*scale}" y="{oy+y1*scale}" width="{(x2-x1)*scale}" height="{(y2-y1)*scale}" fill="#dbeaf7" stroke="#4780ae" stroke-dasharray="5 4"/>'
        for p in design['parts']:
            ref=p['ref']; pads=p['pad_centers_mm']
            if ref in body:
                bounds=p.get('body_bounds_local_mm',body[ref])
                if design is current and ref=='U1':
                    assert 'body_bounds_local_mm' in p, 'Nano body bounds must come from current CAD'
                x1,y1,x2,y2=bounds; th=math.radians(p['rotation'])
                points=[(p['xy'][0]+x*math.cos(th)+y*math.sin(th),p['xy'][1]-x*math.sin(th)+y*math.cos(th)) for x,y in [(x1,y1),(x1,y2),(x2,y1),(x2,y2)]]
                xs,ys=zip(*points); x1,x2=min(xs),max(xs); y1,y2=min(ys),max(ys)
                fill='#b6cbd7'; stroke='#597688'
            else:
                margin=1.27; x1=min(q['x'] for q in pads)-margin; x2=max(q['x'] for q in pads)+margin
                y1=min(q['y'] for q in pads)-margin; y2=max(q['y'] for q in pads)+margin
                fill='#32776b' if ref.startswith('J') else '#bc9b69'; stroke=fill
            s+=f'<rect x="{ox+x1*scale:.2f}" y="{oy+y1*scale:.2f}" width="{(x2-x1)*scale:.2f}" height="{(y2-y1)*scale:.2f}" rx="1" fill="{fill}" stroke="{stroke}"/>'
            if ref in names:
                s+=f'<text x="{ox+(x1+x2)*scale/2:.2f}" y="{oy+(y1+y2)*scale/2:.2f}" text-anchor="middle" font-size="13" fill="#193748">{names[ref]}</text>'
        r=design['mechanics']['rj45']; a,z=r['face_global_mm']; nx,ny=r['outward_normal_global']
        cx,cy=(a[0]+z[0])/2,(a[1]+z[1])/2
        s+=f'<line x1="{ox+a[0]*scale}" y1="{oy+a[1]*scale}" x2="{ox+z[0]*scale}" y2="{oy+z[1]*scale}" stroke="#287a63" stroke-width="4"/>'
        sx,sy=ox+(cx+nx*2)*scale,oy+(cy+ny*2)*scale
        ex,ey=ox+(cx+nx*10)*scale,oy+(cy+ny*10)*scale
        s+=f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#287a63" stroke-width="3"/>'
        s+=f'<polygon points="{ex},{ey} {ex-nx*10-ny*6},{ey-ny*10+nx*6} {ex-nx*10+ny*6},{ey-ny*10-nx*6}" fill="#287a63"/>'
        s+=text(ox,oy-12,f'{w:g} mm horizontal × {height:g} mm vertical',18,weight=700)
    s+=text(32,650,'Same scale. Dashed blue: removed USB cable clearance. Green: headers and RJ45 exit.',17)
    s+=text(32,684,'Carrier outline only; cable bends, external modules and enclosure walls add space.',16)
    return s+'</g></svg>'


def recovery_diagram():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="480" viewBox="0 0 1240 480" role="img" aria-label="Bounded Thread recovery"><rect width="1240" height="480" fill="#fff"/><g font-family="Arial,sans-serif">'
    s+=text(32,46,'A failed Thread radio must not cause a reboot loop',28,weight=700)
    s+=box(32,100,350,155,'Boot + RCP preflight',['Ethernet ready; probe H2','No response → quarantine','Keep the other services running'])
    s+=box(444,100,350,155,'Thread operational',['Local border router + REST','Normal transient recovery stays','Terminal fault → record failure'])
    s+=box(856,100,350,155,'Persistent quarantine',['At most one controlled restart','Next boot leaves Thread stopped','User retry explicitly re-arms it'])
    for x in (382,794):
        s+=f'<path d="M{x} 175 h58 m-9 -7 l9 7 -9 7" fill="none" stroke="#2c698d" stroke-width="3"/>'
    s+=box(32,300,1174,105,'Other services still share the S3',['A terminal Thread fault briefly interrupts every service during the restart. This is bounded recovery, not hardware isolation.'],'#f6eedf')
    s+=text(32,452,'Commissioning, power-loss recovery and simultaneous-load acceptance still require the assembled hardware.',17)
    return s+'</g></svg>'

def update_diagram():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="565" viewBox="0 0 1280 565" role="img" aria-label="Initial programming and network updates for the three controllers"><rect width="1280" height="565" fill="#fff"/><g font-family="Arial,sans-serif">'
    s+=text(32,48,'Program loose modules first. Update through Ethernet afterwards.',28,weight=700)
    s+=box(32,85,1216,100,'Before permanent soldering',['Prepare the specified H2 revision (R7 isolation), install all three matching images, then verify the update paths.'],'#f5f1e9')
    s+=box(32,220,382,205,'S3 host',['Ethernet → ESPHome OTA','Normal application updates','No USB cable space reserved','Failed bootloader or lost network:','physical recovery may be needed.'],'#e4eff7')
    s+=box(449,220,382,205,'H2 Thread radio',['Ethernet → S3 → H2 ROM UART','S3 controls BOOT and RESET','H2 RX23 / TX24; R7 removed','Explicitly armed update session','Thread remains paused during update.'],'#eaf4ed')
    s+=box(866,220,382,205,'MG24 Zigbee radio',['Ethernet → S3 UART bridge','Ember software bootloader entry','GBL application update','Stop ZHA / Zigbee2MQTT first','Bootloader must remain intact.'],'#edf0f8')
    s+=text(32,481,'J8 / J9 remain unpopulated local recovery pads. They add no fitted header or USB cable corridor.',18,weight=700)
    s+=text(32,526,'Network update support does not guarantee recovery from every hardware, bootloader or power-loss failure.',17)
    return s+'</g></svg>'

def produce():
    p=json.loads((HERE/'presentation.json').read_text())
    current=json.loads((HERE/'cad/design.json').read_text())
    design=runpy.run_path(str(HERE/'cad/design.py'))
    parts=design['parts']
    counts={k:sum(1 for x in parts if x['ref'].startswith(k) and x.get('fitted',True)) for k in ['C','R','D','U','J']}
    old_counts=[]
    for relative in ['carrier','carrier/mg24-adapter','integrated']:
        rows_old=list(csv.DictReader((ROOT/'hardware/low-power'/relative/'assembly-bom.csv').open()))
        old_counts.append(sum(int(x['Quantity']) for x in rows_old if x['Reference'].startswith(('C','R'))))
    compare=[('C0 + M0 · historical',sum(old_counts[:2])),('I0 · historical',old_counts[2]),('MC1 · current',counts['C']+counts['R'])]
    chart='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-label="Builder-installed capacitor and resistor counts"><rect width="1200" height="420" fill="white"/><g font-family="Arial,sans-serif">'
    chart+=text(32,45,'Builder-installed capacitors + resistors',28,weight=700)
    chart+=text(32,79,'Component placements from the respective BOMs; alternative builds are not added together.',17)
    for i,(label,count) in enumerate(compare):
        y=112+i*70
        chart+=text(32,y+25,label,18)+f'<rect x="285" y="{y}" width="{count*8}" height="37" rx="3" fill="'+('#287a63' if i==2 else '#8298a7')+'"/>'+text(300+count*8,y+26,str(count),21,weight=700)
    module_joints=sum(len(x['pins']) for x in parts if x['ref'].startswith('U'))
    chart+=text(32,351,f"MC1 also has {counts['D']} through-hole diodes, {counts['J']} fitted connectors and {counts['U']} complete board modules.",18)
    chart+=text(32,383,f"{module_joints} module header pins still need through-hole solder joints. Factory-fitted module parts are excluded above.",17)
    chart+='</g></svg>'
    nets={}
    for part in parts:
        for pin,net in part['pins'].items():
            if net: nets.setdefault(net,[]).append(f"{part['ref']}.{pin}")
    rows=''.join(f'<tr data-net="{h(net.lower())}"><th>{h(net)}</th><td>{h(" · ".join(ends))}</td></tr>' for net,ends in sorted(nets.items()))
    partrows=''.join(f'<tr><th>{h(x["ref"])}</th><td>{h(x["model"])}{" — unpopulated pads" if not x.get("fitted",True) else ""}</td><td>{h(x["notes"])}</td></tr>' for x in parts)
    functions=''.join(f'<tr><th>{h(x["name"])}</th><td>{h(x["implementation"])}</td><td>{h(x["retained"])}</td><td>{h(x["test"])}</td></tr>' for x in p['functions'])
    steps=''.join(f'<li>{h(x)}</li>' for x in p['assembly_steps'])
    gates=''.join(f'<li>{h(x)}</li>' for x in p['unproven'])
    sources=''.join(f'<a href="{h(u)}">{h(n)}</a>' for n,u in p['sources'])
    evidence_path=HERE/'verification-summary.json'
    evidence=json.loads(evidence_path.read_text()) if evidence_path.exists() else {'checks':[],'status':'Validation in progress'}
    checks=''.join(f'<tr><th>{h(x["check"])}</th><td>{h(x["result"])}</td><td>{h(x["scope"])}</td></tr>' for x in evidence['checks'])
    checks=checks or '<tr><td colspan="3">Validation results have not been recorded. No pass is implied.</td></tr>'
    native=''.join(f'<figure><a href="images/{n}"><img src="images/{n}" alt="{h(cap)}"></a><figcaption>{h(cap)} · <a href="images/{n}">Open full size</a></figcaption></figure>' for n,cap in [('mc1-board-top.png','Native KiCad render · actual MC1 PCB, top'),('mc1-board-bottom.png','Native KiCad render · actual MC1 PCB, underside')] if (HERE/'images'/n).exists())
    concept=''
    photo_link=''
    concept_path=HERE/'images/mc1-assembled-concept.png'
    provenance_path=HERE/'images/generated-image-provenance.json'
    provenance=json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    concept_is_current=(concept_path.exists() and (HERE/'cad/assembly-top.png').exists()
        and provenance.get('sha256')==sha(concept_path)
        and provenance.get('reference_images',{}).get('../cad/assembly-top.png')==sha(HERE/'cad/assembly-top.png'))
    if concept_is_current:
        photo_link='<a href="#photos">Photo concept</a>'
        concept='<h3 id="photos">Assembly illustration</h3><figure><img src="images/mc1-assembled-concept.png" alt="Generated assembly illustration, not a manufactured board photograph"><figcaption>Generated assembly illustration. Module bodies, connector positions and small labels are approximate. Use native CAD for construction; this is not a manufactured board photograph.</figcaption></figure>'
    boardview='<figure><a href="cad/assembly-top.svg"><img src="cad/assembly-top.svg" alt="MC1 assembly drawing from CAD"></a><figcaption>Current CAD assembly drawing. Connector references belong to MC1 only. <a href="cad/assembly-top.svg">Open full size</a></figcaption></figure>' if (HERE/'cad/assembly-top.svg').exists() else ''
    b=current['board']
    dimensions=f"{b['width_mm']:g} × {b['height_mm']:g} mm"
    baseline=json.loads((HERE/'layout-baseline.json').read_text())['board']
    area_reduction=100*(1-b['width_mm']*b['height_mm']/(baseline['width_mm']*baseline['height_mm']))
    prior=json.loads((HERE/'layout-usb-service.json').read_text())['board']
    previous_reduction=100*(1-b['width_mm']*b['height_mm']/(prior['width_mm']*prior['height_mm']))
    rj45=current['mechanics']['rj45']
    direction=rj45['opening_direction'].split(' / ')[0]
    mouth=max(rj45.get('mouth_beyond_'+side+'_edge_mm',0) for side in ('left','right','top','bottom'))
    edge_access=f'RJ45 faces outward at the {direction} edge; its mouth projects {mouth:g} mm beyond the carrier.'
    compact=f'<p>The carrier is <strong>{dimensions}</strong>, with <strong>{previous_reduction:.1f}% less PCB area</strong> than the preceding 80 × 90 mm carrier and {area_reduction:.1f}% less than the original 160 × 100 mm outline. The three empty USB cable corridors are removed. The same four finished modules are packed around internal harness headers; physical connector bodies, antenna exclusions and the outward Ethernet jack remain accounted for. Program and verify each controller before soldering. Later updates use the network paths described below.</p><figure><a href="layout-comparison.svg"><img src="layout-comparison.svg" alt="Previous and compact MC1 placement at the same scale"></a><figcaption>Historical versus current placement at the same scale. <a href="layout-comparison.svg">Open comparison</a>. PCB area excludes external finished modules, cables and enclosure.</figcaption></figure>'
    compact+='<p>Both dimensions stay within the 100 × 100 mm size ceiling used by advertised low-cost prototype offers. All components remain on top; the underside carries copper and solder joints. A smaller outline does not imply a proportional reduction in the delivered fabrication price. <a href="../../docs/module-carrier.md#compact-placement-and-fabrication-cost">Cost rationale and source offers</a>; shipping and final fabrication specifications need their own quote.</p>'
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC1 — one module carrier</title><style>
:root{--ink:#193748;--muted:#5b7180;--accent:#27698e;--line:#c7d6df;--paper:#fff;--soft:#eef4f7}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#edf2f5;color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1260px;margin:auto;background:var(--paper);padding:36px}nav{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}a{color:var(--accent)}h1{font-size:42px;line-height:1.14;max-width:900px;margin:26px 0 18px}h2{font-size:27px;line-height:1.2;margin:40px 0 18px}h3{font-size:19px}p{max-width:1000px}.lead{font-size:20px}.eyebrow{letter-spacing:.12em;font-size:13px;font-weight:650;color:var(--muted)}.notice{padding:18px 24px;border-left:4px solid var(--accent);background:var(--soft)}.muted,figcaption{color:var(--muted)}.facts{display:flex;gap:36px;flex-wrap:wrap;padding:22px 0;border-bottom:1px solid var(--line)}.facts b{display:block;font-size:25px}.facts span{font-size:14px}.two{display:grid;grid-template-columns:1fr 1fr;gap:28px}figure{margin:24px 0}img{display:block;max-width:100%;height:auto}figcaption{font-size:14px;margin-top:10px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}th{font-weight:650}thead{background:var(--soft)}input,button{font:inherit;padding:10px 14px;border:1px solid var(--line);border-radius:4px;background:white;color:var(--ink)}input{max-width:100%;width:480px}li{margin-bottom:10px}.sources{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}code{font-size:.9em;background:#eef2f4;padding:2px 5px}details{margin-top:22px}summary{cursor:pointer;font-weight:650}@media(max-width:700px){main{padding:20px}h1{font-size:31px}.two{display:block}.facts{gap:22px}td,th{padding:8px}nav{gap:14px}}@media print{body{background:white}main{padding:0}nav,input,button{display:none}figure{break-inside:avoid}h2{break-after:avoid}}
</style></head><body><main>
<nav><a href="#board">Board</a><a href="#pcb">PCB</a>__PHOTO_LINK__<a href="#wiring">Wiring</a><a href="#assembly">Assembly</a><a href="#evidence">Evidence</a><a href="../../docs/module-carrier.md">English guide</a><a href="../../docs/design-history.md">Design history</a></nav>
<p class="eyebrow">HA RADIO HUB / MC1 / 17 OCTOBER 2026</p><h1>One carrier.<br>Finished modules.<br>Familiar protocols.</h1>
<p class="lead">S3-Nano-M + H2 + Ember MG24. One Ethernet uplink, local Thread, three active BLE slots and the existing Home Assistant interfaces. Solder factory module pins directly into the carrier.</p>
<div class="notice"><strong>One current design, no competing integrated version.</strong> Engineering prototype: no physical assembly, measured power, RF qualification or production approval is implied.</div>
<div class="facts"><div><b>__DIMENSIONS__</b><span>two-layer custom PCB</span></div><div><b>0</b><span>female module sockets</span></div><div><b>3</b><span>dedicated radio/host controllers</span></div><div><b>7</b><span>retained function groups</span></div></div>
<h2 id="board">The selected architecture</h2><figure><img src="architecture.svg" alt="MC1 module architecture"><figcaption>Logical topology. The CAD defines physical placement; this diagram does not claim routing lengths.</figcaption></figure>
<p>The former C0/M0, I0 and D0 paths are historical references. The all-H2 experiment was not selected because its local border-router implementation and Zigbee integration/backup behavior did not meet the compatibility priority.</p>
<h2 id="pcb">The compact PCB</h2>__COMPACT__<p><strong>__EDGE_ACCESS__</strong> Keep the marked plug and latch corridor clear. Use the new Nano pin map and matching firmware.</p>__BOARDVIEW__<div class="two">__NATIVE__</div><p><a href="cad/board-top.svg">Top copper and silk</a> · <a href="cad/board-bottom.svg">Bottom copper and silk</a> · <a href="cad/mc1.kicad_pcb">Native two-layer PCB</a></p>__CONCEPT__
<h2>What changed after the SMLIGHT review</h2><p>The host and two independent radios remain. W5500 and CC1101 share one SPI bus with separate chip selects, freeing three host pins. No extra processor, GPIO expander or internal Ethernet hop is introduced. The smaller Nano retains 16 MB flash and 8 MB PSRAM. <a href="studies/slzb-thread/index.html">Source review</a> · <a href="studies/compact-s3/index.html">Host selection history</a>.</p><figure><img src="thread-recovery.svg" alt="Bounded Thread recovery with persistent quarantine"><figcaption>Recovery policy; source and model tests do not establish hardware fault-injection results. <a href="../../firmware/module-carrier/thread-recovery.md">Firmware controls and acceptance</a>.</figcaption></figure><h2>Function and compatibility contract</h2><p>These are the functions retained in the design. The last column names the hardware acceptance still required; a retained protocol is not a completed bench test.</p><div class="scroll"><table><thead><tr><th>Function</th><th>Implementation</th><th>Retained interface</th><th>Bench acceptance</th></tr></thead><tbody>__FUNCTIONS__</tbody></table></div>
<h2 id="updates">Programming without USB service gaps</h2><p>Initial programming is performed before the modules are soldered. Subsequent S3 updates use ESPHome OTA; H2 updates pass through the S3 to its ROM UART; MG24 application updates use its existing Ember bootloader and serial bridge. See the <a href="../../firmware/module-carrier/README.md">firmware instructions and tested limits</a>.</p><div class="notice"><strong>Required H2 preparation:</strong> on the specified DevKitM-1 v1.3, remove R7 (470 Ω) before assembly to isolate the USB-UART transmitter. The carrier now uses H2 RX23 / TX24. Verify the actual board revision and load the matching RCP image; the former RX4 / TX5 image is incompatible.</div><figure><a href="network-updates.svg"><img src="network-updates.svg" alt="Preassembly programming and later network update paths"></a><figcaption>Three update paths; no permanent USB cable corridor. <a href="network-updates.svg">Open full size</a>.</figcaption></figure>
<h2 id="wiring">Actual net endpoints</h2><p>Generated from the current MC1 CAD design source. <strong>References identify carrier pads, not arbitrary clone pin numbers.</strong> Module connector labels and physical orientation must match the CAD.</p><label for="net-search">Find a net or endpoint</label><br><input id="net-search" type="search" placeholder="Example: THREAD, U2, ZB_CTS"><p id="net-count" class="muted"></p><div class="scroll"><table><thead><tr><th>Net</th><th>Carrier endpoints</th></tr></thead><tbody id="nets">__NETS__</tbody></table></div>
<h2 id="assembly">Direct solder mounting</h2><figure><img src="direct-solder.svg" alt="Factory male pins through plated holes with underside solder"><figcaption>Only the factory male header spacer remains between module and carrier. No additional female socket.</figcaption></figure><ol>__STEPS__</ol>
<div class="notice"><strong>Power and assembly:</strong> separate the controller supply paths from the peripheral 3.3 V rail. Do not parallel regulator outputs. Carrier diode drops require loaded-rail checks. Nano receives the diode-isolated 5 V branch at VIN; VBUS and local 3V3 remain isolated. This is below its documented external VIN range and needs a loaded-rail test. Complete individual USB programming and checks before soldering; the assembled layout reserves no USB insertion space.</div>
<h3>What is removed from manual assembly</h3><figure><img src="assembly-counts.svg" alt="BOM comparison of capacitors and resistors placed by the builder"><figcaption>Counts refer only to separately placed resistors and capacitors, not every component or solder joint in the completed hub.</figcaption></figure><details><summary>Carrier parts and module references</summary><div class="scroll"><table><thead><tr><th>Reference</th><th>Part</th><th>Assembly notes</th></tr></thead><tbody>__PARTS__</tbody></table></div></details>
<h2 id="evidence">What has actually been checked</h2><div class="scroll"><table><thead><tr><th>Check</th><th>Result</th><th>Scope / limitation</th></tr></thead><tbody>__CHECKS__</tbody></table></div>
<p><a href="verification-summary.json">Machine-readable verification summary</a> · <a href="../../firmware/module-carrier/README.md">Firmware evidence and build instructions</a> · <a href="cad/">Native CAD and reports</a> · <a href="images/README.md">Image provenance</a></p>
<h3>Still requires the real assembly</h3><ul>__GATES__</ul><p>One current layout reduces the choice and assembly burden. Board-specific firmware configuration and UART-transport hardening remain real work; no claim of zero software changes or guaranteed lower power is made.</p>
<h2>Manufacturer and implementation sources</h2><div class="sources">__SOURCES__</div><p class="muted">The current MC1 documentation is in English. Old hardware images retain their original identity and provenance in the historical archive.</p>
<script>const input=document.getElementById('net-search');const rows=Array.from(document.querySelectorAll('#nets tr'));function filter(){const q=input.value.trim().toLowerCase();let n=0;for(const row of rows){const visible=row.textContent.toLowerCase().includes(q);row.hidden=!visible;if(visible)n++;}document.getElementById('net-count').textContent=n+' of '+rows.length+' nets shown';}input.addEventListener('input',filter);filter();</script>
</main></body></html>'''
    for name,value in dict(DIMENSIONS=dimensions,EDGE_ACCESS=edge_access,COMPACT=compact,BOARDVIEW=boardview,NATIVE=native,CONCEPT=concept,PHOTO_LINK=photo_link,FUNCTIONS=functions,NETS=rows,STEPS=steps,PARTS=partrows,CHECKS=checks,GATES=gates,SOURCES=sources).items(): page=page.replace('__'+name+'__',value)
    wiring={'revision':'MC1','source':'cad/design.py','source_sha256':sha(HERE/'cad/design.py'),'nets':nets,'parts':parts}
    return {'index.html':page,'architecture.svg':architecture(),'direct-solder.svg':assembly(),'assembly-counts.svg':chart,'layout-comparison.svg':layout_comparison(current),'thread-recovery.svg':recovery_diagram(),'network-updates.svg':update_diagram(),'wiring.json':json.dumps(wiring,indent=2)+'\n'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');args=a.parse_args()
    out=produce()
    for name,content in out.items():
        path=HERE/name
        if args.check:
            assert path.exists() and path.read_text()==content, f'Stale MC1 output: {name}'
        else: path.write_text(content)
    print('MC1 presentation '+('verified' if args.check else 'generated')+': '+', '.join(out))
if __name__=='__main__': main()
