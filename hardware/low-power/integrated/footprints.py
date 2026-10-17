"""Manufacturer-dimensional footprints; quantities in mm, PCB top view.
Do not substitute board-header positions for module pads. Source drawings in sources.md.
"""
import json,shutil
from pathlib import Path
Q=lambda x:json.dumps(str(x))
def fp(name,rect,pads,descr):
 x1,y1,x2,y2=rect
 lines=[f'(footprint {Q(name)} (version 20260206) (generator "pcbnew") (layer "F.Cu") (descr {Q(descr)})',f'(property "Reference" "REF**" (at 0 {y1-1.5}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',f'(property "Value" {Q(name)} (at 0 {y2+1.5}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
 for layer,gap in [('F.Fab',0),('F.CrtYd',0.5)]:lines.append(f'(fp_rect (start {x1-gap} {y1-gap}) (end {x2+gap} {y2+gap}) (stroke (width 0.05) (type solid)) (fill none) (layer "{layer}"))')
 for p in pads:
  n,x,y,w,h,*rest=p;drill=rest[0] if rest else 0;np=rest[1] if len(rest)>1 else False
  kind='np_thru_hole' if np else 'thru_hole' if drill else 'smd';shape='circle' if np else 'rect' if str(n) in ('1','VIN') else 'oval' if drill else 'roundrect'
  s=f'(pad {Q(n)} {kind} {shape} (at {x} {y}) (size {w} {h}) '
  s+=f'(drill {drill}) (layers "*.Cu" "*.Mask")' if drill else '(layers "F.Cu" "F.Paste" "F.Mask")'
  if shape=='roundrect':s+=' (roundrect_rratio 0.5)'
  lines.append(s+')')
 return '\n'.join(lines+[')'])+'\n'
def build_custom(dst):
 dst.mkdir(parents=True,exist_ok=True)
 parts={}
 parts['MGM240P']=fp('MGM240P',(0,0,12.9,15),[(n,.8,.7+n-1,2.4,.6) for n in range(1,15)]+[(n,2.95+n-15,14.2,.6,2.4) for n in range(15,23)]+[(n,12.1,13.7-(n-23),2.4,.6) for n in range(23,37)],'Silicon Labs MGM240P Rev1.0 Fig8.3 top-view land pattern. Verify current rev before production.')
 parts['D24V22F3']=fp('D24V22F3',(0,0,17.8,17.8),[(n,1.27+i*2.54,16.53,1.8,1.8,1.02) for i,n in enumerate(['PG','EN','VIN','GND','VOUT'])]+[('GND2',1.27,5.84,1.8,1.8,1.02),('',2.3,2.3,2.18,2.18,2.18,True),('',15.5,15.5,2.18,2.18,2.18,True)],'Pololu0J1031 topview, symbolic pin names, actual module foto crosscheck; soldered header vertical mount')
 # Primary pin1..6, 30.48mm gap from6 to7, 7..10 secondary.
 parts['Ag97000_FL']=fp('Ag97000_FL',(-2.03,-8.5,54.98,2.5),[(n,(n-1)*2.54,0,1.9,1.9,1.12) for n in range(1,7)]+[(n,43.18+(n-7)*2.54,0,1.9,1.9,1.12) for n in range(7,11)],'Silvertel Ag97000V2.0 Fig14; standing module; primary6pins and secondary4pins; explicit board isolation keepout')
 pads=[(1,-5.08,15.24,1.4,1.4,.9),(2,-3.048,15.24,1.4,1.4,.9),(5,3.048,15.24,1.4,1.4,.9),(6,5.08,15.24,1.4,1.4,.9),(7,-6.096,17.78,1.4,1.4,.9),(8,-4.064,17.78,1.4,1.4,.9),(9,-2.032,17.78,1.4,1.4,.9),(10,2.032,17.78,1.4,1.4,.9),(11,4.064,17.78,1.4,1.4,.9),('S1',-8.0645,-3.175,2.5,2.5,1.6),('S2',8.0645,-3.175,2.5,2.5,1.6),('',-6.35,0,3.25,3.25,3.25,True),('',6.35,0,3.25,3.25,3.25,True)]
 parts['Bel_0813_1X1T_57_F']=fp('Bel_0813_1X1T_57_F',(-8.18,-10.92,8.18,19.56),pads,'Bel0813-1X1T-57-F RevF sheet4 COMPONENT SIDE VIEW. Missing3/4/12 intentional. Separate PoE taps.')
 parts['Littelfuse_449']=fp('Littelfuse_449',(-3.15,-1.47,3.15,1.47),[(1,-2.45,0,1.96,3.15),(2,2.45,0,1.96,3.15)],'Littelfuse449 manufacturer land pattern,1.5A time-delay')
 for name,text in parts.items():(dst/(name+'.kicad_mod')).write_text(text)
 # H2 source footprint is vendored alongside this generator, with its license.
 source=Path(__file__).parent/'vendor'/'ESP32-H2-MINI-1.kicad_mod'
 shutil.copyfile(source,dst/source.name)
