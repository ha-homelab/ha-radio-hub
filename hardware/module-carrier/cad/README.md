# MC1 Nano — two-sided 51 × 75 mm carrier

The carrier is **51 × 75 mm, two copper layers**: 3,825 mm², **21.54% smaller** than the preceding 65 × 75 mm single-sided layout. The three controller modules face the room. WIZ850io, all seven fitted male harness headers and the five axial parts face the ceiling. All module pins are factory male pins directly soldered into plated holes; there are no sockets or carrier SMT components. The existing H2 R7 removal prerequisite remains.

There are **16 fitted parts, 18 footprint positions, 133 plated signal/power holes and 31 connected nets**. J8/J9 remain unpopulated recovery pads. Native PCB and schematic DNP states match `fitted` in the ledger. The electrical contract and firmware pin map have not changed from the preceding layout.

This is an **engineering prototype, not a fabrication release**. Native DRC reports **43 intentional opposite-side PTH/body projections**: 33 rear header pins beneath H2 and 10 rear axial pins beneath Nano. These are retained in the raw report, not suppressed. Exact classification requires zero other violations, zero unrouted items and zero schematic mismatches. **Physical Z clearance is not yet qualified.** Neither a 2D overlap classification nor electrical DRC proves that stock male-header spacers clear the opposing solder joints.

## Files and geometry authority

Open `mc1.kicad_pro` in KiCad 10. `design.py` generates the native board/schematic and `design.json`, including `side`, global body bounds, pad centres, socket shells, mating housings, RF areas and stack requirements. `assembly-top.svg` shows the room-facing front; `assembly-bottom.svg` is a mirrored physical view from the ceiling side. The native copper plots follow the same viewing convention. A dashed WIZ outline on the front drawing shows occupied reverse-side volume.

Coordinates are millimetres from the front-view top-left. Back modules use a **real native KiCad flip**; their canonical local Y is reflected before the listed rotation. Never reuse front-side pad numbering on a back footprint without that reflection.

- U1 **Waveshare ESP32-S3-Nano-M**, front, **(49.5,39), 180°**. Body17.78 ×43.18; rows15.24 apart, pitch2.54. Antenna top, USB down. [Manufacturer dimensions and pinout](https://docs.waveshare.com/ESP32-S3-Nano).
- U2 **ESP32-H2-DevKitM-1-N4S**, front, **(2,1.5), 0°**. Body25.40 ×48.26; rows22.86 apart. Antenna nominal y−5.475..−0.075 beyond the top edge. [Manufacturer drawing](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- U3 **Seeed XIAO MG24 102010690**, front, **(18,57.5), 270°**. Body17.78 ×20.955; rows15.24 apart. Antenna left, USB right. [Manufacturer CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).
- U4 **WIZ850io**, back, **(28.84,67.9), 0° after flip**. PCB x27.5..50.5,y49.3..74.3; opening x30.95..47.05,y77, **2 mm beyond the bottom edge**. [Manufacturer dimensions](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png), [pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png).

Module holes are1.10 mm in1.80 mm pads, giving0.35 mm annulus. This is a fit allowance for nominal0.64 mm square pins, not a manufacturer carrier land pattern. Three2.7 mm NPTH supports are at **(29.5,8), (29.5,44), (24.2,57.5)**; use nylon hardware no wider than5 mm and verify enclosure support under Ethernet insertion load.

`usb_service_envelopes_mm` is empty. Physical socket projections remain explicitly modelled: Nano2 mm, H2 1 mm, XIAO3 mm beyond their PCB edges. The seven rear harnesses use narrow5.5 mm mating-shell allowances, with vertical wire departure. Generic wide shrouded housings are not interchangeable. Removing USB cable space does not remove the socket bodies or their metal.

## Opposite-side assembly and height acceptance

The solder-order graph is acyclic, using a2 mm tool-access halo: **rear headers/axials → front controllers → rear WIZ**. WIZ is below Nano rather than directly beneath a controller pin field, so its front-side solder lands remain accessible last.

1. Program and test loose controller boards; prepare H2 R7 as below. Measure the actual module underside-to-carrier gap when its factory plastic is normally seated, and map underside component projections.
2. Fit rear J1–J7 and D1–D3/R1–R2. Solder from the front, trim and inspect before installing the controller boards. Leave J8/J9 empty.
3. At **every** overlapping rear solder joint require: **measured front-module gap − local underside component height − highest tail/solder fillet ≥1.0 mm**. An initial trim target is≤1.0 mm including the fillet, **only if a sound PTH joint remains**. With1.0 mm underside protrusion that example requires3.0 mm gap; the factory spacer height is not known and is not asserted to meet it. Do not force almost-flush cuts, omit a proper fillet, float a module above its spacer, or assume a thin insulation sheet fixes the geometry. If samples fail, stop assembly and revise the spacing/layout.
4. Fit the front controllers and solder their rear rows through the clear tool lanes. Trim and inspect their tails. Fit rear WIZ last; its front solder lands are unobstructed. Check all pin tips, bodies and harness plastics on both sides.
5. Set ceiling support height from the **measured tallest assembled rear feature, mated connector and wire bend plus5 mm** allowance. The WIZ catalog18 mm height has an unspecified datum and does not determine the standoff by itself. Maintain RF clearance from ceiling metal and wiring.

The ledger records the gaps as `null` and physical qualification as pending. The43 DRC findings are a precise inventory for this measured acceptance, not a waiver of shorts or workmanship.

## H2 preparation and network maintenance

The host remains GPIO43 TX / GPIO44 RX, but the H2 end changes from application GPIO4/5 to its ROM UART: **J3.3 / GPIO23 RX** and **J3.2 / GPIO24 TX**. H2 EN and BOOT remain host GPIO47/48 open-drain controls. Host firmware, RCP firmware and the carrier must all use this new mapping.

On the official v1.3 schematic, the onboard CP2102N TXD reaches H2 RX through **R7, 470 Ω**. The bridge's VDD and REGIN remain powered from VCC_3V3 even when no USB cable is attached. Consequently, unplugging USB does not provide electrical isolation. J5 disconnects the H2 module supply for current measurement; it is not a bridge-disable jumper.

Before permanent assembly:

1. Identify the exact H2 board revision and compare its schematic. The manufacturer documents the 470 Ω R7 change for boards at/after PW-2024-02-0362. Earlier boards require checking their corresponding schematic.
2. With all power disconnected, identify the **TX-series R7** by reference and continuity between CP2102N TXD and H2 GPIO23. Remove only that resistor and verify the path is open. Do not short the pads, substitute a different resistor or remove R9, the bridge's receive path.
3. Use the **native H2 USB Serial/JTAG port** to program and test the new GPIO23/24 RCP while the module is loose. Its USB-UART connector can no longer program H2 after R7 removal. Verify host-controlled ROM entry and network flashing before the modules are soldered into the carrier.

See the [official v1.3 schematic](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.3_schematics.pdf), [revision guidance](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html#hardware-revision-details), and [published v1.2 board layout](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_pcb_layout.pdf). The older layout is a locating aid, **not proof of a v1.3 component position**. The new diagram shows electrical topology only.

J8 exposes XIAO PC00/BOOT to GND and J9 exposes Nano GPIO0 to GND as unpopulated pads. They are fallback electrical access points, not a guarantee that a USB cable can be inserted after assembly. No blanket promise of recovery from every corrupted bootloader is made. Follow the separate firmware maintenance procedure; a failed host or corrupted recovery firmware may require removing the assembly for repair.

## Power, RF and assembly boundaries

J1 receives fused, isolated, regulated 5 V from a finished active PoE splitter. No raw PoE or battery voltage enters the carrier. J2 connects the separate D24V22F3 buck: pin1 VIN, pin2 GND, pin3 peripheral 3.3 V output, pin4 GND. Never join that 3.3 V output to any controller's local regulator output.

D1 feeds Nano JP1.15 VIN; JP1.12 VBUS and JP1.2 3V3 remain NC. D2 and D3 feed the H2 and XIAO branches. Diode pad1/cathode/band faces the module; pad2/anode faces common 5 V. Nano's onboard USB diode also feeds VIN. The selected input is below the vendor's advertised 6–21 V external-VIN range although its own USB powers the same rail below 5 V; measure loaded voltage, ripple, temperature and brownout margin. The diodes prevent supply backfeed between branches but do not prevent I/O-pin backpower.

J3 is a harness to the separate DFR0627 WK2132 module, not its footprint. IA1=IA0=1 gives register address0x70/FIFO0x71; physical UART1 is software channel0. J4 is ZAC93, J5 CC1101, J6 LD2450 and J7 BME680. Exact pin assignments are in `connectors.json`.

All antenna exclusions are prototype engineering provisions. H2's nominal antenna lies beyond the carrier; Nano and XIAO ceramic ends partly overlap its projection. The XIAO retains a no-pour/no-via reservation x0..5,y64.5..73.5, with only the existing 0.25 mm ZB_RX trace allowed through x2.5..3.8,y72.48..73.5. Regression tests inspect native copper for that exception. The [Kinghelm KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf) gives an evaluation-board example, not approval for this complete carrier. Keep enclosure metal and permanent wires away from antennas and test the assembled ceiling installation.

Follow the staged assembly sequence above. Use current-limited initial power, verify all rails and absence of shorts, and do not hot-plug signal harnesses. Physical USB sockets remain, but there is no supported postassembly cable-insertion corridor.

## Reproduce and validate

Use KiCad 10's Python with `pcbnew`, its CLI and libraries. `project_rules.py` retains 0.20 mm clearance, 0.25 mm signal / 0.80 mm power traces, 0.80/0.40 mm vias and 0.50 mm copper-to-edge minimum. No DRC severity or exclusion is relaxed. `validate_drc.py` preserves the raw report and checks an exact43-pair native UUID/ref/pad/position/side contract; any missing, extra or other finding fails. It also requires connectivity and schematic-parity lists to be present and empty. Native ERC must remain zero.

```sh
"$KICAD_PY" generate.py --libraries "$KICAD_LIBRARIES"
"$KICAD_CLI" sch export netlist --format kicadxml -o .build/mc1.xml mc1.kicad_sch
cp routing/mc1.ses .build/mc1.ses
"$KICAD_PY" finalize.py
"$KICAD_PY" apply_manual_route.py
python3 render_assembly.py
"$KICAD_CLI" sch erc --format json --output checks/erc.json mc1.kicad_sch
python3 validate_drc.py --cli "$KICAD_CLI"
python3 test_design.py
"$KICAD_CLI" pcb export svg --layers F.Cu,F.SilkS,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --output board-top.svg mc1.kicad_pcb
"$KICAD_CLI" pcb export svg --layers B.Cu,B.SilkS,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --mirror --output board-bottom.svg mc1.kicad_pcb
"$KICAD_CLI" sch export svg --output .build/schematic-export mc1.kicad_sch
cp .build/schematic-export/mc1.svg schematic.svg
"$KICAD_CLI" sch export pdf --output schematic.pdf mc1.kicad_sch
python3 record_verification.py
python3 reproduce_check.py --python "$KICAD_PY" --cli "$KICAD_CLI" --libraries "$KICAD_LIBRARIES"
```

The committed router session plus explicit manual centerlines are specific to this placement. Clean reproduction and native check counts/hashes are recorded in `checks/reproduction.json` and `verification.json`. Generic passive-terminal module symbols do not model internal regulators or establish electrical safety. No Gerbers or hardware order are included.
