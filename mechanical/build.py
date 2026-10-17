#!/usr/bin/env python3
"""Generate printable STL, editable CSG/OpenSCAD, mesh report and layout previews.

Units: mm. parameters.json is the authoritative parametric input. Each operation
is evaluated in Manifold and emitted to OpenSCAD from the same CSG node. No
commercial PCB hole pattern or connector dimension is inferred by this model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
EPS = 0.02


class Node:
    def __init__(self, solid, scad):
        self.solid, self.scad = solid, scad

    def move(self, xyz):
        return Node(self.solid.translate(xyz), f"translate({list(xyz)}) {{ {self.scad} }}")

    def rotate(self, xyz):
        return Node(self.solid.rotate(xyz), f"rotate({list(xyz)}) {{ {self.scad} }}")


def box(x, y, z):
    assert min(x, y, z) > 0
    return Node(mf.Manifold.cube((x, y, z)), f"cube([{x},{y},{z}]);")


def cylinder(d, h, sides=48):
    assert min(d, h) > 0
    return Node(mf.Manifold.cylinder(h, d / 2, circular_segments=sides),
                f"cylinder(d={d},h={h},$fn={sides});")


def union(*nodes):
    return Node(mf.Manifold.batch_boolean([n.solid for n in nodes], mf.OpType.Add),
                "union() {\n" + "\n".join(n.scad for n in nodes) + "\n}")


def subtract(node, *cuts):
    if not cuts:
        return node
    return Node(mf.Manifold.batch_boolean([node.solid] + [n.solid for n in cuts], mf.OpType.Subtract),
                "difference() {\n" + node.scad + "\n" + "\n".join(n.scad for n in cuts) + "\n}")


def slot(x, y, z, length, width, height):
    # Straight sided through-slot, bridge span = width when printed flat.
    return box(length, width, height).move((x, y, z))


def models(p):
    w, d, h = p['width'], p['depth'], p['base_height']
    t, f, lt = p['wall'], p['floor'], p['lid_thickness']
    off, bd = p['boss_offset'], p['boss_diameter']
    dm, dz, dt = p['deck_margin'], p['deck_z'], p['deck_thickness']
    hole, ins, idep = p['m3_clearance'], p['insert_pilot'], p['insert_depth']
    assert w >= 240 and d >= 200 and h >= 72, 'These modules require a fit review below this envelope'
    assert h - dz - dt >= 28 and dz - f >= 32
    assert 0 < p['radar_skin'] < lt
    corners = [(off,off),(w-off,off),(off,d-off),(w-off,d-off)]
    deck_corners = [(dm,dm),(w-dm,dm),(dm,d-dm),(w-dm,d-dm)]
    shell = subtract(box(w,d,h), box(w-2*t,d-2*t,h).move((t,t,f)))
    bosses = [cylinder(bd,h).move((x,y,0)) for x,y in corners]
    # Dedicated deck supports, deliberately distinct from the lid bosses.
    pillars = [cylinder(9,dz).move((x,y,0)) for x,y in deck_corners]
    base = union(shell,*bosses,*pillars)
    cuts = [cylinder(ins,idep+EPS).move((x,y,h-idep)) for x,y in corners]
    cuts += [cylinder(ins,idep+EPS).move((x,y,dz-idep)) for x,y in deck_corners]
    # Side vent windows; 3 mm spans can bridge in the default print orientation.
    for y in range(38,int(d)-30,7):
        for x in (-EPS,w-t-EPS):
            # Leave material around the ambient-sensor cable gland on the left.
            if x == -EPS and abs(y + 1.5 - p['bme_exit_y']) < 10:
                continue
            cuts.append(box(t+2*EPS,3,17).move((x,y,52)))
    # Rear RJ45 cable access: allow connector passage; fit a split grommet later.
    cuts.append(box(22,t+2*EPS,16).move((w/2-11,d-t-EPS,12)))
    # Confirmed external antenna adapters only. Unused holes receive printed caps.
    for x in (-EPS,w-t-EPS):
        cuts.append(cylinder(p['bulkhead_hole'],t+2*EPS).rotate((0,90,0)).move((x,d-26,60)))
    # Exit for the remote, naturally ventilated ambient sensor pod.
    cuts.append(cylinder(p['bme_cable_hole'],t+2*EPS).rotate((0,90,0)).move((-EPS,p['bme_exit_y'],p['bme_exit_z'])))
    # Universal strap slots, not claimed to match any manufacturer's mounting holes.
    for x in range(30,int(w)-25,30):
        for y in range(30,int(d)-25,30):
            cuts.append(slot(x-6,y-1.5,-EPS,12,3,f+2*EPS))
    # Keyholes for screw heads on a wall; add rubber spacers behind base.
    for x in (w/4,3*w/4):
        cuts.append(cylinder(8,f+2*EPS).move((x,d-20,-EPS)))
        cuts.append(box(4,9,f+2*EPS).move((x-2,d-20,-EPS)))
    base = subtract(base,*cuts)

    # Lid local Z=0 is the outer face. Print outer face on the bed, lip upward.
    gap = p['lid_clearance']
    lip_outer = box(w-2*(t+gap), d-2*(t+gap),3).move((t+gap,t+gap,lt))
    lip_inner = box(w-2*(t+gap+1.8), d-2*(t+gap+1.8),3+2*EPS).move((t+gap+1.8,t+gap+1.8,lt-EPS))
    lip = subtract(lip_outer,lip_inner,*[cylinder(bd+1,3+2*EPS).move((x,y,lt-EPS)) for x,y in corners])
    lid = union(box(w,d,lt),lip)
    rx, ry = w/2, p['radar_window_center_y']
    rw, rd = p['radar_window_width'], p['radar_window_depth']
    # Four carrier bosses outside the antenna window. They connect only to lid.
    radar_mounts = [(rx-38,ry-22),(rx+38,ry-22),(rx-38,ry+22),(rx+38,ry+22)]
    lid = union(lid,*[cylinder(8,9).move((x,y,lt-EPS)) for x,y in radar_mounts])
    lid_cuts = [cylinder(hole,lt+2*EPS).move((x,y,-EPS)) for x,y in corners]
    # Shallow counterbores on the outer face; pan/button head screws, not countersunk.
    lid_cuts += [cylinder(6.8,1.2+EPS).move((x,y,-EPS)) for x,y in corners]
    lid_cuts += [cylinder(ins,idep+EPS).move((x,y,lt+9-idep)) for x,y in radar_mounts]
    lid_cuts.append(box(rw,rd,lt-p['radar_skin']+EPS).move((rx-rw/2,ry-rd/2,p['radar_skin'])))
    # Keep the sensor window and the middle deck ventilated regions distinct.
    for x in range(28,int(w)-25,8):
        for y in (90,125,160):
            lid_cuts.append(box(3,22,lt+2*EPS).move((x,y,-EPS)))
    lid = subtract(lid,*lid_cuts)

    # Tray is 214 x 174 at defaults, including corner tabs at the support centres.
    deck_x,deck_y=dm-5,dm-5
    deck_w,deck_d=w-2*dm+10,d-2*dm+10
    deck = box(deck_w,deck_d,dt)
    dcuts=[]
    for x,y in deck_corners:
        dcuts.append(cylinder(hole,dt+2*EPS).move((x-deck_x,y-deck_y,-EPS)))
    for x in range(17,int(deck_w)-14,17):
        for y in range(17,int(deck_d)-14,17):
            dcuts.append(box(10,5,dt+2*EPS).move((x-5,y-2.5,-EPS)))
    # Open cable chase from edge: plug dimensions do not need to fit drilled holes.
    dcuts.append(box(30,28,dt+2*EPS).move((deck_w/2-15,deck_d-27,-EPS)))
    deck=subtract(deck,*dcuts)

    # Radar holder is a frame, not an invented LD2450 snap-fit; use insulated ties.
    carrier=box(84,52,2)
    ccuts=[box(30,8,2+2*EPS).move((27,22,-EPS))]
    for x in (4,80):
        for y in (4,48):
            ccuts.append(cylinder(hole,2+2*EPS).move((x,y,-EPS)))
    for x in (22,58):
        for y in (14,36):
            ccuts.append(box(2,3,2+2*EPS).move((x,y,-EPS)))
    carrier=subtract(carrier,*ccuts)

    # Blanking plug: friction fit is deliberately loose; retain with neutral silicone.
    cap=union(cylinder(p['bulkhead_hole']-0.3,t+1.5),cylinder(10,1.2))

    # Remote BME680 pod: universal mounting, free airflow, no tight PCB clips.
    pw,pd,ph,pt=p['pod_width'],p['pod_depth'],p['pod_height'],p['pod_wall']
    pod= subtract(box(pw,pd,ph-pt),box(pw-2*pt,pd-2*pt,ph).move((pt,pt,pt)))
    pc=[(4,4),(pw-4,pd-4)]
    pod=union(pod,*[cylinder(6,ph-pt).move((x,y,0)) for x,y in pc])
    pcuts=[cylinder(1.8,8).move((x,y,ph-pt-8)) for x,y in pc]
    for y in range(9,int(pd)-8,5):
        for x in (-EPS,pw-pt-EPS):
            pcuts.append(box(pt+2*EPS,2.5,9).move((x,y,6)))
    for x in range(12,int(pw)-10,6):
        pcuts.append(box(2.5,pt+2*EPS,9).move((x,pd-pt-EPS,6)))
    pcuts.append(box(5,pt+2*EPS,4).move((pw/2-2.5,-EPS,ph-pt-4)))
    for x in (12,pw-16):
        pcuts.append(box(4,2,pt+2*EPS).move((x,pd/2,-EPS)))
    pod=subtract(pod,*pcuts)
    pod_lid=box(pw,pd,pt)
    plc=[cylinder(2.3,pt+2*EPS).move((x,y,-EPS)) for x,y in pc]
    for x in range(10,int(pw)-8,6):
        plc.append(box(2.5,pd-16,pt+2*EPS).move((x,8,-EPS)))
    pod_lid=subtract(pod_lid,*plc)
    # Small first-print coupon: left three holes are clearance, right three insert pilots.
    coupon=box(72,20,8)
    checks=[]
    for i,diameter in enumerate((3.2,3.4,3.6)):
        checks.append(cylinder(diameter,8+2*EPS).move((8+i*10,10,-EPS)))
    for i,diameter in enumerate((4.0,4.2,4.4)):
        checks.append(cylinder(diameter,6+EPS).move((44+i*10,10,2)))
    coupon=subtract(coupon,*checks)
    return {'base':base,'lid':lid,'deck':deck,'radar_carrier':carrier,
            'antenna_blank':cap,'bme680_pod_base':pod,'bme680_pod_lid':pod_lid,
            'fit_coupon':coupon}


def mesh_of(node):
    raw=node.solid.to_mesh()
    return trimesh.Trimesh(vertices=raw.vert_properties[:,:3],faces=raw.tri_verts,process=True)


def preview(meshes,p,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    navy='#10283e'; teal='#18a7a5'; gold='#f2ba54'
    # Exploded render from actual generated meshes, not a conceptual image.
    fig=plt.figure(figsize=(14,9),facecolor='#f4f7fa')
    ax=fig.add_axes([0.02,0.04,0.74,0.86],projection='3d',facecolor='#f4f7fa')
    scene=[('base',(0,0,0),navy,0.30),('deck',(p['deck_margin']-5,p['deck_margin']-5,94),teal,.85),
           ('lid',(0,0,139),'#c8d6e4',.68),('radar_carrier',(p['width']/2-42,p['radar_window_center_y']-26,122),gold,1),
           ('bme680_pod_base',(-75,p['bme_exit_y']-18,40),teal,.85),('bme680_pod_lid',(-75,p['bme_exit_y']-18,74),'#c8d6e4',1)]
    for name,offset,color,alpha in scene:
        vertices=meshes[name].vertices.copy()
        if name=='lid':
            vertices[:,2]*=-1
        vertices+=offset
        collection=Poly3DCollection(vertices[meshes[name].faces],facecolor=color,edgecolor='none',alpha=alpha)
        ax.add_collection3d(collection)
    ax.set(xlim=(-85,p['width']),ylim=(0,p['depth']),zlim=(0,145))
    ax.set_box_aspect((p['width']+85,p['depth'],170));ax.view_init(elev=27,azim=-120);ax.set_axis_off()
    fig.text(.04,.94,'HA RADIO HUB',fontsize=24,fontweight='bold',color=navy)
    fig.text(.04,.898,'DRAFT V0  /  printable enclosure and two-level arrangement',fontsize=12,color='#456078')
    text='240 × 200 × 80 mm\nMain enclosure\n\n01  Vented lid\n      1.2 mm radar window\n\n02  LD2450 carrier\n      Insulated ties; fit to verify\n\n03  Removable cable tray\n      z = 40 mm assembled\n\n04  Base + mounting pillars\n      PoE / Linux / switch below\n\n05  Ambient BME680 pod\n      45 × 36 × 20 mm\n\nSTL geometry validated\nComponent / RF / thermal fit pending'
    fig.text(.76,.80,text,va='top',linespacing=1.65,fontsize=11,color=navy)
    fig.savefig(out/'exploded-preview.png',dpi=160);plt.close(fig)
    # Practical envelope plan, every box denotes an allocation, not actual PCB CAD.
    fig,axes=plt.subplots(1,2,figsize=(14,7.8),facecolor='#f4f7fa')
    zones=[[
      (26,99,72,90,'Raspberry Pi 4\nrotated 90 degrees\nports towards cable lane'),
      (116,103,110,75,'TL-SF1005D switch\n104 × 70 case'),
      (22,27,108,34,'5 V PoE splitter\n102.5 × 29.6 case'),
      (139,28,75,35,'Fused 5 V\ndistribution'),
      (22,66,202,30,'Cable lane: Ethernet / USB / 5 V'),
    ],[
      (22,104,91,64,'ESP32-S3-ETH\n+ ZAC93 allocation'),
      (128,104,90,64,'RF S3-ETH or NodeMCU\n+ CC1101 allocation'),
      (22,76,105,23,'MG24 stick + lead'),
      (148,76,68,23,'Thread PCA10059'),
      (78,14,84,52,'LD2450 carrier\non lid above this zone'),
    ]]
    colors=[teal,'#6596bd',gold,'#bda6d2','#d7e0e8']
    for ai,(ax,items) in enumerate(zip(axes,zones)):
        ax.set_aspect('equal');ax.set_xlim(-10,p['width']+10);ax.set_ylim(-10,p['depth']+14)
        ax.add_patch(Rectangle((0,0),p['width'],p['depth'],fill=False,lw=2.2,edgecolor=navy))
        for i,(x,y,w,d,label) in enumerate(items):
            ax.add_patch(Rectangle((x,y),w,d,fc=colors[i],ec=navy,alpha=.7,lw=1))
            ax.text(x+w/2,y+d/2,label,ha='center',va='center',fontsize=8.7,color=navy)
        for x in (p['deck_margin'],p['width']-p['deck_margin']):
            for y in (p['deck_margin'],p['depth']-p['deck_margin']):
                ax.add_patch(plt.Circle((x,y),4.5,fc=navy))
        ax.text(120,204,'BACK: PoE cable / service lane',ha='center',fontsize=9,color=navy)
        ax.set_title(('LOWER LAYER · floor z = 3 mm','UPPER LAYER · tray z = 40–43 mm')[ai],fontsize=13,color=navy,pad=22)
        ax.set_xlabel('x / mm');ax.set_ylabel('y / mm');ax.grid(alpha=.13)
    fig.suptitle('DRAFT ALLOCATION PLAN · all cables and antenna clearance need a physical mock-up',fontsize=15,color=navy)
    fig.text(.05,.04,'Antenna elements must stay clear of copper, switch casing and cables. Keep the BME680 pod outside the heat plume.',color=navy,fontsize=10)
    fig.tight_layout(rect=(0,.08,1,.94));fig.savefig(out/'layout-plan.png',dpi=160);plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parameters',type=Path,default=ROOT/'parameters.json')
    parser.add_argument('--output',type=Path,default=ROOT/'generated')
    parser.add_argument('--no-preview',action='store_true')
    args=parser.parse_args()
    p=json.loads(args.parameters.read_text())
    args.output.mkdir(parents=True,exist_ok=True)
    nodes=models(p); meshes={};report={'status':p['status'],'units':'mm','parts':{}}
    preamble='// Generated from parameters.json by build.py. Edit parameters.json, then rebuild.\n// CSG and STL share the same source. See docs/enclosure.md. Units mm.\n'
    for name,node in nodes.items():
        mesh=mesh_of(node);meshes[name]=mesh
        path=args.output/f'{name}.stl';mesh.export(path)
        # Validate the exported binary STL again, not only the in-memory manifold.
        reread=trimesh.load_mesh(path,process=True)
        bodies=len(reread.split(only_watertight=False))
        detail={'watertight':bool(reread.is_watertight),'winding_consistent':bool(reread.is_winding_consistent),
                'connected_bodies':bodies,'positive_volume':bool(reread.volume>0),
                'volume_mm3':round(float(reread.volume),2),'triangles':len(reread.faces),
                'bounds_mm':np.round(reread.bounds,3).tolist(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        assert detail['watertight'] and detail['winding_consistent'] and bodies==1 and detail['positive_volume'],(name,detail)
        report['parts'][name]=detail
        (args.output/f'{name}.scad').write_text(preamble+node.scad+'\n')
    report['checks_not_performed']=['physical component and cable fit','actual FDM print fit','heat-set insert pull-out',
      'RF coexistence / radiation efficiency','LD2450 radome transmission','thermal soak under full load','wall fastener load test']
    # Check printable pieces in the assembled transform, excluding fasteners.
    transforms={
      'base':(0,0,0),
      'deck':(p['deck_margin']-5,p['deck_margin']-5,p['deck_z']),
      'lid':(0,0,p['base_height']+p['lid_thickness']),
      'radar_carrier':(p['width']/2-42,p['radar_window_center_y']-26,p['base_height']-11+EPS),
      'bme680_pod_base':(-75,p['bme_exit_y']-18,40),
      'bme680_pod_lid':(-75,p['bme_exit_y']-18,40+p['pod_height']-p['pod_wall'])
    }
    assembled={}
    for name,offset in transforms.items():
        solid=nodes[name].solid
        if name=='lid': solid=solid.mirror((0,0,1))
        assembled[name]=solid.translate(offset)
    collision_report={}
    names=list(assembled)
    for i,name in enumerate(names):
        for other in names[i+1:]:
            volume=float((assembled[name] ^ assembled[other]).volume())
            collision_report[f'{name}/{other}']=round(volume,6)
            assert volume < 0.001,(name,other,volume)
    report['assembled_intersection_volume_mm3']=collision_report
    (args.output/'mesh-report.json').write_text(json.dumps(report,indent=2)+'\n')
    # The OpenSCAD assembly transforms also follow parameters.json.
    scad=['// Visualization only; print individual parts, not this assembly.']
    scene=trimesh.Scene()
    colors={'base':[36,66,90,180],'deck':[25,167,165,255],'lid':[196,210,225,180],
            'radar_carrier':[241,186,85,255],'bme680_pod_base':[25,167,165,255],
            'bme680_pod_lid':[196,210,225,255]}
    for name,offset in transforms.items():
        mirror='mirror([0,0,1]) ' if name=='lid' else ''
        scad.append(f'translate({list(offset)}) {mirror}import("{name}.stl");')
        part=meshes[name].copy()
        matrix=np.eye(4)
        if name=='lid': matrix[2,2]=-1
        matrix[:3,3]=offset
        part.apply_transform(matrix)
        # glTF uses metres. STL and all source parameters remain millimetres.
        part.apply_scale(0.001)
        part.visual.vertex_colors=np.tile(colors[name],(len(part.vertices),1))
        scene.add_geometry(part,node_name=name,geom_name=name)
    (args.output/'assembly.scad').write_text('\n'.join(scad)+'\n')
    scene.export(args.output/'assembly.glb')
    if not args.no_preview:preview(meshes,p,args.output)
    print(json.dumps({'parts':len(nodes),'all_watertight':True,'single_body_each':True,'output':str(args.output)},indent=2))


if __name__=='__main__':main()
