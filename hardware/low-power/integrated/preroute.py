"""Short F.Cu PHY routes and ground stitching, reserved before autorouting."""
import math
import pcbnew as pcb

def add_phy_routes(board):
 fps={f.GetReference():f for f in board.GetFootprints()}
 def pad(ref,num):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))
 def xy(p):return (pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y))
 def route(net,pts):
  ni=next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()==net)
  for a,b in zip(pts,pts[1:]):
   if math.dist(a,b)<.00001:continue
   t=pcb.PCB_TRACK(board);t.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])));t.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]),pcb.FromMM(b[1])));t.SetWidth(pcb.FromMM(.2));t.SetLayer(pcb.F_Cu);t.SetNet(ni);t.SetLocked(True);board.Add(t)
 route('eth_txp',[xy(pad('U4',2)),(55.8,101.75),(54.502,103.048),(50,103.048),xy(pad('J1',2))])
 route('eth_txn',[xy(pad('U4',1)),(55.5,101.25),(54.718,102.032),(50,102.032),(49,101.032),(47,101.032),(46,102.032),xy(pad('J1',9))])
 route('eth_txp',[(50,103.048),xy(pad('R31',1))])
 route('eth_txn',[(46,102.032),xy(pad('R32',1))])
 route('eth_rxn',[xy(pad('U4',5)),(55.3,103.25),(54.55,104),(51.5,104),(51.5,105),(52.3,105),(52.3,106),(50,106),(50,108),(47.5,108),xy(pad('C35',1))])
 route('eth_rxp',[xy(pad('U4',6)),(55.5,103.75),(49.25,110),(48,110),xy(pad('C34',1))])
 route('eth_rxn',[(47.5,108),xy(pad('R35',1))])
 route('eth_rxp',[(48,110),xy(pad('R34',1))])
 route('mag_rxn',[xy(pad('J1',8)),(40,104.064),(43.55,107.614),xy(pad('C35',2))])
 route('mag_rxp',[xy(pad('J1',1)),(40,105.08),(41.6,106.68),(41.6,110),xy(pad('C34',2))])
 # Reserved pad23 direct ground return on the lower side of the PHY package.
 p=pad('U4',23);vxy=(63.25,109.8);route('gnd',[xy(p),vxy])
 ni=next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='gnd')
 v=pcb.PCB_VIA(board);v.SetPosition(pcb.VECTOR2I(pcb.FromMM(vxy[0]),pcb.FromMM(vxy[1])));v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(ni);v.SetLocked(True);board.Add(v)

def add_stitching(board):
 gnd=next(n for n in board.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='gnd')
 # Reserve nearby returns before the router fills the available channels.
 keepouts=[(15,0,70,18),(80,0,104,17),(141.05,0,149.85,4.8),(66,119,72,141),(0,91,42,117)]
 for x in range(15,156,10):
  for y in range(15,137,10):
   if y>117 and x<73:continue
   if any(a-.7<x<c+.7 and b-.7<y<d+.7 for a,b,c,d in keepouts):continue
   pt=pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
   blocked=False
   for f in board.GetFootprints():
    for p in f.Pads():
     bb=p.GetBoundingBox();bb.Inflate(pcb.FromMM(.7))
     if bb.Contains(pt):blocked=True;break
    if blocked:break
   if blocked:continue
   for t in board.GetTracks():
    bb=t.GetBoundingBox();bb.Inflate(pcb.FromMM(.7))
    if bb.Contains(pt):blocked=True;break
   if blocked:continue
   v=pcb.PCB_VIA(board);v.SetPosition(pt);v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(gnd);v.SetLocked(True);board.Add(v)
