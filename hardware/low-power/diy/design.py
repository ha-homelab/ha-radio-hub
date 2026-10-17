"""LP-D0, through-hole/wire-assisted implementation of the verified C0 contract."""
from pathlib import Path
import copy, importlib.util
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('c0_design', ROOT.parent/'carrier/design.py')
c0=importlib.util.module_from_spec(spec);spec.loader.exec_module(c0)
parts=copy.deepcopy(c0.parts);connectors=copy.deepcopy(c0.connectors);SOURCES=copy.deepcopy(c0.SOURCES)
WIDTH,HEIGHT=190,145
SOURCES['adapter_headers']='https://www.adafruit.com/product/400'
SOURCES['adapter_header_drawing']='https://cdn-shop.adafruit.com/datasheets/18072.pdf'
SOURCES.update(adafruit1208='https://www.adafruit.com/product/1208',adafruit1230='https://www.adafruit.com/product/1230',adapter_cad='https://github.com/adafruit/Adafruit-SMT-Breakout-PCBs/tree/dbd7a1928c2b668a9edf3d53277063eac4c3e938',crystal='https://abracon.com/Resonators/ab.pdf',fuse='https://www.littelfuse.com/assetdocs/powr-gard-catalog?assetguid=85d36235-a32b-4608-bfed-f9878aa43af0',fuseholder='https://www.littelfuse.com/assetdocs/fuse-holder-150-datasheet?assetguid=662e5ae4-2c3a-4d7a-8642-e7d9db02703d')
positions={
'J1':(15,12,0),'J2':(42,12,0),'J3':(20,30,0),'J4':(55,18,0),'J5':(151,18,0),'J6':(151,43,0),'J7':(50,43,0),'J8':(116,130,0),'J9':(57,130,0),'J10':(20,121,0),
'F1':(24,12,0),'U1':(85,60,0),'U2':(67,101,0),'Y1':(71,77,90),
'R1':(108,93,0),'R2':(110,85,0),'R3':(75,111,0),'R4':(113,77,0),
'R5':(113,69,0),'R6':(113,61,0),'R7':(130,61,0),'R8':(130,69,0),'R9':(130,77,0),'R10':(130,85,0),'R11':(147,77,0),'R12':(147,85,0),
'R13':(65,53,0),'R14':(49,53,0),'R15':(67,28,0),'R16':(154,30,0),'R17':(170,30,0),
'C1':(78,72,90),'C2':(78,79,90),'C3':(80,86,90),'C4':(74,90,90),'C5':(60,106,0),'C6':(60,98,0),'C7':(149,31,90),'C8':(54,8,0),'C9':(62,8,0),
'C10':(32,30,90),'C11':(86,18,90),'C12':(176,18,90),'C13':(173,43,90),'C14':(77,43,90),'C15':(136,130,90),'C16':(75,130,90),'C17':(36,121,90)}
for p in parts:
 if p['ref'].startswith('#'):continue
 p['xy']=positions[p['ref']][:2];p['rotation']=positions[p['ref']][2]
 if p['ref']=='J3':p['footprint']='DIY:Wurth_61204021621'
 elif p['ref']=='J10':
  p.update(model='B4B-XH-A',footprint='Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical')
  p['pins']={k:v for k,v in p['pins'].items() if k.isdigit()};p['source']='jst_xh';p['notes']='TH XH to factory STEMMA QT cable; same logical order as C0, mechanically NOT a QT socket.'
 elif p['ref']=='U1':p.update(footprint='DIY:Adafruit1208_TSSOP28',source='adafruit1208',notes='SC16IS752IPW,128 soldered to factory Adafruit1208 TSSOP side; pin1 adapter orientation verified from published CAD; no SOIC chip. Solder 2x14 male headers to adapter.')
 elif p['ref']=='U2':p.update(footprint='DIY:Adafruit1230_SOT23_6',source='adafruit1230',notes='TPS3808G33DBVR soldered to factory Adafruit1230 SOT23-6 adapter, two 1x3 male headers. Do not populate reverse-side transistor footprints.')
 elif p['ref']=='Y1':p.update(model='AB-3.6864MHZ-B2',footprint='DIY:HC49U',source='crystal',notes='Through-hole HC49/U 3.6864MHz18pF; 4.88mm lead pitch; initial22/33pF loads, validate oscillation/frequency on hardware.')
 elif p['ref']=='F1':p.update(model='Littelfuse 022901.5MXP',footprint='DIY:FuseHarness',notes='1.5A slow-blow 2AG cartridge in external01500274Z holder. Holder leads adapt to22AWG at F1 holes; insulate splices. <=1A continuous design. Do not bridge.',source='fuse')
 elif p['ref'].startswith('R'):p.update(footprint='DIY:Axial_R_P10.16',notes='Axial 1%0.25W resistor, body<=6.8x2.5mm, leads formed to10.16mm pitch.')
 elif p['ref'].startswith('C'):
  bulk=p['ref'] in ['C8','C9'];p.update(footprint='DIY:Radial_C_P2.54',notes=('22uF >=10V radial electrolytic, body<=5mm, pin1 positive. ' if bulk else 'Radial ceramic >=10V, body<=5x3mm, C0G for crystal loads; X7R otherwise. ')+'Form leads to2.54mm pitch; no adjacent lead shorts.')
for c in connectors:
 c['viewing_convention']=c['viewing_convention'].replace('Carrier','DIY PCB')
 if c['ref']=='J10':
  c.update(model='B4B-XH-A',mating_model='XHP-4',contacts='SXH-001T-P0.6',label='BME680 via XH-to-factory-QT cable; NOT direct QT')
  for p in c['pins']:p['notes']='XH end follows PCB numbering; splice to precrimped QT cable by continuity, not colors; keep same four logical nets.'
