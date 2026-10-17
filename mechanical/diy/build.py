#!/usr/bin/env python3
"""Native KiCad bottom-copper artwork and dimensioned DIY assembly documents.

The copper is never re-created from pad/track approximations. KiCad plots B.Cu;
Cairo converts that SVG to vector PDF at its declared millimetre dimensions.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOARD = ROOT / 'hardware/low-power/diy/diy.kicad_pcb'
DEFAULT_OUT = ROOT / 'hardware/low-power/diy/print'
MM = 72 / 25.4


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sexpr(text):
    stack = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            node = []; stack[-1].append(node); stack.append(node)
        elif token == ')':
            if len(stack) == 1:
                raise ValueError('Unbalanced board')
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError('Invalid board')
    return stack[0][0]


def child(node, name):
    return next((x for x in node if isinstance(x, list) and x[0] == name), None)


def children(node, name):
    return [x for x in node if isinstance(x, list) and x[0] == name]


def board_geometry(path):
    tree = sexpr(Path(path).read_text())
    outline = []
    for node in tree:
        if not isinstance(node, list):
            continue
        layer = child(node, 'layer')
        if layer and layer[1] == 'Edge.Cuts':
            if node[0] not in ('gr_line', 'gr_rect'):
                raise ValueError('Only a rectangular straight-edge DIY outline is supported')
            outline += [list(map(float, child(node, p)[1:3])) for p in ('start', 'end')]
        if node[0] in ('segment', 'arc') and layer[1] != 'B.Cu':
            raise ValueError('DIY copper tracks must be on B.Cu; use physical wire jumpers')
        if node[0] in ('via', 'zone'):
            raise ValueError('This DIY print contract excludes vias and copper zones')
    if not outline:
        raise ValueError('Missing board outline')
    x0, y0 = min(p[0] for p in outline), min(p[1] for p in outline)
    width, height = max(p[0] for p in outline)-x0, max(p[1] for p in outline)-y0
    # Native fit-to-board SVG must preserve these source coordinates; origin zero
    # avoids relying on version-specific crop translations.
    if (x0, y0) != (0, 0):
        raise ValueError('DIY board outline origin must be (0, 0)')
    holes, refs = [], []
    for fp in children(tree, 'footprint'):
        at = child(fp, 'at'); fx, fy = map(float, at[1:3])
        angle = math.radians(float(at[3]) if len(at) > 3 else 0)
        layer = child(fp, 'layer')[1]
        if layer != 'F.Cu':
            raise ValueError('DIY components must be placed on the top side')
        ref = next((p[2] for p in children(fp, 'property') if p[1] == 'Reference'), '?')
        value = next((p[2] for p in children(fp, 'property') if p[1] == 'Value'), '')
        refs.append(dict(ref=ref, value=value, x_mm=fx, y_mm=fy))
        for pad in children(fp, 'pad'):
            if pad[2] not in ('thru_hole', 'np_thru_hole'):
                raise ValueError(f'{ref}.{pad[1]} is not a through-hole pad')
            drill = child(pad, 'drill')
            if not drill or len(drill) != 2:
                raise ValueError('Only round drill holes are supported')
            p = child(pad, 'at'); x, y = map(float, p[1:3])
            px = fx + math.cos(angle)*x + math.sin(angle)*y
            py = fy - math.sin(angle)*x + math.cos(angle)*y
            net = child(pad, 'net')
            holes.append(dict(id=f'{ref}.{pad[1] or "mount"}', ref=ref, pad=pad[1],
                x_mm=round(px, 6), y_mm=round(py, 6), drill_mm=float(drill[1]),
                electrical=pad[2]=='thru_hole', net=net[-1] if net else ''))
    tracks = children(tree, 'segment') + children(tree, 'arc')
    return dict(width_mm=width, height_mm=height, holes=holes, components=refs,
                minimum_track_mm=min(float(child(t, 'width')[1]) for t in tracks) if tracks else None)


def normalize_native_svg(path, geometry):
    """Keep 1 SVG unit = 1 mm; verify native pilot centres before PDF conversion."""
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.attrib['viewBox'].split()]
    width, height = geometry['width_mm'], geometry['height_mm']
    if abs(vb[2]-width) > .1 or abs(vb[3]-height) > .1 or vb[:2] != [0, 0]:
        raise ValueError('Native SVG crop does not match the DIY outline')
    circles = [(float(e.attrib['cx']), float(e.attrib['cy'])) for e in root.iter()
               if e.tag.endswith('}circle')]
    for hole in geometry['holes']:
        if hole['electrical'] and not any(abs(x-hole['x_mm']) < .015 and
                abs(y-hole['y_mm']) < .015 for x, y in circles):
            raise ValueError(f'Native B.Cu plot is missing unmirrored pilot {hole["id"]}')
    # KiCad's fit box can differ by a few micrometres due to its plot units.
    # Expand the viewport to the nominal outline without scaling any content.
    root.set('width', f'{width}mm'); root.set('height', f'{height}mm')
    root.set('viewBox', f'0 0 {width} {height}')
    for el in list(root):
        if el.tag.endswith('}title'):
            root.remove(el)  # Remove volatile native timestamp.
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def sheet_canvas(paper):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter
    stream = io.BytesIO()
    size = A4 if paper == 'a4' else letter
    c = canvas.Canvas(stream, pagesize=size, invariant=1, pageCompression=1)
    c.setAuthor('HA Radio Hub contributors'); c.setTitle('LP-D0 DIY print package')
    c.setViewerPreference('PrintScaling','None'); c.setViewerPreference('Duplex','Simplex')
    return stream, c, size


def text(c, x, y, value, size=9, bold=False):
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawString(x*MM, y*MM, str(value))


def line(c, x1, y1, x2, y2, width=.15):
    c.setLineWidth(width*MM); c.line(x1*MM, y1*MM, x2*MM, y2*MM)


def ruler(c, x, y, vertical=False):
    line(c, x, y, x if vertical else x+100, y+100 if vertical else y)
    for i in range(101):
        n=2 if i % 10 == 0 else 1
        if vertical: line(c, x, y+i, x+n, y+i)
        else: line(c, x+i, y, x+i, y+n)


def header(c, size, title, subtitle):
    top=size[1]/MM
    text(c, 15, top-17, title, 15, True)
    text(c, 15, top-24, subtitle, 8)
    paper_label='A4' if abs(size[0]/MM-210)<.01 else 'US Letter'
    text(c, 15, 10, f'LP-D0 prototype | {paper_label} | CAD/print checks only; not physically fabricated', 8)


def finish(stream, c):
    c.save(); return stream.getvalue()


def native_plot(cli, board, out, layers, drill=1):
    command=[cli, 'pcb', 'export', 'svg', '--layers', layers, '--black-and-white',
             '--drill-shape-opt', str(drill), '--mode-single', '--fit-page-to-board',
             '--exclude-drawing-sheet', '--scale', '1', '--output', str(out), str(board)]
    if 'F.Fab' in layers:
        command.insert(-1, '--sketch-pads-on-fab-layers')
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return command


def add_vector(base, svg, x, y, geometry, mirror=False):
    import cairosvg
    from pypdf import PdfReader, PdfWriter, Transformation
    source = PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=svg))).pages[0]
    if abs(float(source.mediabox.width)-geometry['width_mm']*MM) > .01:
        raise ValueError('SVG-to-PDF conversion changed physical width')
    if abs(float(source.mediabox.height)-geometry['height_mm']*MM) > .01:
        raise ValueError('SVG-to-PDF conversion changed physical height')
    target = PdfReader(io.BytesIO(base)).pages[0]
    transform=(Transformation().scale(-1,1).translate((x+geometry['width_mm'])*MM,y*MM)
               if mirror else Transformation().translate(x*MM,y*MM))
    target.merge_transformed_page(source, transform)
    writer=PdfWriter(); writer.add_page(target)
    writer.add_metadata({'/Title': 'LP-D0 DIY print package', '/Author': 'HA Radio Hub contributors'})
    writer.set_page_layout('/SinglePage')
    from pypdf.generic import DictionaryObject, NameObject
    writer._root_object.update({NameObject('/ViewerPreferences'): DictionaryObject({
        NameObject('/PrintScaling'): NameObject('/None'), NameObject('/Duplex'): NameObject('/Simplex')})})
    result=io.BytesIO(); writer.write(result); return result.getvalue()


def calibration(paper):
    stream,c,size=sheet_canvas(paper)
    header(c,size,'Print calibration - actual size / 100%', 'Measure on paper; disable fit/shrink, duplex, toner saving and all mirror options.')
    ruler(c,35,125); ruler(c,35,125,True)
    text(c,45,230,'100.00 mm axes; project target +/-0.20 mm',9)
    text(c,45,119,'100.00 mm',9)
    c.setLineWidth(.15*MM); c.rect(65*MM,160*MM,50*MM,50*MM,fill=0,stroke=1)
    text(c,67,183,'50.00 x 50.00 mm',8)
    for i in range(11):
        c.circle((135+i*2.54)*MM,195*MM,.5*MM,stroke=1,fill=0)
    text(c,132,201,'10 pitches = 25.40 mm',8)
    text(c,15,101,'Transfer coupon: cut around this strip only; the rulers are not an etch mask.',8)
    # An asymmetric transferable coupon, no small IC geometry claimed.
    line(c,20,70,180,70); line(c,20,70,20,94); line(c,180,70,180,94); line(c,20,94,180,94)
    for j,w in enumerate((.4,.5,.6,.8,1.0)):
        x=40+j*27
        for k in range(4):
            line(c,x,74+k*2*w,x+18,74+k*2*w,w)
        text(c,x,87,f'{w:.1f} mm line / gap',6)
    # Pad coupon: 2.0 mm copper lands with 0.4 mm drill-centre pilot marks.
    for px in (25, 32):
        for py in (75, 79, 83):
            c.setFillColorRGB(0, 0, 0); c.circle(px*MM,py*MM,1.0*MM,stroke=0,fill=1)
            c.setFillColorRGB(1, 1, 1); c.circle(px*MM,py*MM,.2*MM,stroke=0,fill=1)
    c.setFillColorRGB(0, 0, 0)
    # Distinct corner counts expose mirror reversal after toner-down transfer.
    for x,y in ((24,90),(174,90),(177,90)):
        c.circle(x*MM,y*MM,.8*MM,stroke=0,fill=1)
    text(c,15,64,'Pad coupon: 2.0 mm copper lands; drill 1.1 mm after etching to test the annular ring.',8)
    text(c,15,57,'Printed: one dot at left, two at right. On copper after transfer: two left, one right.',8)
    text(c,15,50,'The coupon is sacrificial and electrically separate from the carrier.',8)
    text(c,15,43,'Pass only after etching: no opens, bridges, pinholes or unacceptable undercut.',8)
    return finish(stream,c)


def drill_sheet(geometry,paper):
    stream,c,size=sheet_canvas(paper); w,h=geometry['width_mm'],geometry['height_mm']
    header(c,size,'Drilling / inspection - bottom copper view', 'NOT an etch mask. Mirrored from component view. All holes are unplated in the DIY process.')
    x0=(size[0]/MM-w)/2; y0=size[1]/MM-37-h
    c.setLineWidth(.15*MM); c.rect(x0*MM,y0*MM,w*MM,h*MM)
    diameters=sorted({h['drill_mm'] for h in geometry['holes']})
    symbols=['+','x','square','diamond','triangle','ring']
    def marker(x,y,d):
        r=d/2; k=diameters.index(d)
        c.circle(x*MM,y*MM,r*MM,fill=0,stroke=1)
        if k==0:
            line(c,x-.7,y,x+.7,y,.1);line(c,x,y-.7,x,y+.7,.1)
        elif k==1:
            line(c,x-.6,y-.6,x+.6,y+.6,.1);line(c,x-.6,y+.6,x+.6,y-.6,.1)
        elif k==2:
            c.rect((x-.6)*MM,(y-.6)*MM,1.2*MM,1.2*MM,stroke=1,fill=0)
        elif k==3:
            for a,b in (((x,y+.75),(x+.75,y)),((x+.75,y),(x,y-.75)),((x,y-.75),(x-.75,y)),((x-.75,y),(x,y+.75))):
                line(c,*a,*b,.1)
        elif k==4:
            for a,b in (((x,y+.75),(x+.65,y-.5)),((x+.65,y-.5),(x-.65,y-.5)),((x-.65,y-.5),(x,y+.75))):
                line(c,*a,*b,.1)
        elif k>5:
            raise ValueError('More than six drill sizes need an explicit drill symbol legend')
    for hole in geometry['holes']:
        x=x0+w-hole['x_mm']; y=y0+h-hole['y_mm']
        marker(x,y,hole['drill_mm'])
    y=y0-10
    text(c,15,y,f'Outline: {w:g} x {h:g} mm. Hole circles show actual nominal drill diameter.',9)
    for diameter,count in sorted(Counter(p['drill_mm'] for p in geometry['holes']).items()):
        y-=6; marker(17,y+1,diameter);text(c,22,y,f'{diameter:g} mm drill: {count} holes ({symbols[diameters.index(diameter)]})',9)
    y-=8; text(c,15,y,'Confirm drill against the actual lead; avoid enlarging a hole beyond its copper annulus.',8)
    y-=6; text(c,15,y,'Complete pad coordinates and nets: drill-map.json (component/top coordinates).',8)
    return finish(stream,c)



def wire_schedule_pdf(plan, geometry, paper):
    """Actual endpoint/cut schedule, in component-view coordinates."""
    terminals={t['ref']:t for t in plan['terminals']}
    source_pads={h['id']:h for h in geometry['holes']}
    for name,t in terminals.items():
        if t.get('kind')=='adapter_pin':
            physical=t['physical_pin']
            if t.get('connection_height_mm',0)<=0:
                raise ValueError(f'Raised adapter joint lacks height: {name}')
        else:
            physical=name+'.1'
        if physical not in source_pads:
            raise ValueError(f'Wire terminal absent from native PCB: {name} ({physical})')
        p=source_pads[physical]
        if any(abs(a-b)>.001 for a,b in zip(t['xy'],(p['x_mm'],p['y_mm']))):
            raise ValueError(f'Wire terminal position differs from native PCB: {name}')
    for wire in plan['wires']:
        for end in ('from','to'):
            name=wire[end+'_terminal']; t=terminals[name]
            physical=t['physical_pin'] if t.get('kind')=='adapter_pin' else name+'.1'
            if wire.get(end+'_pin',physical)!=physical:
                raise ValueError(f'Wire {wire["ref"]} disagrees with physical pin of {name}')
            height=t.get('connection_height_mm',0)
            if wire.get(end+'_height_mm',height)!=height:
                raise ValueError(f'Wire {wire["ref"]} disagrees with joint height of {name}')
    stream,c,size=sheet_canvas(paper)
    rows=plan['wires']
    for offset in range(0,len(rows),31):
        header(c,size,'Assembly - insulated wire schedule', 'Coordinates in mm, component/top view. Follow terminal IDs; crossings do not connect.')
        top=size[1]/MM; y=top-36
        columns=[15,29,71,111,152,177]
        for x,label in zip(columns,['Wire','Logical net','From (x,y)','To (x,y)','Cut mm','AWG']):
            text(c,x,y,label,8,True)
        line(c,15,y-2,195,y-2)
        for row in rows[offset:offset+31]:
            y-=6.3
            endpoints=[]
            for key in ('from_terminal','to_terminal'):
                name=row[key];xv,yv=terminals[name]['xy']
                endpoints.append(f'{name}: {terminals[name]["physical_pin"]} @{terminals[name]["connection_height_mm"]:g}mm'
                    if terminals[name].get('kind')=='adapter_pin' else f'{name} ({xv:g},{yv:g})')
            vals=[row['ref'],row['logical_net'],*endpoints,str(row['cut_length_mm']),str(row['awg'])]
            for x,value in zip(columns,vals):
                text(c,x,y,value,6.6)
        text(c,15,top-247,'Strip 5 mm at each end; cut length includes 14 mm plus any raised-joint allowance.',7)
        text(c,15,top-253,'Confirm actual bend/insulation clearance before cutting a complete batch.',7)
        c.showPage()
    raised=[t for t in terminals.values() if t.get('kind')=='adapter_pin']
    if raised:
        header(c,size,'Assembly - raised adapter-pin joints', 'These are existing component leads, not extra drill holes or T-terminal pads.')
        top=size[1]/MM; y=top-40
        for t in raised:
            text(c,15,y,f'{t["ref"]}: {t["physical_pin"]}, component coordinates {t["xy"]} mm',10,True)
            y-=7
            text(c,15,y,f'Solder joint: {t["connection_height_mm"]:g} mm above the carrier board.',9)
            y-=13
        text(c,15,y-3,'Maintain the specified 6 mm clearance below the adapter PCB.',9)
        text(c,15,y-10,'Keep the first/last 3 mm of wire above the header at the stated joint height, then descend.',8)
        text(c,15,y-17,'Make, insulate and inspect these joints before seating the adapter.',9)
        text(c,15,y-24,'Do not drill a new hole at an E endpoint; use the named existing component lead.',9)
        text(c,15,y-31,'Cut lengths already include the vertical allowance recorded in the wire schedule.',9)
        text(c,15,y-38,'Verify continuity and clearance to adjacent pins before applying power.',9)
        c.showPage()
    return finish(stream,c)


def append_pdf(first, extra):
    from pypdf import PdfReader,PdfWriter
    writer=PdfWriter()
    writer.append(PdfReader(io.BytesIO(first))); writer.append(PdfReader(io.BytesIO(extra)))
    from pypdf.generic import DictionaryObject,NameObject
    writer._root_object.update({NameObject('/ViewerPreferences'):DictionaryObject({
        NameObject('/PrintScaling'):NameObject('/None'),NameObject('/Duplex'):NameObject('/Simplex')})})
    stream=io.BytesIO();writer.write(stream);return stream.getvalue()


def compose(board, out, cli, paper='a4', jumper_path=None):
    geom=board_geometry(board); out.mkdir(parents=True,exist_ok=True)
    if jumper_path is None and (board.parent/'routing-plan.json').exists():
        jumper_path=board.parent/'routing-plan.json'
    from reportlab.lib.pagesizes import A4, letter
    page=A4 if paper=='a4' else letter
    if geom['width_mm']>page[0]/MM-20 or geom['height_mm']>page[1]/MM-105:
        raise ValueError('Board does not fit at 1:1 with drill schedule: use a deliberately larger paper design')
    x=(page[0]/MM-geom['width_mm'])/2; y=(page[1]/MM-geom['height_mm'])/2
    with tempfile.TemporaryDirectory(prefix='ha-diy-print-') as td:
        temp=Path(td); commands=[]
        commands.append(native_plot(cli,board,temp/'copper.svg','B.Cu'))
        copper=normalize_native_svg(temp/'copper.svg',geom)
        (out/'copper-native.svg').write_bytes(copper)
        stream,c,_=sheet_canvas(paper)
        # No text, outlines, dimension lines or assembly marks in the etch mask.
        # Four external crop corners sit 2 mm outside the nominal board outline.
        for dx,dy,sx,sy in ((0,0,-1,-1),(geom['width_mm'],0,1,-1),
                            (0,geom['height_mm'],-1,1),(geom['width_mm'],geom['height_mm'],1,1)):
            px,py=x+dx,y+dy
            line(c,px+sx*2,py,px+sx*4,py)
            line(c,px,py+sy*2,px,py+sy*4)
        (out/'toner-transfer.pdf').write_bytes(add_vector(finish(stream,c),copper,x,y,geom))
        commands.append(native_plot(cli,board,temp/'assembly.svg','F.Cu,F.Fab,F.SilkS,Edge.Cuts',2))
        # Assembly native SVG may not contain pilot circles when actual holes are
        # drawn as compound polygons. Copper has already verified all positions.
        root=ET.parse(temp/'assembly.svg').getroot()
        viewport=[float(v) for v in root.attrib['viewBox'].split()]
        if viewport[:2] != [0, 0] or any(abs(a-b)>.1 for a,b in zip(viewport[2:],(geom['width_mm'],geom['height_mm']))):
            raise ValueError('Native assembly plot crop differs from the board outline')
        root.set('width',f'{geom["width_mm"]}mm'); root.set('height',f'{geom["height_mm"]}mm')
        root.set('viewBox',f'0 0 {geom["width_mm"]} {geom["height_mm"]}')
        svg=ET.tostring(root)
        stream,c,_=sheet_canvas(paper)
        header(c,page,'Assembly - component / top view', 'Actual size. Wire links are physical insulated jumpers; a crossing is not an electrical junction.')
        ay=page[1]/MM-37-geom['height_mm']
        plan=json.loads(jumper_path.read_text()) if jumper_path else None
        if plan:
            c.saveState(); c.setStrokeColorRGB(.10,.37,.66)
            for wire in plan['wires']:
                for a,b in zip(wire['route_mm'],wire['route_mm'][1:]):
                    line(c,x+a[0],ay+geom['height_mm']-a[1],x+b[0],ay+geom['height_mm']-b[1],.18)
            for t in plan['terminals']:
                if t.get('kind')=='adapter_pin':
                    px=x+t['xy'][0];py=ay+geom['height_mm']-t['xy'][1]
                    c.circle(px*MM,py*MM,1.4*MM,stroke=1,fill=0)
                    text(c,px+2,py+2,t['ref'],7,True)
            c.restoreState()
        text(c,15,ay-9,'Square copper pads identify pin 1. Confirm breakout headers before fitting modules.',8)
        text(c,15,ay-15,'Regular leads: bottom soldering. E1 uses the raised-pin joint described on the last page.',8)
        text(c,15,ay-21,'Blue paths are insulated wire guides, not copper; use the following endpoint schedule.',8)
        assembly=add_vector(finish(stream,c),svg,x,ay,geom)
        if plan:
            if plan['wires']:
                assembly=append_pdf(assembly,wire_schedule_pdf(plan,geom,paper))
        (out/'assembly.pdf').write_bytes(assembly)
        stream,c,_=sheet_canvas(paper)
        header(c,page,'Copper inspection - bottom view', 'NOT AN ETCH MASK. Already mirrored to match the physical copper side after transfer.')
        text(c,15,ay-10,'Compare every etched path with this view; use page 1 for drill diameters and symbols.',8)
        text(c,15,ay-16,'Keep the designated top edge at the top when turning the board over.',8)
        inspection=add_vector(finish(stream,c),copper,x,ay,geom,mirror=True)
        (out/'drilling.pdf').write_bytes(append_pdf(drill_sheet(geom,paper),inspection))
        (out/'calibration.pdf').write_bytes(calibration(paper))
    (out/'drill-map.json').write_text(json.dumps(geom,indent=2)+'\n')
    files=['toner-transfer.pdf','assembly.pdf','drilling.pdf','calibration.pdf','copper-native.svg','drill-map.json']
    manifest={'schema_version':1,'design':'LP-D0','status':'print_geometry_checked_not_physically_fabricated',
      'paper':paper,'page_mm':[round(v/MM,6) for v in page], 'scale':1,
      'board':str(board.relative_to(ROOT)) if board.is_relative_to(ROOT) else board.name,
      'board_sha256':digest(board),'generator_sha256':digest(__file__),
      'kicad_version':subprocess.check_output([cli,'version'],text=True).strip(),
      'outline_mm':[geom['width_mm'],geom['height_mm']],
      'copper_layer':'B.Cu','native_plot_mirror':False,'transfer_contact':'toner against copper',
      'inspection_view':'bottom: x = board_width - component_x; y unchanged',
      'pilot_marks':'KiCad small drill marks; see drill map for actual diameters',
      'minimum_track_mm':geom['minimum_track_mm'],'hole_count':len(geom['holes']),
      'physical_gates':['printer calibration','toner transfer','etching','drilling','assembly','electrical test'],
      'outputs':{f:digest(out/f) for f in files}}
    from pypdf import PdfReader
    manifest['pdf_pages']={f:len(PdfReader(out/f).pages) for f in files if f.endswith('.pdf')}
    if jumper_path:
        manifest['jumper_schedule']={'path':str(jumper_path.relative_to(ROOT)), 'sha256':digest(jumper_path)}
        manifest['wire_count']=len(plan['wires'])
        manifest['dedicated_terminal_count']=sum(t.get('kind')!='adapter_pin' for t in plan['terminals'])
        manifest['raised_endpoint_count']=sum(t.get('kind')=='adapter_pin' for t in plan['terminals'])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def check(out, board=None):
    from pypdf import PdfReader
    manifest=json.loads((out/'manifest.json').read_text())
    if digest(__file__)!=manifest['generator_sha256']:
        raise ValueError('Print generator changed; regenerate outputs')
    if board and digest(board)!=manifest['board_sha256']:
        raise ValueError('Native board changed; regenerate outputs')
    for name,sha in manifest['outputs'].items():
        if digest(out/name)!=sha:
            raise ValueError(f'Output changed: {name}')
        if name.endswith('.pdf'):
            pdf=PdfReader(out/name)
            if len(pdf.pages)!=manifest['pdf_pages'][name]:
                raise ValueError(f'Unexpected page count: {name}')
            for page in pdf.pages:
                for actual,expected in zip((page.mediabox.width,page.mediabox.height),manifest['page_mm']):
                    if abs(float(actual)/MM-expected)>.001:
                        raise ValueError(f'Incorrect physical page size: {name}')
    schedule=manifest.get('jumper_schedule')
    if schedule and digest(ROOT/schedule['path'])!=schedule['sha256']:
        raise ValueError('Jumper schedule changed; regenerate outputs')
    return manifest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',type=Path,default=DEFAULT_BOARD)
    ap.add_argument('--output',type=Path,default=DEFAULT_OUT)
    ap.add_argument('--kicad-cli',default='kicad-cli')
    ap.add_argument('--paper',choices=('a4','letter'),default='a4')
    ap.add_argument('--jumper-schedule',type=Path)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    if args.check: result=check(args.output,args.board)
    else:
        result=compose(args.board.resolve(),args.output,args.kicad_cli,args.paper,args.jumper_schedule)
        check(args.output,args.board)
    print(f'LP-D0 print package checked: {result["outline_mm"]} mm, {result["hole_count"]} holes, {result["paper"]}, scale 1:1')


if __name__=='__main__': main()
