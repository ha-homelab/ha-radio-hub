"""Deterministic local ground escapes and short post-route connections."""
import pcbnew as pcb

def repair(board):
    def point(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
    nets={n.GetNetname():n for n in board.GetNetInfo().NetsByNetcode().values()}
    def route(net,coords,layer=pcb.F_Cu,width=.2):
      for a,b in zip(coords,coords[1:]):
        t=pcb.PCB_TRACK(board);t.SetStart(point(*a));t.SetEnd(point(*b));t.SetWidth(pcb.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);board.Add(t)
    original_tracks=list(board.GetTracks()); removals=[]
    for a,b in [((83.1375,56.425),(84.8,56.425)),((88.8625,63.575),(87.2,63.575))]:
      line=pcb.SHAPE_SEGMENT(point(*a),point(*b),pcb.FromMM(.2));circle=pcb.SHAPE_CIRCLE(point(*b),pcb.FromMM(.4))
      # Release only conflicting signal copper; the subsequent completion pass
      # must reconnect it and native DRC must report zero opens.
      removed=0
      for t in original_tracks:
        if t.GetNetname()=='gnd':continue
        shape=t.GetEffectiveShape(t.GetLayer())
        if shape.Collide(circle,pcb.FromMM(.2)) or (t.IsOnLayer(pcb.F_Cu) and shape.Collide(line,pcb.FromMM(.2))):removals.append(t);removed+=1
      route('gnd',[a,b]);v=pcb.PCB_VIA(board);v.SetPosition(point(*b));v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(nets['gnd']);v.SetLocked(True);board.Add(v)
      print('Reserved ground escape; reroute segments:',removed)
    for t in {t.m_Uuid.AsString():t for t in removals}.values():board.Remove(t)
    board._removed_tracks=removals
    route('chassis',[(17.825,91.9355),(18,91.9355),(18,108.0645),(17.825,108.0645)],pcb.B_Cu)
    # Give the missing analogue supply pad a direct internal-side escape.
    supply=[(59.25,108.1625),(59.25,107.3),(60.4562,106.25)]
    for t in list(board.GetTracks()):
      if t.GetNetname()!='eth_tocap' or not t.IsOnLayer(pcb.F_Cu):continue
      if any(t.GetEffectiveShape(pcb.F_Cu).Collide(pcb.SHAPE_SEGMENT(point(*a),point(*b),pcb.FromMM(.2)),pcb.FromMM(.2)) for a,b in zip(supply,supply[1:])):
        board.Remove(t);removals.append(t)
    route('3v3_analog',supply)
    route('POE_78',[(40.475,111),(40.475,119.53),(37.62,119.53)],width=.5)
