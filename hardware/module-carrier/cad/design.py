from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={
's3':'https://dl.espressif.com/dl/schematics/esp_idf/DXF_ESP32-S3-DevKitC-1_V1.1_20220429.pdf',
'h2':'https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf',
'xiao':'https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip',
'wiz':'https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png',
'weikai':'https://wiki.dfrobot.com/dfr0627',
'connector':'https://www.samtec.com/products/tsw',
'diode':'https://www.vishay.com/docs/88525/1n5817.pdf',
'resistor':'https://www.vishay.com/docs/28729/mrs16.pdf',
}
parts=[]
def add(ref,model,fp,pins,xy,rotation=0,source='connector',notes=''):
 parts.append(dict(ref=ref,model=model,footprint=fp,pins={str(k):v for k,v in pins.items()},types={},xy=xy,rotation=rotation,source=source,notes=notes))
s3names={'J1': ['3V3','3V3','EN','4','5','6','7','15','16','17','18','8','3','46','9','10','11','12','13','14','5V','GND'], 'J3':['GND','43','44','1','2','42','41','40','39','38','37','36','35','0','45','48','47','21','20','19','GND','GND']}
s3nets={'5V':'+5V_S3','GND':'GND','4':'RF_GDO0','5':'RF_GDO2','6':'RF_MISO','7':'RF_SCK','8':'RF_MOSI','15':'RF_CS','16':'ZB_CTS','17':'ZB_RX','18':'ZB_TX','9':'ETH_RESET','10':'ETH_INT','11':'ETH_MOSI','12':'ETH_MISO','13':'ETH_SCK','14':'ETH_CS','1':'I2C_SDA','2':'I2C_SCL','41':'THREAD_RX','42':'THREAD_TX','39':'RADAR_RX','40':'RADAR_TX','47':'THREAD_EN','48':'THREAD_BOOT','21':'ZB_RTS'}
add('U1','ESP32-S3-DevKitC-1-N8R8 v1.1','MC1:S3_DevKitC1_v11',{f'{row}.{i+1}':s3nets.get(n) for row,ns in s3names.items() for i,n in enumerate(ns)},(44,3),source='s3',notes='Factory male headers solder directly; 3V3 outputs NC; USB19/20 and bridge43/44 untouched; no sockets')
h2names={'J1':['3V3','EN','0','1','2','3','13','14','4','5','NC','VBAT','GND','5V','GND'],'J3':['GND','24','23','10','11','25','12','8','22','GND','9','GND','27','26','GND']}
h2nets={'5V':'+5V_H2','GND':'GND','EN':'THREAD_EN','4':'THREAD_RX','5':'THREAD_TX','9':'THREAD_BOOT'}
add('U2','ESP32-H2-DevKitM-1-N4S','MC1:H2_DevKitM1',{f'{row}.{i+1}':h2nets.get(n) for row,ns in h2names.items() for i,n in enumerate(ns)},(86,3),source='h2',notes='RCP RX4 TX5; native USB and UART bridge pins untouched; 3V3/VBAT NC')
xiaopins={str(i):None for i in range(1,15)}
xiaopins.update({'1':'ZB_BOOT_SERVICE','5':'ZB_CTS','6':'ZB_RTS','7':'ZB_TX','8':'ZB_RX','13':'GND','14':'+5V_ZB'})
add('U3','Seeed XIAO MG24 pre-soldered 102010690','MC1:XIAO_MG24',xiaopins,(143,18),180,source='xiao',notes='External UART PC06/PC07; CTS PC04 RTS PC05; USB probe preserved; 3V3 OUT NC')
wizpins={'J1.1':'GND','J1.2':'GND','J1.3':'ETH_MOSI','J1.4':'ETH_SCK','J1.5':'ETH_CS','J1.6':'ETH_INT','J2.1':'GND','J2.2':'+3V3','J2.3':'+3V3','J2.4':None,'J2.5':'ETH_RESET','J2.6':'ETH_MISO'}
add('U4','WIZ850io finished module','MC1:WIZ850io',wizpins,(17,72),source='wiz',notes='Direct factory pins; two1x6 at20.32 rowspacing; NO PoE extraction;3.3V only')
add('J1','FUSED ISOLATED 5V INPUT','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'+5V',2:'GND'},(13,93),90,notes='Offboard assembled active PoE splitter and fused 5V harness. No raw PoE voltage on carrier.')
add('J2','D24V22F3 external assembled buck','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'+3V3',4:'GND'},(36,93),90,notes='Harness interface only; pin1 buckVIN; pin2GND;pin3buckVOUT;pin4GND. Buck remains separate ready module.')
add('J3','DFR0627 WK2132 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'I2C_SDA',4:'I2C_SCL',5:'ZWAVE_RX',6:'ZWAVE_TX'},(92,93),90,source='weikai',notes='Harness to DFR0627 I2C and UART1, no WK2132 SMD on carrier. J3.5=module TX1;J3.6=module RX1; IA1=1 IA0=1; register address 0x70, FIFO 0x71; verify physical markings.')
add('J4','ZAC93 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'GND',4:'ZWAVE_RX',5:'ZWAVE_TX'},(126,93),90,notes='Carrier1->ZACpin1;2->pin6;3->pin9;4->pin8RX;5->pin10TX. Different from ZAC physical header layout.')
add('J5','CC1101 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'RF_SCK',4:'RF_MOSI',5:'RF_MISO',6:'RF_CS',7:'RF_GDO0',8:'RF_GDO2'},(58,77),90,notes='3.3V; GDO0 open-drain TX with external4.7k pullup; GDO2 receiver.')
add('J6','LD2450 radar harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'RADAR_RX',4:'RADAR_TX'},(150,57),notes='Carrier3->radarRX;carrier4<-radarTX;5V supply;3.3V data.')
add('J7','BME680 external pod harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'GND',2:'+3V3',3:'I2C_SDA',4:'I2C_SCL'},(150,79),notes='External pod,1GND2VDD3SDA4SCL;I2C pullups on modules;do notaddunreviewedpullups.')
for i,xy,out in [(1,(44,86),'+5V_S3'),(2,(75,86),'+5V_H2'),(3,(130,48),'+5V_ZB')]:
 add('D'+str(i),'1N5819 USB supply isolation','Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal',{1:out,2:'+5V'},xy,source='diode',notes='Cathodepad1->board5V;anodepad2->fused5Vbus. VerifyUSBprogrammingpowerpaths;forwarddropheadroom.')
add('R1','4.7k RF GDO0 pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_GDO0'},(67,68),source='resistor')
add('R2','10k RF CS idle pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_CS'},(82,68),source='resistor')
add('J8','XIAO BOOT service short to GND','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'ZB_BOOT_SERVICE',2:'GND'},(141,35),90,notes='Temporary short D0/PC00 to GND while resetting XIAO for recovery. Normally OPEN.')
connectors=[dict(ref=p['ref'],model=p['model'],pins=p['pins'],notes=p['notes']) for p in parts if p['ref'].startswith(('U','J'))]
