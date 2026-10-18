# MC1 Nano native carrier

This is the **80 × 90 mm, two-layer MC1 Nano candidate**. It replaces the large S3 DevKit with a factory-pinned **Waveshare ESP32-S3-Nano-M** while retaining H2 Thread RCP, XIAO MG24 Ember NCP, WIZ850io, the existing sensor/radio harnesses and five axial components. Male module pins go directly into carrier plated holes and are soldered underneath: no female sockets, no carrier SMT assembly and no underside flying signal wires. All electronic components are on top.

**Engineering prototype; not a fabrication release.** Clean ERC/DRC establishes modeled connectivity and clearances, not physical fit, supply integrity, RF performance or simultaneous firmware operation. No hardware was ordered, flashed or measured by this change.

Open `mc1.kicad_pro` in KiCad 10. The editable schematic and routed board are `mc1.kicad_sch` and `mc1.kicad_pcb`. `design.py` is the placement/net source; `design.json` includes every pad, module body, service envelope and RF exclusion. `connectors.json` is the harness pin authority. `nano-pin-plan.json` is the reviewed application GPIO contract. Native copper exports are `board-top.svg`/`board-bottom.svg`; `assembly-top.svg` is a scale drawing generated from the same ledger.

## What changed

The previous carrier was 100 × 90 mm (9,000 mm²); this one is 80 × 90 mm (7,200 mm²), **20% less area**. Against the earlier 160 × 100 mm carrier it uses 55% less area. The Nano's body is 17.78 × 43.18 mm, versus the old S3 board's 25.40 × 62.74 mm; carrier area does not shrink by the same ratio because USB, antennas and harnesses still require space.

There are 18 fitted carrier references and 133 physical pads: the host changes from 44 to 30 pins, and **J9**, a two-pin GPIO0 recovery header, is added. The other finished modules retain their pin assignments. W5500 and CC1101 now share `SPI_SCK`, `SPI_MOSI`, `SPI_MISO`, with separate chip selects. No GPIO expander is added. The host uses 21 application GPIO; native USB19/20 remain dedicated to service. H2 UART uses host GPIO43/44, and the RCP is reset before Spinel startup to clear ROM boot chatter.

## Manufacturer geometry and placement

All coordinates are millimetres from carrier top-left. Rotation follows KiCad's component-side convention.

- **U1 Nano-M:** anchor (39,2), 270°. Factory two 1×15 rows, 2.54 pitch and 15.24 row spacing. USB-up local JP1.1=(0,0), JP1.15=(0,35.56), JP2.15=(15.24,0), JP2.1=(15.24,35.56). Body bounds are (−1.27,−3.81)..(16.51,39.37). The manufacturer's 40.64 mm dimension is between corner holes, **not** the 35.56 mm signal-pin span. Antenna faces left; USB faces right. [Dimension/pinout](https://docs.waveshare.com/ESP32-S3-Nano), [schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf).
- **U2 H2-DevKitM-1 N4S:** anchor (78.5,28), 270°. 25.40 × 48.26 mm body, 2.54 pitch, 22.86 row spacing; 5.40 mm antenna extension. Antenna faces right; both USB ports face left. Verify purchased N4S/v1.3 mechanics against the v1.2 drawing. [Official dimensions](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- **U3 XIAO MG24 102010690:** anchor (18,70), 270°. Official native inner header centres give 15.24 row spacing, 2.54 pitch and 17.78 × 20.955 mm body. Antenna faces left; USB faces right. [Seeed CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).
- **U4 WIZ850io:** anchor (76,82.9), 180°. Two 1×6 rows at 20.32 spacing, 2.54 pitch. PCB bounds are x=54.34..77.34,y=64.30..89.30. The RJ45 mouth is **y=92.00**, x=57.79..73.89, facing bottom/outward and projecting 2 mm past the carrier edge. [WIZ dimensions](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png), [top pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png).

Module carrier holes are 1.10 mm finished diameter in 1.80 mm pads (0.35 mm annulus), an engineering allowance for nominal 0.64 mm square pins, not a quoted manufacturer hole specification. Confirm actual pin width, free length, header plastic height, solder access and underside parts using exact modules and a printed 1:1 template before fabrication release.

J1–J9 form two horizontal harness rows between the radio boards. Mating envelopes assume **5.5 mm-wide narrow housings**, 1.75 mm beyond each end pin and vertical wire exit. Generic wider shrouded connectors are not interchangeable. Blue USB envelopes reserve 30 mm for straight plug/insertion access; they are engineering allowances, not guarantees for every plug. Do not route permanent harnesses or leave service pigtails in these envelopes.

Three 2.7 mm NPTH holes at (4,22.1), (50,21.4), (77,60.9) accept nylon M2.5 supports with at most 5 mm head/body diameter. H3 is near WIZ to support insertion loads. The tightest provisions still require sample checks: D1/XIAO courtyard gap ≈0.23 mm, adjacent diode courtyard gaps 0.28 mm, H3/WIZ courtyard gap 0.40 mm, and H1/Nano and H1/H2-USB gaps ≈0.59/0.60 mm. These are model clearances, not manufacturing acceptance measurements. Keep insulation below exposed solder joints.

Antenna ends face outer edges. RF areas prohibit tracks, vias and pours on both copper layers; exact rectangles are in the ledger. H2's full nominal antenna region starts at x80.075 and ends at x85.475, beyond the right carrier edge. The closest carrier pad edge is x79.4, leaving 0.6 mm to the PCB edge. The final enclosure must accommodate that 5.475 mm extension. The Nano/XIAO ceramic ends partly overlap the carrier projection and have explicit edge copper exclusions. The Nano antenna depiction is a placement allowance based on vendor imagery, not a measured RF keepout specification. The XIAO retains the original x0..5/y77..86 no-pour/no-via reservation. A **1.3 × 1.02 mm trace-only pocket** at x2.5..3.8/y84.98..86 lets the existing PC07/RX trace leave pad8. Everywhere else that region also forbids tracks; a regression checks that the pocket contains only the 0.25 mm ZB_RX trace and no via. The [KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf) gives a 5.2 ±0.2 by 2.0 ±0.2 mm body and an evaluation-board example, not an approved XIAO-carrier clearance. The pocket starts 1.08 mm below the nominal ceramic body ending y83.8996; the module's own header/ground geometry is already part of its antenna surroundings. **This is a prototype RF provision, not manufacturer-certified clearance; test the actual complete assembly.** Keep enclosure metal and wire loops away from all antenna ends; these provisions do not replace RF/coexistence testing or the manufacturer's surrounding-space guidance.

## Power and harness boundaries

J1 accepts only fused, isolated, regulated 5 V from an assembled active PoE splitter. No raw PoE or battery voltage enters the carrier. J2 is a harness to the finished D24V22F3 buck: pin1 VIN, pin2 GND, pin3 peripheral 3.3 V output, pin4 GND. Peripheral 3.3 V powers WIZ850io, WK2132, CC1101, ZAC93 and BME680. Never parallel it with a controller board's 3.3 V output.

Three 1N5819 diodes isolate the host, H2 and XIAO input branches. Pad1/cathode/band faces the module; pad2/anode faces the common 5 V bus. **D1 feeds Nano JP1.15 VIN; JP1.12 VBUS and JP1.2 3V3 are NC.** Nano onboard USB D3 also feeds VIN, and the onboard MP2322 supplies local 3.3 V. This input uses the same rail normally powered below 5 V through the USB diode, but is below Waveshare's advertised 6–21 V external-VIN range. Its loaded voltage, brownout margin, ripple and temperature must be measured; the IC's operating range alone is not module qualification. [Nano schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf).

H2 retains its onboard 3.3 V regulator. XIAO retains its local supplies. The branch diodes prevent a USB supply feeding the common 5 V rail; they do not prevent signal-pin backpower. Measure every rail under concurrent Ethernet, Thread, active BLE and peripheral load.

J3 is a **harness**, not the physical DFR0627 footprint: its 3.3 V supply and I2C connect to the finished WK2132 board, IA1=IA0=1 (register address 0x70/FIFO 0x71). Physical UART1 is software channel 0. J3.5 is module TX1→ZAC RX; J3.6 is module RX1←ZAC TX. J4 is the ZAC93 harness; J5 CC1101; J6 LD2450; J7 BME680 at 0x77. Follow `connectors.json`; matching pin counts never imply mechanical plug compatibility.

## Assembly and USB recovery

1. Program and test loose MCU modules before permanently soldering them. Meter carrier polarity, isolation and shorts; fit the five axial parts and headers first. Use a temporary alignment jig for exact factory-pinned modules, then solder from underneath.
2. Bring up the complete assembly with current limiting; verify peripheral 3.3 V before attaching the peripheral modules. Do not hot-plug signal harnesses. Check both radio UARTs, WK2132 registers, WIZ reset, radar frames and BME ID before stress tests.
3. Preserve the whole assembly's normal supply during subsequent USB service and use a **module-specific, bench-verified USB power procedure**. Nano USB power goes through onboard D3 to VIN; carrier D1 isolates its branch. XIAO's SAMD11 probe requires USB VBUS, so a blanket VBUS-blocking adapter fails there. The actual powered-USB arrangements and absence of backfeed must be measured. Do not simply turn off PoE and power one controller while connected peers remain unpowered.
4. J9 is normally open. Short J9.1/GPIO0 to J9.2/GND while using Nano's onboard RESET to enter native USB ROM recovery, then release. J8 similarly exposes XIAO D0/PC00 to GND for its bootloader recovery; it does not replace the USB/SAMD11 independent programmer. No underside test-point wiring is required.
5. H2 EN and GPIO9/BOOT remain host-controlled open-drain signals (GPIO47/48). The H2 intrinsic reset-time GPIO9 pull-up is retained; Nano's GPIO48 also has a weak onboard MOSFET-gate pull-down, so measure BOOT high through reset/hold time. Avoid restarting the host or triggering its initial Ethernet startup reset while programming H2. The host does not automatically update RCP firmware. Never attach simultaneous programmers.

## Reproduce the routed candidate

Use KiCad 10's Python with `pcbnew`, KiCad CLI, and the supplied libraries. `project_rules.py` restores Default 0.25 mm/Power 0.80 mm tracks, 0.20 mm clearance, 0.80/0.40 mm vias and 0.50 mm copper-to-edge minimum after board saves; no DRC severity or exclusion is relaxed.

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

The saved router session plus `manual-route.json` are placement-specific. A new autorouter run is not an identical reproduction and must pass the native gates again. Native PCB/schematic and source hashes are recorded in `verification.json`. The generic module schematic uses passive terminals and cannot model internal board power circuits; clean ERC therefore does not establish safe supplies. The final board has 482 track/via objects. Four selected ground pads use routed 0.8 mm returns with local pour clearance instead of starved thermal islands; WIZ grounds have direct pour connections. No Gerbers or fabrication order are included.
