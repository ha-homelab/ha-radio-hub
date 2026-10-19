from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={
'host':'https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html',
'host_module':'https://www.espressif.com/sites/default/files/documentation/esp32-wrover-e_esp32-wrover-ie_datasheet_en.pdf',
'host_schematic':'https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf',
'host_layout':'https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_pcb_layout.pdf',
'wiz_schematic':'https://docs.wiznet.io/assets/files/wiz850io_sch_v110-3fcc19fc2acaf16f15c5f08f9c8330cb.pdf',
'host_dimensions':'https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_dimensions.pdf',
'c6':'https://github.com/UnexpectedMaker/esp32c6/tree/7c3137962e469be55a295d0eb7ccebed2a6354d1/TinyC6',
'xiao':'https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip',
'wiz_photo':'https://docs.wiznet.io/img/products/wiz850io/wiz850io.png',
'wiz_pinmap':'https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png',
'wiz':'https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png',
'weikai':'https://wiki.dfrobot.com/dfr0627',
'connector':'https://www.samtec.com/products/tsw',
'diode':'https://www.vishay.com/docs/88525/1n5817.pdf',
'resistor':'https://www.vishay.com/docs/28729/mrs16.pdf',
}
BOARD_W=100
BOARD_H=100
BOARD_OUTLINE=[(0,0),(100,0),(100,100),(0,100)]
MOUNT_HOLES=[(4,4),(96,4),(4,96),(96,96)]
MOUNT_REFS=['H1','H2','H3','H4']
RAIL_LANDS=[]
RAIL_COPPER_KEEPOUTS=[]
# Factory external RF ports; antenna radiators reside outside this PCB.
RF_KEEPOUTS=[]
RF_POUR_ONLY_KEEPOUTS=[]
USB_ENVELOPES={'U1':[17,70,29,99],'U2':[48,0,60,12],'U3':[77,0,91,12]}
USB_SOCKET_BOUNDS_LOCAL={'U1':[8,44.5,17.4,50], 'U2':[-4.21,-18.718,4.43,-10.89], 'U3':[3.12,-5.921,12.12,-2.921]}
BODY_BOUNDS={'U1':[-1.27,-7.34,26.67,46.99],'U2':[-8.78,-18,9,16.67735],'U3':[-1.27,-2.921,16.51,18.034],'U4':[-1.34,-6.4,21.66,18.6]}
parts=[]
def add(ref,model,fp,pins,xy,rotation=0,source='connector',notes=''):
 if ref.startswith('J') and rotation==270:rotation=90
 parts.append(dict(ref=ref,model=model,footprint=fp,pins={str(k):v for k,v in pins.items()},types={},fitted=ref not in ('J8','J9'),side='front',xy=xy,rotation=rotation,source=source,notes=notes))
hostnames={'J2':['3V3','EN','36','39','34','35','32','33','25','26','27','14','12','GND','13','9','10','11','5V'],'J3':['GND','23','22','1','3','21','GND','19','18','5','17','16','4','0','2','15','8','7','6']}
hostnets={'5V':'+5V_HOST','GND':'GND','0':'HOST_BOOT_SERVICE','25':'RF_GDO0','35':'RF_GDO2','13':'RF_CS','33':'ZB_CTS','14':'ZB_RTS','23':'RADAR_RX','32':'ZB_RX','39':'ZB_TX','4':'ETH_RESET','34':'ETH_INT','2':'SPI_MOSI','19':'SPI_MISO','12':'SPI_SCK','5':'ETH_CS','21':'I2C_SDA','22':'I2C_SCL','26':'THREAD_RX','36':'THREAD_TX','18':'RADAR_TX','27':'THREAD_EN','15':'THREAD_BOOT'}
add('U1','ESP32-DevKitC-VIE','MC2:ESP32_DevKitC_VIE',{f'{row}.{i+1}':hostnets.get(n) for row,ns in hostnames.items() for i,n in enumerate(ns)},(9.27,20),0,source='host',notes='Factory male pins; WROVER-IE external U.FL; 8MB flash/8MB quad PSRAM; 5V via D1; GPIO0 boot,1/3 USB-UART,6-11 flash,16/17 PSRAM reserved; BLE4.2, no BLE5 extended advertising')
c6names={'1':'VBAT','2':'GND','3':'5V','4':'3V3','5':'3','6':'2','7':'1','8':'0','9':'11','10':'8','11':'9','12':'17','13':'16','14':'GND','15':'EN','16':'15','17':'5','18':'6','19':'7','20':'18','21':'19','22':'20','23':'21'}
c6nets={'3V3':'C6_LOCAL_3V3','8':'C6_STRAP8','5V':'+5V_C6','GND':'GND','EN':'THREAD_EN','17':'THREAD_RX','16':'THREAD_TX','9':'THREAD_BOOT'}
add('U2','Unexpected Maker TinyC6-U-01','MC2:TinyC6_U',{n:c6nets.get(g) for n,g in c6names.items()},(53.78,30),0,source='c6',notes='Original TC6-U-01 fixed U.FL; NOT TC6D-01; solder supplied 1x12 + 1x11 male headers; native USB no bridge; ROM RX17 TX16; EN/BOOT9 accessible; no LiPo fitted')
xiaopins={str(i):None for i in range(1,15)}
xiaopins.update({'1':'ZB_BOOT_SERVICE','5':'ZB_CTS','6':'ZB_RTS','7':'ZB_TX','8':'ZB_RX','13':'GND','14':'+5V_ZB'})
add('U3','Seeed XIAO MG24 pre-soldered 102010690','MC2:XIAO_MG24',xiaopins,(76.27,14.921),0,source='xiao',notes='External UART PC06/PC07; CTS PC04 RTS PC05; USB probe preserved; 3V3 OUT NC; external U.FL selected by firmware PB04=1 PB05=1')
wizpins={'J1.1':'GND','J1.2':'GND','J1.3':'SPI_MOSI','J1.4':'SPI_SCK','J1.5':'ETH_CS','J1.6':'ETH_INT','J2.1':'GND','J2.2':'+3V3','J2.3':'+3V3','J2.4':None,'J2.5':'ETH_RESET','J2.6':'SPI_MISO'}
add('U4','WIZ850io finished module','MC2:WIZ850io',wizpins,(80.66,92.9),180,source='wiz',notes='Direct factory pins; two1x6 at20.32 rowspacing; RJ45 faces BOTTOM with mouth y=102mm; NO PoE extraction;3.3V only')
add('J1','FUSED ISOLATED 5V INPUT','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'+5V',2:'GND'},(40,88),90,notes='Offboard assembled active PoE splitter and fused 5V harness. No raw PoE voltage on carrier.')
add('J2','D24V22F3 external assembled buck','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'+3V3',4:'GND'},(40,79),90,notes='Harness interface only; pin1 buckVIN; pin2GND;pin3buckVOUT;pin4GND. Buck remains separate ready module.')
add('J3','DFR0627 WK2132 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'I2C_SDA',4:'I2C_SCL',5:'ZWAVE_RX',6:'ZWAVE_TX'},(73,48),90,source='weikai',notes='Harness to DFR0627 I2C and UART1, no WK2132 SMD on carrier. J3.5=module TX1;J3.6=module RX1; IA1=1 IA0=1; register address 0x70, FIFO 0x71; verify physical markings.')
add('J4','ZAC93 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'GND',4:'ZWAVE_RX',5:'ZWAVE_TX'},(73,57),90,notes='Carrier1->ZACpin1;2->pin6;3->pin9;4->pin8RX;5->pin10TX. Different from ZAC physical header layout.')
add('J5','CC1101 ready module harness','Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',{1:'+3V3',2:'GND',3:'SPI_SCK',4:'SPI_MOSI',5:'SPI_MISO',6:'RF_CS',7:'RF_GDO0',8:'RF_GDO2'},(40,55),90,notes='3.3V; GDO0 open-drain TX with external4.7k pullup; GDO2 receiver.')
add('J6','LD2450 radar harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'+5V',2:'GND',3:'RADAR_RX',4:'RADAR_TX'},(40,63),90,notes='Carrier3->radarRX;carrier4<-radarTX;5V supply;3.3V data.')
add('J7','BME680 external pod harness','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{1:'GND',2:'+3V3',3:'I2C_SDA',4:'I2C_SCL'},(40,71),90,notes='External pod,1GND2VDD3SDA4SCL;I2C pullups on modules;do notaddunreviewedpullups.')
for i,xy,angle,out in [(1,(40,94),0,'+5V_HOST'),(2,(68,68),0,'+5V_C6'),(3,(81,68),0,'+5V_ZB')]:
 add('D'+str(i),'1N5819 USB supply isolation','Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal',{1:out,2:'+5V'},xy,angle,source='diode',notes='Cathodepad1->board5V;anodepad2->fused5Vbus. VerifyUSBprogrammingpowerpaths;forwarddropheadroom.')
add('R1','4.7k RF GDO0 pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_GDO0'},(68,39),0,source='resistor')
add('R2','10k RF CS idle pull-up','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'+3V3',2:'RF_CS'},(81,39),0,source='resistor')
add('J8','XIAO BOOT unpopulated service pads','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'ZB_BOOT_SERVICE',2:'GND'},(90,83),0,notes='Temporary short D0/PC00 to GND while resetting XIAO for recovery. Normally OPEN.')
add('J9','HOST BOOT unpopulated service pads','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'HOST_BOOT_SERVICE',2:'GND'},(90,92),90,notes='Normally OPEN; short GPIO0 to GND while pressing host RESET for USB-UART ROM recovery.')
add('R3','10k C6 download strap GPIO8','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'C6_LOCAL_3V3',2:'C6_STRAP8'},(69,14),270,source='resistor',notes='GPIO8 must be HIGH for UART download. Connect only to TinyC6 local3V3 pin4; never to shared peripheral3V3.')
# Bootstrap pins drive only SPI slave inputs. Never attach a pull-up or a peer
# output to GPIO12: WROVER-IE requires 3.3V VDD_SDIO selected by MTDI=LOW.
add('R4','10k host GPIO12 SCK boot pull-down','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'GND',2:'SPI_SCK'},(8,74),0,source='resistor',notes='Required LOW at reset: WROVER-IE VDD_SDIO=3.3V; WIZ850io and CC1101 SCK are inputs without pull-ups.')
add('R5','10k host GPIO2 MOSI boot pull-down','Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',{1:'GND',2:'SPI_MOSI'},(8,79),0,source='resistor',notes='Required LOW for serial download with GPIO0=LOW; MOSI connects only to SPI slave inputs.')
connectors=[dict(ref=p['ref'],model=p['model'],pins=p['pins'],notes=p['notes']) for p in parts if p['ref'].startswith(('U','J'))]

# Manufacturer top-view dimensions, in U4 footprint-local coordinates.
WIZ_MECHANICS={
 'pcb_bounds_local_mm':[-1.34,-6.4,21.66,18.6],
 'rj45_face_local_mm':[[2.11,-9.1],[18.21,-9.1]],
 'rj45_outward_normal_local':[0,-1],
 'service_corridor_global_mm':[58,102,85,138],
 'service_corridor_basis':'Engineering reservation for plug/boot/latch; verify actual cable and enclosure. Not a vendor dimension.',
 'evidence':'WIZnet dimension image:16.10mm jack width,20.32mm row spacing,6.40mm first-row offset,2.70mm jack projection. Official angled photo identifies opposite solder-contact side as rear.'
}

# RF port centre estimates used only for cable planning (not manufactured coordinates).
# Measure the supplied modules and coax bend/radius before case qualification.
RF_PORTS={'U1':{'radio':'BLE','connector':'U.FL / MHF1','estimated_xy_mm':[25,16], 'evidence':'Planning estimate for WROVER-IE external connector; measure the delivered DevKitC-VIE before cable qualification'},'U2':{'radio':'Thread','connector':'U.FL / MHF1','estimated_xy_mm':[59,43]},'U3':{'radio':'Zigbee','connector':'U.FL / MHF1','estimated_xy_mm':[79,31], 'evidence':'Bottom-left U.FL on official component-side USB-up front pinout: https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_front_pinout.png'}}
