# MC1 Nano — network-maintained compact carrier

The active carrier is **65 × 75 mm, two copper layers**: 4,875 mm², **32.3% smaller** than the previous 80 × 90 mm USB-service layout. Four finished modules retain their physical USB sockets, but the carrier reserves **no space for inserted USB plugs or cables**. Program and test the modules before soldering; subsequent maintenance uses the host/network paths described in the firmware documentation.

There are **16 fitted parts, 18 footprint positions and 133 plated signal/power holes**: four modules, seven harness headers, three axial diodes and two axial resistors. J8 and J9 are unpopulated recovery pads, not installed headers. Every part has a `fitted` flag in `design.json`; the native board and schematic mark these two footprints DNP. Factory male module pins go directly into plated carrier holes and are soldered underneath. No sockets, carrier SMT assembly or underside flying wires are used. **The H2 module does require removal of its existing SMD resistor R7 before installation.**

This remains an **engineering prototype, not a fabrication release**. Native ERC/DRC and the regression suite verify modeled geometry and connectivity. Actual module fit, power integrity, radio coexistence and reliable network updates still need bench qualification.

## Files and authority

Open `mc1.kicad_pro` in KiCad 10. `mc1.kicad_pcb` and `mc1.kicad_sch` are editable native documents. `design.py` is the placement/net source; `design.json` includes pads, bodies, physical USB shells, mating housings and RF exclusions. `connectors.json` is the pin authority; `nano-pin-plan.json` records the host GPIO map. `assembly-top.svg`/PNG shows the actual placement; `board-top.svg` and mirrored `board-bottom.svg` are native copper plots. `h2-uart-isolation.svg` explains the required H2 modification without pretending to show an exact component location.

## Geometry

Coordinates are millimetres from the carrier's top-left; rotations follow KiCad's component-side convention.

- U1, **Waveshare ESP32-S3-Nano-M**, is at **(62.5,39), 180°**. Its 17.78 × 43.18 mm PCB has two factory 1×15 rows, 2.54 mm pitch and 15.24 mm row spacing. The pin span is 35.56 mm; 40.64 mm in the vendor drawing is the corner-hole span. Antenna faces top; USB faces bottom. [Manufacturer dimensions and pinout](https://docs.waveshare.com/ESP32-S3-Nano).
- U2, **ESP32-H2-DevKitM-1-N4S**, is at **(2,1.5), 0°**. Its 25.40 × 48.26 mm PCB uses 22.86 mm row spacing. The nominal antenna spans y=−5.475..−0.075, fully beyond the top edge; the first pad copper starts at y=0.6. Verify the exact purchased revision and mechanical tolerance. [Manufacturer dimensions](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- U3, **Seeed XIAO MG24 102010690**, is at **(18,57.5), 270°**, antenna left and USB right. Native CAD gives a 17.78 × 20.955 mm PCB, 15.24 mm row spacing and 2.54 mm pitch. [Manufacturer CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).
- U4, **WIZ850io**, is at **(61,67.9), 180°**. PCB bounds are x=39.34..62.34, y=49.30..74.30. The RJ45 opening is x=42.79..58.89, y=77, facing outward **2 mm beyond the bottom edge**. [Manufacturer dimensions](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png), [pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png).

Module pads retain 1.10 mm finished holes in 1.80 mm pads, a 0.35 mm annulus. This is a fit allowance for nominal 0.64 mm square pins, not a quoted vendor land pattern. Confirm actual pins, header plastic, underside parts and solder access before fabrication release.

`usb_service_envelopes_mm` is deliberately empty. The distinct `physical_usb_shells_mm` field retains conservative projections beyond the PCB: Nano 2 mm, H2 1 mm, XIAO 3 mm. The Nano shell-to-R2 courtyard gap is about 0.49 mm and XIAO shell-to-D1 gap about 0.48 mm. These margins require exact sample checks; removing cable access does not permit overlapping socket bodies.

J1–J7 occupy the central aisle. Their mating envelopes assume narrow 5.5 mm housings, 1.75 mm beyond each end pin, with wires leaving vertically. Wider shrouded connectors are not interchangeable. Three 2.7 mm NPTH holes at **(35,6), (24,51.8), (34,72)** accept nylon M2.5 supports with no more than 5 mm body/head diameter. H3 is left of WIZ; check enclosure support under Ethernet insertion loads and insulation beneath solder joints.

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

Fit the five axial components and seven headers first, leave J8/J9 empty, then align and solder the previously programmed modules. Use current-limited initial power, verify rail voltages and shorts, and do not hot-plug signal harnesses. USB sockets remain present but there is no supported postassembly insertion corridor.

## Reproduce and validate

Use KiCad 10's Python with `pcbnew`, its CLI and libraries. `project_rules.py` retains 0.20 mm clearance, 0.25 mm signal / 0.80 mm power traces, 0.80/0.40 mm vias and 0.50 mm copper-to-edge minimum. No DRC severity or exclusion is relaxed.

```sh
"$KICAD_PY" generate.py --libraries "$KICAD_LIBRARIES"
"$KICAD_CLI" sch export netlist --format kicadxml -o .build/mc1.xml mc1.kicad_sch
cp routing/mc1.ses .build/mc1.ses
"$KICAD_PY" finalize.py
"$KICAD_PY" apply_manual_route.py
python3 test_design.py
python3 render_assembly.py
"$KICAD_CLI" sch erc --format json --output checks/erc.json mc1.kicad_sch
"$KICAD_CLI" pcb drc --format json --output checks/drc.json --schematic-parity mc1.kicad_pcb
"$KICAD_CLI" pcb export svg --layers F.Cu,F.SilkS,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --output board-top.svg mc1.kicad_pcb
"$KICAD_CLI" pcb export svg --layers B.Cu,B.SilkS,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --mirror --output board-bottom.svg mc1.kicad_pcb
"$KICAD_CLI" sch export svg --output .build/schematic-export mc1.kicad_sch
cp .build/schematic-export/mc1.svg schematic.svg
"$KICAD_CLI" sch export pdf --output schematic.pdf mc1.kicad_sch
python3 record_verification.py
python3 reproduce_check.py --python "$KICAD_PY" --cli "$KICAD_CLI" --libraries "$KICAD_LIBRARIES"
```

The committed router session plus explicit manual centerlines are specific to this placement. Clean reproduction and native check counts/hashes are recorded in `checks/reproduction.json` and `verification.json`. Generic passive-terminal module symbols do not model internal regulators or establish electrical safety. No Gerbers or hardware order are included.
