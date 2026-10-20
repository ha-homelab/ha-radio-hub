#!/usr/bin/env python3
"""MC2 carrier shell with three fixed-wall SMA ports; trial dimensions in mm."""
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

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

c = load('mc2_csg', ROOT / 'mechanical/build.py')
cad = load('mc2_native_reader', ROOT / 'hardware/module-carrier/audit_carrier.py')
portable = load('mc2_portable', HERE.parent / 'portable_check.py')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source(p):
    directory = ROOT / p['source_directory']
    design = json.loads((directory / 'design.json').read_text())
    board_files = list(directory.glob('*.kicad_pcb'))
    assert len(board_files) == 1, 'Exactly one native carrier board is required'
    board = board_files[0]
    parts = cad.read_board(board)
    bb = cad.board_bounds(board)
    width, length = bb[2] - bb[0], bb[3] - bb[1]
    # Native KiCad footprint order is not geometry; keep the CSG union order stable.
    holes = dict(sorted(((ref, part['at'][:2]) for ref, part in parts.items()
                         if ref.startswith('H')), key=lambda item: tuple(item[1]), reverse=True))
    assert len(holes) >= 3, 'MC2 requires a native three-or-more-point PCB mounting pattern'
    return dict(width=width, length=length, holes=holes, parts=parts, design=design,
                hashes={board.name: sha(board), 'design.json': sha(directory / 'design.json')})

# Recessed lettering avoids separate loose text solids in the STL.
GLYPHS = {
    'Z':['11111','00001','00010','00100','01000','10000','11111'],
    'I':['111','010','010','010','010','010','111'],
    'G':['01110','10001','10000','10111','10001','10001','01110'],
    'B':['11110','10001','10001','11110','10001','10001','11110'],
    'E':['11111','10000','10000','11110','10000','10000','11111'],
    'T':['11111','00100','00100','00100','00100','00100','00100'],
    'H':['10001','10001','10001','11111','10001','10001','10001'],
    'R':['11110','10001','10001','11110','10100','10010','10001'],
    'A':['01110','10001','10001','11111','10001','10001','10001'],
    'D':['11110','10001','10001','10001','10001','10001','11110'],
    'L':['10000','10000','10000','10000','10000','10000','11111'],
}

def lettering(word, center_x, z, depth=.6, pixel=.65):
    width = sum(len(GLYPHS[v][0]) + 1 for v in word) * pixel - pixel
    x = center_x - width / 2
    cells = []
    for char in word:
        glyph = GLYPHS[char]
        for row, line in enumerate(glyph):
            for column, filled in enumerate(line):
                if filled == '1':
                    cells.append(c.box(pixel+.01, depth+.1, pixel+.01).move((x+column*pixel, -.1, z+(6-row)*pixel)))
        x += (len(glyph[0])+1)*pixel
    return c.union(*cells)

def d_hole(diameter, flat_dimension, thickness):
    """Axis -Y; top flat is flat_dimension above the circle's lowest edge."""
    r = diameter/2
    disk = c.cylinder(diameter, thickness).rotate((90, 0, 0))
    return c.subtract(disk, c.box(diameter+2, thickness+2, diameter+2).move((-r-1, -thickness-1, flat_dimension-r)))

def rounded_coax_path(points,radius,straight_minimum):
    """Round each 3-D guide corner with a true circular, radius-limited arc.

    Ten-degree chords stay within 0.026 mm of a 6.8 mm arc; the 1.5 mm
    collision sweep exceeds the physical cable radius by over 0.9 mm.
    """
    corners=[];tangents=[0.0]*len(points)
    for i in range(1,len(points)-1):
        u=[(points[i][k]-points[i-1][k])/math.dist(points[i],points[i-1]) for k in range(3)]
        v=[(points[i+1][k]-points[i][k])/math.dist(points[i+1],points[i]) for k in range(3)]
        cosine=max(-1,min(1,sum(a*b for a,b in zip(u,v))));angle=math.acos(cosine)
        assert angle<math.pi-1e-6,'Coax reversal cannot satisfy its bend radius'
        tangent=radius*math.tan(angle/2);tangents[i]=tangent
        corners.append((i,u,v,angle,tangent))
    for i in range(len(points)-1):
        assert tangents[i]+tangents[i+1]<=math.dist(points[i],points[i+1]),'Coax bend radius requires more straight length'
    lead=math.dist(points[0],points[1])-tangents[1]
    assert lead>=straight_minimum,'Coax bend reaches the bulkhead heatshrink'
    result=[points[0]];arcs=[]
    for i,u,v,angle,tangent in corners:
        start=[points[i][k]-u[k]*tangent for k in range(3)]
        if angle<1e-6:
            result.append(points[i]);continue
        normal=[(v[k]-u[k]*math.cos(angle))/math.sin(angle) for k in range(3)]
        center=[start[k]+normal[k]*radius for k in range(3)]
        steps=max(1,math.ceil(math.degrees(angle)/10))
        for j in range(steps+1):
            a=angle*j/steps
            # The SVG uses these coordinates verbatim. Quantize far below
            # physical tolerances so different libm implementations reproduce
            # the same source drawing rather than disagreeing in the last bit.
            result.append([round(center[k]-normal[k]*radius*math.cos(a)+u[k]*radius*math.sin(a),9) for k in range(3)])
        arcs.append({'center_mm':center,'radius_mm':radius,'angle_degrees':math.degrees(angle)})
    result.append(points[-1])
    return result,arcs,lead



def geometry(s, p):
    q = p['case']; r = p['rf']
    W,H,Z = q['width'],q['length'],q['height']; t=q['wall']; f=q['floor']; lt=q['lid']
    bx,by=q['board_origin_xy']; seat=q['board_seat_z']
    assert bx>=t+8 and by>=t+8 and bx+s['width']<=W-t-8 and by+s['length']<=H-t-8, 'Native PCB exceeds trial shell clearance'
    assert 0 < seat-f and seat+q['board_thickness'] < Z-10
    # These are the CAD's component-side XY reservations, not measured heights.
    # Keep the visible host envelope tied to the selected electrical revision.
    modules=[]
    for part in s['design']['parts']:
        if not part['ref'].startswith('U') or not part['body_bounds_global_mm']:
            continue
        x0,y0,x1,y1=part['body_bounds_global_mm']
        bounds=[bx+x0,by+y0,bx+x1,by+y1]
        assert t < bounds[0] < bounds[2] < W-t and t < bounds[1] < bounds[3] < H-t, 'Native module XY reservation exceeds shell interior'
        modules.append({'ref':part['ref'],'model':part['model'],'bounds_case_mm':bounds})
    pcb_holes={ref:(bx+xy[0],by+xy[1]) for ref,xy in s['holes'].items()}
    corridor=s['design']['mechanics']['rj45']['service_corridor_global_mm']
    rearcenter=bx+(corridor[0]+corridor[2])/2
    rearwidth=corridor[2]-corridor[0]+8
    routes=[]
    for port in r['ports']:
        endpoint=s['design']['mechanics']['rf_ports'][port['module_ref']]['estimated_xy_mm']
        start=[port['center'][0],t,port['center'][2]]
        support=[port['strap_xy'][0],port['strap_xy'][1],port['center'][2]]
        assert support[0] == start[0] and support[1]-start[1] >= r['internal_straight_reservation'], 'Bulkhead straight lead-in reservation is too short'
        end=[bx+endpoint[0],by+endpoint[1],r['module_connector_z_trial']]
        guide_length=math.dist(start,support)+math.dist(support,end)
        assert r['cable_length_minimum_budget'] == r['cable_length_trial']-r['cable_length_shortfall_allowance'], 'Cable minimum budget omits the shortfall allowance'
        assert guide_length+30 <= r['cable_length_minimum_budget'], 'Trial cable lacks 30 mm connector/slack allowance'
        smooth,arcs,lead=rounded_coax_path([start,support,end],r['cable_bend_radius_trial'],r['unbent_connector_allowance'])
        routes.append({'radio':port['label'],'module_ref':port['module_ref'],'points_mm':[start,support,end],
                       'polyline_guide_length_mm':round(guide_length,3),'cable_length_trial_mm':r['cable_length_trial'],'cable_length_minimum_budget_mm':r['cable_length_minimum_budget'],'minimum_bend_radius_mm':r['cable_bend_radius_trial'],'rounded_points_mm':smooth,'bend_arcs':arcs,'straight_bulkhead_lead_mm':lead,
                       'status':'XY endpoint estimated by hardware layout; all Z and formed bend paths unmeasured'})
    corners=[(8,8),(W-8,8),(8,H-8),(W-8,H-8)]
    # The antenna wall remains attached to the base when the lid is removed.
    base=c.subtract(c.box(W,H,Z),c.box(W-2*t,H-2*t,Z).move((t,t,f)))
    base=c.union(base,*[c.cylinder(9,Z).move((x,y,0)) for x,y in corners],
                 *[c.cylinder(7,seat).move((x,y,0)) for x,y in pcb_holes.values()])
    holes=[c.cylinder(q['closure_pilot'],12).move((x,y,Z-11)) for x,y in corners]
    holes += [c.cylinder(q['pcb_screw_hole'],seat+.2).move((x,y,-.1)) for x,y in pcb_holes.values()]
    # M2.5 nylon nuts install from below; spacing frame leaves room for their projection.
    holes += [c.cylinder(5.8,2.4,sides=6).move((x,y,-.1)) for x,y in pcb_holes.values()]
    ceiling=[(12,H/2),(W-12,H/2)]
    holes += [c.cylinder(q['mounting_screw_hole'],f+.2).move((x,y,-.1)) for x,y in ceiling]
    # Split low-voltage exit at the rear. It opens to the rim, so harnesses need not pass through a plug-sized hole.
    holes.append(c.box(rearwidth,t+.2,Z-8).move((rearcenter-rearwidth/2,H-t-.1,8)))
    holes += [c.cylinder(3.3,f+.2).move((rearcenter+dx,H-12,-.1)) for dx in [-19,19]]
    # Vent openings are kept off the RF wall and out of the rear cable bay.
    for y in range(43,int(H)-20,10):
        for x in [-.1,W-t-.1]:
            holes.append(c.box(t+.2,3,15).move((x,y,26)))
    straps=[]
    for port in r['ports']:
        x,y,z=port['center']
        assert y==0 and 18<=x<=W-18 and 20<=z<=Z-12
        holes.append(c.cylinder(r['nominal_hole_diameter']+r['print_allowance'],t+.2).rotate((90,0,0)).move((x,t+.1,z)))
        holes.append(lettering(port['label'],x,z-12))
        sx,sy=port['strap_xy']
        # Paired towers support a soft loop at bulkhead height without loading the AMC jack.
        pillar=c.box(12,6,z-f-2).move((sx-6,sy-3,f))
        loop=c.box(8,6.2,2).move((sx-4,sy-3.1,z-5))
        straps.append(c.subtract(pillar,loop))
    base=c.subtract(c.union(base,*straps),*holes)
    lid=c.box(W,H,lt)
    lid=c.subtract(lid,*[c.cylinder(q['closure_hole'],lt+.2).move((x,y,-.1)) for x,y in corners])
    # Separate base cable bar uses ties through its slots; no guessed hole pattern on a module.
    clamp=c.box(46,12,3)
    clamp=c.subtract(clamp,*[c.box(3,8,3.2).move((x,2,-.1)) for x in [14,29]],
                     *[c.cylinder(3.3,3.2).move((x,6,-.1)) for x in [4,42]])
    spacing=q['ceiling_spacing']
    frame=c.subtract(c.box(W,H,spacing),c.box(W-32,H-32,spacing+.2).move((16,16,-.1)),
                     *[c.cylinder(q['mounting_screw_hole'],spacing+.2).move((x,y,-.1)) for x,y in ceiling],
                     *[c.cylinder(8,spacing+.2).move((rearcenter+dx,H-12,-.1)) for dx in [-19,19]])
    # Test this small coupon first, with the purchased pigtail and actual print settings.
    coupon=c.box(45,24,t)
    for i,allowance in enumerate([0.0,.2,.4]):
        cut=c.cylinder(r['nominal_hole_diameter']+allowance,t+.2).move((8+14*i,12,-.1))
        coupon=c.subtract(coupon,cut)
        for j in range(i+1): coupon=c.subtract(coupon,c.box(.8,3,.6).move((5+14*i+j*1.4,3,t-.5)))
    distances=[math.dist(a['center'],b['center']) for i,a in enumerate(r['ports']) for b in r['ports'][i+1:]]
    assert min(distances)>=r['minimum_center_spacing_trial'], 'Ports do not meet initial mechanical spacing target'
    return dict(nodes={'base':base,'cover':lid,'ceiling-spacing-frame':frame,'cable-bar':clamp,'bulkhead-fit-coupon':coupon},
                assembled={'base':base,'cover':lid.move((0,0,Z)),'ceiling-spacing-frame':frame.move((0,0,-spacing)), 'cable-bar':clamp.move((rearcenter-23,H-18,f))},
                pcb_holes=pcb_holes,ceiling=ceiling,distances=distances,routes=routes,rearcenter=rearcenter,rear_bay=[rearcenter-rearwidth/2,rearcenter+rearwidth/2],modules=modules)


def svg(s,p,g):
    q=p['case'];r=p['rf'];sc=3.5;ox=65;oy=240
    a=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1040" viewBox="0 0 1400 1040">',
       '<style>text{font-family:Arial,sans-serif;fill:#e2edf3}.h{font-size:27px;font-weight:bold}.s{font-size:18px}.n{font-size:15px}.warning{fill:#ffc670}</style>',
       '<rect width="1400" height="1040" fill="#0d1b29"/>',
       '<text x="40" y="48" class="h">MC2 · three external antennas, one fixed antenna wall</text>',
       '<text x="40" y="83" class="s">Carrier-only printable shell. 65 mm port spacing is a starting geometry, not a range specification.</text>',
       '<text x="40" y="115" class="s warning">Native PCB XY + provisional component heights, coax routes and purchased-part fit. Not production-qualified.</text>',
       f'<rect x="{ox}" y="{oy}" width="{q["width"]*sc}" height="{q["length"]*sc}" rx="8" fill="#284556" stroke="#a5c8d6"/>']
    bx,by=q['board_origin_xy']; x=ox+bx*sc;y=oy+by*sc
    a.append(f'<rect x="{x}" y="{y}" width="{s["width"]*sc}" height="{s["length"]*sc}" fill="#17483f" stroke="#78d8af"/>')
    a.append(f'<text x="{x}" y="{y-12}" class="s">MC2 carrier {s["width"]:g} × {s["length"]:g} mm · native module XY</text>')
    for module in g['modules']:
        x0,y0,x1,y1=module['bounds_case_mm']
        a.append(f'<rect x="{ox+x0*sc}" y="{oy+y0*sc}" width="{(x1-x0)*sc}" height="{(y1-y0)*sc}" fill="#223749" stroke="#9ab9cb"/>')
        a.append(f'<text x="{ox+x0*sc+5}" y="{oy+y0*sc+18}" class="n">{html.escape(module["ref"])}</text>')
    host=next(module['model'] for module in g['modules'] if module['ref']=='U1')
    a.append(f'<text x="40" y="150" class="s">Host U1: {html.escape(host)} · component heights remain unmeasured.</text>')
    for ref,(hx,hy) in g['pcb_holes'].items():
        a.append(f'<circle cx="{ox+hx*sc}" cy="{oy+hy*sc}" r="9" fill="#a2cabd"/><text x="{ox+hx*sc+12}" y="{oy+hy*sc+4}" class="n">{ref}</text>')
    for port,col in zip(r['ports'],['#d8a0ff','#7ac1ff','#73dfb4']):
        px,_,pz=port['center'];sx,sy=port['strap_xy'];xx=ox+px*sc
        a += [f'<rect x="{xx-14}" y="{oy-50}" width="28" height="56" rx="7" fill="{col}"/>',
              f'<text x="{xx}" y="{oy-68}" text-anchor="middle" class="s">{port["label"]}</text>',
              f'<path d="M{xx} {oy+6} L{xx} {oy+sy*sc}" stroke="{col}" stroke-width="5" fill="none"/>',
              f'<rect x="{ox+(sx-6)*sc}" y="{oy+(sy-3)*sc}" width="{12*sc}" height="{6*sc}" fill="{col}"/>']
    for route,col in zip(g['routes'],['#d8a0ff','#7ac1ff','#73dfb4']):
        a0,a1,a2=route['points_mm']
        a.append(f'<path d="M{ox+a1[0]*sc} {oy+a1[1]*sc} Q{ox+a1[0]*sc} {oy+(a1[1]+15)*sc} {ox+a2[0]*sc} {oy+a2[1]*sc}" stroke="{col}" stroke-width="3" stroke-dasharray="6 5" fill="none"/>')
        a.append(f'<circle cx="{ox+a2[0]*sc}" cy="{oy+a2[1]*sc}" r="6" fill="{col}"/>')
    notes=[('Enclosure',f'{q["width"]:g} × {q["length"]:g} × {q["height"]+q["lid"]:g} mm; +{q["ceiling_spacing"]:g} mm ceiling spacer.'),
           ('Three independent 50 Ω paths','SMA female → AMC / U.FL-compatible cable → one radio.'),
           ('Fixed-wall ports','Lid lifts without pulling the three coax leads.'),
           ('Round-hole and tool access','6.6 mm project clearance + 0.2 mm trial print allowance.'),
           ('Strain relief','Soft loops at three towers. Do not crush micro-coax.'),
           ('Cable length','150 mm nominal; 144 mm project budget including 6 mm shortfall.'),
           ('Antenna orientation','83.1 mm candidate: keep bodies outside, parallel and clear.'),
           ('Low-voltage rear bay','Separate splitter supplies power; this RJ45 is data-only.'),
           ('Not installed here','PoE converter, Z-Wave, sub-GHz radio and sensors.')]
    for i,(title,body) in enumerate(notes):
        yy=180+i*68
        a += [f'<text x="790" y="{yy}" class="s">{title}</text>',f'<text x="790" y="{yy+25}" class="n">{body}</text>']
    a += [f'<text x="{ox}" y="{oy+q["length"]*sc+35}" class="s">Rear split cable opening · restraint required before connection to modules</text>',
          '<text x="40" y="865" class="h">First print: bulkhead-fit-coupon.stl</text>',
          '<text x="40" y="901" class="s">Three round-hole tolerances (left to right): nominal, +0.2 mm, +0.4 mm. Select from the real connector.</text>',
          '<text x="40" y="939" class="s">Verify nut engagement, anti-rotation, module clearance and formed cable routes before printing the full shell.</text>',
          '<text x="40" y="987" class="s warning">No coverage promise for 1,000 ft². Test all radios concurrently, closed case, at the central ceiling position.</text>','</svg>']
    return '\n'.join(a)+'\n'


def render_meshes(shapes, width=1300, height=760):
    """Orthographic software Z-buffer keeps large case faces from hiding antennas."""
    import numpy as np
    from matplotlib.colors import to_rgb
    camera=np.array([1.,-1.6,1.2]);camera/=np.linalg.norm(camera)
    right=np.cross(np.array([0.,0.,1.]),camera);right/=np.linalg.norm(right)
    up=np.cross(camera,right)
    light=np.array([-1.,-2.,3.]);light/=np.linalg.norm(light)
    vertices=[];colors=[]
    for node,color in shapes:
        mesh=c.mesh_of(node)
        vertices.extend(mesh.triangles)
        rgb=np.array(to_rgb(color))
        shade=.38+.62*np.maximum(mesh.face_normals@light,0)
        colors.extend(shade[:,None]*rgb)
    tri=np.asarray(vertices);colors=np.asarray(colors)
    screen=np.stack((tri@right,-tri@up,tri@camera),axis=-1)
    lo=screen[:,:,:2].min(axis=(0,1));hi=screen[:,:,:2].max(axis=(0,1))
    scale=min((width-80)/(hi[0]-lo[0]),(height-70)/(hi[1]-lo[1]))
    screen[:,:,:2]=(screen[:,:,:2]-(lo+hi)/2)*scale+[width/2,height/2]
    image=np.zeros((height,width,3),dtype=np.uint8);image[:]=[13,27,41]
    depth=np.full((height,width),-np.inf)
    for t,color in zip(screen,colors):
        x0=max(0,int(np.floor(t[:,0].min())));x1=min(width-1,int(np.ceil(t[:,0].max())))
        y0=max(0,int(np.floor(t[:,1].min())));y1=min(height-1,int(np.ceil(t[:,1].max())))
        if x1<x0 or y1<y0:continue
        a,b,d=t;den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
        if abs(den)<1e-9:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        u=((b[1]-d[1])*(xx-d[0])+(d[0]-b[0])*(yy-d[1]))/den
        v=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/den
        w=1-u-v;z=u*a[2]+v*b[2]+w*d[2]
        block=depth[y0:y1+1,x0:x1+1];mask=(u>=-1e-7)&(v>=-1e-7)&(w>=-1e-7)&(z>block)
        block[mask]=z[mask];image[y0:y1+1,x0:x1+1][mask]=np.clip(color*255,0,255).astype(np.uint8)
    return image

def preview(output,g,p):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(18,7),facecolor='#0d1b29')
    for i,(name,color) in enumerate([('base','#5dc4ad'),('cover','#7fb7e3'),('bulkhead-fit-coupon','#ebc171')]):
        ax=fig.add_subplot(1,3,i+1,facecolor='#0d1b29');ax.set_axis_off()
        ax.imshow(render_meshes([(g['nodes'][name],color)],width=760,height=700))
        ax.set_title(name.replace('-',' ').title(),color='#e2edf3',fontsize=18)
    fig.suptitle('MC2 generated printable geometry · antennas and electronics omitted',fontsize=20,color='#e2edf3')
    fig.text(.04,.08,'Separate printed parts. Relative panel scales differ. Print and measure the round-hole coupon first.',color='#c3d5dd',fontsize=14)
    fig.text(.04,.035,'Prototype: no test print, material strength, module fit, thermal or RF qualification.',color='#ffc670',fontsize=14)
    fig.savefig(output/'print-parts.png',dpi=130,facecolor=fig.get_facecolor());plt.close(fig)
    fig=plt.figure(figsize=(12,9),facecolor='#0d1b29');ax=fig.add_axes([.02,.16,.96,.72]);ax.set_axis_off()
    shapes=[(g['assembled']['base'],'#62b5ac'),(g['assembled']['cover'],'#a5d2df')]
    for port in p['rf']['ports']:
        x,y,z=port['center'];length=p['rf']['antenna_length_nominal'];diameter=p['rf']['antenna_diameter_nominal']
        shapes.append((c.cylinder(diameter,length).move((x,-12,z)),'#51616e'))
        shapes.append((c.cylinder(6,12).rotate((90,0,0)).move((x,0,z)),'#dbb55e'))
    ax.imshow(render_meshes(shapes))
    fig.suptitle('MC2 · three independent external antenna ports',fontsize=22,color='#e2edf3',y=.94)
    fig.text(.06,.12,'From left to right on antenna wall: BLE  ·  THREAD  ·  ZIGBEE',color='#dcecf3',fontsize=14)
    fig.text(.06,.08,'Case: actual generated mesh. Antennas: simplified 83.1 × Ø10 mm envelopes.',color='#c3d5dd',fontsize=12)
    fig.text(.06,.045,'Hinge sweep, purchased-part fit and RF performance still require physical testing.',color='#ffc670',fontsize=12)
    fig.savefig(output/'assembly-preview.png',dpi=130,facecolor=fig.get_facecolor());plt.close(fig)


def generate(output,p):
    s=source(p);g=geometry(s,p);output.mkdir(parents=True,exist_ok=True)
    report={'revision':p['revision'],'status':p['status'],'units':'mm','native_source_sha256':s['hashes'],
            'generator_sha256':sha(Path(__file__)),'test_source_sha256':sha(HERE/'test_build.py'),'parameters_sha256':sha(HERE/'parameters.json'),
            'portable_checker_sha256':sha(HERE.parent/'portable_check.py'),'dependency_pins_sha256':sha(ROOT/'mechanical/requirements.txt'),
            'outer_dimensions_mm':[p['case']['width'],p['case']['length'],p['case']['height']+p['case']['lid']],
            'port_center_distances_mm':g['distances'],'rf_route_guides':g['routes'],'module_xy_reservations':g['modules'],'native_layout_revision':s['design']['revision'],'rear_bay_x_mm':g['rear_bay'],'native_pcb_holes':s['holes'],'physical_tests_performed':False,'parts':{},'scope':p['scope']}
    for name,node in g['nodes'].items():
        mesh=c.mesh_of(node);path=output/(name+'.stl');path.write_text(c.trimesh.exchange.stl.export_stl_ascii(mesh));actual=c.trimesh.load_mesh(path,process=True)
        assert actual.is_watertight and actual.is_winding_consistent and actual.volume>0 and len(actual.split())==1
        assert abs(actual.bounds[0][2])<.001
        (output/(name+'.scad')).write_text('// GENERATED. MC2 trial geometry in mm.\n'+node.scad+'\n')
        report['parts'][name]={'watertight':True,'single_solid':True,'volume_mm3':round(float(actual.volume),3),'bounds_mm':actual.bounds.round(4).tolist(),'sha256':sha(path)}
    (output/'assembly.scad').write_text('// REVIEW ONLY: assembled coordinates. Not a part to print.\n'+'\n'.join(f'color("{color}") {{ {g["assembled"][name].scad} }}' for name,color in [('base','Teal'),('cover','SkyBlue'),('ceiling-spacing-frame','Purple'),('cable-bar','Orange')])+'\n')
    (output/'enclosure.svg').write_text(svg(s,p,g));preview(output,g,p)
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MC2 external-antenna shell prototype</title><style>body{margin:0;background:#0d1b29;color:#e2edf3;font:18px system-ui}main{max-width:1400px;margin:auto;padding:24px}a{color:#77ddbb}img{width:100%;height:auto}p{line-height:1.6}</style><main><h1>MC2 external-antenna enclosure</h1><p><a href="README.md">Assembly and limits</a> · <a href="parameters.json">Trial dimensions</a> · <a href="verification.json">Digital checks</a></p><img src="assembly-preview.png" alt="Generated MC2 shell with simplified external antenna envelopes"><img src="enclosure.svg" alt="MC2 native carrier shell with separate Zigbee, Thread and BLE SMA ports"><img src="print-parts.png" alt="Actual generated base, lid and round-hole coupon meshes"><p>Print files: <a href="base.stl">base</a> · <a href="cover.stl">cover</a> · <a href="ceiling-spacing-frame.stl">spacing frame</a> · <a href="cable-bar.stl">cable bar</a> · <a href="bulkhead-fit-coupon.stl">first-print fit coupon</a>. All dimensions in mm. This is an engineering prototype with unmeasured fit and no RF range guarantee.</p></main></html>\n')
    report['generated_sha256']={f.name:sha(f) for f in sorted(output.iterdir()) if f.suffix in ['.svg','.scad','.stl','.html','.png']}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--exact',action='store_true');args=parser.parse_args()
    if args.exact and not args.check:parser.error('--exact requires --check')
    p=json.loads((HERE/'parameters.json').read_text())
    if args.check:
        with tempfile.TemporaryDirectory() as td:
            output=Path(td);generate(output,p);portable.check_outputs(HERE,output,c,exact=args.exact)
        print('MC2 shell outputs match native source and trial parameters. Physical fit unqualified.')
    else:
        r=generate(HERE,p);print('Generated',len(r['parts']),'MC2 trial parts:',r['outer_dimensions_mm'])
if __name__=='__main__':main()
