#!/usr/bin/env python3
"""Native-derived split-rail study; STL output is limited to fit coupons."""
from pathlib import Path
import argparse
import hashlib
import html
import importlib.util
import json
import math
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

cad=load_module('rail_native_audit',ROOT/'hardware/module-carrier/audit_carrier.py')
csg=load_module('rail_csg',ROOT/'mechanical/build.py')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(value):return json.dumps(value,indent=2)+'\n'
def esc(value):return html.escape(str(value))

def native_source(directory):
    d=json.loads((directory/'design.json').read_text());board=directory/'mc1.kicad_pcb'
    parts=cad.read_board(board);outline=cad.board_outline(board);bounds=cad.board_bounds(board)
    w,h=bounds[2]-bounds[0],bounds[3]-bounds[1]
    assert math.isclose(w,d['board']['width_mm'],abs_tol=.001)
    assert math.isclose(h,d['board']['height_mm'],abs_tol=.001)
    supports={r:p['at'][:2] for r,p in parts.items() if r.startswith('H')}
    assert set(supports)=={'H3'},'This interface requires the reviewed single-H3 board'
    lands=d['mechanics']['enclosure_rail_lands']
    assert {x['id'] for x in lands}=={'left','right'}
    for land in lands:
        x1,y1,x2,y2=land['bounds_mm']
        assert 0<=x1<x2<=w and 0<=y1<y2<=h
        assert (x1==0 if land['id']=='left' else x2==w)
    return dict(design=d,parts=parts,outline=outline,width=w,height=h,lands=lands,supports=supports,
                source_sha256={'mc1.kicad_pcb':sha(board),'design.json':sha(directory/'design.json')})


def coupon_node(gap,p,index):
    """A coupon only: 1.2 mm engagement, printed on its outer wall."""
    q=p['coupon'];length=q['length_mm'];wall=q['wall_mm'];base=q['base_mm'];top=q['upper_lip_mm']
    width=q['handling_base_width_mm'];depth=q['engagement_mm'];height=base+gap+top
    assert gap>0 and width>wall+depth and length>=12
    node=csg.union(csg.box(width,length,base),csg.box(wall,length,height),
                   csg.box(wall+depth,length,top).move((0,0,base+gap)))
    cuts=[csg.box(1.05,1.2,base+.04).move((width-1,2+i*3,-.02)) for i in range(index)]
    node=csg.subtract(node,*cuts)
    # Outer wall lies on the bed. The narrow upper lip needs no bridged roof.
    return node.rotate((0,-90,0)).move((height,0,0))


def nominal_contact_bands(s,p):
    budget=p['interface']['trial_edge_displacement_budget_mm'];dx=budget['x'];dy=budget['y']
    assert dx>=0 and dy>=0
    assert 0<=p['interface']['trial_side_clearance_per_edge_mm']<=dx, 'Side clearance exceeds the assumed edge displacement budget'
    result=[]
    for land in sorted(s['lands'],key=lambda x:x['id']):
        x1,y1,x2,y2=land['bounds_mm']
        assert 2*dx<x2-x1 and 2*dy<y2-y1, 'Displacement budget would remove bearing engagement'
        result.append([x1+(dx if land['id']=='right' else 0),y1+dy,
                       x2-(dx if land['id']=='left' else 0),y2-dy])
    return result


def scad_interface(s,p):
    bands=nominal_contact_bands(s,p)
    q=p['interface']
    return f'''// SPLIT-RAIL INTERFACE STUDY, NOT A COMPLETE PRINTABLE ENCLOSURE.
// Coordinates match native PCB front view; local Z=0 is the lower ledge surface.
// Factory module heights, lid depth, jack stop and case attachments are UNKNOWN.
// Only the fit-coupon STL files are intended as printing trials.
board_width = {s['width']};
board_height = {s['height']};
// Inset from CAD maximum bands by the trial displacement budget.
// A measured case must bound movement of EVERY edge point, including rotation.
contact_bands = {bands};
h3 = {s['supports']['H3']};
pcb_preview_thickness = {p['pcb_nominal_thickness_mm']}; // NOMINAL, not measured
slot_height = {q['preview_slot_height_mm']}; // TRIAL ONLY: select after coupons
side_clearance = {q['trial_side_clearance_per_edge_mm']}; // per edge, trial only
wall = {q['wall_mm']};
lip = {q['lip_thickness_mm']};
lid_lift = {q['exploded_lid_lift_mm']}; // 0 for a closed interface preview
show_pcb = true;
mode = "exploded"; // "lower", "upper", "closed", "exploded"
assert(slot_height > pcb_preview_thickness);
module lower_rail(b, right=false) {{
  x0 = right ? b[0] : -side_clearance-wall;
  x1 = right ? board_width+side_clearance+wall : b[2];
  wx = right ? board_width+side_clearance : -side_clearance-wall;
  union() {{
    translate([x0,b[1],-lip]) cube([x1-x0,b[3]-b[1],lip]);
    translate([wx,b[1],-lip]) cube([wall,b[3]-b[1],lip+slot_height/2]);
  }}
}}
module upper_rail(b, right=false) {{
  x0 = right ? b[0] : -side_clearance-wall;
  x1 = right ? board_width+side_clearance+wall : b[2];
  wx = right ? board_width+side_clearance : -side_clearance-wall;
  union() {{
    translate([x0,b[1],slot_height]) cube([x1-x0,b[3]-b[1],lip]);
    translate([wx,b[1],slot_height/2]) cube([wall,b[3]-b[1],lip+slot_height/2]);
  }}
}}
module lower_interfaces() {{for(i=[0:1]) lower_rail(contact_bands[i],i==1);}}
module upper_interfaces() {{for(i=[0:1]) upper_rail(contact_bands[i],i==1);}}
// These separate rail volumes must be integrated into measured case halves.
// The renderer deliberately does not bridge antenna zones or invent screw bosses.
if(mode=="lower") color("Teal") lower_interfaces();
if(mode=="upper") color("SkyBlue") upper_interfaces();
if(mode=="closed" || mode=="exploded") {{
  color("Teal") lower_interfaces();
  translate([0,0,mode=="exploded" ? lid_lift : 0]) color("SkyBlue") upper_interfaces();
  if(show_pcb) %difference() {{
    cube([board_width,board_height,pcb_preview_thickness]);
    translate([h3[0],h3[1],-1]) cylinder(d=2.7,h=pcb_preview_thickness+2,$fn=48);
  }}
}}
'''


def svg_start(title,subtitle,width=1320,height=920):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
      '<style>text{font-family:Arial,sans-serif;fill:#dce8f2}.title{font-size:28px;font-weight:bold}.sub{font-size:17px;fill:#b5c9d9}.label{font-size:16px}.small{font-size:13px}.strong{font-weight:bold}.green{fill:#91e1bb}.warn{fill:#f6c765}</style>',
      f'<rect width="{width}" height="{height}" fill="#0e1b29"/>',
      f'<text x="36" y="46" class="title">{esc(title)}</text>',
      f'<text x="36" y="80" class="sub">{esc(subtitle)}</text>']
def txt(out,x,y,value,cls='label',anchor='start'):
    out.append(f'<text x="{x:g}" y="{y:g}" class="{cls}" text-anchor="{anchor}">{esc(value)}</text>')
def poly(out,points,attrs):
    out.append('<polygon points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in points)+f'" {attrs}/>')
def rect(out,x,y,w,h,attrs):out.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" {attrs}/>')

def plan_svg(s):
    out=svg_start('One PCB retainer. Distributed support along selected edges.',
                  'Native front view: contact bands on both faces; case walls and full enclosure height are not defined.')
    scale=7;ox=83;oy=165
    point=lambda p:(ox+p[0]*scale,oy+p[1]*scale)
    poly(out,list(map(point,s['outline'])),'fill="#193e3b" stroke="#80d3be" stroke-width="2"')
    for r in ['U1','U2','U3']:
        coords=cad.courtyard_polygon(s['parts'][r]);poly(out,list(map(point,coords)),'fill="#355260" fill-opacity="0.7" stroke="#91abbc" stroke-dasharray="4 4"')
        center=[sum(v[i] for v in coords)/len(coords) for i in (0,1)]
        txt(out,*point(center),r+' front','label','middle')
    wiz=cad.transformed_rectangle(s['parts']['U4'],[-1.34,-6.4,21.66,18.6],canonical=True)
    poly(out,list(map(point,wiz)),'fill="#1b4774" fill-opacity="0.7" stroke="#73b5ff" stroke-dasharray="6 3"')
    txt(out,*point((33,63)),'WIZ rear','label','middle')
    for land in s['lands']:
        x1,y1,x2,y2=land['bounds_mm'];rect(out,*point((x1,y1)),(x2-x1)*scale,(y2-y1)*scale,'fill="#f6c765" stroke="#fff0ba"')
    x,y=point(s['supports']['H3']);out.append(f'<circle cx="{x}" cy="{y}" r="17.5" fill="#172f42" stroke="#91e1bb" stroke-width="2"/>')
    out.append(f'<circle cx="{x}" cy="{y}" r="9.45" fill="#0e1b29" stroke="#91e1bb"/>');txt(out,x,y-25,'H3 only','label green','middle')
    txt(out,83,738,f'{s["width"]:g} × {s["height"]:g} mm PCB; two copper layers','label strong')
    txt(out,535,156,'Defined contact regions','label strong')
    for i,land in enumerate(sorted(s['lands'],key=lambda x:x['id'])):
        x1,y1,x2,y2=land['bounds_mm'];yy=198+i*95
        txt(out,535,yy,land['id'].capitalize()+f': x {x1:g}…{x2:g}; y {y1:g}…{y2:g} mm','label green')
        txt(out,535,yy+29,f'{x2-x1:g} mm bearing width × {y2-y1:g} mm length','sub')
    for yy,line in zip([420,450,480,535,565,595,650,680],[
        'Yellow bands are MAXIMUM reach from the actual board edge.',
        'Nominal lips are inset for the trial ±0.2 mm XY motion budget.',
        'Budget includes rotation / print error; measure to establish it.',
        'Lower into an open frame; never push populated PCB through rails.',
        'H3 retains the PCB; case fasteners and locating stops are separate.',
        'The rail outside wall still needs a physical / RF clearance review.',
        'WIZ needs a measured jack stop / cradle and cable strain relief.',
        'Edge grooves alone do not bypass the WIZ header solder joints.']):txt(out,535,yy,line,'sub')
    txt(out,36,804,'Source PCB SHA-256 '+s['source_sha256']['mc1.kicad_pcb'][:24]+'…','small')
    txt(out,36,844,'Geometry proposal, not a verified enclosure. Measure solder growth, board thickness and module heights before release.','label warn')
    return '\n'.join(out)+ '\n</svg>\n'


def section_svg(s,p):
    q=p['interface'];left=next(x['bounds_mm'] for x in s['lands'] if x['id']=='left');maxdepth=left[2]-left[0];depth=nominal_contact_bands(s,p)[0][2]
    gap=q['preview_slot_height_mm'];t=p['pcb_nominal_thickness_mm'];wall=q['wall_mm'];lip=q['lip_thickness_mm'];side=q['trial_side_clearance_per_edge_mm']
    out=svg_start('Split edge support: fit is measured, never zero-clearance.',
                  'Illustrative left-edge section. Dimensions shown are trial settings; the actual PCB thickness is unknown.',height=1020)
    k=70;edge=390;base_y=595
    def box(x,z,w,h,color):rect(out,edge+x*k,base_y-(z+h)*k,w*k,h*k,f'fill="{color}" stroke="#b3d6dd" stroke-width="1.5"')
    box(-side-wall,-lip,wall+side+depth,lip,'#216b65');box(-side-wall,0,wall,gap/2,'#216b65')
    box(-side-wall,gap,wall+side+depth,lip,'#326489');box(-side-wall,gap/2,wall,gap/2,'#326489')
    box(0,0,3.2,t,'#d8b55b')
    txt(out,370,165,'Second case half: removable retaining lip','label','middle')
    txt(out,420,815,'First case half: support ledge','label','middle')
    txt(out,645,520,'PCB','label strong')
    # Dimension h is the clear space between opposing support surfaces.
    x=676;y0=base_y-gap*k;y1=base_y
    out.append(f'<path d="M{x} {y0}V{y1}m-7 0h14M{x-7} {y0}h14" stroke="#91e1bb" fill="none"/>')
    txt(out,697,(y0+y1)/2,f'h = {gap:g} mm','label green')
    txt(out,810,184,'Local interface only','label strong')
    for yy,line in zip([226,258,290,342,374,406,458,490,522,574,606,638],[
        f'Illustrated nominal PCB: {t:g} mm.',
        f'Illustrated slot: {gap:g} mm, not a selected fit.',
        f'Nominal free height: {gap-t:.2f} mm total.',
        f'Nominal lip here: {depth:g} mm; max {maxdepth:g}.',
        f'Side clearance trial: {side:g} mm per edge.',
        'Reserve XY motion; do not assume H3 locates it.',
        '1.6 mm ±10% gives 1.44…1.76 mm.',
        'At 1.76 mm, trial 1.8 / 2.0 / 2.2 slots',
        'leave only 0.04 / 0.24 / 0.44 mm total.',
        'Printer error, finish and warpage consume this.',
        'Measure a coupon with the actual board edge.',
        'No material or fit has been qualified.']):txt(out,810,yy,line,'sub')
    txt(out,36,881,'Front and rear component cavities: UNKNOWN. Model each from measured tallest features and connector / cable envelopes.','label warn')
    txt(out,36,920,'The 2.4 mm lip / wall and 0.2 mm side-clearance values are editable examples, not strength or tolerance guarantees.','sub')
    txt(out,36,959,'Case attachment bosses, lid depth and the H3 support stack are deliberately not invented in this section.','sub')
    return '\n'.join(out)+'\n</svg>\n'


def sequence_svg():
    out=svg_start('Assembly: complete the electronics, then load the open support frame.',
                  'All rear parts are soldered before the three front controllers. Enclosure closure never requires sliding the populated PCB.',height=760)
    cards=[('1','Assemble the carrier',['Program loose modules; perform H2 preparation.','Fit all 13 rear parts, including WIZ.','Solder, trim and inspect from the front.','Then fit and solder the 3 front controllers.']),
           ('2','Measure and calibrate',['Measure actual PCB edge thickness and bow.','Print 1.8 / 2.0 / 2.2 mm gap coupons.','Use the same material, orientation and settings.','Confirm fit using bare offcut / unobstructed edge.']),
           ('3','Lower into open ledges',['Leave the second case half completely removed.','Lower the populated PCB normal to its plane.','Contact only the reviewed edge bands.','Check solder tails, antennas and cables.']),
           ('4','Retain and close',['Retain H3 without bowing or crushing the PCB.','Close upper lips against case hard stops.','Secure case halves independently of the PCB.','Fit the jack stop and strain relief; test loads.'])]
    for i,(number,title,lines) in enumerate(cards):
        x=36+i*320;rect(out,x,138,298,458,'fill="#173246" stroke="#476678" rx="12"')
        out.append(f'<circle cx="{x+40}" cy="184" r="23" fill="#216b65"/>');txt(out,x+40,191,number,'label strong','middle')
        txt(out,x+18,246,title,'label strong')
        for j,line in enumerate(lines):
            # Explicit wrap at a word boundary for predictable SVG text layout.
            words=line.split();rows=['']
            for word in words:
                if len(rows[-1])+len(word)+1>32:rows.append(word)
                else:rows[-1]=(rows[-1]+' '+word).strip()
            for n,row in enumerate(rows):txt(out,x+18,295+j*65+n*23,row,'small')
    txt(out,36,645,'No final shell or overall height is supplied: those require the actual front/rear module, connector and cable measurements.','label warn')
    txt(out,36,694,'Fit coupons establish local clearance only. They do not establish rail stiffness, creep life, thermal performance or RF compatibility.','sub')
    return '\n'.join(out)+'\n</svg>\n'


def comparison_svg(s):
    previous=HERE/'baseline/mc1.kicad_pcb';parts=cad.read_board(previous);outline=cad.board_outline(previous)
    out=svg_start('Mounting successor: four point supports → edge support plus one retainer.',
                  'Equal-scale native plan outlines. The mechanical load path changes; reduced PCB area is not a strength test.',height=920)
    for i,(poly_pts,pt,label) in enumerate([(outline,parts,'Historical: 51 × 75 mm'),(s['outline'],s['parts'],'Current: 47.5 × 75 mm')]):
        ox=110+i*655;oy=180;k=6
        point=lambda p:(ox+p[0]*k,oy+p[1]*k)
        txt(out,60+i*655,136,label,'label strong')
        poly(out,list(map(point,poly_pts)),'fill="#193e3b" stroke="#80d3be" stroke-width="2"')
        for r in ['U1','U2','U3']:
            poly(out,list(map(point,cad.courtyard_polygon(pt[r]))),'fill="#355260" fill-opacity="0.55" stroke="#91abbc" stroke-dasharray="4 4"')
        poly(out,list(map(point,cad.transformed_rectangle(pt['U4'],[-1.34,-6.4,21.66,18.6],canonical=True))),'fill="#1b4774" fill-opacity="0.65" stroke="#73b5ff" stroke-dasharray="6 3"')
        for r,part in pt.items():
            if not r.startswith('H'):continue
            x,y=point(part['at'][:2]);out.append(f'<circle cx="{x}" cy="{y}" r="15" fill="#0e1b29" stroke="#91e1bb" stroke-width="2"/>');txt(out,x,y-23,r,'small','middle')
        if i:
            for land in s['lands']:
                x1,y1,x2,y2=land['bounds_mm'];rect(out,*point((x1,y1)),(x2-x1)*k,(y2-y1)*k,'fill="#f6c765" stroke="#fff0ba"')
        txt(out,60+i*655,692,'4 PCB mounting points; no edge support' if not i else 'H3 retention; two discontinuous edge lands','sub')
    old_bounds=cad.board_bounds(previous);old_area=(old_bounds[2]-old_bounds[0])*(old_bounds[3]-old_bounds[1]);area=s['width']*s['height']
    txt(out,36,755,f'PCB area {old_area:g} → {area:g} mm² ({100*(area/old_area-1):+.2f}%); still two copper layers.','label green')
    txt(out,36,804,'Printed rails replace three PCB supports; they do not remove the need to fasten the enclosure itself.','label warn')
    txt(out,36,848,'An independent jack stop / cradle and cable strain relief are still required to protect WIZ solder joints.','sub')
    return '\n'.join(out)+'\n</svg>\n'



def index_html(s,p):
    figures=[('rail-mount.svg','Contact plan'),('rail-section.svg','Measured fit'),
             ('assembly-sequence.svg','Assembly sequence'),('mounting-comparison.svg','Mounting history')]
    images=''.join(f'<section id="figure-{i}"><h2>{title}</h2><img src="{name}" alt="{title}"></section>' for i,(name,title) in enumerate(figures))
    coupon_links=''.join(f'<li><a href="fit-gap-{gap:.1f}.stl">{gap:.1f} mm nominal gap</a> — {i} identifying edge notch(es)</li>'.replace(f'{gap:.1f}.stl',f'{gap:.1f}'.replace('.','p')+'.stl') for i,gap in enumerate(p['trial_slot_heights_mm'],1))
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MC1 split-rail mounting study</title><style>
:root{{font-family:system-ui,sans-serif;color:#dce8f2;background:#0e1b29}}*{{box-sizing:border-box}}body{{margin:0 auto;max-width:1400px;padding:28px}}a{{color:#94d5ff}}h1{{font-size:clamp(28px,4vw,48px);margin:.2em 0}}h2{{font-size:25px}}p,li{{line-height:1.6}}.lead{{font-size:20px;max-width:1000px;color:#c0d2df}}.note{{border-left:4px solid #f6c765;padding:14px 20px;background:#173246}}.facts{{display:flex;flex-wrap:wrap;gap:18px;margin:25px 0}}.fact{{background:#193e3b;border:1px solid #467568;border-radius:12px;padding:18px;flex:1;min-width:220px}}.fact strong{{display:block;font-size:27px;margin-bottom:6px}}section{{margin:35px 0}}img{{width:100%;height:auto;border:1px solid #385064;border-radius:12px}}code{{overflow-wrap:anywhere}}.links{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:25px}}footer{{border-top:1px solid #385064;padding-top:25px;color:#b5c9d9}}
</style><main><p>MC1 · mechanical fit study</p><h1>Open the frame. Lower the board. Close the retaining lips.</h1>
<p class="lead">Selected edge lands provide distributed support; H3 is the only PCB retainer. The two case halves stay separate while the populated board is loaded. No sliding through a narrow groove.</p>
<div class="facts"><div class="fact"><strong>{s['width']:g} × {s['height']:g} mm</strong>native PCB plan</div><div class="fact"><strong>H3 only</strong>case attachments remain separate</div><div class="fact"><strong>3 fit coupons</strong>1.8 / 2.0 / 2.2 mm trial gaps</div></div>
<p class="note"><strong>This is not a complete or qualified enclosure.</strong> Actual board thickness, module heights, final case depth, fasteners and jack restraint are not measured. STL downloads below are small fit coupons only.</p>
{images}
<section><h2>Print the local fit test first</h2><div class="links"><div><ul>{coupon_links}</ul><p>Print on the outer wall in the supplied orientation. Try a bare board offcut or unobstructed edge. Do not force the populated carrier into a coupon. Fit results depend on the printer, material and settings.</p></div><div><ul><li><a href="rail-interface.scad">Parametric split-rail interface SCAD</a></li><li><a href="fit-coupons.scad">Coupon SCAD</a></li><li><a href="parameters.json">Editable assumptions</a></li><li><a href="mesh-report.json">Coupon geometry checks</a></li><li><a href="verification.json">Source and artifact verification</a></li><li><a href="README.md">Detailed source notes and reproduction</a></li></ul></div></div></section>
<section><h2>Before this becomes an enclosure</h2><p>The ±0.2 mm XY movement budget is an example, not a demonstrated bound. Nominal lips are inset so that their worst allowed reach stays inside the reviewed contact lands. The example side clearance consumes the full X budget, leaving no extra allowance for error or rotation. Measure actual clearance and excursion; both remain unset. Account for translation, rotation, board tolerance and print error at every contact point; H3 alone does not locate the board with zero play.</p><p>The source keeps actual thickness and final height unset. Measure both component sides and connectors, establish case stops and attachment points, and check antenna clearance. A separate jack stop or cradle plus strain relief must carry cable loads away from WIZ header joints.</p></section>
<footer><p>Native revision: <code>{esc(s['design']['layout_revision'])}</code><br>PCB SHA-256: <code>{s['source_sha256']['mc1.kicad_pcb']}</code></p><p>Primary guidance: <a href="https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135">Prusa fit and printing considerations</a> · <a href="https://jlcpcb.com/capabilities/pcb-capabilities/">JLCPCB thickness tolerance</a>.</p></footer></main></html>'''

def generate(directory, output, parameters):
    output.mkdir(parents=True,exist_ok=True);s=native_source(directory);p=parameters
    native={'layout_revision':s['design']['layout_revision'],'source_sha256':s['source_sha256'],
            'board_width_mm':s['width'],'board_height_mm':s['height'],'contact_bands':s['lands'],
            'retainer':s['supports'],'nominal_lip_bands_mm':nominal_contact_bands(s,p),'trial_edge_displacement_budget_mm':p['interface']['trial_edge_displacement_budget_mm'],'status':'unqualified_interface_and_fit_coupon_study',
            'pcb_actual_thickness_mm':p['pcb_actual_thickness_mm'],'case_internal_height_mm':p['case_internal_height_mm']}
    (output/'native-inputs.json').write_text(dump(native))
    (output/'rail-interface.scad').write_text(scad_interface(s,p))
    (output/'rail-mount.svg').write_text(plan_svg(s));(output/'rail-section.svg').write_text(section_svg(s,p))
    (output/'assembly-sequence.svg').write_text(sequence_svg());(output/'mounting-comparison.svg').write_text(comparison_svg(s))
    (output/'index.html').write_text(index_html(s,p))
    report={'status':'fit_coupons_only_not_full_enclosure','units':'mm','native_source':s['source_sha256'],
            'parameters':p,'generator_sha256':sha(Path(__file__)),'csg_helper_sha256':sha(ROOT/'mechanical/build.py'),
            'parts':{},'not_tested':['printed fit','board thickness and bow','module / cable heights','rail strength and creep','RF or thermal behavior','jack insertion load']}
    scad=['// FIT COUPONS ONLY. Print on outer wall in the supplied orientation. Units mm.\n// 1 / 2 / 3 edge notches correspond to 1.8 / 2.0 / 2.2 mm nominal gaps.']
    for i,gap in enumerate(p['trial_slot_heights_mm'],1):
        name=f'fit-gap-{gap:.1f}'.replace('.','p');node=coupon_node(gap,p,i);mesh=csg.mesh_of(node)
        stl=output/(name+'.stl');stl.write_text(csg.trimesh.exchange.stl.export_stl_ascii(mesh))
        actual=csg.trimesh.load_mesh(stl,process=True)
        assert actual.is_watertight and actual.is_winding_consistent and actual.volume>0
        assert len(actual.split(only_watertight=False))==1
        report['parts'][name]={'nominal_slot_mm':gap,'identification_notches':i,'watertight':True,'connected_bodies':1,
          'volume_mm3':round(float(actual.volume),6),'bounds_mm':actual.bounds.round(5).tolist(),'sha256':sha(stl)}
        scad.append(f'// Gap {gap:g} mm; identification notches: {i}\ntranslate([{(i-1)*10},0,0]) {{ {node.scad} }}')
    (output/'fit-coupons.scad').write_text('\n'.join(scad)+'\n')
    (output/'mesh-report.json').write_text(dump(report))
    verification={
      'status':'digital_geometry_checked_physical_fit_unqualified',
      'native_source_sha256':s['source_sha256'],
      'layout_revision':s['design']['layout_revision'],
      'generator_sha256':sha(Path(__file__)),
      'parameters_sha256':sha(HERE/'parameters.json'),
      'unit_test_source_sha256':sha(HERE/'test_build.py'),
      'cad_reader_sha256':sha(ROOT/'hardware/module-carrier/audit_carrier.py'),
      'csg_helper_sha256':sha(ROOT/'mechanical/build.py'),
      'dependency_pins_sha256':sha(ROOT/'mechanical/requirements.txt'),
      'historical_native_sha256':sha(HERE/'baseline/mc1.kicad_pcb'),
      'native_checks':{'only_pcb_retainer':'H3','dimensions_match_ledger':True,
                       'contact_lands_within_outline':True},
      'modeled_movement':{'status':'assumed_not_measured',
                         'pointwise_displacement_budget_mm':p['interface']['trial_edge_displacement_budget_mm'],
                         'nominal_lip_bands_mm':nominal_contact_bands(s,p),
                         'includes_translation_rotation_and_manufacturing_error':True},
      'mesh_checks':{'coupon_count':len(report['parts']), 'all_watertight':True,
                     'all_consistently_oriented':True,'all_single_positive_volume_solids':True},
      'unit_test_command':"python -m unittest discover -s mechanical/module-carrier/rail-mount -p 'test_*.py'",
      'physical_tests_performed':False,
      'complete_enclosure_supplied':False,
      'not_tested':report['not_tested']+['actual in-plane displacement including rotation'],
      'generated_sha256':{f.name:sha(f) for f in sorted(output.iterdir())
                          if f.name in ['native-inputs.json','rail-interface.scad','rail-mount.svg','rail-section.svg',
                                        'assembly-sequence.svg','mounting-comparison.svg','index.html','fit-coupons.scad',
                                        'mesh-report.json'] or f.name.startswith('fit-gap-') and f.suffix=='.stl'}
    }
    (output/'verification.json').write_text(dump(verification));return report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cad',type=Path,default=ROOT/'hardware/module-carrier/cad')
    ap.add_argument('--output',type=Path,default=HERE);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    params=json.loads((HERE/'parameters.json').read_text())
    if args.check:
        with tempfile.TemporaryDirectory(prefix='mc1-rail-check-') as td:
            temp=Path(td);generate(args.cad,temp,params)
            for expected in temp.iterdir():
                actual=args.output/expected.name
                if not actual.exists() or actual.read_bytes()!=expected.read_bytes():
                    raise SystemExit('Stale or missing rail artifact: '+str(actual))
        print('Rail study source, illustrations and coupon meshes match.')
    else:
        report=generate(args.cad,args.output,params);print('Generated',len(report['parts']),'watertight fit coupons; no enclosure STL.')

if __name__=='__main__':main()
