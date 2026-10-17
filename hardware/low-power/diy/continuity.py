"""Independent 2D copper contact and wire-union check; pure Python, no EDA engine.
Segments are round-ended tracks; pads are circles or axis-aligned rectangles.
The final D0 contract contains only these primitives and 0/90 degree footprints.
"""
import math
class DSU:
 def __init__(self,n):self.p=list(range(n))
 def root(self,x):
  while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
  return x
 def join(self,a,b):self.p[self.root(a)]=self.root(b)
def point_seg(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];d=dx*dx+dy*dy
 t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def segdist(a,b,c,d):
 ac,ad,ca,cb=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
 if ac*ad<0 and ca*cb<0:return 0
 return min(point_seg(a,c,d),point_seg(b,c,d),point_seg(c,a,b),point_seg(d,a,b))
def rect_edges(r):
 x1,y1,x2,y2=r;p=[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
 return list(zip(p,p[1:]+p[:1]))
def segrect(a,b,r):
 if any(r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3] for p in [a,b]):return 0
 return min(segdist(a,b,c,d) for c,d in rect_edges(r))
def separation(a,b):
 if 'rect' in a and 'rect' in b:
  r,s=a['rect'],b['rect'];return math.hypot(max(r[0]-s[2],s[0]-r[2],0),max(r[1]-s[3],s[1]-r[3],0))
 if 'rect' in a:a,b=b,a
 if 'rect' in b:return segrect(a['a'],a['b'],b['rect'])-a['radius']
 return segdist(a['a'],a['b'],b['a'],b['b'])-a['radius']-b['radius']
def verify(copper,logical_pins,wires,minimum_clearance=.5):
 ids={o['id']:i for i,o in enumerate(copper)};assert len(ids)==len(copper),'duplicate copper IDs'
 d=DSU(len(copper));minimum=999
 for i,a in enumerate(copper):
  for j in range(i):
   b=copper[j];gap=separation(a,b)
   if a['net']!=b['net']:
    minimum=min(minimum,gap)
    assert gap>=minimum_clearance-.002,('copper clearance/short',a['id'],b['id'],gap)
   elif gap<=.002:d.join(i,j)
 # Each named physical net must already be continuous in bottom copper alone.
 roots={}
 for i,o in enumerate(copper):
  r=d.root(i)
  if o['net'] in roots:assert roots[o['net']]==r,('disconnected bottom island',o['net'],o['id'])
  else:roots[o['net']]=r
 uses={};refs=set()
 for w in wires:
  assert w['ref'] not in refs,'duplicate wire reference'
  refs.add(w['ref'])
  assert w['from_net'].rsplit('__',1)[0]==w['logical_net']==w['to_net'].rsplit('__',1)[0],'wire logical net label mismatch'
  path=w['route_mm'];length=sum(math.dist(a,b) for a,b in zip(path,path[1:]))
  assert abs(length-w['route_length_mm'])<=.011,'incorrect wire length'
  assert w['strip_each_end_mm']==5,'strip length changed'
  assert w['cut_length_mm']>=length+2*w['strip_each_end_mm'],'wire too short'
  extra=sum(w.get(k+'_height_mm',0) for k in ['from','to'])
  assert extra==w.get('height_allowance_mm',0),'incorrect height allowance'
  assert w['cut_length_mm']<=math.ceil(length+14+extra),'wire cut exceeds reviewed allowance'
  assert len(path)>=2,'empty wire path'
  a,b=w.get('from_pin',w['from_terminal']+'.1'),w.get('to_pin',w['to_terminal']+'.1')
  assert a in ids and b in ids,('unknown wire terminal',w['ref'])
  def center(o):return [(o['rect'][0]+o['rect'][2])/2,(o['rect'][1]+o['rect'][3])/2] if 'rect' in o else o['a']
  assert math.dist(path[0],center(copper[ids[a]]))<.001 and math.dist(path[-1],center(copper[ids[b]]))<.001,'wire route endpoints do not match holes'
  for side,key in [('from',a),('to',b)]:
   raised=key!=w[side+'_terminal']+'.1'
   assert not raised or key.split('.')[0] in ['U1','U2'],'unapproved component lead joint'
   assert w.get(side+'_height_mm',0)==(4 if raised else 0),'incorrect joint height'
   uses[key]=uses.get(key,0)+1;assert uses[key]<=(1 if raised else 2),('more than 2 ends in hole or 1 on adapter pin',key)
  assert copper[ids[a]]['net']==w['from_net'] and copper[ids[b]]['net']==w['to_net'],'swapped wire terminal'
  assert w['awg']<= (24 if w['logical_net'] in ['GND','+3V3','+5V','+5V_IN'] else 26),'undersized link'
  d.join(ids[a],ids[b])
 expected={};actual={}
 for name,net in logical_pins.items():
  assert name in ids,('missing physical pin',name)
  key=net if net else 'NC:'+name;root=d.root(ids[name])
  if key in expected:assert expected[key]==root,('OPEN ASSEMBLY',key,name)
  else:expected[key]=root
  if root in actual:assert actual[root]==key,('SHORT ASSEMBLY',key,actual[root])
  else:actual[root]=key
 return dict(logical_nets=len([n for n in expected if not n.startswith('NC:')]),physical_copper_islands=len(roots),minimum_copper_clearance_mm=round(minimum,6),verified_pins=len(logical_pins),wire_links=len(wires))
