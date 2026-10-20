#!/usr/bin/env python3
"""Generate FH1 full-hub print parts, labelled layouts and auditable fit checks.

CAD solids and OpenSCAD share one CSG source. Electronics are explicitly
conservative bounding volumes, not supplier STEP models or fit measurements.
"""
from pathlib import Path
import argparse
import hashlib
import html
import importlib.util
import json
import math
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

c = load('fullhub_csg', ROOT / 'mechanical/build.py')
old = load('fullhub_old', ROOT / 'mechanical/module-carrier/external-antenna-prototype/build.py')
portable = load('fullhub_portable', ROOT / 'mechanical/module-carrier/portable_check.py')
printing = load('fullhub_printing', HERE / 'print_package.py')

COLORS = {'carrier':'#23725c','poe_splitter':'#303842','buck':'#18608c',
          'wk2132':'#25699c','zwave':'#346baa','cc1101':'#17663d',
          'ld2450':'#4c83ac','bme680':'#6938a1','dc_adapter':'#354548','fuse_holder':'#aa7440'}
LABELS = {'carrier':'MC2-C carrier + U1–U4','poe_splitter':'Isolated PoE splitter',
          'buck':'RECOM 3.3 V + 27 µF','wk2132':'DFR0627 / WK2132','zwave':'Zooz ZAC93 Z-Wave',
          'cc1101':'CC1101 RF transceiver','ld2450':'LD2450 radar → room','bme680':'BME680 ambient sensor','dc_adapter':'Insulated 5 V DC adapter','fuse_holder':'Insulated inline DC fuse'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def overlap(a,b,gap=0):
    return all(a[i] < b[i+3]+gap and b[i] < a[i+3]+gap for i in range(3))
def bounds(origin,size): return list(origin)+[origin[i]+size[i] for i in range(3)]
def bodybox(bb): return c.box(*[bb[i+3]-bb[i] for i in range(3)]).move(bb[:3])
def contains(a,b): return all(a[i] <= b[i]+1e-6 and a[i+3] >= b[i+3]-1e-6 for i in range(3))

def manifest():
    data=json.loads((HERE/'components.json').read_text())
    rows=data['components']
    result={r['id']:r for r in rows} if isinstance(rows,list) else rows
    result.update({r['id']:r for r in data['accessories'] if r['id'] in ['dc_adapter','fuse_holder']})
    return result

def source():
    return old.source({'source_directory':'hardware/external-antenna/cad'})

def cradle(size, raised=False):
    """A removable, screwed down insulated tray; straps, not PCB drill holes."""
    x,y,z=size; w=x+8; d=y+8
    plate=c.box(w,d,2.4)
    # Small stop walls restrain translation; open ends admit the harness.
    rails=[c.box(2,d-8,16).move((0,4,0)),c.box(2,d-8,16).move((w-2,4,0))]
    if raised:
        # ZAC93's socket occupies the centre below the PCB. Two narrow ledges
        # support its PCB edges at the trial PCB plane, with no central post.
        rails=[c.box(2,d-8,20.4).move((1,4,0)),c.box(2,d-8,20.4).move((w-3,4,0))]
        rails += [c.box(4,d-8,1.2).move((1,4,19.2)),c.box(4,d-8,1.2).move((w-5,4,19.2))]
    plate=c.union(plate,*rails)
    cuts=[c.cylinder(2.2,2.6).move((a,b,-.1)) for a,b in [(2,2),(w-2,2),(2,d-2),(w-2,d-2)]]
    # One strap location stays on the connector half of the ZAC93. Real PCB
    # orientation/trace antenna must be verified before tightening the strap.
    for sx in ([8] if raised else [w*.3,w*.7]):
        for sy in [2.5,d-5.5]: cuts.append(c.box(3,3,2.6).move((sx,sy,-.1)))
    if not raised: cuts.append(c.box(4.2,max(d-12,4),20).move((-.1,6,5.8)))
    if raised: cuts.append(c.box(max(x-10,8),max(y-8,8),2.6).move((9,8,-.1)))
    return c.subtract(plate,*cuts)

def regulator_cradle(size):
    """Edge supports leave a real underside cavity for hand-soldered wires."""
    x,y,z=size;w=x+8;d=y+8
    plate=c.box(w,d,2.4)
    # PCB lower face is 6 mm above tray origin. No post enters its solder area.
    plate=c.union(plate,c.box(2,y,6).move((4,4,0)),c.box(2,y,6).move((x+2,4,0)),
                  c.box(2,y,9).move((1,4,0)),c.box(2,y,9).move((w-3,4,0)),
                  c.box(x,1,7).move((4,2,0)),c.box(x,1,7).move((4,d-3,0)))
    cuts=[c.cylinder(2.2,2.6).move((a,b,-.1)) for a,b in [(2,2),(w-2,2),(2,d-2),(w-2,d-2)]]
    # One loose nonconductive strap bears on the cleared rear FR4 band.
    for sx in [2, w-4]: cuts.append(c.box(2,2.5,12).move((sx,24.5,-.1)))
    # Raised anchor behind the board, so a harness bundle never occupies the
    # restricted solder cavity underneath it. Fit a soft loop through this eye.
    plate=c.union(plate,c.box(7,3,8).move((w/2-3.5,d-3,0)))
    cuts.append(c.cylinder(2.5,7.2).rotate((0,90,0)).move((w/2-3.6,d-1.5,5)))
    return c.subtract(plate,*cuts)


def regulator_details(p,m):
    x,y,z=p['placements']['buck'];mount=m['buck']['mount']
    board=bounds([x,y,mount['pcb_underside_z_mm']],mount['perfboard_mm'])
    def detail(origin_key,size_key):
        origin=mount[origin_key];size=mount[size_key]
        return bounds([x+origin[0],y+origin[1],z+origin[2]],size)
    return {'perfboard':board,
            'regulator':detail('regulator_local_body_origin_mm','regulator_max_body_mm'),
            'input_capacitor':detail('capacitor_local_body_origin_mm','capacitor_max_body_mm'),
            'underside_solder':bounds([x+2,y+2,mount['pcb_underside_z_mm']-mount['maximum_tail_below_board_mm']],[20,20,mount['maximum_tail_below_board_mm']])}


def geometry(p,m,s):
    q=p['case']; W=q['width'];D=q['length'];H=q['height'];t=q['wall'];f=q['floor'];lt=q['lid']
    placements=p['placements']; bb={k:bounds(placements[k],m[k]['design_envelope_mm']) for k in placements}
    # The carrier stack is tied to the native board, not an invented footprint.
    bb['carrier']=bounds(placements['carrier'],[s['width'],s['length']+2,30])
    corners=[(8,8),(W-8,8),(8,D-8),(W-8,D-8)]
    nodes={}; poses={}; mounting={}
    base=c.subtract(c.box(W,D,H),c.box(W-2*t,D-2*t,H).move((t,t,f)))
    base=c.union(base,*[c.cylinder(11,H).move((x,y,0)) for x,y in corners])
    cuts=[c.cylinder(2.5,12).move((x,y,H-11)) for x,y in corners]
    bx,by,bz=placements['carrier']
    carrier_holes=[(bx+v[0],by+v[1]) for v in s['holes'].values()]
    base=c.union(base,*[c.cylinder(7,bz).move((x,y,0)) for x,y in carrier_holes])
    cuts += [c.cylinder(2.7,bz+.2).move((x,y,-.1)) for x,y in carrier_holes]
    cuts += [c.cylinder(5.8,2.4,sides=6).move((x,y,-.1)) for x,y in carrier_holes]
    mounting['carrier']={'kind':'four native M2.5 mounting holes','case_xy_mm':carrier_holes,'seat_z_mm':bz}
    # Five separate removable peripheral trays. Generic tray hardware is M2;
    # foam pads and loose soft nylon straps prevent solder-joint compression.
    for key in ['poe_splitter','buck','wk2132','zwave','cc1101']:
        size=m[key]['design_envelope_mm']; x,y,z=placements[key];tw=size[0]+8;td=size[1]+8
        origin=[x-4,y-4,6]; name=key.replace('_','-')+'-tray'
        nodes[name]=cradle(size,key=='zwave'); poses[name]=((0,0,0),origin)
        if key=='buck':nodes[name]=regulator_cradle(size)
        holes=[(origin[0]+u,origin[1]+v) for u,v in [(2,2),(tw-2,2),(2,td-2),(tw-2,td-2)]]
        base=c.union(base,*[c.cylinder(5,6).move((hx,hy,0)) for hx,hy in holes])
        cuts += [c.cylinder(1.7,5.2).move((hx,hy,1)) for hx,hy in holes]
        mounting[key]={'kind':'screwed removable insulated tray and soft nylon straps','tray':name,'tray_origin_mm':origin,
                       'tray_inner_xy_mm':bounds([x-2,y-2,0],[size[0]+4,size[1]+4,100]),'case_xy_mm':holes,
                       'seat_or_pad_top_z_mm':26.4 if key=='zwave' else 12,'hardware':'4 × M2 × 6 mm thread-forming screws; measure pilot coupon first',
                       'requires':'insulating pads at measured component-free board edges; no drilling module; socket/header clearance verified on arrival'}
    mounting['buck'].update({'kind':'24 x 24 mm perfboard on two insulated edge supports with rear-band restraint','pcb_underside_z_mm':12,'maximum_tail_below_board_mm':2,'minimum_solder_to_floor_gap_mm':1.6,'local_hole_centres_mm':[],'restraint_band_local_y_mm':[20.5,23],'hardware':'4 × M2 × 6 mm tray screws and one soft nonconductive board strap; separate harness loop','requires':'2 mm copper-free board rim and cleared rear restraint band; SIP body seated on board; capacitor vent clear; no loose live solder joints'})
    mounting['zwave'].update({'pcb_underside_z_mm':26.4,'socket_envelope_mm':[placements['zwave'][0]+2,placements['zwave'][1]+2,17.4,placements['zwave'][0]+10,placements['zwave'][1]+15,26.4],'antenna_half_direction':'+X toward the plastic right wall','restraint':'one soft strap on electronics/connector half at x147.5; no strap over antenna half'})
    # One shared, positively retained utility tray holds both insulated power
    # accessories. Neither the DC adapter nor fuse holder hangs from its wires.
    utility=c.box(48,52,2.4)
    for x,y in [(2,2),(46,2),(2,50),(34,50)]:
        utility=c.subtract(utility,c.cylinder(2.2,2.6).move((x,y,-.1)))
    for x in [8,35]:
        for y in [3,22,28,47]:utility=c.subtract(utility,c.box(3,3,2.6).move((x,y,-.1)))
    utility=c.union(utility,c.box(2,40,16).move((0,6,0)),c.box(2,40,16).move((46,6,0)))
    utility=c.subtract(utility,c.cylinder(12,25).move((45,47.5,-.1)))
    nodes['power-utility-tray']=utility;poses['power-utility-tray']=((0,0,0),(162,159.5,6))
    utility_holes=[(164,161.5),(208,161.5),(164,209.5),(196,209.5)]
    base=c.union(base,*[c.cylinder(5,6).move((x,y,0)) for x,y in utility_holes])
    cuts += [c.cylinder(1.7,5.2).move((x,y,1)) for x,y in utility_holes]
    for key in ['dc_adapter','fuse_holder']:
        mounting[key]={'kind':'shared screw-fixed utility tray with separate soft straps','tray':'power-utility-tray','tray_inner_xy_mm':[164,161.5,0,208,209.5,100],'case_xy_mm':utility_holes,'seat_or_pad_top_z_mm':12,'hardware':'4 × M2 × 6 mm screws total for the shared tray'}
    # The three 2.4 GHz connectors remain on the fixed wall while the lid lifts.
    for port in p['rf_ports']:
        x,y,z=port['center']
        rf=p['rf_harness']
        cuts.append(c.cylinder(rf['nominal_hole_diameter_mm']+rf['print_allowance_mm'],t+.2).rotate((90,0,0)).move((x,t+.1,z)))
        cuts.append(old.lettering(port['label'],x,z-12))
        # Leave the straight coax above the tower; the soft loop retains it.
        tower=c.box(12,6,z-4.9).move((x-6,23,2.9))
        tower=c.subtract(tower,c.box(8,6.2,2).move((x-4,22.9,z-6)))
        base=c.union(base,tower)
    # Separate stock sub-GHz antenna exits. ZAC93 antenna remains INTERNAL;
    # this CC1101 opening is deliberately not described as another ZAC93 port.
    a=p['cc1101_antenna']['center']
    cuts.append(c.cylinder(p['cc1101_antenna']['opening_diameter'],t+.2).rotate((0,90,0)).move((W-t-.1,a[1],a[2])))
    ep=p['poe_entry'];ey=ep['center_y'];ez=ep['center_z'];wy,wz=ep['opening_yz']
    cuts.append(c.box(t+.2,wy,wz).move((-.1,ey-wy/2,ez-wz/2)))
    # Pod wiring exits above the warm electronics, then descends outside.
    cuts.append(c.cylinder(6.5,t+.2).rotate((0,90,0)).move((W-t-.1,153,52)))
    for y in range(40,165,10):
        cuts.append(c.box(t+.2,3,14).move((-.1,y,50)))
    for y in [139,149,159,169]:
        cuts.append(c.box(t+.2,3,12).move((W-t-.1,y,55)))
    # Wall fixing is through the base only, with the electrical hardware removed.
    cuts += [c.cylinder(4.5,f+.2).move((x,15,-.1)) for x in [70,145]]
    # Dedicated cable anchor eyes are part of the base and clear the components.
    anchor_xy=[(121,67),(121,111),(123,151),(148,194),(18,163)]
    for x,y in anchor_xy:
        eye=c.box(8,6,7).move((x-4,y-3,0))
        eye=c.subtract(eye,c.box(4,6.2,2).move((x-2,y-3.1,4)))
        base=c.union(base,eye)
    # Pod support arms bolt through the side wall at two known assembly points.
    for y in [147,171]:
        cuts.append(c.cylinder(3.3,t+.2).rotate((0,90,0)).move((W-t-.1,y,21)))
    nodes['base']=c.subtract(base,*cuts); poses['base']=((0,0,0),(0,0,0))
    lid=c.box(W,D,lt)
    lid=c.subtract(lid,*[c.cylinder(3.3,lt+.2).move((x,y,-.1)) for x,y in corners])
    # Print outer face down: the recess leaves a 0.8 mm RF window. On assembly
    # the whole lid flips about X; the radome itself never becomes a hole.
    rx,ry,rz=placements['ld2450']; rw,rd,rh=m['ld2450']['design_envelope_mm']
    radar_window=[rx-3,ry-3,rw+6,rd+6]
    # Lid's local X is reflected by a rigid 180-degree Y rotation on assembly.
    lx=W-(rx+rw+3);ly=ry-3
    lid=c.subtract(lid,c.box(rw+6,rd+6,lt-q['radome_skin']+.1).move((lx,ly,q['radome_skin'])))
    radar_holes=[(rx-7,ry-4),(rx+rw+7,ry-4),(rx-7,ry+rd+4),(rx+rw+7,ry+rd+4)]
    for x,y in radar_holes:
        lid=c.union(lid,c.cylinder(6,H-rz+.01).move((W-x,y,lt-.01)))
        lid=c.subtract(lid,c.cylinder(1.7,8.1).move((W-x,y,lt+H-rz-8)))
    nodes['lid']=lid;poses['lid']=((0,180,0),(W,0,H+lt))
    # Radar open-frame back support. Soft straps locate the two board ends;
    # no metal screw or strap crosses the active front antenna face.
    rw2=rw+20;rd2=rd+12
    radar=c.box(rw2,rd2,2)
    radar=c.subtract(radar,c.box(rw-8,rd-4,2.2).move((14,8,-.1)))
    radar=c.subtract(radar,*[c.cylinder(2.2,2.2).move((x,y,-.1)) for x,y in [(3,2),(rw2-3,2),(3,rd2-2),(rw2-3,rd2-2)]])
    for x in [10,rw2-14]:
        for y in [3,rd2-6]:radar=c.subtract(radar,c.box(2.5,3,2.2).move((x,y,-.1)))
    nodes['radar-holder']=radar; poses['radar-holder']=((0,0,0),(rx-10,ry-6,rz-2))
    mounting['ld2450']={'kind':'lid-mounted open frame plus insulated board-end restraint','tray':'radar-holder','case_xy_mm':radar_holes,'front_direction':'+Z room facing','radome_skin_mm':q['radome_skin'],'nominal_antenna_plane_z_mm':p['radar']['antenna_plane_z_mm'],'nominal_air_gap_mm':p['radar']['air_gap_mm'],'metal_free_window_case_xy_mm':radar_window,'board_end_strap_x_ranges_mm':[[rx,rx+2.5],[rx+rw-4,rx+rw-1.5]]}
    # Pod has a positive mechanical connection: two identical L arms, each
    # with one side-wall M3 bolt and two base screws. Printed flat, assembled
    # by a rigid rotation. The 17 mm air gap reduces conduction, not all bias.
    arm=c.union(c.box(31,8,3),c.box(3,8,13))
    arm=c.subtract(arm,c.cylinder(3.3,3.2).rotate((0,90,0)).move((-.1,4,8)),c.cylinder(2.2,3.2).move((25,4,-.1)))
    nodes['pod-arm']=arm
    # Arms below the pod floor; a thin wall tab remains beside it.
    arm_poses=[((0,0,0),(W,y-4,13)) for y in [147,171]]
    poses['pod-arm']=arm_poses[0]
    po=p['pod']['origin'];pw,pd,ph=p['pod']['size']
    pod=c.subtract(c.box(pw,pd,ph-2),c.box(pw-4,pd-4,ph).move((2,2,2)))
    podcorners=[(4,4),(pw-4,pd-4)]
    pod=c.union(pod,*[c.cylinder(6,ph-2).move((x,y,0)) for x,y in podcorners])
    pod=c.subtract(pod,*[c.cylinder(1.7,8).move((x,y,ph-9)) for x,y in podcorners])
    for y in range(10,pd-7,5):
        for x in [-.1,pw-2.1]: pod=c.subtract(pod,c.box(2.2,2.5,10).move((x,y,7)))
    for x in range(12,pw-7,6):pod=c.subtract(pod,c.box(2.5,2.2,10).move((x,pd-2.1,7)))
    pod=c.subtract(pod,c.cylinder(6.5,2.2).rotate((0,90,0)).move((-.1,16,14)))
    # Two mounting holes agree exactly with the arm's far hole centres.
    for y in [147,171]:pod=c.subtract(pod,c.cylinder(2.2,2.2).move((W+25-po[0],y-po[1],-.1)))
    # Board restraint holes, insulating pads give the electronics its seat.
    for x in [10,30]:
        for y in [7,25]:pod=c.subtract(pod,c.box(2.5,3,2.2).move((x,y,-.1)))
    nodes['bme680-pod']=pod;poses['bme680-pod']=((0,0,0),po)
    plid=c.box(pw,pd,2)
    plid=c.subtract(plid,*[c.cylinder(2.2,2.2).move((x,y,-.1)) for x,y in podcorners])
    for x in range(12,pw-8,6):plid=c.subtract(plid,c.box(2.5,pd-14,2.2).move((x,7,-.1)))
    nodes['bme680-pod-lid']=plid;poses['bme680-pod-lid']=((0,0,0),(po[0],po[1],po[2]+ph-2))
    mounting['bme680']={'kind':'vented pod, two bolted support arms, insulated pads and soft straps','air_gap_mm':p['pod']['air_gap'],'pod_bounds_mm':bounds(po,[pw,pd,ph]),'arm_quantity':2}
    # Plug-in fit coupon, independent of any purchased PCB.
    coupon=c.box(90,26,t)
    for i,dia in enumerate([1.6,1.7,1.8,2.2,2.5,2.7,3.3]):
        coupon=c.subtract(coupon,c.cylinder(dia,t+.2).move((7+i*10,8,-.1)))
    for i,allow in enumerate([0,.2,.4]):
        coupon=c.subtract(coupon,c.cylinder(p['rf_harness']['nominal_hole_diameter_mm']+allow,t+.2).move((15+30*i,19,-.1)))
    nodes['fit-coupon']=coupon
    # A separate CC1101 port blank closes the trial opening if the installed
    # antenna is routed by another documented adapter. It is not an RF jack.
    nodes['cc1101-port-blank']=c.union(c.cylinder(9.6,3),c.cylinder(14,1.2))
    assembled={k:nodes[k].rotate(v[0]).move(v[1]) for k,v in poses.items()}
    assembled['pod-arm-2']=nodes['pod-arm'].rotate(arm_poses[1][0]).move(arm_poses[1][1])
    return {'nodes':nodes,'poses':poses,'assembled':assembled,'bounds':bb,'mounting':mounting,
            'radar_window':radar_window,'carrier_holes':carrier_holes,'anchors':anchor_xy}

rounded_coax_path = old.rounded_coax_path


def cable_routes(p,s):
    bx,by,bz=p['placements']['carrier']; routes=[]
    rf=p['rf_harness']
    for port in p['rf_ports']:
        endpoint=s['design']['mechanics']['rf_ports'][port['ref']]['estimated_xy_mm'];x,y,z=port['center']
        guide=[[x,p['case']['wall'],z],[x,p['case']['wall']+rf['bulkhead_straight_reservation_mm'],z],
               [bx+endpoint[0],by+endpoint[1],40],[bx+endpoint[0],by+endpoint[1],bz+14]]
        pts,arcs,lead=rounded_coax_path(guide,rf['minimum_bend_radius_mm'],rf['unbent_connector_allowance_mm'])
        routes.append({'id':port['label'].lower()+'-coax','points_mm':pts,'guide_points_mm':guide,
                       'guide_length_upper_bound_mm':round(sum(math.dist(a,b) for a,b in zip(guide,guide[1:])),3),
                       'radius_mm':1.5,'bend_arcs':arcs,'straight_bulkhead_lead_mm':lead,
                       'length_budget_mm':rf['minimum_length_budget_mm'],'nominal_cable_length_mm':rf['nominal_length_mm'],
                       'project_shortfall_allowance_mm':rf['project_length_shortfall_allowance_mm'],
                       'slack_allowance_mm':rf['service_slack_mm'],'allowed_contact':['carrier'],
                       'kind':'50 ohm Taoglas CAB.618.E coax; radius-limited route, delivered fit unmeasured'})
    routes += [
      {'id':'ethernet','points_mm':[[84.5,137,30],[84.5,164,30],[148,164,30],[148,193,30],[129,193,25]],'radius_mm':3,'allowed_contact':['poe_splitter','carrier'],'kind':'splitter captive data tail to WIZ850io; no extra PoE entering carrier'},
      {'id':'main-harness','points_mm':[[122,80,50],[122,151,50]],'radius_mm':4,'allowed_contact':[],'kind':'overhead restrained low-voltage harness corridor'},
      {'id':'ambient-harness','points_mm':[[122,151,50],[209,153,52],[225,153,52],[225,159,30],[234,159,30],[240,159,30]],'radius_mm':2,'allowed_contact':['bme680'],'kind':'I2C/power to attached ambient pod'},
      {'id':'radar-service-loop','points_mm':[[57.81,97,30],[57.81,97,50],[32,97,50],[32,93,63],[40,93,63]],'radius_mm':2,'allowed_contact':['ld2450','carrier'],'kind':'removable lid harness; unplug before separating lid'},
      {'id':'poe-input','points_mm':[[-15,192.4,24],[25,192.4,24]],'radius_mm':4,'allowed_contact':['poe_splitter'],'kind':'one upstream PoE Ethernet cable, restrained at wall opening'},
      {'id':'cc1101-stock-antenna','points_mm':[[199,55,26],[218,55,26]],'radius_mm':2,'allowed_contact':['cc1101'],'kind':'unmodified stock antenna or selected matching adapter; physical length unverified'}]
    def add(name,points,contacts,description):
        routes.append({'id':name,'points_mm':points,'radius_mm':1.5,'allowed_contact':contacts,'kind':description})
    headers=s['design']['mechanics']['header_mating_envelopes_mm']
    def jack(ref):
        v=headers[ref];return [bx+(v[0]+v[2])/2,by+(v[1]+v[3])/2,30]
    add('j3-wk2132', [jack('J3'),[122,82,48],[122,141,48],[126,141,23]], ['carrier','wk2132'], 'J3 six-wire harness:3.3V,GND,SDA,SCL,TX1,RX1; UART returns through carrier to J4')
    add('j4-zac93', [jack('J4'),[122,91,46],[122,78,46],[149,78,16],[149,91,16]], ['carrier','zwave'], 'J4 five-wire harness to ZAC93 pins1/6/9/8/10:3.3V,twoGND,RX,TX')
    add('j5-cc1101', [jack('J5'),[123,89,46],[130,58,46],[137,58,22]], ['carrier','cc1101'], 'J5 shared SPI and RF GPIOs to CC1101')
    add('j2-buck', [jack('J2'),[jack('J2')[0],jack('J2')[1],48],[122,113,48],[122,159,48],[180,159,48],[180,154,24],[187,148.35,17]], ['carrier','buck'], 'Four-wire J2 harness to RECOM perfboard: fused5V VIN,GND,regulated3.3V VOUT,GND; both grounds join SIP pin2; 27uF at VIN/GND')
    add('poe-dc-adapter', [[129,192,25],[153,192,37],[153,173,37],[166,173,24]], ['poe_splitter','dc_adapter'], 'Captive5V lead to insulated female barrel adapter')
    add('dc-adapter-fuse', [[185,180,24],[185,186,24],[185,191,24]], ['dc_adapter','fuse_holder'], '5V feed through inline fuse before branching')
    add('fuse-j1', [[167,199,25],[154,199,42],[154,172,48],[122,172,48],[122,122,48],[jack('J1')[0],jack('J1')[1],48],jack('J1')], ['fuse_holder','carrier'], 'Fused5V to J1')
    ambient=next(v for v in routes if v['id']=='ambient-harness')
    ambient['points_mm']=[jack('J7'),[122,105,50]]+ambient['points_mm'];ambient['allowed_contact'].append('carrier')
    for row in routes:
        pts=row['points_mm'];r=row['radius_mm']; row['length_mm']=round(sum(math.dist(a,b) for a,b in zip(pts,pts[1:])),3)
        row['segment_envelopes_mm']=[[min(a[i],b[i])-r for i in range(3)]+[max(a[i],b[i])+r for i in range(3)] for a,b in zip(pts,pts[1:])]
    return routes

def capsule(a,b,r):
    """A real 3-D swept cable segment, including rounded end caps."""
    v=[b[i]-a[i] for i in range(3)];length=math.dist(a,b)
    sphere=c.Node(c.mf.Manifold.sphere(r,16),f'sphere(r={r},$fn=16);')
    if length<1e-6:return sphere.move(a)
    pitch=math.degrees(math.acos(v[2]/length));yaw=math.degrees(math.atan2(v[1],v[0]))
    tube=c.cylinder(2*r,length,24).rotate((0,pitch,yaw)).move(a)
    return c.union(tube,sphere.move(a),sphere.move(b))


def validate(p,m,s,g):
    W,D,H=p['case']['width'],p['case']['length'],p['case']['height'];t=p['case']['wall'];f=p['case']['floor']
    main=[t,t,f,W-t,D-t,H];boxes=g['bounds']
    for key,bb in boxes.items():
        space=main if key!='bme680' else bounds([v+2 for v in p['pod']['origin']],[p['pod']['size'][i]-4 for i in range(3)])
        assert contains(space,bb),f'{key} body exceeds its enclosure: {bb} not in {space}'
    for name,box in regulator_details(p,m).items():
        assert contains(boxes['buck'],box),f'Regulator {name} escapes allocated assembly envelope'
    keys=list(boxes)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:assert not overlap(boxes[a],boxes[b]),f'Component overlap {a} / {b}'
    # Native RJ45 insertion/latch reservation gets a real Z envelope and must
    # remain unoccupied by all other components; it is NOT counted as PCB area.
    b=p['placements']['carrier'];cor=s['design']['mechanics']['rj45']['service_corridor_global_mm']
    rj=[b[0]+cor[0],b[1]+cor[1],20,b[0]+cor[2],b[1]+cor[3],44]
    zac=[175,82,10,W-t,124,58]
    keepouts={'native-wiz850io-plug-and-latch':rj,'zac93-outboard-antenna-air-reservation':zac}
    for name,bb in keepouts.items():
        assert contains(main,bb),f'{name} exceeds case'
        for key,part in boxes.items():
            assert not overlap(bb,part),f'{name} blocked by {key}'
    for key,entry in g['mounting'].items():
        if 'tray_inner_xy_mm' in entry:
            part=boxes[key];inside=entry['tray_inner_xy_mm'];assert contains(inside,part),f'{key} not contained by tray'
    plastic_parts=list(g['assembled'].items())
    for i,(a,anode) in enumerate(plastic_parts):
        for b,bnode in plastic_parts[i+1:]:
            assert (anode.solid ^ bnode.solid).volume()<.6,f'Printed-part collision {a} / {b}'
    assert math.isclose(p['radar']['inner_window_z_mm']-p['radar']['antenna_plane_z_mm'],p['radar']['air_gap_mm'],abs_tol=.001)
    routes=cable_routes(p,s)
    rf=p['rf_harness']
    assert rf['minimum_length_budget_mm']==rf['nominal_length_mm']-rf['project_length_shortfall_allowance_mm'],'Coax minimum length must include the shortfall allowance'
    for row in routes:
        if 'length_budget_mm' in row:
            assert max(row['length_mm'],row['guide_length_upper_bound_mm'])+row['slack_allowance_mm']<=row['length_budget_mm'],f'{row["id"]} insufficient coax length'
        for envelope in row['segment_envelopes_mm']:
            for key,bb in boxes.items():
                assert key in row['allowed_contact'] or not overlap(envelope,bb),f'{row["id"]} cable envelope blocks {key}'
            assert not overlap(envelope,zac),f'{row["id"]} crosses ZAC93 antenna air space'
    # Inspect every swept 3-D cable segment against every real printed part.
    # Openings and slots must exist in the solid; there are no plastic skips.
    cable_collisions=[]
    module_boxes={}
    carrier_origin=p['placements']['carrier']
    for part in s['design']['parts']:
        if not part['ref'].startswith('U'):continue
        x0,y0,x1,y1=part['body_bounds_global_mm']
        usb=s['design']['mechanics']['physical_usb_shells_mm'].get(part['ref'])
        if usb:
            x0,y0,x1,y1=min(x0,usb[0]),min(y0,usb[1]),max(x1,usb[2]),max(y1,usb[3])
        module_boxes[part['ref']]=[carrier_origin[0]+x0,carrier_origin[1]+y0,carrier_origin[2]+9,carrier_origin[0]+x1,carrier_origin[1]+y1,carrier_origin[2]+(23.6 if part['ref']=='U4' else 17)]
        assert contains(boxes['carrier'],module_boxes[part['ref']]),f'{part["ref"]} module exceeds the populated carrier reservation'
        nominal=s['design']['mechanics']['module_geometry'].get(part['ref'])
        if nominal and 'model_height_mm' in nominal:
            available=module_boxes[part['ref']][5]-module_boxes[part['ref']][2]
            assert nominal['model_height_mm']<=available,f'{part["ref"]} nominal model exceeds the allocated module height'
    endpoint_refs={'ble-coax':'U1','thread-coax':'U2','zigbee-coax':'U3'}
    for route in routes:
        for index,(start,end) in enumerate(zip(route['points_mm'],route['points_mm'][1:])):
            tube=capsule(start,end,route['radius_mm'])
            for name,node in g['assembled'].items():
                volume=(tube.solid ^ node.solid).volume()
                if volume>.15:cable_collisions.append({'route':route['id'],'segment':index,'obstacle':name,'volume_mm3':round(volume,3)})
            for ref,box in module_boxes.items():
                tested=tube
                if endpoint_refs.get(route['id'])==ref:
                    # Only the named U.FL connector column may enter its radio
                    # envelope, including the final radius-limited approach.
                    x,y,z=route['points_mm'][-1]
                    tested=c.subtract(tube,c.box(6,6,16).move((x-3,y-3,z-2)))
                volume=(tested.solid ^ bodybox(box).solid).volume()
                if volume>.15:cable_collisions.append({'route':route['id'],'segment':index,'obstacle':ref,'volume_mm3':round(volume,3)})
    assert not cable_collisions,f'Cable sweep collides: {cable_collisions}'
    # Underside sockets and pin access are distinct solids/air reservations;
    # never waive the entire ZAC93 just because its outer box includes air.
    z=p['placements']['zwave'];zx,zy,zz=z
    detailed={
      'zwave':[[zx,zy,26.4,zx+28.5,zy+28.5,28.0],[zx+2,zy+2,17.4,zx+10,zy+15,26.4],[zx+8,zy+6,28,zx+18,zy+19,30]],
      'buck':list(regulator_details(p,m).values())}
    connector_boxes={
      'zac93-underside-mating-header':[zx+2,zy+2,12,zx+10,zy+15,17.4],
      'zac93-socket-exit':[zx+2,zy-6,9,zx+10,zy+2,18],
      'cc1101-header':[134,50,12,142,65,27],
      'dfr0627-header':[124,134,12,132,151,28],
      'bme680-cable-plug':[234,155,24,240,163,34],
      'ld2450-cable-plug':[39,90,59.9,45,96,67.9]}
    native_header_boxes={ref:[p['placements']['carrier'][0]+v[0],p['placements']['carrier'][1]+v[1],27,p['placements']['carrier'][0]+v[2],p['placements']['carrier'][1]+v[3],40] for ref,v in s['design']['mechanics']['header_mating_envelopes_mm'].items()}
    for ref,box in native_header_boxes.items():
        for key,component in boxes.items():
            if key!='carrier':assert not overlap(box,component),f'Native {ref} header intersects {key}'
        for name,node in g['assembled'].items():
            assert (node.solid ^ bodybox(box).solid).volume()<.15,f'Native {ref} header clashes with {name}'
        for name,component in module_boxes.items():
            assert not overlap(box,component),f'Native {ref} header clashes with module {name}'
    # Headers seated inside the parent component are accounted for in the
    # corresponding component box. These are outward mated-plug allocations.
    for name,box in connector_boxes.items():
        for key,component in boxes.items():
            if name.startswith('zac93') and key=='zwave':continue
            assert not overlap(box,component),f'{name} intersects {key}'
        for name2,node in g['assembled'].items():
            # Header socket exits through a purpose-made central tray slot.
            assert (node.solid ^ bodybox(box).solid).volume()<.6,f'{name} clashes with {name2}'
    # Verify actual generated plastic against electronics, rather than solely
    # trusting bounding boxes. PCB bodies may touch their own support ledges.
    plastic_collisions=[]
    for key,bb in boxes.items():
        for detail in detailed.get(key,[bb]):
            # 0.15mm numerical surface margin; real tolerance is set in CAD.
            shrink=[detail[i]+.15 for i in range(3)]+[detail[i+3]-.15 for i in range(3)]
            for name,node in g['assembled'].items():
                volume=(node.solid ^ bodybox(shrink).solid).volume()
                if volume>.5:plastic_collisions.append({'component':key,'part':name,'volume_mm3':round(volume,3)})
    assert not plastic_collisions,f'Plastic crosses body reservation: {plastic_collisions}'
    thread_part=next(part for part in s['design']['parts'] if part['ref']=='U2')
    thread_route=next(route for route in routes if route['id']=='thread-coax')
    thread_fit={
        'model':thread_part['model'],
        'manufacturer_geometry':s['design']['mechanics']['module_geometry']['U2'],
        'allocated_envelope_case_mm':module_boxes['U2'],
        'coax_route_length_mm':thread_route['length_mm'],
        'coax_service_allowance_mm':thread_route['slack_allowance_mm'],
        'coax_length_budget_mm':thread_route['length_budget_mm'],
        'status':'Nominal PCB and RF connector XY checked against manufacturer STEP; header seating, mated plug and formed bends require physical fit.'
    }
    return {'interior_component_containment':True,'pairwise_component_boxes_clear':True,'mount_containment':True,
            'native_rj45_access_clear':True,'zac93_antenna_air_space_clear':True,'cable_envelopes_clear':True,
            'plastic_body_intersections_mm3':plastic_collisions,'keepouts_mm':keepouts,'routes':routes,
            'thread_radio_nominal_fit':thread_fit,'regulator_subassembly_mm':regulator_details(p,m),
            'cable_sweeps_clear_of_printed_parts':True,'cable_sweeps_clear_of_native_modules':True,'native_module_boxes_mm':module_boxes,'carrier_mated_headers_clear':True,'carrier_mated_header_boxes_mm':native_header_boxes,'mated_connector_boxes_mm':connector_boxes,'detailed_component_solids_mm':detailed,'physical_fit_verified':False,'verification_scope':'Conservative digital envelopes and generated plastic only. Does not establish header orientation, material RF loss, purchased-part fit, thermal bias or RF coverage.'}

def regulator_shapes(p,m):
    """Sourced body envelopes with the same 2.54 mm pad plan as the wiring guide."""
    details=regulator_details(p,m);x,y,z=p['placements']['buck'];shapes=[]
    shapes.append((bodybox(details['perfboard']),'#9e844e'))
    reg=details['regulator'];shapes.append((bodybox(reg),'#252a30'))
    cap=details['input_capacitor'];diameter=cap[3]-cap[0]
    shapes.append((c.cylinder(diameter,cap[5]-cap[2]).move(((cap[0]+cap[3])/2,(cap[1]+cap[4])/2,cap[2])),'#46586c'))
    shapes.append((c.cylinder(diameter*.85,.2).move(((cap[0]+cap[3])/2,(cap[1]+cap[4])/2,cap[5])),'#a6b4c0'))
    # Row eight is cleared for the soft board restraint, as are the outer edges.
    for col in range(8):
        for row in range(7):
            shapes.append((c.cylinder(1.5,.05).move((x+3.11+col*2.54,y+3.11+row*2.54,13.6)),'#ceab6c'))
    for px in [5.65,8.19,10.73,18.35,20.89]:
        shapes.append((c.cylinder(.64,3.6).move((x+px,y+8.19,10)),'#b4bec4'))
    return shapes


def electronics(p,m,s,g):
    """Simplified, consistently located electronic solids for CAD explanation."""
    result=[]
    for key,bb in g['bounds'].items():
        x,y,z=bb[:3];w,h,d=[bb[i+3]-bb[i] for i in range(3)];color=COLORS[key]
        if key in ['poe_splitter','dc_adapter','fuse_holder']:result.append((bodybox(bb),color));continue
        if key=='carrier':
            result.append((c.box(s['width'],s['length'],1.6).move((x,y,z)),color))
            for part in s['design']['parts']:
                if not part['ref'].startswith('U'):continue
                v=part['body_bounds_global_mm'];a,b,aa,bb2=v
                result.append((c.box(aa-a,bb2-b,1.6).move((x+a,y+b,z+9)),'#183947'))
                result.append((c.box((aa-a)*.75,(bb2-b)*.6,5 if part['ref']!='U4' else 12).move((x+a+(aa-a)*.12,y+b+2,z+10.6)),'#b5bec4'))
            continue
        if key=='buck':
            result.extend(regulator_shapes(p,m));continue
        board_z=z+d-3.6 if key=='zwave' else z+3
        result.append((c.box(w,h,1.6).move((x,y,board_z)),color))
        if key=='zwave':
            result.append((c.box(8,13,9).move((x+2,y+2,board_z-9)),'#202226'))
            result.append((c.box(10,13,2).move((x+8,y+6,board_z+1.6)),'#a4a8ac'))
            # Stock printed trace antenna on the outboard edge; not an SMA.
            for yy in [2,7,12,17,22]:result.append((c.box(6,.6,.3).move((x+w-7,y+yy,board_z+1.6)),'#d2ac55'))
        elif key=='ld2450':
            for xx in [3,12,21,30]:result.append((c.box(5,6,.3).move((x+xx,y+4,board_z+1.6)),'#bdaa68'))
        else:result.append((c.box(w*.45,h*.5,max(1,min(d-4.6,4))).move((x+w*.25,y+h*.2,board_z+1.6)),'#252a30'))
    return result

def svg(p,m,g,checks):
    W=p['case']['width'];D=p['case']['length'];scale=3;ox=50;oy=120
    a=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1000" viewBox="0 0 1400 1000">',
       '<style>text{font-family:Arial,sans-serif;fill:#e7f0f5}.h{font-size:27px;font-weight:bold}.s{font-size:18px}.n{font-size:15px}</style>',
       '<rect width="1400" height="1000" fill="#10202e"/>',
       '<text x="40" y="45" class="h">FH1 full-hub enclosure · MC2-C + Z-Wave + RF + radar + ambient sensors</text>',
       '<text x="40" y="79" class="s">Top view, lid removed. Solid areas are component envelopes; dashed areas are reserved access/cable space.</text>',
       f'<rect x="{ox}" y="{oy}" width="{W*scale}" height="{D*scale}" fill="#263f4e" stroke="#7b9caa" stroke-width="8"/>']
    for key,bb in g['bounds'].items():
        x,y,x2,y2=bb[0],bb[1],bb[3],bb[4]
        a.append(f'<rect x="{ox+x*scale}" y="{oy+y*scale}" width="{(x2-x)*scale}" height="{(y2-y)*scale}" fill="{COLORS[key]}" stroke="#d2e1e8" stroke-dasharray="{6 if key=="ld2450" else 0}"/>')
        num=list(g['bounds']).index(key)+1
        a.append(f'<text x="{ox+(x+x2)/2*scale}" y="{oy+(y+y2)/2*scale}" text-anchor="middle" class="s">{num}</text>')
    for bb in checks['keepouts_mm'].values():
        a.append(f'<rect x="{ox+bb[0]*scale}" y="{oy+bb[1]*scale}" width="{(bb[3]-bb[0])*scale}" height="{(bb[4]-bb[1])*scale}" fill="none" stroke="#edc27a" stroke-width="2" stroke-dasharray="6 4"/>')
    for row in checks['routes']:
        pts=' '.join(f'{ox+pt[0]*scale},{oy+pt[1]*scale}' for pt in row['points_mm'])
        a.append(f'<polyline points="{pts}" fill="none" stroke="#92cdd2" stroke-width="3" stroke-dasharray="4 5"/>')
    for port in p['rf_ports']:
        x=port['center'][0];a.append(f'<text x="{ox+x*scale}" y="{oy-12}" class="n" text-anchor="middle">{port["label"]}</text>')
    for i,key in enumerate(g['bounds']):
        yy=140+i*62;size=m[key]['design_envelope_mm']
        a += [f'<text x="900" y="{yy}" class="s">{i+1}. {html.escape(LABELS[key])}</text>',f'<text x="900" y="{yy+25}" class="n">Envelope {size[0]:g} × {size[1]:g} × {size[2]:g} mm</text>']
    a += ['<text x="40" y="840" class="s">215 × 215 × 78 mm main case; attached ambient pod extends overall width to 277 mm.</text>',
          '<text x="40" y="873" class="s">ZAC93: 2×5 socket faces downward into the open cradle; stock antenna faces the plastic right wall.</text>',
          '<text x="40" y="906" class="s">LD2450 attaches to the lid, faces +Z through a 0.8 mm window; disconnect its harness before lifting lid away.</text>',
          '<text x="40" y="952" class="s" style="fill:#ffd294">Engineering prototype: digital clearances passed; print fit, exact board revision, cable bends, RF and temperature bias unmeasured.</text>','</svg>']
    return '\n'.join(a)+'\n'

def preview(out,p,m,s,g):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # Direct deterministic mesh rendering. AI images, if present, are separate.
    elec=electronics(p,m,s,g)
    for name,exploded in [('full-assembly-preview',False),('exploded-preview',True)]:
        shapes=[]
        for key,node in g['assembled'].items():
            shift=0
            if exploded:
                shift=150 if key=='lid' else 115 if key=='radar-holder' else 30 if key.endswith('-tray') else 90 if key=='bme680-pod-lid' else 0
            elif key in ['lid','radar-holder']:continue # cut-away open lid
            displace=(-120,80,190) if exploded and key=='lid' else (0,0,shift)
            shapes.append((node.move(displace),'#7b9b9e' if key=='base' else '#d3dce0' if key=='lid' else '#8caeb2'))
        for node,color in elec:
            # Radar and other components are separated by Z in the explanatory
            # view; their relative XY always remains assembly-exact.
            z0=c.mesh_of(node).bounds[0][2]
            shift=(115 if z0>=60 else 65) if exploded else 0
            shapes.append((node.move((0,0,shift)),color))
        fig=plt.figure(figsize=(16,14),facecolor='#0d1b29');ax=fig.add_axes([.01,.24,.98,.68]);ax.axis('off')
        ax.imshow(old.render_meshes(shapes,width=1700,height=1300))
        fig.suptitle('FH1 · full hub exploded assembly' if exploded else 'FH1 · all modules installed, lid removed',color='#edf3f7',fontsize=24,y=.96)
        # The labels are projected with exactly the renderer's camera/scale.
        import numpy as np
        cam=np.array([1.,-1.6,1.2]);cam/=np.linalg.norm(cam)
        right=np.cross(np.array([0.,0.,1.]),cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        vv=np.concatenate([c.mesh_of(node).vertices for node,col in shapes]);uv=np.column_stack((vv@right,-vv@up))
        lo=uv.min(axis=0);hi=uv.max(axis=0);scale=min((1700-80)/(hi[0]-lo[0]),(1300-70)/(hi[1]-lo[1]))
        for index,(key,bb) in enumerate(g['bounds'].items(),1):
            pos=np.array([(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,bb[5]])
            if exploded:pos[2]+=115 if key=='ld2450' else 65
            point=(np.array([pos@right,-pos@up])-(lo+hi)/2)*scale+[850,650]
            ax.annotate(str(index),point,color='white',ha='center',va='center',fontsize=12,bbox=dict(boxstyle='circle,pad=.25',fc='#10202e',ec='#b3cdd7',lw=1))
            column=(index-1)%3;row=(index-1)//3
            fig.text(.04+column*.325,.205-row*.033,f'{index}. {LABELS[key]}',color='#e2edf3',fontsize=11)
        fig.text(.04,.062,'Lid is displaced sideways for visibility; components lift vertically above their exact XY mounting locations.' if exploded else 'Lid removed; cable centerlines are documented in the numbered layout and verification report.',color='#c5dce5',fontsize=12)
        fig.text(.04,.038,'ZAC93 is the small blue board in the right bay. Fit, heights, antenna orientation and cable bends require physical verification.',color='#ffd294',fontsize=12)
        fig.savefig(out/(name+'.png'),dpi=130,facecolor=fig.get_facecolor());plt.close(fig)


def regulator_preview(out,p,m,g):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(14,7),facecolor='#0d1b29')
    for i,raised in enumerate([False,True]):
        ax=fig.add_axes([.02+i*.49,.20,.47,.65]);ax.axis('off')
        shapes=[(g['assembled']['buck-tray'],'#8caeb2')]
        shapes += [(node.move((0,0,14 if raised else 0)),color) for node,color in regulator_shapes(p,m)]
        ax.imshow(old.render_meshes(shapes,width=1000,height=850))
        ax.set_title('Installed on edge supports' if not raised else 'Perfboard lifted to show solder clearance',color='#e9f2f7',fontsize=16)
    fig.suptitle('PWR1 · RECOM R-78K3.3-1.0 + 27 µF input capacitor',color='#e9f2f7',fontsize=20,y=.96)
    fig.text(.04,.12,'24 × 24 × 1.6 mm isolated-pad board · four M2 tray screws · no holes in regulator or capacitor',color='#e9f2f7',fontsize=12)
    fig.text(.04,.08,'Clear rear band takes a soft strap; restrain the J2 harness separately. Keep capacitor vent open.',color='#e9f2f7',fontsize=12)
    fig.text(.04,.04,'CAD body envelopes; point-to-point wires and straps omitted for clarity. Physical fit and operation unverified.',color='#ffd294',fontsize=11)
    fig.savefig(out/'power-assembly-preview.png',dpi=140,facecolor=fig.get_facecolor());plt.close(fig)


def generate(out,p,package=True):
    m=manifest();s=source();g=geometry(p,m,s);checks=validate(p,m,s,g);out.mkdir(parents=True,exist_ok=True)
    report={'revision':p['revision'],'status':p['status'],'native_pcb_revision':s['design']['revision'],
            'source_sha256':{'build.py':sha(HERE/'build.py'),'test_build.py':sha(HERE/'test_build.py'),'print_package.py':sha(HERE/'print_package.py'),'test_print_package.py':sha(HERE/'test_print_package.py'),'parameters.json':sha(HERE/'parameters.json'),'components.json':sha(HERE/'components.json'),'rf-evidence.json':sha(HERE/'rf-evidence.json'),'../module-carrier/external-antenna-prototype/build.py':sha(old.HERE/'build.py'),**s['hashes']},
            'units':'mm','printer_profiles':p['printer_profiles'],'outer_case_mm':[p['case']['width'],p['case']['length'],p['case']['height']+p['case']['lid']],
            'overall_with_pod_mm':[277,215,78],'checks':checks,'component_bounds_mm':g['bounds'],'mounting':g['mounting'],'parts':{}}
    for key,node in g['nodes'].items():
        mesh=c.mesh_of(node);path=out/(key+'.stl');path.write_text(c.trimesh.exchange.stl.export_stl_ascii(mesh));actual=c.trimesh.load_mesh(path,process=True)
        assert actual.is_watertight and actual.is_winding_consistent and actual.volume>0 and len(actual.split())==1,f'{key} mesh invalid'
        assert abs(actual.bounds[0][2])<.01,f'{key} not flat on build plate'
        dim=actual.extents
        assert dim[0]+2*p['printer_profiles']['generic']['brim_mm']<=p['case']['print_bed'][0] and dim[1]+2*p['printer_profiles']['generic']['brim_mm']<=p['case']['print_bed'][1],f'{key} exceeds build plate'
        (out/(key+'.scad')).write_text('// Generated FH1 print part; mm. See parameters.json and physical-fit limits.\n'+node.scad+'\n')
        report['parts'][key]={'quantity':2 if key=='pod-arm' else 1,'watertight':True,'single_solid':True,'bounds_mm':actual.bounds.round(4).tolist(),'volume_mm3':round(float(actual.volume),3),'sha256':sha(path),'fits_220x220_plate':True}
    elec=electronics(p,m,s,g)
    assembly='// Review assembly only. Do not print as one object.\n'+'\n'.join('color("LightSteelBlue") {'+v.scad+'}' for v in g['assembled'].values())
    assembly+='\n'+'\n'.join('color("'+color+'") {'+node.scad+'}' for node,color in elec)
    (out/'assembly.scad').write_text(assembly+'\n')
    exploded=[]
    for key,node in g['assembled'].items():
        dz=190 if key=='lid' else 115 if key=='radar-holder' else 30 if key.endswith('-tray') else 90 if key=='bme680-pod-lid' else 0
        exploded.append('color("LightSteelBlue") {'+node.move((-120,80,190) if key=='lid' else (0,0,dz)).scad+'}')
    for node,color in elec:
        dz=115 if c.mesh_of(node).bounds[0][2]>=60 else 65
        exploded.append('color("'+color+'") {'+node.move((0,0,dz)).scad+'}')
    (out/'exploded.scad').write_text('// Exploded review only, not printable. Lid displaced sideways; component XY unchanged, Z offsets explanatory.\n'+'\n'.join(exploded)+'\n')
    (out/'layout.svg').write_text(svg(p,m,g,checks));preview(out,p,m,s,g);regulator_preview(out,p,m,g)
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FH1 complete radio hub enclosure</title><style>body{background:#10202e;color:#e9f2f7;font:18px system-ui;margin:0}main{max-width:1400px;padding:24px;margin:auto}a{color:#84e7cf}a:focus-visible{outline:3px solid #fff;outline-offset:4px}img{width:100%}p,li{line-height:1.6}.download{display:inline-block;background:#84e7cf;color:#10202e;padding:12px 18px;font-weight:bold;border-radius:6px}.notice{border-left:4px solid #f6c575;padding:4px 20px;background:#192d3e}.table-scroll{overflow-x:auto}table{border-collapse:collapse;font-size:16px;width:100%}caption{text-align:left;margin:14px 0}th,td{padding:12px;border-bottom:1px solid #416073;text-align:left;vertical-align:top}thead{background:#192d3e}@media print{body{background:white;color:black}a{color:black}main{padding:0}.download{display:none}table{font-size:11px}th,td{padding:6px}.table-scroll{overflow:visible}}</style><main><h1>FH1 complete radio hub enclosure</h1><nav aria-label="Build navigation"><a href="../../guide/index.html">Build guide</a> · <a href="../../guide/print.html">Print and assembly instructions</a> · <a href="#print-parts">Download print parts</a> · <a href="verification.json">Digital verification</a> · <a href="components.json">Component sources and fit uncertainty</a> · <a href="assembly.scad">Editable assembly</a> · <a href="exploded.scad">Exploded model</a></nav><p><strong>FH1-MC2-C-PWR1: MC2-C with TinyC6[D] TC6D-01.</strong> PWR1 adds the RECOM R-78K3.3-1.0 and 27 µF input capacitor on a 24 × 24 mm perfboard with a revised tray. It retains RF1 Taoglas CAB.618.E cables, round 6.8 mm ports and a matching 3 mm thick fit coupon. Earlier D-hole base files are superseded. <a href="rf-evidence.json">RF fit evidence</a>. The Thread board outline and relocated U.FL socket follow the manufacturer STEP model. Use the MC2-C RCP firmware to select the external antenna. <a href="sources.md#tinyc6d-revision-change">Source and fit evidence</a>.</p><p>Every module has a declared location and mechanical retention. Digital checks do not replace measuring the actual ZAC93, other purchased modules, connector access, print tolerance or RF testing.</p><section id="print-parts"><h2>Download and print in stages</h2><p><a class="download" download href="'+printing.ARCHIVE+'">Download all 14 STL files + print checklist (ZIP)</a></p><p><a href="PRINT-FIRST.txt">Read the print-first checklist</a> · <a href="print-manifest.json">Quantities and SHA-256 manifest</a> · <a href="README.md">Markdown instructions</a></p><div class="notice"><p><strong>Start with the fit coupon and ZAC93 cradle.</strong> Confirm the real socket, mating header, fasteners and SMA bulkhead fit with power disconnected. Then check the other small parts before printing the large base and lid. The existing CC1101, DC adapter and fuse must be measured.</p><p><strong>Print two pod arms.</strong> Reuse the first ZAC93 cradle if it fits. The CC1101 port blank is optional. Physical fit remains unverified.</p></div><p>Use millimetres, 100% scale and the supplied bed orientation. Largest part: 215 × 215 mm. The nominal TRONXY XY-3 bed is 310 × 310 mm; check the actual printable area and brim in the slicer. A generic 220 × 220 mm bed allows only 2.5 mm per edge. Assembly and exploded SCAD files are inspection models, not combined print jobs.</p>'+printing.print_table()+'</section><h2>RECOM power assembly</h2><img src="power-assembly-preview.png" alt="RECOM and input capacitor on a removable 24 mm perfboard tray, installed and lifted views"><p>Use the cleared rear band for a soft board restraint and a separate loop for cable strain relief. No mounting holes are assumed in either purchased component. <a href="README.md">Assembly details</a>.</p><h2>Where the parts fit</h2><img src="exploded-preview.png" alt="Exploded full hub, generated from print meshes and component envelopes"><img src="layout.svg" alt="Numbered layout locating all hub components and cable reservations"><img src="full-assembly-preview.png" alt="Open full hub with every component"><p>Main shell 215 × 215 × 78 mm; BME680 pod attached across a 17 mm air gap. Radar faces the room through the lid. ZAC93 stock antenna stays unmodified.</p></main></html>\n')
    outputs=[name+suffix for name in g['nodes'] for suffix in ['.stl','.scad']]+['assembly.scad','exploded.scad','layout.svg','full-assembly-preview.png','exploded-preview.png','power-assembly-preview.png','index.html']
    report['generated_sha256']={name:sha(out/name) for name in sorted(outputs)}
    report=json.loads(json.dumps(report))
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    # ZIP and manifest describe these stored STL bytes, independent of a
    # different platform's equivalent mesh serialization.
    if package: printing.publish(out)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();p=json.loads((HERE/'parameters.json').read_text())
    if args.check:
        with tempfile.TemporaryDirectory() as td:
            generate(Path(td),p,package=False)
            portable.check_outputs(HERE,Path(td),c)
        printing.publish(HERE,check=True)
        print('FH1 full-hub geometry and print package reproducible; all digital checks pass. Physical fit remains unverified.')
    else:
        report=generate(HERE,p);print('Generated',len(report['parts']),'unique print parts; digital component/cable/mesh checks passed.')
if __name__=='__main__':main()
