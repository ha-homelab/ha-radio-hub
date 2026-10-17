"""Native KiCad schematic writer, shared by the routing and final assembly models."""
def write_schematic(ROOT,parts,U,Q):
    # Symbol bodies contain actual physical pin numbers; net labels are on real wire stubs.
    symbols=[];instances=[];wires=[];labels=[];ncs=[]
    rootid=U('schematic')
    def geom(obj):
        count=len(obj['pins']);left=(count+1)//2 if count>8 else count
        if count==2 and obj['ref'][0] in 'RCYF':
            return [(num,net,(-7.62 if i==0 else 7.62),0,(0 if i==0 else 180),i==1) for i,(num,net) in enumerate(obj['pins'].items())],1
        r=[]
        for i,(num,net) in enumerate(obj['pins'].items()):
            right=i>=left;rank=i-left if right else i
            r.append((num,net,20.32 if right else -20.32, -rank*2.54,180 if right else 0,right))
        return r,left
    for idx,obj in enumerate(parts):
        ref=obj['ref'];g,left=geom(obj);name='LP_'+ref.replace('#','')
        ymin=-max(1,left-1)*2.54-2.54
        sym=[f'(symbol {Q(name)} (pin_names (offset 0.508)) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") or obj.get("off_board") else "yes"})',
        f'(property "Reference" {Q(ref)} (at 0 5.08 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(obj["model"])} (at 0 2.54 0) (effects (font (size 1.27 1.27))))',
        f'(symbol "{name}_0_1" (rectangle (start -15.24 1.27) (end 15.24 {ymin}) (stroke (width 0.254) (type default)) (fill (type background))))',f'(symbol "{name}_1_1"']
        for num,net,x,y,ang,right in g:
            typ=obj['types'].get(num,'passive');pinname=net or 'NC'
            short=len(obj['pins'])==2 and ref[0] in 'RCYF';pinlen=3.81 if short else 5.08;shown='~' if short else pinname
            sym.append(f'(pin {typ} line (at {x} {y} {ang}) (length {pinlen}) (name {Q(shown)} (effects (font (size 0.8 0.8)))) (number {Q(num)} (effects (font (size 1 1)))))')
        sym.append('))')
        if len(obj['pins'])==2 and ref[0] in 'RCYF':
            # Conventional IEC passives keep the schematic readable at useful zoom.
            body=f'(symbol "{name}_0_1" '
            if ref[0]=='C':
                body+=''.join(f'(polyline (pts (xy {xx} -2.54) (xy {xx} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))' for xx in [-1.27,1.27])
                body+=''.join(f'(polyline (pts (xy {a} 0) (xy {b} 0)) (stroke (width 0.254) (type default)) (fill (type none)))' for a,b in [(-3.81,-1.27),(1.27,3.81)])
            else:
                body+='(rectangle (start -3.81 -1.27) (end 3.81 1.27) (stroke (width 0.254) (type default)) (fill (type none)))'
            body+=')'
            sym[3]=body
        symbols.append('\n'.join(sym))
        row=idx//7
        x=43.18+(idx%7)*81.28;y=25.4+min(row,2)*68.58+max(0,row-2)*38.1
        iid=U('symbol/'+ref)
        inst=[f'(symbol (lib_id "DIY:{name}") (at {x:.4f} {y:.4f} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") or obj.get("off_board") else "yes"}) (dnp no) (uuid "{iid}")',f'(property "Reference" {Q(ref)} (at {x} {y-6.35} 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(obj["model"])} (at {x} {y-3.81} 0) (effects (font (size 1.0 1.0))))',f'(property "Footprint" {Q(obj["footprint"])} (at {x} {y} 0) (effects (font (size 1 1)) hide))']
        for num,net,px,py,ang,right in g:
            inst.append(f'(pin {Q(num)} (uuid "{U(ref+"/pin/"+num)}"))')
            xx=round(x+px,4);yy=round(y-py,4);end=round(xx+(5.08 if right else -5.08),4)
            if net is None:ncs.append(f'(no_connect (at {xx} {yy}) (uuid "{U(ref+"/NC/"+num)}"))')
            else:
                wires.append(f'(wire (pts (xy {xx} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{U(ref+"/wire/"+num)}"))')
                labels.append(f'(label {Q(net)} (at {end} {yy} {0 if right else 180}) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid "{U(ref+"/label/"+num)}"))')
        inst.append(f'(instances (project "diy" (path "/{rootid}" (reference {Q(ref)}) (unit 1)))) )');instances.append('\n'.join(inst))
    (ROOT/'DIY.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+'\n'.join(symbols)+'\n)\n')
    (ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "DIY")(type "KiCad")(uri "${KIPRJMOD}/DIY.kicad_sym")(options "")(descr "LP-D0 explicit physical pin symbols")))\n')
    embedded=[s.replace('(symbol "LP_', '(symbol "DIY:LP_',1) for s in symbols]
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "User" 610 1500) (title_block (title "LP-D0 low-voltage module carrier - PROTOTYPE") (date "2026-10-17") (rev "D0") (comment 1 "3.3V logic; external isolated5V and buck; named harnesses, no unverified module footprints"))\n(lib_symbols\n'+'\n'.join(embedded)+')\n'+'\n'.join(wires+labels+ncs+instances)+'\n)\n'
    (ROOT/'diy.kicad_sch').write_text(sch)
