#!/usr/bin/env python3
"""MC2 physical-ledger, pin-contract, and native-check acceptance."""
import json, hashlib
from pathlib import Path
from design import parts, s3names, BOARD_W, BOARD_H
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text()); P={p['ref']:p for p in D['parts']}
assert (BOARD_W,BOARD_H)==(100,100)
assert all(p['side']=='front' for p in parts)
assert len(P['U1']['pins'])==44 and len(P['U2']['pins'])==23
assert sum(p['fitted'] for p in parts)==17
assert len({n for p in parts for n in p['pins'].values() if n})==33
# Do not accept the historical stacked-body arrangement in this revision.
def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
for ref,p in P.items():
 b=p['body_bounds_global_mm']
 if not b:continue
 for other,q in P.items():
  if other==ref:continue
  for pad in q['pad_centers_mm']:
   assert not (b[0]<pad['x']<b[2] and b[1]<pad['y']<b[3]),(ref,other,pad)
 for other,q in P.items():
  if other<=ref or not q['body_bounds_global_mm']:continue
  assert not overlap(b,q['body_bounds_global_mm']),(ref,other)
for p in parts:
 assert P[p['ref']]['pins']==p['pins'],p['ref']
plan=json.loads((R/'pin-plan.json').read_text())
for name,assignment in plan['assignments'].items():
 row,i=assignment['header_pin'].split('.')
 assert s3names[row][int(i)-1]==str(assignment['gpio']),name
used={a['gpio'] for a in plan['assignments'].values()}
assert not used.intersection({0,3,19,20,35,36,37,38,43,44,45,46,48})
for pin,net in {'J1.8':'THREAD_RX','J1.9':'THREAD_TX','J3.17':'THREAD_EN','J3.9':'THREAD_BOOT','J3.8':'RADAR_TX'}.items():assert P['U1']['pins'][pin]==net
for pin,net in {'12':'THREAD_RX','13':'THREAD_TX','15':'THREAD_EN','11':'THREAD_BOOT','3':'+5V_C6'}.items():assert P['U2']['pins'][pin]==net
assert P['U1']['pins']['J1.1'] is None and P['U2']['pins']['4']=='C6_LOCAL_3V3' and P['U3']['pins']['12'] is None
assert D['mechanics']['rj45']['outward_normal_global']==[0.0,1.0]
assert D['mechanics']['rj45']['mouth_beyond_bottom_edge_mm']==2
assert D['mechanics']['mounting_holes_mm']==[[4,4],[96,4],[4,96],[96,96]]
assert {p['radio'] for p in D['mechanics']['rf_ports'].values()}=={'BLE','Thread','Zigbee'}
assert all(p['connector']=='U.FL / MHF1' for p in D['mechanics']['rf_ports'].values())
# The native reports are evidence, not waived warnings: every category must be present and empty.
report=json.loads((R/'checks/drc.json').read_text())
for k in ['violations','unconnected_items','schematic_parity']:assert k in report and report[k]==[],(k,report.get(k))
erc=json.loads((R/'checks/erc.json').read_text())
assert 'sheets' in erc and all(s['violations']==[] for s in erc['sheets'])


assert P['U2']['pins']['10']=='C6_STRAP8'
assert P['R3']['pins']=={'1':'C6_LOCAL_3V3','2':'C6_STRAP8'}
assert not any(n=='+3V3' for n in P['R3']['pins'].values())

if (R/'verification.json').exists():
    recorded=json.loads((R/'verification.json').read_text())
    for name,digest in recorded['source_sha256'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,('Stale verification input',name)
print('MC2: exact header pin map, module separation, 3 independent RF paths, native ERC/DRC/parity PASS')
