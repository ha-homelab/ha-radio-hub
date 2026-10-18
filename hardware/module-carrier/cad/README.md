# MC1 Nano — one PCB retainer and enclosure edge support

The two-layer carrier is a **47.5 × 75 mm rectangle**, area **3,562.5 mm²**, with one **H3** retention hole. It is 3.5 mm narrower and 6.86% smaller than the preceding 51 × 75 mm four-hole carrier. Two reserved edge-contact bands let a split printed enclosure support the PCB; H3 retains it in the enclosure. Removing screws alone does not establish adequate support. No lower fabrication price or measured stiffness is claimed.

Three controller modules face the room. WIZ850io, all seven fitted male harness headers and five axial parts face the ceiling. All rear components, including WIZ, are soldered before the front controllers. Factory male pins remain directly soldered into plated holes; there are no sockets or carrier SMT components. H2 R7 removal remains required before assembly.

There are **16 fitted parts, 18 footprint positions, 133 plated signal/power holes and 31 connected nets**. J8/J9 remain unpopulated recovery pads. Native PCB and schematic DNP states match `fitted` in the ledger. The electrical contract and firmware pin map have not changed from the preceding layout.

The [CAD pin manifest](nano-pin-plan.json) and [active firmware manifest](../../../firmware/module-carrier/pin-plan.json) both use H2 **RX23/TX24**. Their parity and the native carrier crossover are checked by the firmware regression suite; H2 preparation and image verification also reject the old RX4/TX5 assignment. The smaller outline does not require a different S3 or H2 application image.

This is an **engineering prototype, not a fabrication release**. Native DRC reports **41 intentional opposite-side PTH/body projections**: 33 rear header pins beneath H2, six axial pins beneath Nano, and two D3 pins beneath XIAO. D2 is clear of front-module bodies. These are retained in the raw report, not suppressed. Exact classification requires zero other violations, zero unrouted items and zero schematic mismatches. **Physical Z clearance is not yet qualified.** Neither a 2D overlap classification nor electrical DRC proves that stock male-header spacers clear the opposing solder joints.

## Files and geometry authority

Open `mc1.kicad_pro` in KiCad 10. `design.py` generates the native board/schematic and `design.json`, including `side`, global body bounds, pad centres, socket shells, mating housings, RF areas and stack requirements. `assembly-top.svg` shows the room-facing front; `assembly-bottom.svg` is a mirrored physical view from the ceiling side. The native copper plots follow the same viewing convention. A dashed WIZ outline on the front drawing shows occupied reverse-side volume.

Coordinates are millimetres from the front-view top-left. Back modules use a **real native KiCad flip**; their canonical local Y is reflected before the listed rotation. Never reuse front-side pad numbering on a back footprint without that reflection.

- U1 **Waveshare ESP32-S3-Nano-M**, front, **(44.57,39), 180°**. Body17.78 ×43.18; rows15.24 apart, pitch2.54. Antenna top, USB down. [Manufacturer dimensions and pinout](https://docs.waveshare.com/ESP32-S3-Nano).
- U2 **ESP32-H2-DevKitM-1-N4S**, front, **(2.57,1.5), 0°**. Body25.40 ×48.26; rows22.86 apart. Antenna nominal y−5.475..−0.075 beyond the top edge. [Manufacturer drawing](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- U3 **Seeed XIAO MG24 102010690**, front, **(1.5,58.3), 0°**. Body17.78 ×20.955; rows15.24 apart. Antenna bottom, USB up. [Manufacturer CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).
- U4 **WIZ850io**, back, **(22.84,67.9), 0° after flip**. PCB x21.5..44.5,y49.3..74.3; opening x24.95..41.05,y77, **2 mm beyond the bottom edge**. [Manufacturer dimensions](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png), [pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png).

Module holes are1.10 mm in1.80 mm pads, giving0.35 mm annulus. This is a fit allowance for nominal0.64 mm square pins, not a manufacturer carrier land pattern. The only 2.7 mm NPTH retention hole is **H3(18,52.03)**. Its identity is preserved; H1/H2/H4 are absent. Use nylon hardware no wider than 5 mm. This screw retains the PCB in a supported enclosure; it is not the sole structural support or a ceiling attachment.

`usb_service_envelopes_mm` is empty. Physical socket projections remain explicitly modelled: Nano2 mm, H2 1 mm, XIAO3 mm beyond their PCB edges. The seven rear harnesses use narrow5.5 mm mating-shell allowances, with vertical wire departure. Generic wide shrouded housings are not interchangeable. Removing USB cable space does not remove the socket bodies or their metal.

## Enclosure edge contacts and routing

The carrier reserves these **contact lands on both faces**:

- Left: **x0–0.85, y15–54.5 mm**.
- Right: **x46.3–47.5, y8–74 mm** (1.2 mm deep).

These are interrupted edge lips in a split enclosure, not a continuous slide-in groove. Load the assembled PCB normally to its plane into an open shell, then close the retaining half. A continuous groove would interfere with the H2/XIAO module edges, antennas, USB shells or their solder tails. Do not extrapolate the lands beyond their stated ends. The left lip starts farther down the H2 edge to keep the case contact away from its antenna; this does not establish full RF qualification of the enclosure.

Native keepouts exclude **tracks, pads, vias and poured copper on both layers** from larger strips: left x0–1.3/y14.7–54.8 and right x46–47.5/y7.7–74.3 mm. This leaves flat, solder-free lands. The nominal part-body clearances to the lips are 0.45 mm left and 0.46 mm right. Nearest pad copper is 0.82/0.83 mm away. Allowing 0.5 mm outward solder growth leaves **0.32/0.33 mm** nominal residual. These are engineering allowances, not measurements of delivered modules, joints or printed plastic. Inspect actual fillets and test the enclosure fit; never grind a sound joint or force the PCB into a tight groove.

The groove opening must use measured PCB thickness and printer-specific clearance. It must not clamp module bodies, exposed pads or pin ends. Do not infer a ready-to-print enclosure height from this 2D carrier. H3 needs access after the PCB is placed; the case-to-ceiling attachment is a separate structural design.

WIZ still attaches through its header pins. An **insulating enclosure cradle/end-stop around the robust jack housing or module body**, plus cable strain relief, should carry insertion force into the enclosure. Do not press on components, the latch opening, antenna areas or solder tails. No stiffness, insertion-force or drop testing has been completed.

The three Nano-side axial parts move left with Nano: D1(40.07,16),250°; R1(33.57,30),10°; R2(33.07,23.5),90°. D2(3,50.8),0° and D3(12.5,65),180° remain. H2 and all seven rear harness headers move right 0.57 mm. J8/J9 are horizontal unpopulated front pads at (29,47)/(37,47),90°. All signal and supply assignments are unchanged.

`routing-metrics.json` compares native saved copper against the preceding four-hole carrier at **c3c8107**. It excludes pours, module-internal wiring and external harnesses. Routed centreline length decreases from **1736.7132 mm to 1612.1049 mm (7.17%)**, while vias increase from **18 to 24**. No straight-line or globally optimal wiring claim is made, and individual nets can become longer.

## Opposite-side assembly and height acceptance

The solder-order test enforces **all rear parts first → all front controllers second**, with a 2 mm tool-access allowance. It rejects an acyclic arrangement if any front part would need soldering before a rear part. Native rear bodies and mating housings leave every front module solder land accessible. Physical socket bodies are also retained in the check. The 2 mm allowance is an engineering tool envelope, not a measured universal soldering-iron requirement.

1. Program and test loose controller boards; prepare H2 R7 as below. Measure the actual module underside-to-carrier gap when its factory plastic is normally seated, and map underside component projections.
2. Fit **all rear parts: WIZ U4, J1–J7 and D1–D3/R1–R2**. Solder from the front, trim and inspect before installing the controller boards. Leave J8/J9 empty.
3. D3 now requires a separate XIAO underside-height check. At **every** overlapping rear solder joint require: **measured front-module gap − local underside component height − highest tail/solder fillet ≥1.0 mm**. An initial trim target is≤1.0 mm including the fillet, **only if a sound PTH joint remains**. With1.0 mm underside protrusion that example requires3.0 mm gap; the factory spacer height is not known and is not asserted to meet it. Do not force almost-flush cuts, omit a proper fillet, float a module above its spacer, or assume a thin insulation sheet fixes the geometry. If samples fail, stop assembly and revise the spacing/layout.
4. Fit the front controllers and solder their rear rows through the clear tool lanes. Trim and inspect their tails. All rear parts are already present; no later WIZ installation is needed. Check all pin tips, bodies and harness plastics on both sides.
5. Set ceiling support height from the **measured tallest assembled rear feature, mated connector and wire bend plus5 mm** allowance. The WIZ catalog18 mm height has an unspecified datum and does not determine the standoff by itself. Maintain RF clearance from ceiling metal and wiring.

The ledger records the gaps as `null` and physical qualification as pending. The41 DRC findings are a precise inventory for this measured acceptance, not a waiver of shorts or workmanship.

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

All antenna exclusions are prototype engineering provisions. H2's nominal antenna lies beyond the carrier; Nano and XIAO ceramic ends partly overlap its projection. The XIAO retains a no-pour/no-via reservation the source-transformed bottom-edge region x8.5..17.5,y71.3..75, with only the existing 0.25 mm ZB_RX trace allowed through x16.48..17.5,y72.5..73.8. Regression tests inspect native copper for that exception. The [Kinghelm KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf) gives an evaluation-board example, not approval for this complete carrier. The rotated XIAO ceramic is about 6.1 mm from the WIZ PCB edge and 9.55 mm from the jack lateral edge. No universal minimum for this complete XIAO carrier was found; this does not establish unchanged RF range. Keep enclosure metal and permanent wires away from antennas and test the assembled ceiling installation.

Follow the staged assembly sequence above. Use current-limited initial power, verify all rails and absence of shorts, and do not hot-plug signal harnesses. Physical USB sockets remain, but there is no supported postassembly cable-insertion corridor.

## Reproduce and validate

Use KiCad 10's Python with `pcbnew`, its CLI and libraries. `project_rules.py` retains 0.20 mm clearance, 0.25 mm signal / 0.80 mm power traces, 0.80/0.40 mm vias and 0.50 mm copper-to-edge minimum. No DRC severity or exclusion is relaxed. `validate_drc.py` preserves the raw report and checks an exact41-pair native UUID/ref/pad/position/side contract; any missing, extra or other finding fails. It also requires connectivity and schematic-parity lists to be present and empty. Native ERC must remain zero.

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

Measure any revision with `"$KICAD_PY" measure_routing.py --board mc1.kicad_pcb --output current-routing.json`. The baseline native board is preserved under `../../../mechanical/module-carrier/rail-mount/baseline/`.

The committed router session plus explicit manual centerlines are specific to this placement. Clean reproduction and native check counts/hashes are recorded in `checks/reproduction.json` and `verification.json`. Generic passive-terminal module symbols do not model internal regulators or establish electrical safety. No Gerbers or hardware order are included.
