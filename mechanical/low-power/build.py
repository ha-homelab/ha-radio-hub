#!/usr/bin/env python3
"""Generate and check a low-power concept enclosure, never a production PCB.

Reuses the existing CAD boolean/export helpers without changing the older model.
All geometry is in mm, while glTF exports use metres.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
HELPER = ROOT.parent / 'build.py'
spec = importlib.util.spec_from_file_location('hub_cad_geometry', HELPER)
cad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cad)
box, cylinder, union, subtract = cad.box, cad.cylinder, cad.union, cad.subtract
EPS = 0.02


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cuboid(item):
    return box(*item['size']).move(item['origin'])


def mount_points(p):
    b = p['carrier']
    return [(b['origin'][0] + x, b['origin'][1] + y) for x, y in b['mount_centres']]


def radar_mounts(p):
    r = p['radar_holder']; x, y, _ = r['origin']; w, d, _ = r['size']; i = r['mount_inset']
    return [(x + xx, y + yy) for xx in (i, w-i) for yy in (i, d-i)]


def models(p):
    c = p['case']; b = p['carrier']; r = p['radar_holder']
    w, d, total = c['width'], c['depth'], c['height']
    wall, floor, lid = c['wall'], c['floor'], c['lid']; h = total-lid
    off = c['boss_offset']; corners = [(x, y) for x in (off, w-off) for y in (off, d-off)]
    assert 0 < c['radar_skin'] < lid
    assert wall >= 2 and floor >= 2 and c['insert_depth'] < r['boss_height']
    assert np.isclose(r['origin'][2]+r['size'][2], h-r['boss_height']), 'Radar holder must meet lid bosses'
    base = subtract(box(w,d,h), box(w-2*wall,d-2*wall,h).move((wall,wall,floor)))
    base = union(base, *[cylinder(c['boss_diameter'], h).move((x,y,0)) for x,y in corners],
                 *[cylinder(8, b['origin'][2]).move((x,y,0)) for x,y in mount_points(p)])
    cuts = [cylinder(c['insert_pilot'],c['insert_depth']+EPS).move((x,y,z-c['insert_depth']))
            for points,z in ((corners,h),(mount_points(p),b['origin'][2])) for x,y in points]
    px,pz,pw,ph = c['poe_opening']
    cuts.append(box(pw,wall+2*EPS,ph).move((px,d-wall-EPS,pz)))
    cuts.append(cylinder(c['bme_hole'],wall+2*EPS).rotate((0,90,0)).move((-EPS,c['bme_exit_y'],c['bme_exit_z'])))
    # Straight 3 mm bridges on the long sides. Keep front BME exit clear.
    for y in range(55,int(d)-20,8):
        for x in (-EPS,w-wall-EPS):
            cuts.append(box(wall+2*EPS,3,8).move((x,y,h-13)))
    base = subtract(base,*cuts)
    # Lid's local Z=0 is its outward face; assembly uses a rigid Y-axis flip.
    gap = c['lid_gap']; inset = wall+gap
    lip = subtract(box(w-2*inset,d-2*inset,2).move((inset,inset,lid)),
                   box(w-2*(inset+1.6),d-2*(inset+1.6),2+2*EPS).move((inset+1.6,inset+1.6,lid-EPS)),
                   *[cylinder(c['boss_diameter']+1,2+2*EPS).move((x,y,lid-EPS)) for x,y in corners])
    # Reflect X coordinates because this printable lid is rotated for assembly.
    mounts = [(w-x,y) for x,y in radar_mounts(p)]
    top = union(box(w,d,lid),lip,*[cylinder(8,r['boss_height']).move((x,y,lid)) for x,y in mounts])
    lcuts = [cylinder(c['m3_clearance'],lid+2*EPS).move((x,y,-EPS)) for x,y in corners]
    lcuts += [cylinder(c['insert_pilot'],c['insert_depth']+EPS).move((x,y,lid+r['boss_height']-c['insert_depth'])) for x,y in mounts]
    rx,ry,rw,rd = c['radar_window']
    lcuts.append(box(rw,rd,lid-c['radar_skin']+EPS).move((w-rx-rw,ry,c['radar_skin'])))
    # Vents in rear region, away from the radar's experimental window.
    for x in range(38,int(w)-35,9):
        lcuts.append(box(3,18,lid+2*EPS).move((x,d-40,-EPS)))
    top = subtract(top,*lcuts)
    blank = subtract(box(*b['size']),*[cylinder(c['m3_clearance'],b['size'][2]+2*EPS).move((x,y,-EPS)) for x,y in b['mount_centres']])
    holder = box(*r['size']); rw,rd,rt = r['size']; inset = r['mount_inset']
    hcuts = [cylinder(c['m3_clearance'],rt+2*EPS).move((x,y,-EPS)) for x in (inset,rw-inset) for y in (inset,rd-inset)]
    # Universal tie slots only. Never pass a tie across radar antenna patches.
    for x in (10,rw-12):
        for y in (8,rd-11):
            hcuts.append(box(2,3,rt+2*EPS).move((x,y,-EPS)))
    holder = subtract(holder,*hcuts)
    coupon = subtract(box(72,20,8),
                      *[cylinder(v,8+2*EPS).move((8+10*i,10,-EPS)) for i,v in enumerate((3.2,3.4,3.6))],
                      *[cylinder(v,6+EPS).move((44+10*i,10,2)) for i,v in enumerate((4.0,4.2,4.4))])
    return {'mockup_base':base,'mockup_lid':top,'carrier_fit_blank':blank,'radar_holder':holder,'fit_coupon':coupon}


def poses(p):
    c = p['case']
    return {'mockup_base':((0,0,0),(0,0,0)),
            'mockup_lid':((0,180,0),(c['width'],0,c['height'])),
            'carrier_fit_blank':((0,0,0),p['carrier']['origin']),
            'radar_holder':((0,0,0),p['radar_holder']['origin'])}


def validate_layout(p,nodes):
    c=p['case']; w,d,h=c['width'],c['depth'],c['height']-c['lid']
    parts={k:nodes[k].solid.rotate(rot).translate(offset) for k,(rot,offset) in poses(p).items()}
    components={x['id']:cuboid(x).solid for x in p['components']}
    result={'printed_part_intersections_mm3':{},'component_intersections_mm3':{},'minimum_component_gap_mm':{},
            'antenna_reservations':'Declared spatial reservations only; NOT manufacturer-certified keep-outs or RF isolation',
            'physical_fit':'NOT TESTED','pcb_fabrication':'NOT READY'}
    for group,items in (('printed_part_intersections_mm3',parts),('component_intersections_mm3',components)):
        for (a,sa),(b,sb) in itertools.combinations(items.items(),2):
            volume=float((sa^sb).volume()); result[group][a+'/'+b]=round(volume,6)
            if volume > 0.001: raise ValueError(f'{a}/{b}: volume interference {volume:g} mm3')
    # Include screw heads above the carrier: a clear PCB hole alone is insufficient.
    head_d,head_h=p['carrier']['fastener_head_envelope']
    heads=[cylinder(head_d,head_h).move((x,y,p['carrier']['origin'][2]+p['carrier']['size'][2])).solid for x,y in mount_points(p)]
    for name,component in components.items():
        if any(float((component^head).volume()) > 0.001 for head in heads):
            raise ValueError(f'{name}: intersects a carrier fastener head reservation')
    result['carrier_fastener_head_envelope_mm']=[head_d,head_h]
    for comp in p['components']:
        origin=np.array(comp['origin']); end=origin+comp['size']
        if min(origin[0]-c['wall'],origin[1]-c['wall'],origin[2]-c['floor'],w-c['wall']-end[0],d-c['wall']-end[1],h-end[2]) < -0.001:
            raise ValueError(f'{comp["id"]}: outside available case envelope')
        for name,part in parts.items():
            volume=float((components[comp['id']]^part).volume())
            if volume > 0.001: raise ValueError(f'{comp["id"]}/{name}: volume interference {volume:g} mm3')
        result['minimum_component_gap_mm'][comp['id']]={'to_nominal_lid':round(float(h-end[2]),3)}
    for keep in p['antenna_reservations']:
        if any(float((cuboid(keep).solid^head).volume()) > 0.001 for head in heads):
            raise ValueError(f'{keep["owner"]} antenna reservation intersects a fastener head')
        for name,component in components.items():
            if name==keep['owner']:continue
            volume=float((cuboid(keep).solid^component).volume())
            if volume > 0.001:raise ValueError(f'{keep["owner"]} antenna reservation intersects {name}')
    for item in p['service_reservations']:
        solid=cuboid(item).solid
        for name,part in parts.items():
            if float((solid^part).volume()) > 0.001:raise ValueError(f'{item["id"]}: blocked by {name}')
        for name,component in components.items():
            if float((solid^component).volume()) > 0.001:raise ValueError(f'{item["id"]}: blocked by {name}')
    # Numeric design-center distances are geometric facts, not RF performance.
    centers={x['owner']:np.array(x['origin'][:2])+np.array(x['size'][:2])/2 for x in p['antenna_reservations']}
    result['antenna_reservation_centre_distances_mm']={a+'/'+b:round(float(np.linalg.norm(ca-cb)),2) for (a,ca),(b,cb) in itertools.combinations(centers.items(),2)}
    result['checked_component_count']=len(components)
    result['service_reservations_checked']=[x['id'] for x in p['service_reservations']]
    result['unchecked']=['Real modules, header heights, plugs and cable bends','RF coexistence, antenna matching and actual PCB copper keep-outs',
        'Creepage, electrical isolation and PCB routing','FDM tolerances, material strength and screw engagement',
        'Radar performance through 1.2 mm plastic','PoE efficiency, thermal soak and module ambient temperature',
        'BME cable electrical stability and temperature error','Mounting for actual components; layout blank is not a populated PCB']
    return result


COLORS={'radio':'#318f99','digital':'#4675a1','power':'#bd7930','connector':'#666782','radar':'#be5890'}


def preview(p,meshes,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    c=p['case']; b=p['carrier']; w,d=c['width'],c['depth']
    fig,ax=plt.subplots(figsize=(13,8.5)); fig.patch.set_facecolor('#f6f8fa'); ax.set_facecolor('#ffffff')
    ax.add_patch(Rectangle((0,0),w,d,fill=False,lw=2.5,ec='#203b51'))
    ax.add_patch(Rectangle(b['origin'][:2],*b['size'][:2],fc='#dfebdc',ec='#6c8664',lw=1.5))
    for comp in p['components']:
        x,y,_=comp['origin']; cw,cd,_=comp['size']
        if comp['kind']=='radar':continue
        ax.add_patch(Rectangle((x,y),cw,cd,fc=COLORS[comp['kind']],ec='#ffffff',alpha=.82))
        ax.text(x+cw/2,y+cd/2,comp['id'],ha='center',va='center',color='white',fontsize=10,weight='bold')
    for keep in p['antenna_reservations']:
        ax.add_patch(Rectangle(keep['origin'][:2],*keep['size'][:2],fill=False,ec='#aa3449',hatch='///',lw=1.3))
    for service in p['service_reservations']:
        ax.add_patch(Rectangle(service['origin'][:2],*service['size'][:2],fill=False,ec='#56718a',ls='--',lw=1.3))
    radar=next(x for x in p['components'] if x['id']=='LD2450')
    ax.add_patch(Rectangle(radar['origin'][:2],*radar['size'][:2],fill=False,ec=COLORS['radar'],lw=2,ls='--'))
    radar_center=np.array(radar['origin'][:2])+np.array(radar['size'][:2])/2
    ax.annotate('LD2450 above carrier\nantenna faces lid / room',xy=radar_center,xytext=(w/2,-17),ha='center',fontsize=9,
                arrowprops={'arrowstyle':'->','color':COLORS['radar']},color=COLORS['radar'])
    for x,y in mount_points(p):ax.add_patch(plt.Circle((x,y),1.7,fc='#203b51'))
    pod=p['bme_pod']; ax.add_patch(Rectangle(pod['origin'][:2],*pod['size'][:2],fc='#dceced',ec='#318f99',lw=1.5))
    pod_center=np.array(pod['origin'][:2])+np.array(pod['size'][:2])/2
    pod_end=pod['origin'][0]+pod['size'][0]
    ax.text(*pod_center,'External\nBME680\npod',ha='center',va='center',fontsize=10,color='#203b51')
    ax.plot([pod_end,0,25],[c['bme_exit_y']]*3,color='#318f99',lw=1.8)
    ax.text(pod_center[0],pod['origin'][1]-6,f'{-pod_end:g} mm drawn gap;\nposition to avoid warm air',ha='center',va='top',fontsize=8,color='#203b51')
    ax.text(155,175,'one PoE cable',ha='center',fontsize=10,color='#203b51')
    ax.set_xlim(-76,w+8);ax.set_ylim(-26,d+36);ax.set_aspect('equal');ax.grid(alpha=.12);ax.set_xlabel('x / mm');ax.set_ylabel('y / mm')
    ax.set_title(f'LOW-POWER CONCEPT | {w:g} x {d:g} x {c["height"]:g} mm | {b["size"][0]:g} x {b["size"][1]:g} mm carrier reservation',weight='bold',fontsize=14,pad=20)
    fig.text(.12,.045,'Hatching = provisional antenna reserve. Boxes = allocation envelopes, not module CAD.\nNo PCB routing, manufacturer keep-out validation, mounting detail or hardware fit has been established.',fontsize=10,color='#8a3946')
    fig.tight_layout(rect=(0,.08,1,.97));fig.savefig(out/'layout-plan.png',dpi=155);plt.close(fig)
    fig=plt.figure(figsize=(14,7)); fig.patch.set_facecolor('#f6f8fa')
    for panel in (0,1):
        ax=fig.add_subplot(1,2,panel+1,projection='3d')
        triangles=[]; colors=[]
        for name,(rot,xyz) in poses(p).items():
            if (panel==0 and name=='mockup_lid') or (panel==1 and name!='mockup_lid'):continue
            mesh=meshes[name].copy()
            if panel==0:mesh.apply_transform(cad.pose_matrix(rot,xyz))
            # The lid is shown separately in print orientation, underside up.
            color={'mockup_base':(0.75,0.80,0.84,0.22),'mockup_lid':(0.72,0.79,0.84,1),
                   'carrier_fit_blank':(0.63,0.74,0.60,1),'radar_holder':(0.85,0.64,0.74,1)}[name]
            triangles.extend(mesh.triangles);colors.extend([color]*len(mesh.faces))
        if panel==0:
            for comp in p['components']:
                mesh=cad.mesh_of(cuboid(comp))
                triangles.extend(mesh.triangles);colors.extend([COLORS[comp['kind']]]*len(mesh.faces))
        ax.add_collection3d(Poly3DCollection(triangles,facecolors=colors,edgecolor='none',zsort='average'))
        ax.set_xlim(0,w);ax.set_ylim(0,d);ax.set_zlim(0,50);ax.set_box_aspect((w,d,50));ax.view_init(elev=38,azim=-65)
        ax.set_xlabel('x / mm');ax.set_ylabel('y / mm');ax.set_zlabel('z / mm')
        ax.set_title(('Base, fit blank and allocated parts','Lid: print orientation, bosses upward')[panel],fontsize=12,pad=16)
    fig.suptitle('FIT MOCK-UP | printable mesh geometry + allocation boxes',fontsize=15,weight='bold',y=.96)
    fig.text(.07,.055,'Left: transparent base, actual carrier/holder meshes, rectangular component reservations. Right: lid separated.\nThis is a cold-fit model. Physical mounting, RF, thermal and electrical validation remain open.',fontsize=11,color='#8a3946')
    fig.tight_layout(rect=(0,.1,1,.94));fig.savefig(out/'exploded-preview.png',dpi=145);plt.close(fig)


def generate(p,out):
    out.mkdir(parents=True,exist_ok=True);nodes=models(p);meshes={}
    report={'status':p['status'],'units':'mm','parts':{},'inputs':{'parameters':p,'generator_sha256':sha(Path(__file__)),'helper_sha256':sha(HELPER)}}
    report['layout']=validate_layout(p,nodes)
    for name,node in nodes.items():
        path=out/(name+'.stl');mesh=cad.mesh_of(node);mesh.export(path);meshes[name]=mesh
        reread=trimesh.load_mesh(path,process=True);cad.solid_from_mesh(reread,name)
        report['parts'][name]={'watertight':bool(reread.is_watertight),'winding_consistent':bool(reread.is_winding_consistent),'connected_bodies':len(reread.split()),'volume_mm3':round(float(reread.volume),3),'bounds_mm':np.round(reread.bounds,4).tolist(),'sha256':sha(path)}
        (out/(name+'.scad')).write_text('// CONCEPT MOCK-UP ONLY. Units mm. Generated from parameters.json; not a fabrication-ready PCB.\n'+node.scad+'\n')
    lines=['// Visualization only; not one printable object. Units mm.','// Opaque parts are printable; translucent boxes are allocation envelopes.'];scene=trimesh.Scene()
    for name,(rot,xyz) in poses(p).items():
        lines.append(f'translate({list(xyz)}) rotate({list(rot)}) import("{name}.stl");')
        mesh=meshes[name].copy();mesh.apply_transform(cad.pose_matrix(rot,xyz));mesh.apply_scale(.001)
        mesh.visual.vertex_colors=np.tile([130,156,166,105] if name in ('mockup_base','mockup_lid') else [148,172,130,210],(len(mesh.vertices),1))
        scene.add_geometry(mesh,node_name=name,geom_name=name)
    for comp in p['components']+[dict(p['bme_pod'],id='BME_POD_ENVELOPE')]:
        node=cuboid(comp);lines.append(f'color([0.2,0.65,0.7,0.45]) {{ {node.scad} }} // {comp["id"]}')
        mesh=cad.mesh_of(node);mesh.apply_scale(.001);mesh.visual.vertex_colors=np.tile([38,143,154,150],(len(mesh.vertices),1))
        scene.add_geometry(mesh,node_name=comp['id'],geom_name=comp['id'])
    (out/'assembly.scad').write_text('\n'.join(lines)+'\n');scene.export(out/'assembly.glb')
    preview(p,meshes,out)
    report['artifacts']={path.name:sha(path) for path in sorted(out.iterdir()) if path.name!='mesh-report.json'}
    (out/'mesh-report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def check(actual,expected):
    cad.check_assets(actual,expected)
    have=json.loads((actual/'mesh-report.json').read_text());want=json.loads((expected/'mesh-report.json').read_text())
    if have.get('layout')!=want['layout']:raise ValueError('Stored layout/interference report is stale')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parameters',type=Path,default=ROOT/'parameters.json');parser.add_argument('--output',type=Path,default=ROOT/'generated');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    try:
        p=json.loads(args.parameters.read_text())
        if args.check:
            with tempfile.TemporaryDirectory(prefix='ha-low-power-cad-check-') as directory:
                report=generate(p,Path(directory));check(args.output,Path(directory))
        else:report=generate(p,args.output)
    except (ValueError,AssertionError,OSError,KeyError) as error:parser.exit(1,f'Low-power CAD failed: {error}\n')
    print(json.dumps({'status':p['status'],'parts':len(report['parts']),'components_checked':report['layout']['checked_component_count'],'current_assets':args.check,'output':str(args.output)},indent=2))


if __name__=='__main__':main()
