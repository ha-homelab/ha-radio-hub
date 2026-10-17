# LP-M0 exact-target MGM240P adapter

**Prototype, not hardware validated.** This 60 × 40 × 1.6 mm, two-layer daughterboard carries the exact **MGM240PA22VNA3** module used by the project's [NCP firmware build](../../../../firmware/low-power/mg24/README.md). One M0 is required per modular C0 hub. It provides the power/ground lands, bypass capacitors, boot pull-up, antenna clearance and service connections that a bare module needs. It is a populated adapter board, not a substitute module variant or an unverified purchased breakout.

Open [mg24-adapter.kicad_pro](mg24-adapter.kicad_pro) in KiCad 10. Review the [schematic](outputs/schematic.pdf), [assembly drawing](outputs/assembly-top.svg), [top copper](outputs/board-top.svg), [BOM](assembly-bom.csv), [connector map](connectors.json) and [native validation report](outputs/validation/summary.json). [Prototype Gerbers and drill files](outputs/prototype-gerbers.zip) are for engineering review and first-article manufacture; passing CAD checks does not establish radio performance or assembly yield.

## Connections and assembly

J1 is a JST **B6B-XH-A** header, mating **XHP-6** with **SXH-001T-P0.6** contacts. Connect it to C0 J6 with a **straight number-to-number** cable: 1 = 3.3 V, 2 = GND, 3 = host TX/module PA05 RX, 4 = module PA06 TX/host RX, 5 = host RTS/module PB01 CTS, 6 = module PB00 RTS/host CTS. Both connectors need XHP-6 housings; the C0 harness BOM lists the C0 end, and this adapter's harness BOM adds the M0 end. No 5 V may reach this board.

J2 is a JST **B7B-XH-A** service header, mating **XHP-7**, with the same contact family. Pins are 1 = probe VTref sense (3.3 V, **not an external supply**), 2 = GND, 3 = SWCLK/PA01, 4 = SWDIO/PA02, 5 = RESET, 6 = PA00 BOOT, 7 = GND. RESET belongs to the module's **internal DVDD domain**: the probe may only pull it low and release it. Never add an external 3.3 V pull-up or drive it high. Pull BOOT low during reset only when the selected bootloader requires it; R1 otherwise pulls BOOT high. Use the exact firmware kit's SWD/boot instructions.

Connector numbers refer to **PCB component-side/top view**, with square pad and silk `1` identifying pin 1. The cable mating face is mirrored. Use the actual pad coordinates in `connectors.json` and continuity-test every cable; wire colors are not a pin-number convention.

The MGM240P is a fine-pitch castellated SMT module. Assemble it with a stencil and controlled reflow, or have the adapter populated by an assembler; this is not a breadboard plug-in soldering task. C1 is 100 nF, C2 is 1 µF and C3 is 10 µF, all X7R rated at least 10 V; account for capacitance loss under DC bias. C1 and C2 use 0805 pads, C3 uses 1206, and R1 is 10 kΩ, 1%, 0805. The assembly BOM specifies generic passive values/ratings where an exact stocked manufacturer part has not been selected. Inspect all 36 module lands, particularly its ground and VDD pads, before power is applied.

## Mechanical and RF constraints

The board is **60 × 40 mm**, nominal 1.6 mm FR-4, two copper layers, nominal 1 oz copper. Four 2.2 mm NPTH mounting holes have centres **(3,3), (57,3), (3,37), (57,37) mm**, measured from the board's upper-left corner in top view. Use nonconductive M2 standoffs/fasteners and check their head clearances. This adapter has not been fitted to the project's previous enclosure mock-up.

The module's upper-left body corner is **(23.55,0) mm**; its antenna edge aligns with the PCB edge. The 60 mm board width follows the manufacturer's recommended 55–60 mm ground-plane width. The module-local antenna exclusion x = 2.05–10.85 mm, y = 0–4.8 mm becomes board **x = 25.60–34.40 mm, y = 0–4.80 mm**. A native all-copper-layer keepout excludes tracks, vias and plane fill; no other component is placed over it. Both copper layers have ground fill elsewhere, every module ground land connects directly rather than through thermal relief, and ground stitching vias are within 2 mm of those lands. RFOUT pad 33 is deliberately unconnected for the built-in antenna.

Maintain the datasheet's **at least 10 mm clearance from metal/conductive objects around the antenna**, subject to its stated application-ground-plane exception. Do not place the antenna against plastic. The antenna keepout on this PCB does not enforce clearance to another PCB, a cable, enclosure hardware or a neighbouring radio. Validate those in the assembled product.

Manufacturing minima in this prototype are 0.20 mm track/clearance, 0.25 mm copper-to-routed-edge clearance and 0.30 mm minimum through-drill; the actual general signal routes use 0.25 mm tracks and normal vias are 0.8/0.4 mm. Power routes use 0.8 mm where routed, with short VDD land escapes. The edge clearance is intentionally 0.25 mm to permit the manufacturer's edge-aligned module lands and ground stitching. Confirm all constraints with the fabricator and inspect the ground-plane continuity after fabrication.

The reference is the [Silicon Labs MGM240P datasheet](https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf), Revision 1.0, especially §§7.1–7.2 and Figure 8.3; check for relevant later revisions before production. Connector geometry follows the [JST XH drawing](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf). [NOTICE.md](NOTICE.md) distinguishes the project-authored module footprint from bundled KiCad footprints.

## Reproduce and validate

Run in this directory with KiCad 10.0.6 and its matching `pcbnew` Python module. The module footprint is committed source; no sibling PCB directory is required to regenerate this board.

```sh
python3 generate.py --libraries /path/to/KiCad/SharedSupport
kicad-cli sch export netlist mg24-adapter.kicad_sch --format kicadxml -o .build/mg24-adapter.xml
java -jar /path/to/freerouting-1.9.0.jar -da -dct 0 -de .build/mg24-adapter.dsn -do .build/mg24-adapter.ses -mp 40 -mt 0
python3 finalize.py
python3 -m unittest discover -s . -p 'test_*.py'
python3 validate.py --kicad-cli kicad-cli --out .build/validation
python3 export.py --kicad-cli kicad-cli
python3 validate.py --kicad-cli kicad-cli --check-hashes --out .build/recheck
```

FreeRouting 1.9.0 needs a display (Xvfb for a headless reroute). CI only validates the committed routing, without running the router. Native ERC/DRC, schematic parity, complete physical-pad/NC coverage, all module land coordinates, the independent module pin atlas, C0 cable mapping, ground stitching and antenna keepout are checked. `test_contract.py` also injects swapped UART/flow-control pins, missing ground/NC pads, RFOUT grounding, an incorrect module variant, RESET overvoltage, reversed cable power and wrong BOOT bias. Default metadata-only DRC ignores match the C0 project; no electrical, clearance or unconnected errors are waived.

`outputs/sha256.json` binds the native design, generation/checking scripts, BOM/connector metadata, local footprints and exports. Gerbers use descriptive `.gbr` names, not firmware-like `.gbl` names. Physical SWD flashing, pairing, RF range/coexistence, rail behaviour and extended operation remain untested.
