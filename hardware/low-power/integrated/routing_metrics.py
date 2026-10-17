#!/usr/bin/env python3
"""Measure copper centerline length and pad-to-pad shortest paths (pad copper excluded).
Vias have zero geometric length in the planar metric; layer transitions are counted.
This is a routing sanity check, not an impedance or propagation-delay simulation.
"""
import heapq,math
from collections import defaultdict

def measure(board,child,children,net_name):
 lookup={n[1]:n[2] for n in children(board,'net') if len(n)>2}
 segments=defaultdict(list);via_at=defaultdict(list);pads=defaultdict(list)
 for s in children(board,'segment'):
  n=net_name(child(s,'net'),lookup);a=tuple(map(float,child(s,'start')[1:3]));b=tuple(map(float,child(s,'end')[1:3]));layer=child(s,'layer')[1]
  segments[n].append((a,b,layer))
 for v in children(board,'via'):via_at[net_name(child(v,'net'),lookup)].append(tuple(map(float,child(v,'at')[1:3])))
 for f in children(board,'footprint'):
  ref=next(p[2] for p in children(f,'property') if p[1]=='Reference');at=child(f,'at');fx,fy=map(float,at[1:3]);angle=math.radians(float(at[3]) if len(at)>3 else 0)
  for p in children(f,'pad'):
   n=net_name(child(p,'net'),lookup)
   if not n:continue
   pa=child(p,'at');px,py=map(float,pa[1:3]);cx=fx+px*math.cos(angle)+py*math.sin(angle);cy=fy-px*math.sin(angle)+py*math.cos(angle);w,h=map(float,child(p,'size')[1:3]);pa_angle=math.radians(float(pa[3]) if len(pa)>3 else math.degrees(angle))
   pads[n].append((ref+'.'+p[1],cx,cy,w,h,pa_angle,child(p,'layers')[1:]))
 def path(net,start,end):
  seg=segments[net];layers={x[2] for x in seg};points={(round(p[0],6),round(p[1],6),l) for a,b,l in seg for p in (a,b)}
  for x,y in via_at[net]:points.update((round(x,6),round(y,6),l) for l in layers)
  g=defaultdict(list)
  def edge(a,b,length,via=0):g[a].append((b,length,via));g[b].append((a,length,via))
  for a,b,l in seg:
   dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
   on=[]
   for p in points:
    if p[2]!=l:continue
    t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(length*length) if length else 0
    if -.000001<=t<=1.000001 and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)<.00001:on.append((t,p))
   on.sort()
   for (_,u),(_,v) in zip(on,on[1:]):edge(u,v,math.hypot(u[0]-v[0],u[1]-v[1]))
  for x,y in via_at[net]:
   vs=[p for p in points if abs(p[0]-x)<1e-5 and abs(p[1]-y)<1e-5]
   for i,u in enumerate(vs):
    for v in vs[i+1:]:edge(u,v,0,1)
  for label,x,y,w,h,a,pl in pads[net]:
   for p in points:
    dx,dy=p[0]-x,p[1]-y;xx=dx*math.cos(a)-dy*math.sin(a);yy=dx*math.sin(a)+dy*math.cos(a)
    if (p[2] in pl or '*.Cu' in pl) and abs(xx)<=w/2+1e-5 and abs(yy)<=h/2+1e-5:edge(label,p,0)
  q=[(0.,0,0,start,frozenset())];counter=0;best={}
  while q:
   d,vc,_,u,used=heapq.heappop(q)
   if u in best:continue
   best[u]=(d,vc)
   if u==end:return {'track_mm':round(d,3),'via_transitions':vc,'layers':sorted(used)}
   for v,length,via in g[u]:
    if v in best:continue
    counter+=1;heapq.heappush(q,(d+length,vc+via,counter,v,used|({v[2]} if isinstance(v,tuple) and length else set())))
  return {'error':'No copper-only path found; inspect native connectivity.'}
 endpoints={'eth_txp':('U4.2','J1.2'),'eth_txn':('U4.1','J1.9'),'eth_rxp':('U4.6','C34.1'),'eth_rxn':('U4.5','C35.1'),'mag_rxp':('C34.2','J1.1'),'mag_rxn':('C35.2','J1.8'),'usb_dp':('U1.14','R20.2'),'usb_dm':('U1.13','R19.2'),'usb_dp_port':('R20.1','J2.A6'),'usb_dm_port':('R19.1','J2.A7')}
 paths={n:{'from':a,'to':b,**path(n,a,b),'total_net_track_mm':round(sum(math.dist(a,b) for a,b,l in segments[n]),3),'total_net_vias':len(via_at[n])} for n,(a,b) in endpoints.items()}
 pairs={}
 for label,pos,neg in [('ethernet_tx',['eth_txp'],['eth_txn']),('ethernet_rx',['eth_rxp','mag_rxp'],['eth_rxn','mag_rxn']),('usb',['usb_dp','usb_dp_port'],['usb_dm','usb_dm_port'])]:
  if all('track_mm' in paths[n] for n in pos+neg):
   p=sum(paths[n]['track_mm'] for n in pos);m=sum(paths[n]['track_mm'] for n in neg);pairs[label]={'positive_track_mm':round(p,3),'negative_track_mm':round(m,3),'track_skew_mm':round(abs(p-m),3)}
 return {'method':'Planar track-centerline shortest path. Pad and series-component body lengths excluded; via barrel length excluded. Not impedance/delay qualification.','paths':paths,'pairs':pairs}
