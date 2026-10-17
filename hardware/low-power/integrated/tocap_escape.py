"""Reserve the W5500 internal-regulator capacitor escape before final routing."""
import pcbnew as pcb

def add(board):
 def pt(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
 net=next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='eth_tocap')
 a=pt(61.75,108.1625);b=pt(61.75,109.4)
 shapes=[pcb.SHAPE_SEGMENT(a,b,pcb.FromMM(.2)),pcb.SHAPE_CIRCLE(b,pcb.FromMM(.4))]
 removed=[]
 for t in board.GetTracks():
  if t.GetNetname()!='gnd' or isinstance(t,pcb.PCB_VIA) or not t.IsOnLayer(pcb.F_Cu):continue
  if any(t.GetEffectiveShape(pcb.F_Cu).Collide(s,pcb.FromMM(.2)) for s in shapes):removed.append(t)
 for t in removed:board.Remove(t)
 board._tocap_removed=removed
 t=pcb.PCB_TRACK(board);t.SetStart(a);t.SetEnd(b);t.SetWidth(pcb.FromMM(.2));t.SetLayer(pcb.F_Cu);t.SetNet(net);t.SetLocked(True);board.Add(t)
 v=pcb.PCB_VIA(board);v.SetPosition(b);v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(net);v.SetLocked(True);board.Add(v)
 print('Reserved TOCAP escape; replaced local ground segments:',len(removed))

def restore_ground_return(board):
 """Keep pad19 grounded after the TOCAP via occupies the outer escape."""
 def pt(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
 def coords(p):return (round(pcb.ToMM(p.x),4),round(pcb.ToMM(p.y),4))
 wanted=[{(62.25,108.1625),(62.25,107.231)},{(62.25,107.231),(61.269,106.25)},{(61.269,106.25),(60.4562,106.25)}]
 old=[t for t in board.GetTracks() if not isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='3v3_analog' and t.GetLayer()==pcb.F_Cu and {coords(t.GetStart()),coords(t.GetEnd())} in wanted]
 if len(old)!=3:return
 for t in old:board.Remove(t)
 board._return_removed=old
 nets={n.GetNetname():n for n in board.GetNetInfo().NetsByNetcode().values()}
 def route(net,points):
  for a,b in zip(points,points[1:]):
   t=pcb.PCB_TRACK(board);t.SetStart(pt(*a));t.SetEnd(pt(*b));t.SetWidth(pcb.FromMM(.2));t.SetLayer(pcb.F_Cu);t.SetNet(nets[net]);t.SetLocked(True);board.Add(t)
 route('3v3_analog',[(62.25,108.1625),(62.25,107.35),(62.0,107.1),(62.0,105.8),(60.4562,105.8),(60.4562,106.25)])
 route('gnd',[(61.25,108.1625),(61.25,106.9)])
 v=pcb.PCB_VIA(board);v.SetPosition(pt(61.25,106.9));v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(nets['gnd']);v.SetLocked(True);board.Add(v)
 print('Restored dedicated W5500 pad19 ground return')
