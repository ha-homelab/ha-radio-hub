#!/usr/bin/env python3
"""Prepare a locked existing route for a second, fine-pitch escape routing pass.

Existing power trunks are retained. Only unconnected items may receive narrow
0.2 mm escape routing. Native DRC and the final connectivity validator remain
mandatory after the completion session is imported.
"""
import math, heapq, json, argparse, re
from pathlib import Path
import pcbnew as pcb
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'.build'

def ground_escape(board,pad,ground):
    """Connect a trapped fine-pitch ground pad to the reference plane.

Search only a short straight 0.2mm escape with a fully cleared 0.8mm via.
The native checker is still authoritative after the polygons are refilled.
"""
    origin=pad.GetPosition();foreign=[]
    for item in [p for f in board.GetFootprints() for p in f.Pads()]+list(board.GetTracks()):
      if item.GetNetname()=='gnd':continue
      shape=item.GetEffectiveShape(item.GetLayer());bb=item.GetBoundingBox();bb.Inflate(pcb.FromMM(3))
      foreign.append((item,shape,bb,pcb.FromMM(2.5 if item.GetNetname().startswith('POE_') else .2)))
    options=sorted((math.hypot(x,y),x,y) for x in range(-20,21) for y in range(-20,21) if 4<=math.hypot(x,y)<=20)
    for _,dx,dy in options:
      p=pcb.VECTOR2I(origin.x+pcb.FromMM(dx*.2),origin.y+pcb.FromMM(dy*.2))
      circle=pcb.SHAPE_CIRCLE(p,pcb.FromMM(.4));line=pcb.SHAPE_SEGMENT(origin,p,pcb.FromMM(.2));blocked=False
      for item,shape,bb,clearance in foreign:
        if not bb.Contains(p) and not bb.Contains(origin):continue
        if shape.Collide(circle,clearance) or (item.IsOnLayer(pcb.F_Cu) and shape.Collide(line,clearance)):
          blocked=True;break
      if blocked:continue
      if any(z.GetIsRuleArea() and (z.Outline().Collide(circle,pcb.FromMM(.2)) or z.Outline().Collide(line,pcb.FromMM(.2))) for z in board.Zones()):continue
      t=pcb.PCB_TRACK(board);t.SetStart(origin);t.SetEnd(p);t.SetWidth(pcb.FromMM(.2));t.SetLayer(pcb.F_Cu);t.SetNet(ground);t.SetLocked(True);board.Add(t)
      v=pcb.PCB_VIA(board);v.SetPosition(p);v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(ground);v.SetLocked(True);board.Add(v)
      print('Ground pad escape:',pad.GetParentFootprint().GetReference(),pad.GetNumber(),pcb.ToMM(p.x),pcb.ToMM(p.y));return True
    # A bounded grid search handles pads trapped behind existing top-side traces.
    nearby=[q for q in foreign if q[2].Contains(origin)]
    queue=[(0.0,(0,0))];distance={(0,0):0.0};previous={};done=set()
    def point(node):return pcb.VECTOR2I(origin.x+pcb.FromMM(node[0]*.2),origin.y+pcb.FromMM(node[1]*.2))
    def clear_shape(shape,top_only):
      for item,obstacle,bb,clearance in nearby:
        if top_only and not item.IsOnLayer(pcb.F_Cu):continue
        if obstacle.Collide(shape,clearance):return False
      return not any(z.GetIsRuleArea() and z.Outline().Collide(shape,pcb.FromMM(.2)) for z in board.Zones())
    target=None
    while queue:
      cost,node=heapq.heappop(queue)
      if node in done:continue
      done.add(node);pos=point(node)
      if cost>.8 and clear_shape(pcb.SHAPE_CIRCLE(pos,pcb.FromMM(.4)),False):target=node;break
      if cost>6:continue
      for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        nxt=(node[0]+dx,node[1]+dy)
        if max(abs(nxt[0]),abs(nxt[1]))>25:continue
        value=cost+.2*math.hypot(dx,dy)
        if value>=distance.get(nxt,float('inf')):continue
        if not clear_shape(pcb.SHAPE_SEGMENT(pos,point(nxt),pcb.FromMM(.2)),True):continue
        distance[nxt]=value;previous[nxt]=node;heapq.heappush(queue,(value,nxt))
    if target is None:return False
    nodes=[target]
    while nodes[-1]!=(0,0):nodes.append(previous[nodes[-1]])
    for a,b in zip(nodes,nodes[1:]):
      t=pcb.PCB_TRACK(board);t.SetStart(point(a));t.SetEnd(point(b));t.SetWidth(pcb.FromMM(.2));t.SetLayer(pcb.F_Cu);t.SetNet(ground);t.SetLocked(True);board.Add(t)
    v=pcb.PCB_VIA(board);v.SetPosition(point(target));v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(ground);v.SetLocked(True);board.Add(v)
    print('Ground pad bounded escape:',pad.GetParentFootprint().GetReference(),pad.GetNumber(),round(distance[target],3));return True

def ground_stitch(board):
    ground=next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='gnd')
    zones=[z for z in board.Zones() if not z.GetIsRuleArea() and z.GetLayer()==pcb.F_Cu]
    items=[p for f in board.GetFootprints() for p in f.Pads()]+list(board.GetTracks())
    vias=[t for t in board.GetTracks() if isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='gnd']
    gnd_pth=[p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()=='gnd' and p.GetAttribute()==pcb.PAD_ATTRIB_PTH]
    count=0
    for z in zones:
      polys=z.GetFilledPolysList(pcb.F_Cu)
      for i in range(polys.OutlineCount()):
        if any(polys.Contains(v.GetPosition(),i) for v in vias+gnd_pth):continue
        box=polys.COutline(i).BBox();center=box.GetCenter()
        candidates=[]
        for x in range(box.GetX(),box.GetRight()+1,pcb.FromMM(.25)):
          for y in range(box.GetY(),box.GetBottom()+1,pcb.FromMM(.25)):
            candidates.append((math.hypot(x-center.x,y-center.y),x,y))
        for _,x,y in sorted(candidates):
          p=pcb.VECTOR2I(x,y)
          if not all(polys.Contains(pcb.VECTOR2I(round(x+pcb.FromMM(.41)*math.cos(a*math.pi/4)),round(y+pcb.FromMM(.41)*math.sin(a*math.pi/4))),i) for a in range(8)):continue
          circle=pcb.SHAPE_CIRCLE(p,pcb.FromMM(.4));blocked=False
          for item in items:
            if item.GetNetname()=='gnd':continue
            clearance=pcb.FromMM(2.5 if item.GetNetname().startswith('POE_') else .2)
            if item.GetEffectiveShape(item.GetLayer()).Collide(circle,clearance):blocked=True;break
          if blocked:continue
          if any(k.GetIsRuleArea() and k.Outline().Collide(circle,pcb.FromMM(.2)) for k in board.Zones()):continue
          v=pcb.PCB_VIA(board);v.SetPosition(p);v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(ground);v.SetLocked(True);board.Add(v);vias.append(v);items.append(v);count+=1;break
        else:
          pads=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()=='gnd' and polys.Contains(p.GetPosition(),i)]
          print('Ground island requires narrow escape:',pads)
          for f in board.GetFootprints():
            for pad in f.Pads():
              if pad.GetNetname()=='gnd' and polys.Contains(pad.GetPosition(),i):ground_escape(board,pad,ground)
    print('Added local ground stitching vias:',count)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reroute-open',action='store_true',help='Reroute complete non-critical nets listed by the latest native DRC report');args=parser.parse_args()
    board=pcb.LoadBoard(str(ROOT/'integrated.kicad_pcb'))
    report=BUILD/'routing-check.json'
    if args.reroute_open:
      nets=set()
      for violation in json.loads(report.read_text())['unconnected_items']:
        for item in violation['items']:
          match=re.search(r'\[([^]]+)\]',item['description'])
          if match:nets.add(match.group(1))
      protected={'eth_txp','eth_txn','eth_rxp','eth_rxn','mag_rxp','mag_rxn','usb_dp','usb_dm','usb_dp_mcu','usb_dm_mcu','usb_dp_port','usb_dm_port','gnd'}
      if nets & protected:raise SystemExit('Refusing to rip up a protected pair or ground reference')
      removed=[t for t in board.GetTracks() if t.GetNetname() in nets]
      for t in removed:board.Remove(t)
      print('Reroute entire affected nets:',sorted(nets))
    else:
      from local_repairs import repair
      ground_stitch(board)
      repair(board)
    if args.reroute_open and 'eth_tocap' in nets:
      from tocap_escape import add
      add(board)
    zone_refs=list(board.Zones())
    for z in zone_refs:
      if z.GetZoneName()=='No copper below RJ45 transformer body':
        board.Remove(z)
        k=pcb.ZONE(board);k.SetIsRuleArea(True);k.SetLayerSet(pcb.LSET.AllCuMask());k.SetDoNotAllowPads(False);k.SetDoNotAllowTracks(True);k.SetDoNotAllowVias(True);k.SetDoNotAllowZoneFills(True);k.SetZoneName('No copper below RJ45 transformer body');o=k.Outline();o.NewOutline()
        for x,y in [(0,94),(17,94),(17,106),(0,106)]:o.Append(pcb.FromMM(x),pcb.FromMM(y))
        board.Add(k)
      elif not z.GetIsRuleArea() and z.GetLayer() in (pcb.F_Cu,pcb.B_Cu):board.Remove(z)
    for t in board.GetTracks():t.SetLocked(True)
    # Existing 0.8mm power trunks are locked; this pass only completes escapes.
    board.GetDesignSettings().m_NetSettings.GetNetclasses()['Power'].SetTrackWidth(pcb.FromMM(.2))
    board.BuildConnectivity();pcb.SaveBoard(str(BUILD/'completion.kicad_pcb'),board)
    pcb.ExportSpecctraDSN(board,str(BUILD/'completion.dsn'))
    s=(BUILD/'completion.dsn').read_text().replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)')
    p=s.index('  (wiring\n');k=s[:p].rfind('  )')
    s=s[:k]+'    (class_class (classes PoE kicad_default) (rule (clearance 2500)))\n    (class_class (classes PoE Power) (rule (clearance 2500)))\n'+s[k:]
    (BUILD/'completion.dsn').write_text(s)
