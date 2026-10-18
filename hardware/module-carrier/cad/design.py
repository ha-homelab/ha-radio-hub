from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={
's3':'https://docs.waveshare.com/ESP32-S3-Nano',
'h2':'https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf',
'xiao':'https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip',
'wiz_photo':'https://docs.wiznet.io/img/products/wiz850io/wiz850io.png',
'wiz_pinmap':'https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png',
'wiz':'https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png',
'weikai':'https://wiki.dfrobot.com/dfr0627',
'connector':'https://www.samtec.com/products/tsw',
'diode':'https://www.vishay.com/docs/88525/1n5817.pdf',
'resistor':'https://www.vishay.com/docs/28729/mrs16.pdf',
}
BOARD_W=65
BOARD_H=75
MOUNT_HOLES=[(35,6),(24,51.8),(34,72)]
RF_KEEPOUTS=[(44.5,0,64.5,1.8),(48.5,0,58.5,6),(0,0,29,.4),(5,0,23,11.5),(0,54.5,1.2,75),(0,64.5,5,72.48),(0,72.48,2.5,73.5),(3.8,72.48,5,73.5)]
RF_POUR_ONLY_KEEPOUTS=[(2.5,72.48,3.8,73.5)]
USB_ENVELOPES={}
USB_SOCKET_BOUNDS_LOCAL={'U1':[2,-5.81,13.24,-3.81], 'U2':[-1.27,46.685,24.13,47.685], 'U3':[3.12,-5.921,12.12,-2.921]}
BODY_BOUNDS={'U1':[-1.27,-3.81,16.51,39.37],'U2':[-1.27,-1.575,24.13,46.685],'U3':[-1.27,-2.921,16.51,18.034],'U4':[-1.34,-6.4,21.66,18.6]}
parts=[]
def add(ref,model,fp,pins,xy,rotation=0,source='connector',notes=''):
 if ref.startswith('J') and rotation==270:rotation=90
 parts.append(dict(ref=ref,model=model,footprint=fp,pins={str(k):v for k,v in pins.items()},types={},fitted=ref not in ('J8','J9'),xy=xy,rotation=rotation,source=source,notes=notes))
s3names={'JP1':['48','3V3','46','1','2','3','4','11','12','13','14','VBUS','0','GND','VIN'],'JP2':['43','44','EN','GND','5','6','7','8','9','10','17','18','21','38','47']}
s3nets={'VIN':'+5V_S3','GND':'GND','0':'S3_BOOT_SERVICE','4':'RF_GDO0','5':'RF_GDO2','6':'RF_CS','7':'ZB_CTS','8':'RADAR_RX','17':'ZB_RX','18':'ZB_TX','9':'ETH_RESET','10':'ETH_INT','11':'SPI_MOSI','12':'SPI_MISO','13':'SPI_SCK','14':'ETH_CS','1':'I2C_SDA','2':'I2C_SCL','43':'THREAD_RX','44':'THREAD_TX','38':'RADAR_TX','47':'THREAD_EN','48':'THREAD_BOOT','21':'ZB_RTS'}
add('U1','Waveshare ESP32-S3-Nano-M 16MB flash 8MB PSRAM','MC1:S3_Nano_M',{f'{row}.{i+1}':s3nets.get(n) for row,ns in s3names.items() for i,n in enumerate(ns)},(62.5,39),180,source='s3',notes='Factory male pins direct solder; JP1.15 VIN via D1; VBUS/3V3 NC; nativeUSB19/20; GPIO0 service; sharedSPI; no sockets')
h2names={'J1':['3V3','EN','0','1','2','3','13','14','4','5','NC','VBAT','GND','5V','GND'],'J3':['GND','24','23','10','11','25','12','8','22','GND','9','GND','27','26','GND']}
h2nets={'5V':'+5V_H2','GND':'GND','EN':'THREAD_EN','23':'THREAD_RX','24':'THREAD_TX','9':'THREAD_BOOT'}
add('U2','ESP32-H2-DevKitM-1-N4S','MC1:H2_DevKitM1',{f'{row}.{i+1}':h2nets.get(n) for row,ns in h2names.items() for i,n in enumerate(ns)},(2,1.5),0,source='h2',notes='RCP/ROM RX23 TX24; remove USB-UART TX series R7 before assembly; native USB retained; 3V3/VBAT NC')
xiaopins={str(i):None for i in range(1,15)}
xiaopins.update({'1':'ZB_BOOT_SERVICE','5':'ZB_CTS','6':'ZB_RTS','7':'ZB_TX','8':'ZB_RX','13':'GND','14':'+5V_ZB'})
add('U3','Seeed XIAO MG24 pre-soldered 102010690','MC1:XIAO_MG24',xiaopins,(18,57.5),270,source='xiao',notes='External UART PC06/PC07; CTS PC04 RTS PC05; USB probe preserved; 3V3 OUT NC')
wizpins={'J1.1':'GND','J1.2':'GND','J1.3':'SPI_MOSI','J1.4':'SPI_SCK','J1.5':'ETH_CS','J1.6':'ETH_INT','J2.1':'GND','J2.2':'+3V3','J2.3':'+3V3','J2.4':None,'J2.5':'ETH_RESET','J2.6':'SPI_MISO'}
add('U4','WIZ850io finished module','MC1:WIZ850io',wizpins,(61,67.9),180,source='wiz',notes='Direct factory pins; two1x6 at20.32 rowspacing; RJ45 faces BOTTOM with mouth y=77mm; NO PoE extraction;3.3V only')
add('J1','FUSED ISOLATED 5V INPUT','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'+5V',2:'GND'},(42.5,42.99),0,notes='Offboard assembled active PoE splitter and fused 5V harness. No raw PoE voltage on carrier.')
add('J2','D24V22F3 external assembled buck','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'+3V3',4:'GND'},(42.5,30.87),0,notes='Harness interface only; pin1 buckVIN; pin2GND;pin3buckVOUT;pin4GND. Buck remains separate ready module.')
add('J3','DFR0627 WK2132 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'I2C_SDA',4:'I2C_SCL',5:'ZWAVE_RX',6:'ZWAVE_TX'},(36.25,18.75),0,source='weikai',notes='Harness to DFR0627 I2C and UART1, no WK2132 SMD on carrier. J3.5=module TX1;J3.6=module RX1; IA1=1 IA0=1; register address 0x70, FIFO 0x71; verify physical markings.')
add('J4','ZAC93 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'GND',4:'ZWAVE_RX',5:'ZWAVE_TX'},(36.25,35.95),0,notes='Carrier1->ZACpin1;2->pin6;3->pin9;4->pin8RX;5->pin10TX. Different from ZAC physical header layout.')
add('J5','CC1101 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'SPI_SCK',4:'SPI_MOSI',5:'SPI_MISO',6:'RF_CS',7:'RF_GDO0',8:'RF_GDO2'},(30,18.75),0,notes='3.3V; GDO0 open-drain TX with external4.7k pullup; GDO2 receiver.')
add('J6','LD2450 radar harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'RADAR_RX',4:'RADAR_TX'},(30,41.03),0,notes='Carrier3->radarRX;carrier4<-radarTX;5V supply;3.3V data.')
add('J7','BME680 external pod harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'GND',2:'+3V3',3:'I2C_SDA',4:'I2C_SCL'},(42.5,18.75),0,notes='External pod,1GND2VDD3SDA4SCL;I2C pullups on modules;do notaddunreviewedpullups.')
for i,xy,out in [(1,(26,58.5),'+5V_S3'),(2,(29.6,58.5),'+5V_H2'),(3,(33.2,58.5),'+5V_ZB')]:
 add('D'+str(i),'1N5819 USB supply isolation','Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal',{1:out,2:'+5V'},xy,270,source='diode',notes='Cathodepad1->board5V;anodepad2->fused5Vbus. VerifyUSBprogrammingpowerpaths;forwarddropheadroom.')
add('R1','4.7k RF GDO0 pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_GDO0'},(36.8,58.5),270,source='resistor')
add('R2','10k RF CS idle pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_CS'},(49,46.8),0,source='resistor')
add('J8','XIAO BOOT unpopulated service pads','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'ZB_BOOT_SERVICE',2:'GND'},(3,52.5),90,notes='Temporary short D0/PC00 to GND while resetting XIAO for recovery. Normally OPEN.')
add('J9','Nano BOOT unpopulated service pads','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'S3_BOOT_SERVICE',2:'GND'},(12,52.5),90,notes='Normally OPEN; short GPIO0 to GND while pressing Nano RESET for nativeUSB ROM recovery.')
connectors=[dict(ref=p['ref'],model=p['model'],pins=p['pins'],notes=p['notes']) for p in parts if p['ref'].startswith(('U','J'))]

# Manufacturer top-view dimensions, in U4 footprint-local coordinates.
WIZ_MECHANICS={
 'pcb_bounds_local_mm':[-1.34,-6.4,21.66,18.6],
 'rj45_face_local_mm':[[2.11,-9.1],[18.21,-9.1]],
 'rj45_outward_normal_local':[0,-1],
 'service_corridor_global_mm':[35,74.3,65,113],
 'service_corridor_basis':'Engineering reservation for plug/boot/latch; verify actual cable and enclosure. Not a vendor dimension.',
 'evidence':'WIZnet dimension image:16.10mm jack width,20.32mm row spacing,6.40mm first-row offset,2.70mm jack projection. Official angled photo identifies opposite solder-contact side as rear.'
}
