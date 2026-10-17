"""Exact MGM240PA22VNA3 daughterboard for LP-C0 J6; no firmware target change."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'mg24':'https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf','jst_xh':'https://www.jst-mfg.com/product/pdf/eng/eXH.pdf'}
parts=[];connectors=[]
def part(ref,model,fp,pins,xy,source=None,notes='',types=None):
 p=dict(ref=ref,model=model,footprint=fp,pins={str(k):v for k,v in pins.items()},xy=xy,rotation=0,source=source,notes=notes,types=types or {});parts.append(p);return p
pins={n:None for n in range(1,37)}
for n in [1,14,23,32,34,35,36]:pins[n]='GND'
pins.update({5:'mg24_rts',6:'mg24_cts',7:'BOOT',8:'SWCLK',9:'SWDIO',12:'mg24_tx',13:'mg24_rx',15:'+3V3',31:'RESET'})
part('U1','MGM240PA22VNA3','Carrier:MGM240P',pins,[23.55,0],source='mg24',notes='Exact PA22VNA3 firmware target; all GND pads direct to plane; RFOUT33 intentionally NC',types={'15':'power_in','5':'input','6':'output','7':'input','8':'input','9':'bidirectional','12':'input','13':'output','31':'input'})
def xh(ref,n,label,nets,xy):
 p=part(ref,f'B{n}B-XH-A',f'Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical',dict(enumerate(nets,1)),xy,'jst_xh',label)
 c=dict(ref=ref,model=p['model'],mating_model=f'XHP-{n}',contacts='SXH-001T-P0.6',label=label,viewing_convention='Component/PCB top view; square pad is pin1. Cable mating face is mirrored; continuity-test pin numbers, not colors.',pins=[dict(number=i,net=n,voltage_v=0 if n=='GND' else 3.3,destination='',notes='3.3V only; not hot pluggable') for i,n in enumerate(nets,1)]);connectors.append(c);return c
c=xh('J1',6,'To carrier J6', ['+3V3','GND','mg24_tx','mg24_rx','mg24_rts','mg24_cts'],[7,28])
for p in c['pins']:p['destination']='Carrier J6.'+str(p['number'])+' (straight number-to-number harness)'
c=xh('J2',7,'SWD / reset / boot service',['+3V3','GND','SWCLK','SWDIO','RESET','BOOT','GND'],[37,28])
for p,text in zip(c['pins'],['Probe VTref sense, never external supply','Probe GND','Probe SWCLK -> PA01 pad8','Probe SWDIO -> PA02 pad9','Probe open-drain RESET -> pad31; no3.3V pullup','Temporarily ground PA00 pad7 during reset for bootloader entry','Service GND']):p['destination']=text
c['pins'][4]['voltage_v']=None
c['pins'][4]['notes']='Internal DVDD reset domain; probe may sink only. Never drive high or add an external 3.3V pull-up.'
part('R1','10k','Resistor_SMD:R_0805_2012Metric',{1:'+3V3',2:'BOOT'},[17,10],notes='1%, 0.125W, 0805')
part('C1','100nF','Capacitor_SMD:C_0805_2012Metric',{1:'+3V3',2:'GND'},[26.5,18],notes='10V X7R, 0805, close to VDD15')
part('C2','1uF','Capacitor_SMD:C_0805_2012Metric',{1:'+3V3',2:'GND'},[26.5,22],notes='10V X7R, 0805')
part('C3','10uF','Capacitor_SMD:C_1206_3216Metric',{1:'+3V3',2:'GND'},[20,22],notes='10V X7R, 1206; account for DC bias')
for i,net in enumerate(['+3V3','GND'],1):part('#FLG'+str(i),'PWR_FLAG','',{1:net},[0,0],types={'1':'power_out'})
