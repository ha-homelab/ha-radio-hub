#!/usr/bin/env python3
"""Finish logical nets the optional autorouter could not route.
Add dedicated wire holes with clearance-checked bottom stubs; top insulated
routes go around expanded component envelopes. Output still needs native and
independent validation. Run once while authoring routing-plan.json.
"""
from pathlib import Path
from collections import defaultdict
import json,math,heapq
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'routing-plan.json').read_text());boxes=[box(*r) for r in json.loads((ROOT/'.build/courtyards.json').read_text())]
holes=[p['xy'] for p in j['pads']]+[t['xy'] for t in j['terminals']]
# Raised adapters leave their middle clear; header insulators occupy these strips.
for x,y,span,height in [(85,60,15.24,33.02),(67,101,7.62,5.08)]:
 for xx in [x,x+span]:boxes.append(box(xx-1.5,y-1.5,xx+1.5,y+height+1.5))
shapes=[]
for p in j['pads']:
 x,y=p['xy'];w,h=p['size'];geom=box(x-w/2,y-h/2,x+w/2,y+h/2) if p['shape']=='rect' else Point(x,y).buffer(w/2)
 shapes.append((p['physical_net'] or p['id'],geom))
for t in j['bottom_tracks']:shapes.append((t['physical_net'],LineString([t['a'],t['b']]).buffer(t['width']/2)))
for t in j['terminals']:shapes.append((t['physical_net'],Point(t['xy']).buffer(1)))
parent={p['physical_net']:p['physical_net'] for p in j['pads'] if p['physical_net']}
for t in j['terminals']:parent[t['physical_net']]=t['physical_net']
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
def union(a,b):parent[root(a)]=root(b)
uses=defaultdict(int)
for w in j['wires']:union(w['from_net'],w['to_net']);uses[w['from_terminal']]+=1;uses[w['to_terminal']]+=1
nets=defaultdict(set)
for p in j['pads']:
 if p['physical_net']:nets[p['net']].add(p['physical_net'])
points=defaultdict(list)
for p in j['pads']:
 if p['physical_net']:points[p['physical_net']].append(p['xy'])
for t in j['terminals']:points[t['physical_net']].append(t['xy'])
tree=None;tree_count=-1
def safe_geom(n,g):
 global tree,tree_count
 if tree_count!=len(shapes):tree=STRtree([s for _,s in shapes]);tree_count=len(shapes)
 return all(n==shapes[i][0] or g.distance(shapes[i][1])>.502 for i in tree.query(g.buffer(.503)))
def add_terminal(n,logical,target):
 existing=[t for t in j['terminals'] if t['physical_net']==n and uses[t['ref']]<(1 if t.get('kind')=='adapter_pin' else 2)]
 if existing:return min(existing,key=lambda t:math.dist(t['xy'],target))
 width=1.2 if logical in ['GND','+3V3','+5V','+5V_IN'] else .6
 candidates=[]
 for start in points[n]:
  for radius in [2.54,3,4,5,6,7,8,10,12,15]:
   for angle in range(0,360,15):
    q=[round(start[0]+radius*math.cos(math.radians(angle)),6),round(start[1]+radius*math.sin(math.radians(angle)),6)]
    if not(2<q[0]<188 and 2<q[1]<143):continue
    pad=Point(q).buffer(1)
    if any(pad.distance(b)<.2 for b in boxes) or any(math.dist(q,h)<1.4 for h in holes):continue
    line=LineString([start,q]).buffer(width/2)
    if safe_geom(n,pad) and safe_geom(n,line):candidates.append((radius*.5+math.dist(q,target),q,start,pad,line))
 if not candidates:
  # A straight fanout can be blocked by a routed neighbor. Search a local
  # bottom-copper escape corridor before declaring the layout impossible.
  for start in points[n]:
   heap=[(0,(0,0))];seen=set();previous={};found=None
   while heap:
    _,node=heapq.heappop(heap)
    if node in seen:continue
    seen.add(node);q=[round(start[0]+node[0]*.25,6),round(start[1]+node[1]*.25,6)]
    pad=Point(q).buffer(1)
    if len(seen)>1 and not any(pad.distance(b)<.2 for b in boxes) and all(math.dist(q,h)>=1.4 for h in holes) and safe_geom(n,pad):found=node;break
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
     nxt=(node[0]+dx,node[1]+dy)
     if nxt in seen or abs(nxt[0])>80 or abs(nxt[1])>80:continue
     r=[round(start[0]+nxt[0]*.25,6),round(start[1]+nxt[1]*.25,6)]
     if not(2<r[0]<188 and 2<r[1]<143):continue
     line=LineString([q,r]).buffer(width/2)
     if not safe_geom(n,line):continue
     if nxt not in previous:previous[nxt]=node
     heapq.heappush(heap,(math.hypot(*nxt),nxt))
   if found:
    path=[found]
    while path[-1]!=(0,0):path.append(previous[path[-1]])
    path=[[round(start[0]+x*.25,6),round(start[1]+y*.25,6)] for x,y in path[::-1]]
    for a,b in zip(path,path[1:]):
     j['bottom_tracks'].append(dict(id='escape'+str(len(j['bottom_tracks'])),via=False,net=logical,a=a,b=b,width=width,layer='B.Cu',physical_net=n))
     shapes.append((n,LineString([a,b]).buffer(width/2)))
    candidates.append((math.dist(q,target),q,q,pad,Point(q).buffer(width/2)));break
 if not candidates:
  # A raised adapter exposes its long header shaft. This is a real soldered
  # joint, not an invented second drill hole at the same copper pad.
  pins=[p for p in j['pads'] if p['physical_net']==n and p['id'].split('.')[0] in ['U1','U2'] and not any(t.get('physical_pin')==p['id'] for t in j['terminals'])]
  if not pins:raise RuntimeError(('no clear bottom escape for wire hole',n))
  pin=min(pins,key=lambda p:math.dist(p['xy'],target))
  term=dict(ref='E'+str(1+sum(t.get('kind')=='adapter_pin' for t in j['terminals'])),kind='adapter_pin',physical_pin=pin['id'],xy=pin['xy'],logical_net=logical,physical_net=n,drill_mm=None,connection_height_mm=4,notes='Solder one insulated wire to the exposed adapter header shaft at 4mm above D0 BEFORE installing the adapter at 6mm underside height. No additional hole. Insulate and strain-relieve; inspect clearance to adjacent pins.')
  j['terminals'].append(term);return term
 _,q,start,pad,line=min(candidates,key=lambda x:x[0]);t=dict(ref='T'+str(len(j['terminals'])+1),xy=q,logical_net=logical,physical_net=n,drill_mm=1.1)
 j['terminals'].append(t);holes.append(q);points[n].append(q);shapes.extend([(n,pad),(n,line)])
 if start!=q:j['bottom_tracks'].append(dict(id='completion'+str(len(j['bottom_tracks'])),via=False,net=logical,a=start,b=q,width=width,layer='B.Cu',physical_net=n))
 return t
# Global half-mm occupancy for insulated wires, allowing crossings between wires.
obstacles=[b.buffer(.2) for b in boxes]
obtree=STRtree(obstacles)
def clear_segment(a,b):
 line=LineString([a,b]);return not any(line.intersects(obstacles[i]) for i in obtree.query(line))
def route(a,b):
 if clear_segment(a,b):return [a,b]
 step=.5
 def near(p):
  choices=[]
  for dx in range(-3,4):
   for dy in range(-3,4):
    q=(round(p[0]/step)+dx,round(p[1]/step)+dy)
    xy=[q[0]*step,q[1]*step]
    if clear_segment(p,xy):choices.append((math.dist(p,xy),q))
  assert choices,('no top escape',p)
  return min(choices)[1]
 start,finish=near(a),near(b);heap=[(math.dist(start,finish),0,start)];cost={start:0};prev={};seen=set()
 while heap:
  _,d,p=heapq.heappop(heap)
  if p in seen:continue
  if p==finish:break
  seen.add(p)
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   q=(p[0]+dx,p[1]+dy)
   if not(2<q[0]*step<188 and 2<q[1]*step<143) or q in seen:continue
   dd=d+math.hypot(dx,dy)
   if dd>=cost.get(q,float('inf')):continue
   if not clear_segment([p[0]*step,p[1]*step],[q[0]*step,q[1]*step]):continue
   cost[q]=dd;prev[q]=p;heapq.heappush(heap,(dd+math.dist(q,finish),dd,q))
 else:raise RuntimeError(('top wire has no route',a,b))
 path=[finish]
 while path[-1]!=start:path.append(prev[path[-1]])
 coords=[a]+[[x*step,y*step] for x,y in path[::-1]]+[b]
 # Remove unnecessary grid bends using visible farthest point.
 out=[coords[0]];i=0
 while i<len(coords)-1:
  nxt=max(k for k in range(i+1,len(coords)) if clear_segment(coords[i],coords[k]));out.append(coords[nxt]);i=nxt
 return out
for logical,names in sorted(nets.items()):
 while len({root(n) for n in names})>1:
  choices=[]
  for a in sorted(names):
   for b in sorted(names):
    if a>=b or root(a)==root(b):continue
    dist,x,y=min((math.dist(x,y),x,y) for x in points[a] for y in points[b]);choices.append((dist,a,b,x,y))
  _,a,b,x,y=min(choices);ta=add_terminal(a,logical,y);tb=add_terminal(b,logical,ta['xy'])
  def portal(t):
   xy=t['xy']
   if t.get('kind')!='adapter_pin':return xy
   middle=92.62 if t['physical_pin'].startswith('U1.') else 70.81
   return [xy[0]+(3 if xy[0]<middle else -3),xy[1]]
  pa,pb=portal(ta),portal(tb);coords=route(pa,pb)
  if ta.get('kind')=='adapter_pin':coords=[ta['xy']]+coords
  if tb.get('kind')=='adapter_pin':coords=coords+[tb['xy']]
  length=sum(math.dist(p,q) for p,q in zip(coords,coords[1:]));extra=4*sum(t.get('kind')=='adapter_pin' for t in [ta,tb])
  w=dict(ref='W'+str(len(j['wires'])+1),logical_net=logical,from_terminal=ta['ref'],to_terminal=tb['ref'],from_net=a,to_net=b,route_mm=coords,route_length_mm=round(length,2),cut_length_mm=math.ceil(length+14+extra),awg=24 if logical in ['GND','+3V3','+5V','+5V_IN'] else 26,strip_each_end_mm=5)
  if extra:
   w.update(height_allowance_mm=extra,from_pin=ta.get('physical_pin',ta['ref']+'.1'),to_pin=tb.get('physical_pin',tb['ref']+'.1'),from_height_mm=ta.get('connection_height_mm',0),to_height_mm=tb.get('connection_height_mm',0),notes='Projected route; add 4mm cut allowance per elevated joint. First/last 3mm over an adapter header strip stays at 4mm height, then descends. Fit before adapter.')
  j['wires'].append(w);union(a,b);uses[ta['ref']]+=1;uses[tb['ref']]+=1;print('Added',w['ref'],logical,length,flush=True)
(ROOT/'routing-plan.json').write_text(json.dumps(j,indent=2)+'\n');print('COMPLETE',len(j['wires']),'wires;',len(j['terminals']),'terminals')
