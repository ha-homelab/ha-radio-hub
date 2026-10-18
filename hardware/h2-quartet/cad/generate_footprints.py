#!/usr/bin/env python3
"""Generate original direct-solder carrier footprints from sourced measurements.

Python standard library only. These are carrier holes for factory male pins,
not sockets, castellated SMD lands, or a bare MCU layout.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def generate():
    data = json.loads((ROOT / "mechanics.json").read_text())
    output = ROOT / "Q1.pretty"
    output.mkdir(exist_ok=True)
    for name, module in data["modules"].items():
        xoff = module["first_pin_offset_from_left_edge"]
        yoff = module.get("first_pin_offset_from_usb_edge", module.get("first_pin_offset_from_jack_edge"))
        left, top = -xoff, -yoff
        right, bottom = left + module["board_width"], top + module["board_length"]
        body = [
            f'(footprint "{name}" (version 20260206) (generator "pcbnew") (layer "F.Cu")',
            ' (descr "Factory male headers solder directly into plated carrier holes. NO SOCKETS. Source dimensions in mechanics.json; fit not physically verified.")',
            ' (attr through_hole)',
            f' (property "Reference" "REF**" (at {module["row_spacing"] / 2} {top - 2} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
            f' (property "Value" "{name}" (at {module["row_spacing"] / 2} {bottom + 2} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        ]
        for layer, clearance, width in [("F.Fab", 0, 0.1), ("F.CrtYd", 0.5, 0.05)]:
            body.append(f' (fp_rect (start {left-clearance} {top-clearance}) (end {right+clearance} {bottom+clearance}) (stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
        for x, key in [(0, "left_top_to_bottom"), (module["row_spacing"], "right_top_to_bottom")]:
            for index, number in enumerate(module[key]):
                shape = "rect" if number == module["left_top_to_bottom"][0] else "circle"
                size, drill = data["carrier_hole"]["pad_diameter"], data["carrier_hole"]["finished_drill"]
                body.append(f' (pad "{number}" thru_hole {shape} (at {x} {index * module["pitch"]:.4f}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
        body.append(")")
        (output / f"{name}.kicad_mod").write_text("\n".join(body) + "\n")
    (ROOT / "fp-lib-table").write_text('(fp_lib_table (version 7) (lib (name "Q1") (type "KiCad") (uri "${KIPRJMOD}/Q1.pretty") (options "") (descr "Direct-solder ready-module carrier footprints")))\n')


if __name__ == "__main__":
    generate()
