#!/usr/bin/env python3
"""MC2 physical-ledger, pin-contract, and native-check acceptance."""
import json, hashlib
from pathlib import Path
from design import parts, hostnames, c6names, XIAOC6_EVIDENCE, BOARD_W, BOARD_H
R=Path(__file__).resolve().parent
D=json.loads((R/'design.json').read_text()); P={p['ref']:p for p in D['parts']}
assert D['revision']=='MC2-D'
native=(R/'mc2.kicad_pcb').read_text()
assert '(rev \"MC2-D\")' in native
assert '(copper_finish \"HASL lead-free\")' in native
assert '(material \"FR4\")' in native
assert (BOARD_W,BOARD_H)==(100,100)
assert all(p['side']=='front' for p in parts)
assert len(P['U1']['pins'])==38 and len(P['U2']['pins'])==14
assert sum(p['fitted'] for p in parts)==19
assert len({n for p in parts for n in p['pins'].values() if n})==31
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
 assert hostnames[row][int(i)-1]==str(assignment['gpio']),name
# Check semantic pin-plan roles against actual native schematic/PCB pad nets.
role_nets={'ethernet_sck':'SPI_SCK','ethernet_mosi':'SPI_MOSI','ethernet_miso':'SPI_MISO','ethernet_cs':'ETH_CS','ethernet_irq':'ETH_INT','ethernet_reset':'ETH_RESET','cc1101_sck':'SPI_SCK','cc1101_mosi':'SPI_MOSI','cc1101_miso':'SPI_MISO','cc1101_cs':'RF_CS','cc1101_gdo0_tx':'RF_GDO0','cc1101_gdo2_rx':'RF_GDO2','zigbee_tx':'ZB_RX','zigbee_rx':'ZB_TX','zigbee_rts':'ZB_CTS','zigbee_cts':'ZB_RTS','i2c_sda':'I2C_SDA','i2c_scl':'I2C_SCL','thread_tx':'THREAD_RX','thread_rx':'THREAD_TX','thread_reset':'THREAD_EN','thread_boot':'THREAD_BOOT','radar_tx':'RADAR_RX','radar_rx':'RADAR_TX'}
assert set(role_nets)==set(plan['assignments'])
for role,net in role_nets.items():
 assert P['U1']['pins'][plan['assignments'][role]['header_pin']]==net,(role,net)
used={a['gpio'] for a in plan['assignments'].values()}
assert not used.intersection({0,1,3,6,7,8,9,10,11,16,17})
assert len(used)==21
assert P['D1']['model']=='22AWG WIRE LINK - NO DIODE'
assert P['D1']['footprint']=='MC2:Wire_Link_P7.62mm'
assert P['D1']['pins']=={'1':'+5V_HOST','2':'+5V'}
assert all(P[r]['model']=='1N5819 USB supply isolation' for r in ['D2','D3'])
assert P['R4']['pins']=={'1':'GND','2':'SPI_SCK'}
assert P['R5']['pins']=={'1':'GND','2':'SPI_MOSI'}
assert plan['assignments']['ethernet_sck']['gpio']==12
assert plan['assignments']['ethernet_mosi']['gpio']==2
assert plan['bootstrap_requirements']['GPIO12']['level']==0
assert plan['bootstrap_requirements']['GPIO2']['level']==0
for pin,net in {'J2.10':'THREAD_RX','J2.3':'THREAD_TX','J2.11':'THREAD_EN','J3.16':'THREAD_BOOT','J3.9':'RADAR_TX'}.items():assert P['U1']['pins'][pin]==net
for pin,net in {'8':'THREAD_RX','7':'THREAD_TX','14':'+5V_C6','13':'GND'}.items():assert P['U2']['pins'][pin]==net
assert P['J10']['pins']=={'1':'THREAD_EN','2':'THREAD_BOOT'}
assert P['U1']['pins']['J2.1'] is None and P['U2']['pins']['12'] is None and P['U3']['pins']['12'] is None
assert P['U2']['model']=='Seeed XIAO ESP32C6 pre-soldered 102010636'
assert P['U2']['footprint']=='MC2:XIAO_ESP32C6'
for pad in P['U2']['pad_centers_mm']:
 evidence=XIAOC6_EVIDENCE['header']['pad_map'][pad['number']]
 name=c6names[pad['number']]
 assert evidence['name']==('GPIO'+name if name.isdigit() else name)
 assert [round(pad['x']-P['U2']['xy'][0],4),round(pad['y']-P['U2']['xy'][1],4)]==evidence['local_mm'],pad
for number in XIAOC6_EVIDENCE['electrical']['carrier_unused_pads']:
 assert P['U2']['pins'][number] is None,number
assert D['mechanics']['module_geometry']['U2']==XIAOC6_EVIDENCE['mechanics']
assert D['mechanics']['rf_ports']['U2']['estimated_xy_mm']==[49.484,31.5485]
c6=plan['external_controller_contract']['c6']
assert c6['board']==XIAOC6_EVIDENCE['board'] and c6['sku']==XIAOC6_EVIDENCE['sku']
assert c6['antenna']=={'mode':'external','rf_path':'U.FL','enable_gpio':3,'enable_level':0,'select_gpio':14,'select_level':1,'initialized_before_radio':True}
assert c6['download_strap']['pullup_ohms']==5100
assert 'R3' not in P and all('C6_STRAP8' not in p['pins'].values() for p in P.values())
assert c6['recovery_harness']=={'reset':{'carrier_pin':'J10.1','module_pad':'TP8','net':'EN'},'boot':{'carrier_pin':'J10.2','module_pad':'TP2','gpio':9}}
# Pads must remain accessible through a real inner cutout, including rounded corners.
cut=D['mechanics']['service_cutout'];x1,y1,x2,y2=cut['bounds_mm'];rad=cut['corner_radius_mm']
assert rad==1.5 and x2-x1>=6 and y2-y1>=10
for x,y in D['mechanics']['bottom_service_pads_global_mm'].values():
 assert x1+rad<x<x2-rad and y1+.7<y<y2-.7
for p in P.values():
 for q in p['pad_centers_mm']:
  assert not (x1-.5<q['x']<x2+.5 and y1-.5<q['y']<y2+.5),(p['ref'],q)
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


if (R/'verification.json').exists():
    recorded=json.loads((R/'verification.json').read_text())
    for name,digest in recorded['source_sha256'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,('Stale verification input',name)
print('MC2: exact header pin map, module separation, 3 independent RF paths, native ERC/DRC/parity PASS')
