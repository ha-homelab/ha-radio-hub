"""LP-I0 integrated prototype electrical source. Physical numbers are module/package pads.
Not released for fabrication: see README.md and verification report.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ATLAS=json.loads((ROOT.parent/'visual/connections.json').read_text())
SOURCES=dict(ATLAS['sources'])
SOURCES.update(w5500='https://docs.wiznet.io/img/products/w5500/w5500_sch_v110_use_mag_.pdf',
 bel='https://www.belfuse.com/media/drawings/products/magjack%20ICMs/dr-mag-0813-1x1t-57-f.pdf',
 pololu_dimensions='https://www.pololu.com/file/0J1031/d24v22fx-step-down-voltage-regulator-dimension-diagram.pdf',
 usb='https://www.hroelec.com/UploadFiles/2017/04/TYPE-C-31-M-12.pdf',
 usb_esd='https://www.st.com/resource/en/datasheet/usblc6-2.pdf',
 jst='https://www.jst-mfg.com/product/pdf/eng/eXH.pdf',
 jst_sh='https://www.jst-mfg.com/product/pdf/eng/eSH.pdf')
parts=[];connectors=[]
def part(ref,model,footprint,pins,xy,rotation=0,source=None,notes='',types=None):
 p=dict(ref=ref,model=model,footprint=footprint,pins={str(k):v for k,v in pins.items()},xy=xy,rotation=rotation,source=source,notes=notes,types=types or {})
 parts.append(p);return p

def module(ref,cid,fp,xy,n,rotation=0):
 c=next(c for c in ATLAS['components'] if c['id']==cid)
 assigned={(m['component'],m['pin']):net['id'] for net in ATLAS['nets'] for m in net['members']}
 pins={str(i):None for i in range(1,n+1)};types={}
 typemap={'input':'input','output':'output','bidirectional':'bidirectional','open_drain':'open_collector','power_input':'power_in','power_output':'power_out','ground':'power_in'}
 for p in c['pins']:
  pos=p['physical']['position']
  if pos is not None:
   pins[str(pos)]=assigned.get((cid,p['id']));types[str(pos)]=typemap.get(p['direction'],'passive')
 return part(ref,c['model'],fp,pins,xy,rotation,cid,notes='Module pad numbers, not development-board header positions.',types=types)
module('U1','s3','RF_Module:ESP32-S3-WROOM-1',[42,22],41)
module('U2','h2','Hub:ESP32-H2-MINI-1',[92,20],53)
module('U3','mg24','Hub:MGM240P',[139,0],36)
# Fill service lines absent from the all-device wiring atlas.
parts[0]['pins'].update({'3':'s3_en','27':'s3_boot','13':'usb_dm','14':'usb_dp'})
parts[1]['pins']['15']=None # VBAT internally bonded to 3V3 on standard H4S; no external tie.
parts[2]['pins']['33']=None # Built-in antenna variant: no external RF port connection.
module('U5','sc16','Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm',[86,60],28)
module('U6','supervisor','Package_TO_SOT_SMD:SOT-23-6',[72,60],6)
module('U7','pd','Hub:Ag97000_FL',[30,130],10)
parts[-1]['model']='Ag97005-FL'
parts[-1]['notes']='Bare isolated PoE module installed on this PCB; not the separate EvalPoE bench board.'
parts[-1]['pins'].update({'1':'POE_12','2':'POE_36','3':'POE_45','4':'POE_78'})
part('U8','D24V22F3','Hub:D24V22F3',{'PG':None,'EN':None,'VIN':'5v_fused','GND':'gnd','VOUT':'3v3','GND2':'gnd'},[112,109],source='pololu_dimensions',notes='Only regulator feeding 3V3. 1.5A at 5V input bench gate; soldered headers.',types={'VIN':'power_in','GND':'power_in','GND2':'power_in','VOUT':'power_out','PG':'open_collector','EN':'input'})
w={i:None for i in range(1,49)}
w.update({1:'eth_txn',2:'eth_txp',3:'gnd',4:'3v3_analog',5:'eth_rxn',6:'eth_rxp',8:'3v3_analog',9:'gnd',10:'eth_exres',11:'3v3_analog',14:'gnd',15:'3v3_analog',16:'gnd',17:'3v3_analog',19:'gnd',20:'eth_tocap',21:'3v3_analog',22:'eth_1v2',23:'gnd',28:'3v3',29:'gnd',30:'eth_xi',31:'eth_xo',32:'w5500_cs',33:'w5500_sclk',34:'w5500_miso',35:'w5500_mosi',36:'w5500_irq',37:'w5500_reset',43:'eth_pmode',44:'eth_pmode',45:'eth_pmode',48:'gnd'})
wt={str(i):'power_in' for i in [3,4,8,9,11,14,15,16,17,19,21,23,28,29,48]};wt.update({'32':'input','33':'input','34':'tri_state','35':'input','36':'output','37':'input','43':'input','44':'input','45':'input','30':'input','31':'output'})
part('U4','W5500','Package_QFP:LQFP-48_7x7mm_P0.5mm',w,[61,94],90,'w5500','25MHz crystal; common-CT magnetics with RX AC coupling; hardware PMODE111; firmware selects10M.',wt)
part('J1','0813-1X1T-57-F','Hub:Bel_0813_1X1T_57_F',{1:'mag_rxp',2:'eth_txp',5:'POE_12',6:'POE_45',7:'mag_ct',8:'mag_rxn',9:'eth_txn',10:'POE_36',11:'POE_78','S1':'chassis','S2':'chassis'},[24,100],90,'bel','PoE-capable magjack. PHY-side common CT. Four cable-side power taps, internal bridge in U7.')

def xh(ref,n,label,pins,xy,rotation=0):
 fp=f'Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical'
 p=part(ref,f'B{n}B-XH-A',fp,dict(enumerate(pins,1)),xy,rotation,'jst',label)
 connectors.append(dict(ref=ref,model=p['model'],mating_model=f'XHP-{n}',contacts='SXH-001T-P0.6',label=label,pins=p['pins']))
xh('J3',8,'CC1101 remote RF module',['3v3','gnd','shared_spi_sclk','shared_spi_mosi','shared_spi_miso','cc1101_cs','cc1101_gdo0_tx','cc1101_gdo2_rx'],[146,45],90)
xh('J4',5,'ZAC93 remote module',['3v3','gnd','zwave_tx','zwave_rx','gnd'],[146,78],90)
xh('J5',4,'LD2450 remote radar',['5v_fused','gnd','ld2450_rx','ld2450_tx'],[146,101],90)
part('J6','BM04B-SRSS-TB','Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',{1:'gnd',2:'3v3',3:'bme680_sda',4:'bme680_scl','MP':None},[141,127],source='jst_sh',notes='Standard QT order; breakout pullups only; short external ambient sensor cable.')
xh('J7',6,'MG24 service SWD/boot',['3v3','gnd','mg24_swclk','mg24_swdio','mg24_reset','mg24_boot'],[111,41])
xh('J8',6,'H2 service UART/boot',['3v3','gnd','h2_rx','h2_tx','h2_reset','h2_boot'],[95,39])
# Service UART connector is input-only when external programmer controls H2: disconnect or hold S3 reset.
part('J2','TYPE-C-31-M-12','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',{'A1':'gnd','A4':'usb_vbus','A5':'usb_cc1','A6':'usb_dp_port','A7':'usb_dm_port','A8':None,'A9':'usb_vbus','A12':'gnd','B1':'gnd','B4':'usb_vbus','B5':'usb_cc2','B6':'usb_dp_port','B7':'usb_dm_port','B8':None,'B9':'usb_vbus','B12':'gnd','SH':'gnd'},[13,52],270,'usb','Self-powered USB service only. VBUS feeds ESD reference; never tied to PoE5V.')
part('U9','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',{1:'usb_dm_port',2:'gnd',3:'usb_dp_port',4:'usb_dp_port',5:'usb_vbus',6:'usb_dm_port'},[24,51],source='usb_esd',notes='Low-capacitance ESD near USB; VBUS not board supply.')

rn=0;cn=0
def res(value,a,b,xy,rotation=0,notes='1%,0805,0.125W',fp='Resistor_SMD:R_0805_2012Metric'):
 global rn;rn+=1;return part(f'R{rn}',value,fp,{1:a,2:b},xy,rotation,notes=notes)
def cap(value,a,b,xy,rotation=0,large=False,notes='X7R,16V; evaluate DC-bias effective capacitance'):
 global cn;cn+=1;return part(f'C{cn}',value,'Capacitor_SMD:C_1206_3216Metric' if large else 'Capacitor_SMD:C_0805_2012Metric',{1:a,2:b},xy,rotation,notes=notes)
# Every rail entry locally bypassed. Crystal pinout from footprints (2-pin HC49) is symmetrical.
part('Y1','ABLS-3.6864MHZ-B2-T','Crystal:Crystal_SMD_HC49-SD',{1:'sc16_xtal1',2:'sc16_xtal2'},[87,76],source='sc16',notes='18pF load; verify measured frequency and drive.')
cap('22pF','sc16_xtal1','gnd',[79,71],notes='C0G,50V');cap('33pF','sc16_xtal2','gnd',[95,71],notes='C0G,50V')
# Atlas pin names are intentionally reused exactly.
for p in parts:
 if p['ref']=='U5': p['pins']['6']='sc16_xtal1';p['pins']['7']='sc16_xtal2'
for val,a,b,xy in [
 ('1k','sc16_irq','3v3',(95,58)),('10k','sc16_reset','3v3',(72,55)),('10k','sc16_cs','3v3',(96,62)),
 ('10k','sc16_rxb','3v3',(97,66)),('4.7k','cc1101_gdo0_tx','3v3',(139,62)),('10k','cc1101_cs','3v3',(139,66)),
 ('10k','h2_reset','3v3',(81,29)),('10k','h2_boot','3v3',(103,26)),('10k','h2_gpio8','3v3',(103,22)),('10k','h2_gpio25','gnd',(103,18)),
 ('10k','mg24_boot','3v3',(133,28)),('10k','s3_en','3v3',(27,28)),('10k','s3_boot','3v3',(52,35)),
 ('10k','w5500_cs','3v3',(69,90)),('10k','w5500_reset','3v3',(69,94)),('10k','eth_pmode','3v3',(69,98)),
 ('5.1k','usb_cc1','gnd',(20,59)),('5.1k','usb_cc2','gnd',(25,59)),('22','usb_dm_port','usb_dm',(29,47)),('22','usb_dp_port','usb_dp',(29,51))]:res(val,a,b,xy)
# Match named GPIO strapping nets in model, independent of display labels.
for p in parts:
 if p['ref']=='U2':p['pins'].update({'22':'h2_gpio8','25':'h2_gpio25'})
 if p['ref']=='U5':
  p['pins']['24']='sc16_rxb'
  for n,pad in enumerate([18,19,20,21,25,26,27,28]):p['pins'][str(pad)]=f'sc16_gpio{n}'
for i in range(8):res('100k',f'sc16_gpio{i}','gnd',(106+(i%4)*4,59+(i//4)*5))
# Copper power local bypasses.
for val,a,xy in [('100nF','3v3',(30,25)),('10uF','3v3',(30,21)),('1uF','s3_en',(27,32)),('100nF','3v3',(81,21)),('10uF','3v3',(81,17)),('1uF','h2_reset',(81,25)),('100nF','3v3',(136,24)),('10uF','3v3',(140,28)),('100nF','3v3',(78,63)),('1uF','3v3',(78,67)),('100nF','3v3',(67,60)),('1nF','3v3',(67,64)),('100nF','usb_vbus',(24,55)),('22uF','3v3',(119,132)),('100nF','3v3',(139,80)),('100nF','3v3',(139,48)),('100nF','5v_fused',(140,101))]:cap(val,a,'gnd',xy,large=val in ['22uF','10uF'])
# W5500 analogue reference network: common CT with AC-coupled RX as official reference.
part('FB1','BLM21PG121SN1D','Inductor_SMD:L_0805_2012Metric',{1:'3v3',2:'3v3_analog'},[71,105],notes='120ohm at100MHz, low DCR ferrite; local analog supply filter.')
for xy in [(54,87),(50,93),(54,101),(58,103),(62,103),(65,87)]:cap('100nF','3v3_analog','gnd',xy)
cap('10uF','3v3_analog','gnd',(73,110),large=True);cap('100nF','3v3','gnd',(67,84));cap('10uF','3v3','gnd',(71,84),large=True)
res('12.4k','eth_exres','gnd',(50,99));cap('10nF','eth_1v2','gnd',(61,108));cap('4.7uF','eth_tocap','gnd',(56,107))
part('Y2','ABM8-25.000MHZ-B2-T','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',{1:'eth_xi',2:'gnd',3:'eth_xo',4:'gnd'},[68,78],notes='25MHz,18pF load,<=50ppm total; verify crystal ordering specification.')
res('1M','eth_xi','eth_xo',(68,74));cap('18pF','eth_xi','gnd',(64,78),notes='C0G,50V');cap('18pF','eth_xo','gnd',(72,78),notes='C0G,50V')
res('49.9','eth_txp','3v3_analog',(45,88));res('49.9','eth_txn','3v3_analog',(45,91));res('10','mag_ct','3v3_analog',(45,85));cap('22nF','mag_ct','gnd',(41,85))
cap('6.8nF','eth_rxp','mag_rxp',(45,96));cap('6.8nF','eth_rxn','mag_rxn',(45,100));res('49.9','eth_rxp','eth_rxterm',(49,105));res('49.9','eth_rxn','eth_rxterm',(49,109));cap('10nF','eth_rxterm','gnd',(45,109))
# No PCB copper under magjack. RC chassis link is a rated high-voltage capacitor only.
part('C50','1nF 2kV','Capacitor_THT:C_Disc_D7.5mm_W5.0mm_P7.50mm',{1:'chassis',2:'gnd'},[31,82],notes='Safety/ESD rated capacitor; qualification and touch-current review required.')
# PoE transient suppression is across each input pair, never primary-to-secondary.
for n,a,b,xy in [(1,'POE_12','POE_36',(30,119)),(2,'POE_45','POE_78',(40,119))]:
 part('D'+str(n),'SMBJ58CA','Diode_SMD:D_SMB',{1:a,2:b},xy,notes='Bidirectional58V TVS across input bridge pair; select surge rating during qualification.')
 cap('10nF 100V',a,b,(xy[0],xy[1]-5),large=True,notes='X7R100V minimum, PoE primary only')
# Ag97005 bulk: 3x22uF MLCC minimum66uF nominal per datasheet, DC-bias qualification mandatory.
for x in (79,84,89):cap('22uF','5v_pd','gnd',(x,124),large=True,notes='X7R16V1206;3x22uF; measure effective aggregate under5V bias and startup')
cap('100nF','5v_pd','gnd',(89,128));cap('10uF','5v_pd','gnd',(89,133),large=True)
part('F1','044901.5MR','Hub:Littelfuse_449',{1:'5v_pd',2:'5v_fused'},[99,132],notes='1.5A time-delay secondary fuse,<=1A continuous5V load; verify derating.')
# Service reset/boot buttons, each only pulls low.
for i,net,xy in [(1,'s3_en',(23,38)),(2,'s3_boot',(36,40)),(3,'mg24_reset',(129,36)),(4,'mg24_boot',(140,36))]:
 part('SW'+str(i),'SW_PUSH','Button_Switch_SMD:SW_SPST_TL3342',{1:net,2:'gnd'},xy,notes='Momentary normally open; pulls low, never drives voltage.')
# Power flags describe PSE, local common return, and rails after passive fuse/filter.
for i,net in enumerate(['gnd','POE_12','POE_36','POE_45','POE_78','5v_fused','3v3_analog'],1):part('#FLG'+str(i),'PWR_FLAG','',{1:net},[0,0],types={'1':'power_out'})
# Placement refinements after courtyard/antenna review. Coordinates are mm.
placements={'J1':(21,100),'C4':(26,21),'C7':(74,20),'R13':(58,35),'J8':(86,42),'J7':(111,46),'SW3':(122,33),'SW4':(138,34),'D1':(28,116),'D2':(39,116),'C37':(28,111),'C38':(39,111),'C39':(78,137),'C40':(85,137),'C50':(29,75)}
for p in parts:
 if p['ref'] in placements:p['xy']=placements[p['ref']]

for p in parts:
 if p['ref']=='J6':p['mechanical_pads']=['MP']

# PHY faces the magjack directly; the crystal and bypasses surround their pins.
_phy_placement={
 'U4':(61,104,0),'C20':(54,99.5,0),'C21':(52,112,0),
 'C22':(56,113,0),'C23':(58,111,0),'C24':(61.6,111,0),'C25':(65.2,111,0),
 'C26':(77,116,0),'C27':(73,108,0),'C28':(76,112,0),'FB1':(71,116,0),
 'R29':(55,108.5,0),'C29':(65,114,0),'C30':(60.5,114,0),
 'Y2':(69,104,0),'C31':(69,107.5,0),'C32':(69,100.5,0),'R30':(73,104,90),
 'R14':(70,97,0),'R15':(73,94,0),'R16':(58,96,0),
 'R31':(50,104,270),'R32':(46,99.5,90),
 'C34':(44.5,110,180),'C35':(44.5,108,180),
 'R34':(48,110.9125,270),'R35':(47.5,107.0875,90),'C36':(48,115,0),
}
for _p in parts:
 if _p['ref'] in _phy_placement:
  _x,_y,_a=_phy_placement[_p['ref']];_p['xy']=[_x,_y];_p['rotation']=_a

# Local bypasses follow the edge-mounted MGM module; shorten the SC16 oscillator loop.
for _p in parts:
 if _p['ref']=='C9':_p['xy']=[142,17.3]
 if _p['ref']=='C10':_p['xy']=[146.5,18]
 if _p['ref']=='Y1':_p['xy']=[77.5,59.35];_p['rotation']=90
 if _p['ref']=='C1':_p['xy']=[77.5,68];_p['rotation']=270
 if _p['ref']=='C2':_p['xy']=[77.5,50.5];_p['rotation']=90
 if _p['ref']=='C11':_p['xy']=[81.25,60.3];_p['rotation']=270;_p['footprint']='Capacitor_SMD:C_0603_1608Metric'
 if _p['ref']=='C12':_p['xy']=[86,69]
