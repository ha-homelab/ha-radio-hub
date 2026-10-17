#!/usr/bin/env python3
"""Convert temporary top routes to insulated-wire plans and split physical nets.
Requires Shapely only for this optional one-time routing-plan creation. Final
regeneration/validation do not require it or the autorouter.
"""
import json,math,heapq
from pathlib import Path
from collections import defaultdict
from shapely.geometry import Point,LineString,box
ROOT=Path(__file__).resolve().parent
c=json.loads((ROOT/'.build/candidate.json').read_text())
class DSU:
 def __init__(self,n):self.p=list(range(n))
 def root(self,i):
  while i!=self.p[i]:self.p[i]=self.p[self.p[i]];i=self.p[i]
  return i
 def join(self,a,b):self.p[self.root(a)]=self.root(b)
def shape(o):
 if 'xy' in o:
  x,y=o['xy'];w,h=o['size']
  return box(x-w/2,y-h/2,x+w/2,y+h/2) if o['shape']=='rect' else Point(x,y).buffer(w/2,quad_segs=32)
 return Point(o['a']).buffer(o['width']/2,quad_segs=32) if o['via'] else LineString([o['a'],o['b']]).buffer(o['width']/2,quad_segs=32)
def groups(items):
 d=DSU(len(items));s=[shape(x) for x in items]
 for i,a in enumerate(items):
  for j in range(i):
   if s[i].distance(s[j])<.005:
    assert a['net']==items[j]['net'],('SHORT',a['id'],items[j]['id'])
    d.join(i,j)
 out=defaultdict(list)
 for i,o in enumerate(items):out[d.root(i)].append(o)
 return list(out.values())
bottom=[o for o in c['pads'] if o['net']]+[o for o in c['tracks'] if o['via'] or o['layer']=='B.Cu']
islands=groups(bottom);islands.sort(key=lambda g:(g[0]['net'],min(x['id'] for x in g)))
physical={};members={};counts=defaultdict(int)
for g in islands:
 n=g[0]['net'];counts[n]+=1;name=n+'__'+str(counts[n]);members[name]=[o['id'] for o in g]
 for o in g:physical[o['id']]=name
vias=[o for o in c['tracks'] if o['via']];vias.sort(key=lambda o:(o['net'],o['a']))
terminals={v['id']:dict(ref='T'+str(i+1),xy=v['a'],logical_net=v['net'],physical_net=physical[v['id']],drill_mm=1.1) for i,v in enumerate(vias)}
# Top graphs include component pads to detect forbidden direct attachment.
top=[o for o in c['tracks'] if o['via'] or o['layer']=='F.Cu']+[o for o in c['pads'] if o['net']]
wires=[]
for g in groups(top):
 links=[o for o in g if 'via' in o and not o['via']]
 if not links:continue
 # Never turn a direct component-pad route into a fictitious wire joint.
 # Discard it; explicit terminal completion must join the logical net later.
 if any('xy' in o for o in g):continue
 vs=[o for o in g if o.get('via')]
 assert len(vs)>=2,('TOP_STUB',g)
 adj=defaultdict(list)
 for o in links:
  a,b=tuple(o['a']),tuple(o['b']);dist=math.dist(a,b);adj[a].append((b,dist));adj[b].append((a,dist))
 def path(a,b):
  heap=[(0,tuple(a),[a])];seen=set()
  while heap:
   cost,node,p=heapq.heappop(heap)
   if node==tuple(b):return cost,p
   if node in seen:continue
   seen.add(node)
   for dest,length in adj[node]:heapq.heappush(heap,(cost+length,dest,p+[list(dest)]))
  raise AssertionError(('top graph disconnected',a,b))
 # Simple chain, not a star: at most two stripped wire ends share any terminal.
 pending=sorted(vs,key=lambda v:v['a']);last=pending.pop(0)
 while pending:
  choices=[(path(last['a'],v['a']),i,v) for i,v in enumerate(pending)]
  (length,coords),i,nxt=min(choices,key=lambda v:v[0][0]);pending.pop(i)
  if physical[last['id']]!=physical[nxt['id']]:
   wires.append(dict(ref='W'+str(len(wires)+1),logical_net=last['net'],from_terminal=terminals[last['id']]['ref'],to_terminal=terminals[nxt['id']]['ref'],from_net=physical[last['id']],to_net=physical[nxt['id']],route_mm=coords,route_length_mm=round(length,2),cut_length_mm=math.ceil(length+14),awg=24 if last['net'] in ['GND','+3V3','+5V','+5V_IN'] else 26,strip_each_end_mm=5))
  last=nxt
# Strip all autorouter-only geometry. Every actual copper item is bottom-only.
plan=dict(schema_version=1,revision='LP-D0',board_mm=[190,145],pads=[dict(o,physical_net=physical.get(o['id'])) for o in c['pads']],bottom_tracks=[dict(o,physical_net=physical[o['id']]) for o in c['tracks'] if not o['via'] and o['layer']=='B.Cu'],terminals=list(terminals.values()),wires=wires,islands=members)
(ROOT/'routing-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Plan:',len(islands),'bottom islands,',len(terminals),'terminal holes,',len(wires),'insulated wires')
