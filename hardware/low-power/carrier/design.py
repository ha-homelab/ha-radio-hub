"""LP-C0 low-voltage carrier: single electrical source of truth.
All connector numbering is carrier PCB top view, never an unverified remote board header.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent
CONTRACT = json.loads((ROOT.parent/'pinmap.json').read_text())
SOURCES = {
 'jst_xh':'https://www.jst-mfg.com/product/pdf/eng/eXH.pdf',
 'jst_sh':'https://www.jst-mfg.com/product/pdf/eng/eSH.pdf',
 'idc':'https://www.we-online.com/components/products/datasheet/61204021621.pdf',
 'idc_mate':'https://www.we-online.com/components/products/datasheet/61204023021.pdf',
 'sc16':'https://www.nxp.com/docs/en/data-sheet/SC16IS752_SC16IS762.pdf',
 'tps':'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
 'crystal':'https://abracon.com/Resonators/abls.pdf',
 'fuse':'https://www.littelfuse.com/assetdocs/fuses-449-datasheet?assetguid=7aef6e93-9808-456e-9bee-fba54271285f',
 'buck':'https://www.pololu.com/product/2857',
 'stemma':'https://learn.adafruit.com/introducing-adafruit-stemma-qt/technical-specs',
}
parts=[]; connectors=[]
def part(ref,model,footprint,pins,xy,rotation=0,source=None,notes='',types=None):
    p=dict(ref=ref,model=model,footprint=footprint,pins={str(k):v for k,v in pins.items()},xy=xy,rotation=rotation,source=source,notes=notes,types=types or {})
    parts.append(p); return p

def xh(ref,n,label,pins,xy,rotation=0,dest=None):
    fp=f'Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical'
    p=part(ref,f'B{n}B-XH-A',fp,dict(enumerate(pins,1)),xy,rotation,'jst_xh',label)
    connectors.append(dict(ref=ref,model=p['model'],mating_model=f'XHP-{n}',contacts='SXH-001T-P0.6',label=label,viewing_convention='Carrier PCB top/component view, square copper pad and silkscreen 1 identify pin 1. The cable mating-face view is mirrored; use molded circuit numbers and continuity test, never wire colors alone.',pins=[dict(number=i,net=net,destination=(dest or {}).get(i,label+' / '+net),voltage_v=5.0 if net.startswith('+5') else 0 if net=='GND' else 3.3,notes='22 AWG for 5V/buck power; 26 AWG for logic. No hot plugging.') for i,net in enumerate(pins,1)]))

xh('J1',2,'Isolated regulated 5V input',['+5V_IN','GND'],[12,12],dest={1:'External isolated PoE front end +5V, NOT 48V PoE',2:'External isolated PoE front end return'})
xh('J2',3,'External D24V22F3 buck',['+5V','GND','+3V3'],[30,12],dest={1:'D24V22F3 VIN',2:'D24V22F3 GND',3:'D24V22F3 VOUT (3.3V); sole 3.3V source'})
# Interleave grounds around the fastest SPI signals; no 5V on host header.
host_order=['+3V3','GND','w5500_sclk','GND','w5500_mosi','GND','w5500_miso','GND','w5500_cs','w5500_irq','w5500_reset','GND','shared_spi_sclk','GND','shared_spi_mosi','shared_spi_miso','cc1101_cs','cc1101_gdo0_tx','cc1101_gdo2_rx','sc16_cs','sc16_irq','GND','h2_tx','h2_rx','h2_reset','h2_boot','mg24_tx','mg24_rx','mg24_rts','mg24_cts','ld2450_tx','ld2450_rx','bme680_sda','bme680_scl','GND','GND','GND','GND','+3V3','GND']
roles={p['role']:p for p in CONTRACT['exclusive_pins']}
part('J3','61204021621','Carrier:Wurth_61204021621',dict(enumerate(host_order,1)),[22,27],source='idc',notes='S3 keyed 40-position IDC harness; NOT Raspberry Pi compatible')
connectors.append(dict(ref='J3',model='61204021621',mating_model='61204023021',contacts='IDC 40-conductor ribbon; AWG and insulation per mating connector datasheet',label='S3 host harness, NOT Raspberry Pi pinout',viewing_convention='PCB top: pin1 square at first row, pin2 across row, odd/even columns continue in 2.54mm steps. Socket mating-face view is mirrored. Follow molded pin1 and ribbon conductor1; continuity-test every conductor.',pins=[dict(number=i,net=n,destination=('S3 GPIO'+str(roles[n]['gpio'])) if n in roles else ('S3 3V3 regulated input; isolate USB/board regulator' if n=='+3V3' else 'S3 GND'),voltage_v=0 if n=='GND' else 3.3,notes='Remote header numbers intentionally unspecified; verify actual DevKit schematic. Both 3V3 pins are the same rail, never independent supplies.') for i,n in enumerate(host_order,1)]))
xh('J4',10,'WIZ850io Ethernet module',['+3V3','GND','w5500_sclk','w5500_mosi','w5500_miso','w5500_cs','w5500_irq','w5500_reset','GND','+3V3'],[72,13],dest={1:'WIZ850io J2.3 3V3',2:'WIZ850io J1.1 GND',3:'WIZ850io J1.4 SCLK',4:'WIZ850io J1.3 MOSI',5:'WIZ850io J2.6 MISO',6:'WIZ850io J1.5 SCNn',7:'WIZ850io J1.6 INTn',8:'WIZ850io J2.5 RSTn',9:'WIZ850io J1.2/J2.1 GND; J2.4 NC remains unconnected',10:'WIZ850io J2.2 3V3'})
xh('J5',7,'H2 Thread RCP',['+3V3','GND','h2_tx','h2_rx','h2_reset','h2_boot','GND'],[131,18],90,dest={1:'H2 3V3',2:'H2 GND',3:'H2 GPIO23 RX',4:'H2 GPIO24 TX',5:'H2 EN, open-drain control',6:'H2 GPIO9 BOOT, open-drain control',7:'H2 GND'})
xh('J6',6,'MG24 Zigbee NCP',['+3V3','GND','mg24_tx','mg24_rx','mg24_rts','mg24_cts'],[131,45],90,dest={1:'MGM240P adapter VDD pad15',2:'MGM240P adapter GND',3:'MGM240P PA05 pad12 RX',4:'MGM240P PA06 pad13 TX',5:'MGM240P PB01 pad5 CTS',6:'MGM240P PB00 pad6 RTS'})
xh('J7',8,'CC1101 RF module',['+3V3','GND','shared_spi_sclk','shared_spi_mosi','shared_spi_miso','cc1101_cs','cc1101_gdo0_tx','cc1101_gdo2_rx'],[131,75],90,dest={1:'CC1101 module VCC',2:'CC1101 module GND',3:'CC1101 SCLK',4:'CC1101 SI',5:'CC1101 SO',6:'CC1101 CSn',7:'CC1101 GDO0',8:'CC1101 GDO2'})
xh('J8',5,'ZAC93 Z-Wave module',['+3V3','GND','zac93_tx','zac93_rx','GND'],[91,89],dest={1:'ZAC93 pin1 3V3',2:'ZAC93 pin6 GND',3:'ZAC93 pin8 RX from SC16 TXA',4:'ZAC93 pin10 TX to SC16 RXA',5:'ZAC93 pin9 GND'})
xh('J9',4,'LD2450 radar',['+5V','GND','ld2450_rx','ld2450_tx'],[51,89],dest={1:'LD2450 5V',2:'LD2450 GND',3:'LD2450 TX (3.3V logic) to S3 GPIO40',4:'LD2450 RX from S3 GPIO39'})
part('J10','BM04B-SRSS-TB','Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',{1:'GND',2:'+3V3',3:'bme680_sda',4:'bme680_scl','MP1':None,'MP2':None},[15,88],source='jst_sh',notes='STEMMA QT: 3.3V only; BME680 external ventilated pod')
connectors.append(dict(ref='J10',model='BM04B-SRSS-TB',mating_model='SHR-04V-S',contacts='SSH-003T-P0.2-H; prefer precrimped 100mm Adafruit 4210 cable',label='BME680 STEMMA QT',viewing_convention='Carrier top view; square pad and silk1. JST SH mating face is mirrored. Standard QT order is 1GND 2V+ 3SDA 4SCL.',pins=[dict(number=i,net=n,destination='BME680 QT '+n,voltage_v=0 if i==1 else 3.3,notes='Use breakout I2C pull-ups; no extra pull-ups fitted on carrier.') for i,n in enumerate(['GND','+3V3','bme680_sda','bme680_scl'],1)]))
part('F1','044901.5MR','Carrier:Littelfuse_449',{1:'+5V_IN',2:'+5V'},[22,12],source='fuse',notes='1.5A time-delay; design <=1.0A continuous at 5V, temperature derating applies')
sc={1:None,2:'GND',3:'zac93_tx',4:'zac93_rx',5:'sc16_reset',6:'xtal1',7:'xtal2',8:'+3V3',9:'GND',10:'sc16_cs',11:'shared_spi_mosi',12:'shared_spi_miso',13:'shared_spi_sclk',14:'GND',15:'sc16_irq',16:'GND',17:None,18:'gpio0_unused',19:'gpio1_unused',20:'gpio2_unused',21:'gpio3_unused',22:'GND',23:None,24:'rxb_unused',25:'gpio4_unused',26:'gpio5_unused',27:'gpio6_unused',28:'gpio7_unused'}
part('U1','SC16IS752IPW,128','Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm',sc,[88,57],source='sc16',notes='SPI mode; channel A 115200 8N1, crystal3.6864MHz',types={'3':'output','4':'input','5':'input','6':'input','7':'output','8':'power_in','22':'power_in','10':'input','11':'input','12':'tri_state','13':'input','15':'open_collector'})
part('U2','TPS3808G33DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:'sc16_reset',2:'GND',3:None,4:None,5:'+3V3',6:'+3V3'},[65,69],source='tps',notes='G33 supervisor; CT open=20ms; MR internal pullup',types={'1':'open_collector','2':'power_in','5':'input','6':'power_in'})
part('Y1','ABLS-3.6864MHZ-B2-T','Crystal:Crystal_SMD_HC49-SD',{1:'xtal1',2:'xtal2'},[76,57],rotation=270,source='crystal',notes='18pF CL, initial load caps22pF/33pF; verify frequency/drive on bench')
# Large hand-solderable passives; no blind or buried vias.
def res(ref,value,a,b,xy): return part(ref,value,'Resistor_SMD:R_0805_2012Metric',{1:a,2:b},xy,notes='1%, 0.125W, 0805; select a stocked part meeting these specifications')
def cap(ref,value,a,b,xy,large=False): return part(ref,value,'Capacitor_SMD:C_1206_3216Metric' if large else 'Capacitor_SMD:C_0805_2012Metric',{1:a,2:b},xy,notes='10V minimum; C0G crystal caps, X7R bypass/bulk')
res('R1','1k','+3V3','sc16_irq',[100,53]);res('R2','10k','+3V3','sc16_cs',[100,58]);res('R3','10k','+3V3','sc16_reset',[65,63]);res('R4','10k','+3V3','rxb_unused',[96,68])
for i in range(8): res(f'R{i+5}','100k',f'gpio{i}_unused','GND',[105+4*(i%4),66+5*(i//4)])
res('R13','4.7k','+3V3','cc1101_gdo0_tx',[113,78]);res('R14','10k','+3V3','cc1101_cs',[119,78]);res('R15','10k','+3V3','w5500_cs',[92,23]);res('R16','10k','+3V3','h2_reset',[120,25]);res('R17','10k','+3V3','h2_boot',[120,30])
cap('C1','22pF','xtal1','GND',[81,51]);cap('C2','33pF','xtal2','GND',[81,63]);cap('C3','100nF','+3V3','GND',[84,66]);cap('C4','1uF','+3V3','GND',[84,71]);cap('C5','100nF','+3V3','GND',[60,69]);cap('C6','1nF','+3V3','GND',[60,74]);cap('C7','1uF','h2_reset','GND',[120,20]);cap('C8','22uF','+5V','GND',[42,12],True);cap('C9','22uF','+3V3','GND',[44,20],True)
for num,xy in enumerate([[33,30],[103,13],[124,35],[124,49],[124,81],[107,89],[69,89],[23,88]],10):
    cap('C'+str(num),'100nF','+5V' if num==16 else '+3V3','GND',xy)
# External rails must be explicit outputs for ERC, without pretending a regulator exists on-board.
for i,net in enumerate(['+5V_IN','+5V','+3V3','GND'],1):
    part('#FLG'+str(i),'PWR_FLAG','',{1:net},[0,0],types={'1':'power_out'},notes='Declared external regulated power / return')

# Independently checked remote endpoint namespace. Positions refer to that module,
# not to an unidentified development-board header. Unknown remote positions stay null.
REMOTE={
 'J1':('pd',{1:[('5V','8')],2:[('GND','7')]}),
 'J2':('buck',{1:[('VIN',None)],2:[('GND',None)],3:[('VOUT',None)]}),
 'J4':('w5500',{1:[('3V3B','J2.3')],2:[('GND1','J1.1')],3:[('SCLK','J1.4')],4:[('MOSI','J1.3')],5:[('MISO','J2.6')],6:[('CS','J1.5')],7:[('IRQ','J1.6')],8:[('RESET','J2.5')],9:[('GND2','J1.2'),('GND3','J2.1')],10:[('3V3A','J2.2')]}),
 'J5':('h2',{1:[('3V3','3')],2:[('GND1','1')],3:[('GPIO23','30')],4:[('GPIO24','31')],5:[('EN','8')],6:[('GPIO9','23')],7:[('GND2','2')]}),
 'J6':('mg24',{1:[('VDD','15')],2:[('GND1','1')],3:[('RX','12')],4:[('TX','13')],5:[('CTS','5')],6:[('RTS','6')]}),
 'J7':('cc1101',{i:[(n,None)] for i,n in enumerate(['VCC','GND','SCLK','SI','SO','CS','GDO0','GDO2'],1)}),
 'J8':('zac93',{1:[('3V3','1')],2:[('GND6','6')],3:[('RX','8')],4:[('TX','10')],5:[('GND9','9')]}),
 'J9':('ld2450',{i:[(n,None)] for i,n in enumerate(['5V','GND','TX','RX'],1)}),
 'J10':('bme680',{i:[(n,None)] for i,n in enumerate(['GND','VIN','SDA','SCL'],1)}),
}
for c in connectors:
    if c['ref']=='J3':
        for pin in c['pins']:
            n=pin['net'];pid='GPIO'+str(roles[n]['gpio']) if n in roles else ('3V3' if n=='+3V3' else 'GND1')
            pin['remote_endpoints']=[dict(component='s3',pin=pid,position=None,position_namespace='DevKit header unknown; use labelled GPIO')]
    else:
        comp,mapping=REMOTE[c['ref']]
        for pin in c['pins']:
            pin['remote_endpoints']=[dict(component=comp,pin=n,position=pos,position_namespace='module pad or documented module header; use local adapter for castellated pads') for n,pos in mapping[pin['number']]]
