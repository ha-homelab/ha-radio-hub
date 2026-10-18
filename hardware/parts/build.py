#!/usr/bin/env python3
"""Build the parts gallery from canonical BOM rows; no network access or prices."""
from __future__ import annotations
import argparse
import ast
import csv
import io
import hashlib
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def dimensions(value):
    if not value:return ''
    if isinstance(value,list):
        label=' × '.join(str(v) for v in value if v is not None)+' mm'
        if len(value)==3 and value[2] is None:label+='; height unspecified'
        return label
    return str(value)


def source_url(value):
    if not value:
        return ""
    if isinstance(value, dict):
        return value.get('url', '')
    if value.startswith('{'):
        return ast.literal_eval(value).get('url', '')
    return value if value.startswith('https://') else ''


def read_rows(config, root=ROOT):
    rows = []
    for source in config['sources']:
        path = root / source['path']
        raw = (json.loads(path.read_text())['items'] if path.suffix == '.json'
               else list(csv.DictReader(io.StringIO(path.read_text()))))
        for r in raw:
            fmt = source['format']
            if fmt == 'original':
                ref, qty, model = r['ref'], r['qty'], r['model_or_requirement']
                note = ' · '.join(filter(None, [r.get('item'), r.get('power_or_signal'), r.get('notes')]))
                package, condition = r.get('dimensions_mm', ''), r.get('variant', '')
            elif fmt == 'reference':
                ref, qty, model = r['ref'], r['qty'], r['model']
                note, condition = r.get('note', ''), 'Reference only; ' + r.get('phase', '')
                package = dimensions(r.get('body_mm', ''))
            elif fmt == 'assembly':
                ref, qty, model = r['Reference'], r['Quantity'], r['Manufacturer part / value']
                note, package, condition = r.get('Note', ''), r.get('Footprint', ''), 'Fitted to board'
            elif fmt == 'harness':
                ref, qty, model = r['Item'], r['Quantity'], r['Model/specification']
                note = ' · '.join(filter(None, [r.get('Purpose'), r.get('Notes')]))
                package, condition = '', 'Harness / external / service; read row notes'
            else:
                raise ValueError(f'Unknown BOM format: {fmt}')
            rows.append(dict(key=source['id'] + ':' + ref, source_id=source['id'], ref=ref,
                             qty=str(qty), model=model, note=note, package=package,
                             condition=condition, source=source_url(r.get('source', r.get('Source', '')))))
    return rows


def family(row):
    model, package = row['model'].lower(), row['package'].lower()
    if row['source_id'] == 'modular' and row['ref'].startswith('A'): return 'antenna'
    if ':c_' in package or 'capacitor' in package or re.match(r'^\d+(\.\d+)?\s*(uf|nf|pf)', model): return 'capacitor'
    if ':r_' in package or 'resistor' in package or 'resistor' in model or re.match(r'^\d+(\.\d+)?\s*(k|m|ohm|Ω)(\b|\s)', model): return 'resistor'
    if any(t in model for t in ['smbj', 'usblc6']): return 'diode'
    if any(t in model for t in ['abls-', 'abm8-', 'ab-3.6864']): return 'crystal'
    if any(t in model for t in ['blm21', 'ferrite']): return 'inductor'
    if any(t in model for t in ['044901', 'fuse']): return 'fuse'
    if any(t in model for t in ['b2b-', 'b3b-', 'b4b-', 'b5b-', 'b6b-', 'b7b-', 'b8b-', 'b10b-', 'bm04b', 'xhp-', 'shr-', 'sxh-', 'ssh-', '612040', 'pp3-', 'type-c-', '0813-', 'male header', 'extra-long header']): return 'connector'
    if any(t in model for t in ['screw', 'standoff', 'mounting', 'fastener']): return 'hardware'
    if any(t in model for t in ['enclosure', 'petg', 'asa', 'vented', 'pod']): return 'enclosure'
    if any(t in model for t in ['antenna', 'ipex']): return 'antenna'
    if any(t in model for t in ['cable', 'patch', 'wire', 'ribbon', 'pigtail', 'lead', 'crimp', 'jst-sh', 'jst sh', 'cat5', 'male-female', 'microusb', 'barrel', 'dc plug']): return 'cable'
    if any(t in model for t in ['sw_push', 'momentary', 'button']): return 'switch'
    if any(t in model for t in ['sc16is', 'tps3808', 'w5500']): return 'ic'
    if any(t in model for t in ['tool', 'solder', 'multimeter', 'bench supply', 'dmm', 'probe']): return 'tool'
    return 'module'


def illustration(kind):
    # Original code-native diagrams: illustrative family shapes, never a claimed footprint.
    shapes = {
      'resistor':'<rect x="70" y="64" width="180" height="74" rx="5" fill="#263b4c"/><path d="M70 64h35v74H70zM215 64h35v74h-35z" fill="#b9c9d3"/><text x="160" y="110" text-anchor="middle" fill="white" font-size="25">R</text>',
      'capacitor':'<rect x="70" y="64" width="180" height="74" rx="5" fill="#bc9565"/><path d="M70 64h35v74H70zM215 64h35v74h-35z" fill="#b9c9d3"/>',
      'ic':'<path d="M66 60h188v100H66z" fill="#a5b8c7"/><rect x="85" y="40" width="150" height="135" rx="5" fill="#263b4c"/><circle cx="103" cy="58" r="6" fill="#e7eaf0"/><text x="160" y="115" fill="white" text-anchor="middle">IC</text>',
      'connector':'<rect x="55" y="57" width="210" height="112" rx="8" fill="#e6d8b8" stroke="#96794e" stroke-width="3"/><path d="M140 42h40v30h-40z" fill="#c5ae7c"/>' + ''.join(f'<rect x="{76+i*37}" y="92" width="20" height="35" fill="#576a72"/>' for i in range(5)),
      'cable':'<path d="M70 75C180 15 80 200 235 135" fill="none" stroke="#4e8190" stroke-width="19"/><rect x="42" y="53" width="50" height="42" rx="5" fill="#d8c9a9"/><rect x="220" y="112" width="50" height="42" rx="5" fill="#d8c9a9"/>',
      'antenna':'<path d="M115 157L196 42" stroke="#273f4d" stroke-width="18" stroke-linecap="round"/><rect x="96" y="151" width="36" height="32" fill="#c7a55c"/><path d="M213 54q38 30 0 64M229 40q56 45 0 94" fill="none" stroke="#26a29a" stroke-width="3"/>',
      'crystal':'<rect x="68" y="61" width="185" height="94" rx="40" fill="#c4ced5" stroke="#718390" stroke-width="4"/><text x="160" y="115" text-anchor="middle" fill="#294454">MHz</text>',
      'diode':'<rect x="70" y="60" width="180" height="90" rx="6" fill="#273d4b"/><rect x="97" y="60" width="16" height="90" fill="#d9e1e6"/><path d="M40 105h30m180 0h30" stroke="#8fa4b0" stroke-width="15"/>',
      'fuse':'<rect x="63" y="75" width="195" height="58" rx="8" fill="#d7e5e9" stroke="#8fa4b0" stroke-width="4"/><path d="M65 80h34v48H65zM223 80h32v48h-32z" fill="#8298a4"/><path d="M100 104h120" stroke="#5d7788" stroke-width="3"/>',
      'hardware':'<path d="M135 45h50l14 15v120h-78V60z" fill="#c7d6df" stroke="#7593a5" stroke-width="3"/><ellipse cx="160" cy="61" rx="26" ry="10" fill="#617c8d"/>',
      'enclosure':'<path d="M65 85l85-45 115 45v82l-80 34L65 155z" fill="#dce8ed" stroke="#7194a5" stroke-width="3"/><path d="M65 85l120 48 80-48m-80 48v68" fill="none" stroke="#7194a5" stroke-width="3"/>',
      'switch':'<rect x="83" y="78" width="155" height="85" fill="#b8cad4"/><circle cx="160" cy="95" r="40" fill="#283f4b"/>',
      'inductor':'<rect x="70" y="65" width="180" height="75" fill="#354c59"/><path d="M65 67h27v70H65zM230 67h27v70h-27z" fill="#b3c3cc"/>',
      'tool':'<rect x="100" y="35" width="120" height="150" rx="18" fill="#e7b44c"/><rect x="119" y="57" width="82" height="40" fill="#d0e1d7"/><circle cx="160" cy="138" r="27" fill="#314954"/>',
      'module':'<rect x="55" y="38" width="210" height="145" rx="8" fill="#267c6b"/><rect x="93" y="61" width="120" height="77" rx="5" fill="#d1dce1"/><path d="M80 152h164" stroke="#d4b970" stroke-width="12"/><circle cx="69" cy="52" r="5" fill="#f3f7fa"/>'}
    shapes.update({
      'resistor-axial':'<path d="M28 103h265" stroke="#9aadb8" stroke-width="6"/><rect x="83" y="77" width="155" height="52" rx="24" fill="#77a8c0" stroke="#40748c" stroke-width="3"/><text x="160" y="111" text-anchor="middle" fill="#173b4f">R</text>',
      'capacitor-radial':'<path d="M127 118v75m67-75v75" stroke="#9aadb8" stroke-width="6"/><rect x="91" y="45" width="137" height="97" rx="30" fill="#ba8e57"/><text x="160" y="103" text-anchor="middle" fill="#fff">C</text>',
      'capacitor-electrolytic':'<path d="M139 138v57m43-57v48" stroke="#9aadb8" stroke-width="6"/><path d="M99 53h122v111c-10 19-110 19-122 0z" fill="#334c5a"/><ellipse cx="160" cy="53" rx="61" ry="17" fill="#bcccd5"/><path d="M205 60v100" stroke="#a8c4d2" stroke-width="15"/><text x="205" y="115" text-anchor="middle" fill="#334c5a">−</text>',
      'crystal-through-hole':'<path d="M113 120v75m95-75v75" stroke="#91a8b7" stroke-width="6"/><rect x="71" y="45" width="181" height="98" rx="38" fill="#c4ced5" stroke="#718390" stroke-width="4"/><text x="160" y="103" text-anchor="middle" fill="#294454">MHz</text>'})
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" role="img">'
            f'<title>{kind.title()} family illustration, not a product photograph</title><rect width="320" height="240" fill="#f2f6f8"/>'
            + shapes[kind] + '<text x="160" y="226" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#4c6778">ILLUSTRATION · NOT TO SCALE</text></svg>')


def image_for(row, config):
    # Accessory groups and antennas must not accidentally get a pictured constituent module.
    image = None
    if family(row) in {'module', 'ic'} and not row['model'].startswith(('I0 external', 'LP-P0 module set')):
        image = next((dict(i) for i in config['images'] if re.search(i['match'], row['model'], re.I)), None)
    for token, name in [('ESP32-S3-WROOM-1-N16R8','s3'), ('ESP32-H2-MINI-1-H4S','h2'), ('MGM240PA22VNA3','mg24')]:
        if row['model'].strip() == token:
            image = dict(kind='dimensioned_diagram', url=f'../low-power/visual/physical/generated/{name}-contacts.svg',
                         source='../low-power/visual/physical/README.md', credit='HA Radio Hub project',
                         caption='Source-derived top-view contact drawing. Not a photograph; distinguish bare module pads from development-board headers.')
    profile=family(row)
    if 'Axial_R' in row['package']:profile='resistor-axial'
    if 'Radial_C' in row['package']:
        profile='capacitor-electrolytic' if 'electrolytic' in row['note'].lower() else 'capacitor-radial'
    if row['package'].endswith(':HC49U'):profile='crystal-through-hole'
    return image or dict(kind='original_illustration', url=f'illustrations/{profile}.svg', source='',
                        credit='HA Radio Hub project · MIT', caption='Original family illustration, not a photo or a footprint. Package dimensions and terminal layout must be checked against the exact row and datasheet.')


def purchase_link(row):
    model=row['model']
    if family(row)=='enclosure':
        return dict(kind='project_source',url='../../mechanical/README.md',label='Project enclosure files — print / fabricate')
    if model.startswith('LP-M0'):
        return dict(kind='project_source',url='../low-power/carrier/mg24-adapter/README.md',label='M0 project files — fabricate / assemble')
    if model.startswith(('Single-host PCB', 'LP-P0 module set', 'I0 external')):
        return dict(kind='project_source',url='../../docs/parts-catalog.md',label='Select constituent parts from project BOM')
    return dict(kind='search_unverified',url='https://www.aliexpress.com/wholesale?SearchText='+quote_plus(search_term(row)),label='AliExpress search — unverified results')


def search_term(row):
    term=row['model']
    kind=family(row)
    package=re.search(r'(?:R_|C_|L_)(0402|0603|0805|1206)', row['package'])
    if kind in {'resistor','capacitor','inductor'}:
        if kind=='resistor' and re.fullmatch(r'[0-9.]+',term):term+=' ohm'
        term+=' '+kind
        if package:term+=' '+package[1]
    return term


def inventory(config, root=ROOT):
    rows = read_rows(config, root)
    for a in config.get('accessories', []):
        rows.append(dict(key='accessory:'+a['id'], source_id='accessory', ref=a['id'], qty=a['qty'],
                         model=a['model'], note=a['notes'], package='', condition=a['scope'], source=a['source']))
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r['model'], r['package'])].append(r)
    cards = []
    for (model, package), group in grouped.items():
        row = group[0]
        cards.append(dict(id='p-'+hashlib.sha256((model+'\0'+package).encode()).hexdigest()[:12], model=model,
                          package=package, category=family(row), image=image_for(row, config), rows=group,
                          ali=purchase_link(row)))
    cards.sort(key=lambda c: (c['image']['kind'] not in {'manufacturer_photo', 'manufacturer_render', 'dimensioned_diagram'}, c['category'], c['model']))
    return dict(schema_version=1, checked_date=config['checked_date'], sources=config['sources'], cards=cards)


def render(data):
    esc = html.escape
    labels = {s['id']:s['label'] for s in data['sources']} | {'accessory':'Additional / reusable / conditional'}
    sections=[]
    for card in data['cards']:
        img=card['image']
        grouped=defaultdict(list)
        for row in card['rows']: grouped[row['source_id']].append(row)
        usage=[]
        for sid, rows in grouped.items():
            # Numeric totals are only within one source, never across alternative builds.
            counts = [r['qty'] for r in rows]
            quantity = str(sum(int(q) for q in counts)) if all(q.isdigit() for q in counts) else ', '.join(counts)
            usage.append(f'<div class="usage"><b>{esc(labels[sid])}</b><span class="quantity">Qty {esc(quantity)}</span><div class="refs">{esc(", ".join(r["ref"] for r in rows))}</div></div>')
        details=[]
        for row in card['rows']:
            source = f' <a href="{esc(row["source"])}" target="_blank" rel="noopener noreferrer">Source ↗</a>' if row['source'] else ''
            details.append(f'<li><b>{esc(row["key"])}</b> — {esc(row["condition"])}<p>{esc(row["note"])}{source}</p></li>')
        imgsource = f'<a href="{esc(img["source"])}" target="_blank" rel="noopener noreferrer">Image source ↗</a>' if img['source'] else ''
        fulltext = ' '.join([card['model'],card['package'],card['category']]+[r['note']+' '+r['ref'] for r in card['rows']])
        sections.append(f'''<article id="{card['id']}" data-variants="{esc(' '.join(grouped))}" data-category="{esc(card['category'])}" data-search="{esc(fulltext.lower())}">
        <figure><img loading="lazy" src="{esc(img['url'])}" data-fallback="illustrations/{card['category']}.svg" alt="{esc(img['caption'])}"><span class="image-kind">{esc(img['kind'].replace('_',' '))}</span></figure>
        <div class="body"><div class="category">{esc(card['category'])}</div><h2>{esc(card['model'] + (' Ω' if card['category'] == 'resistor' and re.fullmatch(r'[0-9.]+', card['model']) else ''))}</h2><p class="package">{esc(card['package'])}</p>
        {''.join(usage)}<p class="caption">{esc(img['caption'])}</p><p class="credit">{esc(img['credit'])} {imgsource}</p>
        <a class="buy" href="{esc(card['ali']['url'])}" target="_blank" rel="noopener noreferrer">{esc(card['ali']['label'])} ↗</a>
        <details><summary>Exact BOM notes &amp; official sources ({len(card['rows'])} rows)</summary><ul>{''.join(details)}</ul></details></div></article>''')
    options=''.join(f'<option value="{esc(k)}">{esc(v)}</option>' for k,v in labels.items())
    cats=''.join(f'<option>{esc(x)}</option>' for x in sorted({c['category'] for c in data['cards']}))
    return TEMPLATE.replace('__CARDS__','\n'.join(sections)).replace('__OPTIONS__',options).replace('__CATEGORIES__',cats).replace('__COUNT__',str(len(data['cards']))).replace('__ROWS__',str(sum(len(c['rows']) for c in data['cards']))).replace('__DATE__',data['checked_date'])

TEMPLATE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HA Radio Hub · Assembly parts atlas</title>
<style>
:root{font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;color:#173343;background:#eef3f5}*{box-sizing:border-box}body{margin:0}header{background:#123c4b;color:#fff;padding:48px max(24px,calc((100vw - 1440px)/2)) 34px}header small{letter-spacing:.15em;color:#8bdfcc}h1{font-size:clamp(30px,4vw,52px);line-height:1.08;margin:15px 0}header p{max-width:850px;color:#d5e4e9;line-height:1.55}a{color:#086b67;text-underline-offset:3px}header a{color:#9de5d5}.strip{max-width:1490px;margin:auto;padding:22px 24px}.strip p{line-height:1.5}.boards{display:flex;gap:14px;flex-wrap:wrap}.boards a{background:white;border:1px solid #c6d9df;border-radius:10px;padding:8px 15px;font-weight:650}.controls{position:sticky;top:0;z-index:3;background:#eef3f5ed;border-block:1px solid #cfdee4;backdrop-filter:blur(10px)}.controls .strip{display:flex;gap:14px;flex-wrap:wrap;align-items:end}label{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:650}label:first-child{flex:1;min-width:190px}input,select{font:inherit;padding:11px 12px;background:white;border:1px solid #a9c1ca;border-radius:8px;color:#173343;max-width:100%}#count{font-size:13px;padding-bottom:12px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:20px;max-width:1490px;padding:24px;margin:auto}article{background:white;border:1px solid #d1e0e6;border-radius:15px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 4px 14px #22475906}article[hidden]{display:none}figure{height:230px;background:#f8fafb;position:relative;margin:0;padding:15px}figure img{width:100%;height:100%;object-fit:contain}.image-kind{position:absolute;bottom:8px;left:12px;background:#fffef4ed;border:1px solid #e5debc;padding:4px 8px;border-radius:5px;font-size:10px;text-transform:uppercase;letter-spacing:.06em}.body{padding:20px;display:flex;flex:1;flex-direction:column}h2{font-size:19px;line-height:1.32;margin:7px 0 10px;overflow-wrap:anywhere}.category{text-transform:uppercase;font-size:10px;letter-spacing:.13em;font-weight:750;color:#397c79}.package{font:11px ui-monospace,monospace;color:#586f7c;overflow-wrap:anywhere;margin:0 0 12px}.usage{font-size:11px;padding:8px 0;border-top:1px solid #e4edf0;line-height:1.6}.quantity{display:block;font-weight:700;color:#086b67}.refs{font-family:ui-monospace,monospace;overflow-wrap:anywhere}.caption{font-size:12px;line-height:1.5;color:#536d79;margin-bottom:4px}.credit{font-size:11px;color:#536d79;line-height:1.5}.buy{border:1px solid #b6d5cd;border-radius:7px;padding:10px;font-size:12px;text-align:center;margin-top:auto;background:#f0faf7}.buy:hover{background:#e1f3ed}details{margin-top:16px;font-size:12px;line-height:1.6}summary{cursor:pointer;font-weight:650}details ul{padding-left:16px}details li{overflow-wrap:anywhere}details p{margin-top:3px}footer{max-width:1440px;margin:20px auto;padding:24px;font-size:12px;line-height:1.6;color:#536d79}#empty{display:none;padding:45px;text-align:center}@media(max-width:600px){header{padding:30px 20px}.controls{position:static}.controls .strip{display:block}.controls label{margin:10px 0}.grid{padding:16px;grid-template-columns:1fr}.strip{padding:18px}figure{height:235px}}
</style>
<aside class="strip"><strong>Historical parts catalog.</strong> The only current build is <a href="../module-carrier/index.html">MC1: one finished-module carrier</a>. The entries below reproduce earlier BOMs and are not the MC1 shopping list.</aside><header><small>HA RADIO HUB / HISTORICAL BUILD REFERENCE</small><h1>Earlier parts and builds.</h1><p>Component appearance, exact BOM references and sourcing links in one assembly atlas. __COUNT__ identification cards · __ROWS__ source and accessory rows · checked __DATE__.</p><p><a href="../../docs/parts-catalog.md">Build selection &amp; sourcing notes</a> · <a href="../low-power/visual/generated/index.html">Pin-to-pin wiring atlas</a> · <a href="inventory.json">Machine-readable inventory</a></p></header>
<section class="strip"><div class="boards"><a href="../gallery/carrier-c0.png">C0 bare PCB render</a><a href="../gallery/mg24-m0.png">M0 bare PCB render</a><a href="../gallery/integrated-i0.png">I0 bare PCB render</a><a href="../gallery/diy-d0.png">D0 bare PCB bottom render</a></div><p><strong>Select one build before ordering.</strong> Quantities are per source. AliExpress links are unverified searches.</p><details><summary>Build selection, image types and sourcing notes</summary><p>C0 and D0 need their M0 adapter and external modules; I0 integrates many of those parts. D0 also requires the separately listed adapter PCBs, headers and insulated wire links. LP-P0 is a reference design list, not another shopping list to add on top. The original Pi build has mutually exclusive Wi-Fi and wired-RF options. Quantities are kept per source, never totaled across builds.</p><p><strong>Every AliExpress link below is a search, not a verified offer.</strong> Match the full part number, voltage, package, connector pitch and radio region. Photos are manufacturer-hosted and remain their copyright; renders and original diagrams are labeled. No price or stock claim is made.</p></details></section>
<section class="controls"><div class="strip"><label>Find a model, value or reference<input id="search" type="search" placeholder="Try LD2450, 100nF, JST, C37…"></label><label>Build / BOM<select id="variant"><option value="">All build references</option>__OPTIONS__</select></label><label>Part family<select id="category"><option value="">All families</option>__CATEGORIES__</select></label><span id="count" aria-live="polite"></span></div></section>
<main class="grid">__CARDS__</main><p id="empty">No matching components. Clear a filter to see more.</p>
<footer>Prototype assembly reference. Appearance is not proof of electrical compatibility. Read the original row notes and current manufacturing gates before buying, powering or fabricating. All local family illustrations are original project artwork (MIT); external manufacturer imagery is remotely embedded for identification, not relicensed or included in the repository. Offline or blocked photos fall back to a visibly labeled generic illustration.</footer>
<script>
const cards=[...document.querySelectorAll('article')], search=document.querySelector('#search'), variant=document.querySelector('#variant'), category=document.querySelector('#category');
function filter(){let n=0;const q=search.value.toLowerCase().trim();for(const card of cards){const show=(!q||card.dataset.search.includes(q))&&(!variant.value||card.dataset.variants.split(' ').includes(variant.value))&&(!category.value||card.dataset.category===category.value);card.hidden=!show;if(show)n++;}document.querySelector('#count').textContent=`${n} of ${cards.length} cards`;document.querySelector('#empty').style.display=n?'none':'block';}
for(const input of [search,variant,category])input.addEventListener('input',filter);filter();
for(const img of document.querySelectorAll('img[data-fallback]')){img.addEventListener('error',()=>{if(img.dataset.failed)return;img.dataset.failed='1';img.src=img.dataset.fallback;img.closest('figure').querySelector('.image-kind').textContent='Fallback illustration · photo unavailable';img.alt='Generic family illustration; original product image unavailable';});if(img.complete && img.naturalWidth===0)img.dispatchEvent(new Event('error'));}
</script></html>'''


def markdown_link(url):
    if url.startswith('https://'):return url
    return '../'+str((HERE/url).resolve().relative_to(ROOT))


def render_markdown(data):
    labels={s['id']:s['label'] for s in data['sources']} | {'accessory':'Additional / reusable / conditional'}
    lines=['# Historical assembly parts gallery', '',
           '> **Historical catalog.** Use [the current MC1 guide](../hardware/module-carrier/index.html) and [MC1 hardware](../hardware/module-carrier/README.md) for the single active design. The following entries retain the earlier BOMs.', '',
           'Pictures, exact model identification and every canonical BOM row. '+
           '[Build selection and sourcing notes](parts-catalog.md) · '+
           '[Filterable HTML catalog](../hardware/parts/index.html) (download/open locally) · '+
           '[Pin-to-pin atlas](../hardware/low-power/visual/README.md).', '',
           '**Choose one build.** Quantities below are per source; never add alternative builds together. '+
           'LP-P0 is a bench reference, not an extra purchase list. All AliExpress links are **unverified searches**, not approved offers. '+
           'Images are labeled photos, renders, source-derived diagrams or generic illustrations; appearance does not establish compatibility.', '',
           'Manufacturer images remain remotely hosted and copyrighted by the credited owner. No redistribution license is asserted. '+
           'If GitHub cannot load one, use its source link or the local family-illustration link. '+
           'Local original illustrations are MIT; physical contact diagrams retain their linked source notices.', '',
           '## Main modules and sensors', '']
    prominent=[c for c in data['cards'] if c['image']['kind']!='original_illustration']
    groups=[('Main modules and sensors',prominent)]
    for kind in sorted({c['category'] for c in data['cards'] if c not in prominent}):
        groups.append((kind.title(),[c for c in data['cards'] if c not in prominent and c['category']==kind]))
    for index,(group,cards) in enumerate(groups):
        if index:lines+=['<details>',f'<summary><strong>{group}: {len(cards)} identification cards</strong></summary>', '']
        for card in cards:
            image=card['image']
            title=card['model']+(' Ω' if card['category']=='resistor' and re.fullmatch(r'[0-9.]+',card['model']) else '')
            lines += [f'<a id="{card["id"]}"></a>',f'### {title}', '',
                      f'<img src="{html.escape(markdown_link(image["url"]))}" alt="{html.escape(image["caption"])}" width="360">', '',
                      f'**{image["kind"].replace("_"," ").capitalize()}** — {image["caption"]}', '',
                      f'Image: {image["credit"]}. '+(f'[Source]({markdown_link(image["source"])}) · ' if image['source'] else '')+
                      f'[Local family illustration](../hardware/parts/illustrations/{card["category"]}.svg).', '']
            if card['package']:lines += [f'Package / dimensions: `{card["package"]}`.', '']
            grouped=defaultdict(list)
            for row in card['rows']:grouped[row['source_id']].append(row)
            for sid,rows in grouped.items():
                counts=[r['qty'] for r in rows]
                qty=str(sum(int(q) for q in counts)) if all(q.isdigit() for q in counts) else ', '.join(counts)
                refs=', '.join(r['ref'] for r in rows)
                lines += [f'- **{labels[sid]}:** quantity {qty}; references `{refs}`.']
            lines += ['',f'[{card["ali"]["label"]}]({markdown_link(card["ali"]["url"])})', '',
                      '<details><summary>Exact BOM row conditions, notes and sources</summary>', '']
            for row in card['rows']:
                link=f' [Official / original source]({row["source"]}).' if row['source'] else ''
                lines += [f'- **{row["key"]}:** {row["condition"]}. {row["note"]}{link}']
            lines += ['', '</details>', '']
        if index:lines += ['</details>', '']
    lines += ['---', '', f'Generated from {len(data["sources"])} canonical inventories plus explicitly marked accessories. '+
              'Do not edit this gallery manually; run `python3 hardware/parts/build.py`. '+
              'See [catalog documentation](parts-catalog.md) for validation and image provenance.', '']
    return '\n'.join(lines)


def outputs(config):
    data=inventory(config)
    files={'inventory.json':json.dumps(data,indent=2,ensure_ascii=False)+'\n','index.html':render(data),'../../docs/parts-gallery.md':render_markdown(data)}
    for kind in {c['category'] for c in data['cards']} | {Path(c['image']['url']).stem for c in data['cards'] if c['image']['kind']=='original_illustration'}:
        files[f'illustrations/{kind}.svg']=illustration(kind)+'\n'
    return files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    config=json.loads((HERE/'catalog.json').read_text())
    from validate import validate
    data=inventory(config)
    validate(config,data)
    for name,content in outputs(config).items():
        path=HERE/name
        if args.check:
            if not path.exists() or path.read_text()!=content: raise SystemExit(f'Stale gallery file: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print(f'Parts gallery: {len(read_rows(config))} canonical BOM rows, {len(data["cards"])} cards; '+('fresh' if args.check else 'generated'))

if __name__=='__main__':main()
