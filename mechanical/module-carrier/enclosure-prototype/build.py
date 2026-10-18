#!/usr/bin/env python3
"""Printable carrier-only prototype. Native XY + explicit provisional Z values."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('rail_source', HERE.parent/'rail-mount/build.py')
rail=importlib.util.module_from_spec(spec);spec.loader.exec_module(rail)
c=rail.csg

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(v):return json.dumps(v,indent=2)+'\n'

def geometry(s,p):
    n=p['nominal'];w=s['width'];h=s['height'];t=n['wall'];floor=n['floor']
    inner=(-n['side_margin'],-n['end_margin'],w+n['side_margin'],h+n['end_margin'])
    x0,y0,x1,y1=inner;ox=x0-t;oy=y0-t;W=x1-x0+2*t;H=y1-y0+2*t
    seat=floor+n['rear_cavity'];roof=seat+n['pcb_thickness']+n['front_cavity']
    bands=rail.nominal_contact_bands(s,json.loads((HERE.parent/'rail-mount/parameters.json').read_text()))
    for b in bands:b[1]=max(b[1],n['rail_start_y'])
    bolts=[(x0+3,y0+3),(x1-3,y0+3),(x0+3,y1-3),(x1-3,y1-3)]
    # Case walls never contact the PCB directly. Bridges end in legal edge lands.
    base=c.subtract(c.box(W,H,roof).move((ox,oy,0)),c.box(W-2*t,H-2*t,roof).move((x0,y0,floor)))
    additions=[];tops=[]
    for i,b in enumerate(bands):
        bx0=b[0] if i else x0;bx1=x1 if i else b[2];by0=b[1];by1=b[3]
        additions.append(c.box(bx1-bx0,by1-by0,n['rail_lip']).move((bx0,by0,seat-n['rail_lip'])))
        # A narrow locating wall limits nominal transverse travel; physical tolerance remains unqualified.
        rx=w+n['side_clearance'] if i else -n['side_clearance']-t
        additions.append(c.box(t,by1-by0,seat+n['rail_slot']).move((rx,by0,0)))
        tops.append(c.box(bx1-bx0,by1-by0,roof-(seat+n['rail_slot'])).move((bx0,by0,seat+n['rail_slot'])))
    hx,hy=s['supports']['H3']
    additions.append(c.cylinder(5,seat).move((hx,hy,0)))
    additions += [c.cylinder(8,roof).move((x,y,0)) for x,y in bolts]
    base=c.union(base,*additions)
    cuts=[c.cylinder(n['h3_clearance'],seat+1).move((hx,hy,-.5)),
          c.cylinder(5.8,2.1,sides=6).move((hx,hy,-.01))]
    cuts += [c.cylinder(n['closure_pilot'],11).move((x,y,roof-10)) for x,y in bolts]
    # Broad jack corridor: actual jack height + plug/latch envelope must be measured.
    cuts.append(c.box(30,t+1,seat-3).move((18,y1-.1,3)))
    # Harness side exit. No new connector or socket is introduced on the PCB.
    cuts.append(c.box(t+1,22,17).move((x1-.1,27,6)))
    # Pair of floor slots for an adjustable stop under the WIZ region.
    for x in [25,41]:cuts.append(c.box(3.2,18,floor+.2).move((x-1.6,45,-.1)))
    # Case-to-ceiling mounting holes are separate from H3.
    for x,y in [(x0+6,39),(x1-6,39)]:
        cuts.append(c.cylinder(4.4,floor+.2).move((x,y,-.1)))
        cuts.append(c.cylinder(9,roof).move((x,y,floor+.01)))
    # Small vertical vent slots avoid unsupported wide roof bridges.
    for yy in [4,11,57,64,71]:
        for xx in [ox-.1,x1-.1]:
            for z in [7,34]:cuts.append(c.box(t+.2,3,13).move((xx,yy,z)))
    base=c.subtract(base,*cuts)
    lid=c.union(c.box(W,H,n['lid']).move((ox,oy,roof)),*tops)
    lidcuts=[c.cylinder(n['closure_clearance'],n['lid']+1).move((x,y,roof-.1)) for x,y in bolts]
    for yy in [4,11,18,58,65,72]:
        lidcuts.append(c.box(37,3,n['lid']+.2).move((5,yy,roof-.1)))
    lid=c.subtract(lid,*lidcuts)
    # Trial stop: two slotted feet and a rounded-edge contact crossbar. Its position/height are assumptions.
    sh=n['jack_stop_height'];sy=n['jack_stop_contact_y']
    stop=c.union(c.box(22,10,2.4).move((22,sy-10,floor)),c.box(22,2.4,sh).move((22,sy-2.4,floor)))
    stop=c.subtract(stop,*[c.box(3.2,5,2.6).move((x-1.6,sy-9,floor-.1)) for x in [25,41]])
    # Separate flat-print ceiling frame preserves floor-hardware clearance.
    spacing=n['ceiling_spacing'];rim=12
    frame=c.subtract(c.box(W,H,spacing).move((ox,oy,-spacing)),
                     c.box(W-2*rim,H-2*rim,spacing+.2).move((ox+rim,oy+rim,-spacing-.1)),
                     *[c.cylinder(4.4,spacing+.2).move((x,39,-spacing-.1)) for x in [x0+6,x1-6]])
    antenna=rail.cad.transformed_rectangle(s['parts']['U2'],[4.83,-6.975,18.03,-1.575],canonical=True)
    top_antenna_y=min(point[1] for point in antenna)
    top_wall_gap=top_antenna_y-y0
    assert top_wall_gap>=15, 'H2 antenna end-wall setback is below 15 mm'
    assert spacing>=n['floor_hardware_max_projection']+1
    # Bed orientations: exterior faces on bed, all files use mm.
    oriented={'base':base.move((-ox,-oy,0)),
              'cover':lid.rotate((180,0,0)).move((-ox,y1+t,roof+n['lid'])),
              'jack-stop-trial':stop.move((-22,10-sy,-floor)),
              'ceiling-spacing-frame':frame.move((-ox,-oy,spacing))}
    return dict(nodes=oriented,assembled={'base':base,'cover':lid,'jack-stop-trial':stop,'ceiling-spacing-frame':frame},
                inner=inner,outer=(ox,oy,ox+W,oy+H),size=(W,H,roof+n['lid']),seat=seat,roof=roof,
                bands=bands,bolts=bolts,pcb_size=(w,h),installed_height=roof+n['lid']+spacing,antenna=antenna,h2_top_wall_gap=top_wall_gap)


def svg(s,p,g):
    ox,oy,x1,y1=g['outer'];W,H,Z=g['size'];sc=4.4;X=55;Y=160
    xy=lambda x,y:(X+(x-ox)*sc,Y+(y-oy)*sc)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1360" height="1000" viewBox="0 0 1360 1000">',
         '<style>text{font-family:Arial,sans-serif;fill:#e4edf5}.t{font-size:27px;font-weight:bold}.h{font-size:20px;font-weight:bold}.s{font-size:17px}.n{font-size:14px}.a{fill:#77dfbb}.w{fill:#ffc875}</style>',
         '<rect width="1360" height="1000" fill="#0c1926"/>',
         '<text x="36" y="48" class="t">MC1 carrier enclosure · complete printable prototype</text>',
         '<text x="36" y="83" class="s">Native 47.5 × 75 mm PCB · one H3 retainer · split edge support · dimensions in mm</text>',
         '<text x="36" y="116" class="s w">Trial shell and jack stop. No physical fit, loading, temperature or RF qualification.</text>']
    def rect(x,y,w,h,fill,stroke='#7896a9',dash=''):
        a,b=xy(x,y);out.append(f'<rect x="{a}" y="{b}" width="{w*sc}" height="{h*sc}" fill="{fill}" stroke="{stroke}" {dash}/>')
    rect(ox,oy,W,H,'#253e50');ix,iy,ix1,iy1=g['inner'];rect(ix,iy,ix1-ix,iy1-iy,'#0f2738')
    rect(0,0,s['width'],s['height'],'#17473f','#70d1ac')
    ax=min(p[0] for p in g['antenna']);ay=min(p[1] for p in g['antenna']);aw=max(p[0] for p in g['antenna'])-ax;ah=max(p[1] for p in g['antenna'])-ay
    rect(ax,ay,aw,ah,'#d7b45f','#ffdf87')
    for ref in ['U1','U2','U3','U4']:
        part=next(q for q in s['design']['parts'] if q['ref']==ref);a,b,cc,d=part['body_bounds_global_mm']
        rect(a,b,cc-a,d-b,'#294459' if ref=='U4' else '#377362','#8cafbd','stroke-dasharray="4 3"' if ref=='U4' else '')
        tx,ty=xy((a+cc)/2,(b+d)/2);out.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" class="n">{ref}{" rear" if ref=="U4" else " front"}</text>')
    for a,b,cc,d in g['bands']:rect(a,b,cc-a,d-b,'#ffc875')
    for x,y in g['bolts']:
        a,b=xy(x,y);out.append(f'<circle cx="{a}" cy="{b}" r="12" fill="#658195"/><circle cx="{a}" cy="{b}" r="5" fill="#0c1926"/>')
    hx,hy=s['supports']['H3'];a,b=xy(hx,hy);out.append(f'<circle cx="{a}" cy="{b}" r="10" fill="#ffd471"/><text x="{a-15}" y="{b-17}" class="n">H3</text>')
    rect(18,77,30,y1-77,'none','#69bcff','stroke-dasharray="5 4"')
    tx,ty=xy(33,90);out.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" class="n">RJ45</text>')
    out += [f'<text x="55" y="720" class="h a">{W:g} × {H:g} × {Z:g} mm shell</text>',
            f'<text x="55" y="750" class="s">Installed depth {g["installed_height"]:g} mm with 4 mm spacing frame.</text>',
            f'<text x="55" y="780" class="s">H2 antenna to upper end wall: {g["h2_top_wall_gap"]:.3f} mm.</text>']
    lines=[('Ceiling-side base', 'WIZ850io, male headers, diodes and resistors face the ceiling.'),
           ('Lower onto open seats', 'Fit back parts first, then front modules, then place the PCB.'),
           ('One H3 + retaining cover', 'Case screws hit hard stops. They must not compress the PCB.'),
           ('Jack insertion load', 'Trial stop must touch measured metal cage, never preload pins.'),
           ('External devices stay external', 'PoE splitter, buck, extra radios and sensors are not packed here.')]
    for i,(title,body) in enumerate(lines):
        yy=173+i*95;out += [f'<text x="520" y="{yy}" class="h a">{i+1}. {title}</text>',f'<text x="520" y="{yy+29}" class="s">{body}</text>']
    # Exaggerated section explains actual shell Z values without claiming module envelopes.
    out += ['<text x="520" y="683" class="h">Section through edge support (trial Z)</text>']
    xx=540;yy=915;k=3.3
    for z,hh,fill,label,label_y in [(-4,4,'#9f93d2','ceiling spacer',941),(0,2.4,'#63859b','ceiling base',913),(g['seat']-2.4,2.4,'#ffc875','lower seat',861),(g['seat'],1.6,'#70d1ac','PCB 1.6',833),(g['seat']+2,2.4,'#ffc875','upper lip',805),(g['roof'],2.4,'#63859b','room cover',733)]:
        out += [f'<rect x="{xx}" y="{yy-(z+hh)*k}" width="145" height="{hh*k}" fill="{fill}"/>',f'<path d="M685 {yy-(z+hh/2)*k} L703 {label_y-5}" stroke="#7896a9"/><text x="710" y="{label_y}" class="n">{label} · Z {z:g}</text>']
    out += ['<text x="990" y="739" class="n w">25 mm front cavity</text>', '<text x="990" y="830" class="n w">26 mm rear cavity</text>', '<text x="990" y="865" class="n">Both are assumptions.</text>', '<text x="36" y="967" class="s w">Print coupons first. Measure modules, wiring, rail play and actual jack contact before loading or ceiling installation.</text>', '</svg>']
    return '\n'.join(out)+'\n'


def render_preview(output,g):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    fig=plt.figure(figsize=(20,7),facecolor='#0c1926')
    names=['base','cover','jack-stop-trial','ceiling-spacing-frame'];colors=['#49b99b','#659ed5','#edb859','#9f93d2']
    for i,(name,color) in enumerate(zip(names,colors)):
        ax=fig.add_subplot(1,4,i+1,projection='3d',facecolor='#0c1926')
        mesh=c.mesh_of(g['nodes'][name]);poly=Poly3DCollection(mesh.triangles,facecolors=color,edgecolors='#153c48',linewidths=.09,shade=True,lightsource=matplotlib.colors.LightSource(azdeg=310,altdeg=50))
        ax.add_collection3d(poly);lo,hi=mesh.bounds
        ax.set_xlim(lo[0]-3,hi[0]+3);ax.set_ylim(lo[1]-3,hi[1]+3);ax.set_zlim(0,hi[2]+3)
        ax.set_box_aspect(hi-lo);ax.view_init(30,-60);ax.set_axis_off()
        ax.set_title(name.replace('-',' ').title(),fontsize=17,color='#ddf1ec',pad=15)
        ax.text2D(.1,.02,' × '.join(f'{n:.1f}' for n in hi-lo)+' mm',transform=ax.transAxes,color='#b3cbd9',fontsize=12)
    fig.suptitle('MC1 print parts • actual generated mesh geometry',color='#e4edf5',fontsize=22,y=.96)
    fig.text(.05,.075,'Shown in print orientation. Relative panel scales differ. Modules and hardware omitted.',color='#c0d3df',fontsize=13)
    fig.text(.05,.035,'Prototype only: verify measured fit, jack contact, rail retention, temperature and radio performance.',color='#ffc875',fontsize=12)
    fig.savefig(output/'print-parts.png',dpi=140,facecolor=fig.get_facecolor());plt.close(fig)


def generate(output,p):
    s=rail.native_source(ROOT/'hardware/module-carrier/cad');g=geometry(s,p);output.mkdir(parents=True,exist_ok=True)
    report={'status':p['status'],'units':'mm','native_source_sha256':s['source_sha256'],'portable_checker_sha256':sha(HERE.parent/'portable_check.py'),'generator_sha256':sha(Path(__file__)),'test_source_sha256':sha(HERE/'test_build.py'),'dependency_pins_sha256':sha(ROOT/'mechanical/requirements.txt'),'parameters_sha256':sha(HERE/'parameters.json'),'outer_dimensions_mm':g['size'],'installed_height_including_frame_mm':g['installed_height'],'h2_antenna_to_top_end_wall_mm':g['h2_top_wall_gap'],'pcb_rear_surface_z_mm':g['seat'],'lid_inside_z_mm':g['roof'],'rail_bands_mm':g['bands'],'physical_tests_performed':False,'parts':{},'excluded_devices':p['scope']}
    for name,node in g['nodes'].items():
        mesh=c.mesh_of(node);path=output/(name+'.stl');path.write_text(c.trimesh.exchange.stl.export_stl_ascii(mesh))
        actual=c.trimesh.load_mesh(path,process=True)
        assert actual.is_watertight and actual.is_winding_consistent and actual.volume>0
        assert len(actual.split(only_watertight=False))==1
        assert abs(actual.bounds[0][2])<.001
        (output/(name+'.scad')).write_text('// GENERATED from build.py and parameters.json. Trial dimensions, mm.\n'+node.scad+'\n')
        report['parts'][name]={'watertight':True,'single_solid':True,'volume_mm3':round(float(actual.volume),3),'bounds_mm':actual.bounds.round(4).tolist(),'sha256':sha(path)}
    # Emit true assembled coordinates for CAD review; not a single part to print.
    (output/'assembly.scad').write_text('// REVIEW ONLY: assembled mm coordinates. Do not print merged.\n'+'\n'.join(f'color("{color}") {{ {g["assembled"][name].scad} }}' for name,color in [('base','Teal'),('cover','SkyBlue'),('jack-stop-trial','Orange'),('ceiling-spacing-frame','Purple')])+'\n')
    (output/'enclosure.svg').write_text(svg(s,p,g))
    render_preview(output,g)
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MC1 printable enclosure prototype</title><style>body{margin:0;background:#0c1926;color:#e4edf5;font:18px system-ui}main{max-width:1400px;margin:auto;padding:24px}a{color:#79dcbc}img{width:100%;height:auto}p{line-height:1.6}</style><main><p><a href="../../../hardware/module-carrier/index.html">← MC1 carrier</a> · <a href="README.md">Assembly and release measurements</a> · <a href="parameters.json">Trial dimensions</a></p><img src="enclosure.svg" alt="MC1 prototype enclosure plan and section"><img src="print-parts.png" alt="Generated meshes in print orientation"><p>Printable carrier-only prototype: <a href="base.stl">base STL</a> · <a href="cover.stl">cover STL</a> · <a href="jack-stop-trial.stl">trial jack stop STL</a> · <a href="ceiling-spacing-frame.stl">ceiling frame STL</a> · <a href="assembly.scad">assembled CAD preview</a>. Read the assembly document before printing. Native XY is checked; module Z, cable bends, rail fit and jack restraint remain unmeasured.</p></main></html>\n')
    report['limitations']=['No measured module or mated-cable Z envelopes','No tested rail fit, case closure or loading','Jack stop contact is a parameterized placeholder until cage is measured','No RF/thermal/material qualification','No claim that ventilation rate is sufficient','No complete-system housing: external modules remain external']
    report['generated_sha256']={f.name:sha(f) for f in sorted(output.iterdir()) if f.suffix in ['.svg','.scad','.stl','.html','.png']}
    (output/'verification.json').write_text(dump(report));return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('--exact',action='store_true',help='Require byte-identical exports on the same platform');a=ap.parse_args();p=json.loads((HERE/'parameters.json').read_text())
    if a.exact and not a.check:ap.error('--exact requires --check')
    if a.check:
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);generate(d,p)
            rail.portable.check_outputs(HERE,d,c,exact=a.exact)
        print('Enclosure prototype outputs match source. Physical fit unqualified.')
    else:
        r=generate(HERE,p);print('Generated',len(r['parts']),'single-solid printable trial parts:',r['outer_dimensions_mm'])
if __name__=='__main__':main()
