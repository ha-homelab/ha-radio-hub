# MC1 native KiCad carrier

MC1 is one 160 × 100 mm, two-layer carrier for the retained ESP32-S3 host, ESP32-H2 Thread RCP, XIAO MG24 Ember NCP and WIZ850io. The finished modules' factory male pins pass directly through plated holes and are soldered underneath. There are **no female sockets and no carrier SMT parts**. Eight ordinary THT headers serve external finished modules, peripheral harnesses and the XIAO boot service connection. Three axial Schottky diodes and two axial resistors are the only loose electronic components on MC1.

**Status: engineering prototype, not a fabrication release.** Native connectivity and rule checking do not establish firmware interoperability, EMC performance, module fit or thermal safety. Do not buy a clone with a different pinout or module voltage. The exact population is S3 DevKitC-1 **v1.1 N8R8**, H2 DevKitM-1 **N4S**, XIAO MG24 pre-soldered **102010690**, and WIZ850io.

Open `mc1.kicad_pro` in KiCad 10. `mc1.kicad_sch` is the complete editable schematic and `mc1.kicad_pcb` is the editable routed PCB. `assembly-top.svg` is a scaled placement diagram generated from the same `design.json` pad ledger. Native copper SVGs show actual routes. `BOM.csv` lists fitted carrier items; the system's external splitter, buck, WK2132 and sensor modules are additional purchases.

## Physical evidence and remaining fit checks

The custom module footprints are carrier hole patterns, not SMT footprints copied from modules. All coordinates use the manufacturer component-side view. Espressif left/right physical rows remain `J1`/`J3`; WIZ rows remain `J1`/`J2`. XIAO follows D0=pad1 through D6=pad7, D7=pad8 through VIN=pad14. Rotation in `design.json` gives actual carrier coordinates.

- **S3 v1.1:** official dimension PDF gives a 25.40 × 62.74 mm board, 2.54 mm pin pitch and 22.86 mm between the 22-pin rows. First-hole offset from PCB top is 1.40 mm, derived from the 8.00 mm last-hole-to-bottom dimension. [Espressif drawing](https://dl.espressif.com/dl/schematics/esp_idf/DXF_ESP32-S3-DevKitC-1_V1.1_20220429.pdf).
- **H2:** official v1.2 mechanical drawing gives 25.40 × 48.26 mm, 15 pins per row at 2.54 mm pitch and 22.86 mm row separation. First hole is 1.575 mm below board top, from the 11.125 mm last-hole-to-bottom dimension. Antenna extension is 5.40 mm. Confirm the purchased N4S/v1.3 board retains this mechanical layout. [Espressif drawing](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- **XIAO MG24:** the manufacturer's native 260114 KiCad board contains the actual inner header hole centers: 2.54 mm pitch, 15.24 mm row separation and a 17.78 × 20.955 mm PCB outline. Carrier holes use those inner pin positions, not the castellated edge holes. [Seeed native CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).
- **WIZ850io:** WIZnet drawing and top-view pin map establish two 1×6 rows, 2.54 mm pitch, 20.32 mm separation, 23 × 25 mm PCB and 6.40 mm first-hole offset. The jack projects an additional 2.70 mm. [Dimensions](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png), [pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png).

The four module footprints use **1.10 mm finished PTH holes and 1.90 mm pads** as an engineering allowance for nominal 0.64 mm square pins; that drill size is a carrier choice, not a quoted manufacturer recommendation. Print a 1:1 drill/template view and physically fit the exact purchased boards before releasing Gerbers. Check male-pin free length, underside parts, USB plug shells and cable bend clearances. Maintain insulation/support below exposed solder joints. The 160 × 100 mm legacy outline does not prove any existing enclosure fits the taller assembled modules.

RF keepouts are explicit no-track/no-via/no-pour rule areas on both copper layers. S3 and H2 face the top edge. The XIAO is rotated 180° and its antenna end sits at the edge: the ceramic body spans approximately x=129.10..134.30 mm, y=−0.034..1.966 mm, so it is **not wholly outside the carrier**. The keepout x=128.8..141 mm, y=0..5 mm covers the ceramic body over the carrier while avoiding the left header row. This geometry is independently checked against the manufacturer's native board, but the added-carrier RF performance still requires measurement. No metal enclosure or ground plane should be added above/below these antenna ends.

## Harness and power rules

`connectors.json` is the pin-by-pin authority. J2/J3/J4/J5 are **carrier harness definitions**, not footprints that accept the associated module directly. Route each labeled wire to the finished module's actual named pad; never align those modules by the carrier header's pin count.

J1 accepts **fused, isolated, regulated 5 V DC** from an assembled active PoE splitter. Raw PoE, passive-PoE voltage and battery voltage never enter MC1. The splitter and its Ethernet-data connection to WIZ850io are external. J2 connects an assembled D24V22F3: VIN=J2.1, GND=J2.2/4, VOUT=J2.3. The external buck's 3.3 V powers WIZ850io, WK2132, CC1101, ZAC93 and the BME pod. Each MCU module instead receives its own diode-isolated 5 V branch and uses its own LDO; the MCU 3.3 V output pins are deliberately NC.

D1/D2/D3 are 1N5819 with cathode/band toward their MCU's 5 V rail (pad1), anode toward the common fused 5 V (pad2). Official S3 v1.1 and H2 v1.3 schematics use SGM2212-3.3 LDOs and already diode-isolate USB VBUS from their header 5 V net. MC1's additional diodes block a USB-powered module from driving the common 5 V bus. They do **not** prevent backpower through UART/SPI/I²C pins. [S3 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf), [H2 schematic](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.3_schematics.pdf).

The SGM2212 fixed 3.3 V variant lists up to 610 mV dropout at 800 mA over temperature. The input headroom calculation must also include actual diode drop, splitter tolerance, cable loss and PCB loss; LDO dissipation rises with load. Measure all 5 V/3.3 V rails and module temperature during concurrent Ethernet, active BLE and Thread traffic before considering the supply proven. [SGMICRO datasheet](https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf).

J3 supplies DFR0627 at 3.3 V; IA1=1 and IA0=1 select registers 0x70 and FIFO 0x71. Its physical UART1 is software channel0. TX1 goes to J3.5/ZAC93 RX; RX1 goes to J3.6/ZAC93 TX. The BME680 is at 0x77. Use the module-carrier firmware profile and its bounded WK2132 adapter. This is not a pin-compatible SC16 replacement.

## Assembly and service

1. Program and verify each loose MCU board before soldering it permanently to MC1. Inspect the carrier for shorts; meter J1 polarity, 5 V branches, independent peripheral 3.3 V and ground continuity with power off.
2. Fit the three diodes and two resistors, then headers. Fit exact factory-pinned modules component side up, using a temporary alignment jig. Solder opposite corners first, confirm alignment and level, then complete the pins. No sockets are fitted. Finish with external harnesses, insulation and strain relief.
3. Bring up with current limiting and no signal-peripheral hot plugging. Verify buck output before connecting the 3.3 V modules. Confirm both RCP/NCP UART directions, WK register reads, WIZ reset, radar frames and BME ID before network stress tests.
4. For subsequent USB service keep the **whole assembly normally powered by PoE**, and use a separately verified **VBUS-blocking USB data cable/adapter**. Do not use an ordinary USB cable in parallel. Do not simply remove PoE and power one MCU from USB while the others remain connected: signal lines can backpower the unpowered boards. Verify USB enumeration with the blocker on the real board.
5. J8 is normally open. For local XIAO boot recovery only, temporarily short J8.1/D0/PC00 to J8.2/GND while applying the XIAO reset procedure, then remove the short. No automatic S3-driven XIAO reset is implied. H2 EN/GPIO9 are retained reset/boot controls. The compiled host component drives both as open-drain, releasing high; its startup asserts reset for 10 ms and then releases it. It does not update H2 firmware. Avoid S3 restart or first Ethernet connection during H2 service because host startup issues that reset pulse. Never use simultaneous programmers.

## Reproduction and evidence

`generate.py` uses KiCad's bundled `pcbnew` Python and the KiCad libraries path. It creates `.build/mc1-unrouted.kicad_pcb`, `.build/mc1.dsn`, editable schematic, local libraries, BOM and pad ledger. Export the schematic XML before finalization. Route the DSN locally, then run `finalize.py` to import the SES, restore native net names/NC terminal metadata, add ground pours and save `mc1.kicad_pcb`. Run `test_design.py`, native ERC and native PCB DRC with `--schematic-parity`; `verification.json` records exact results and limitations. `render_assembly.py` generates the scaled SVG from the ledger.

The committed board is the reviewable routed candidate. Do not regenerate it blindly and assume a new autorouter run is identical. Keep the native final PCB as the authority for actual routes. No Gerbers or fabrication order are issued by this package.

Run from this directory, substituting the paths to your installed KiCad and FreeRouting binaries. `KICAD_PY` must be KiCad's Python with `pcbnew`, not an unrelated system Python.

```sh
"$KICAD_PY" generate.py --libraries "$KICAD_LIBRARIES"
"$KICAD_CLI" sch export netlist --format kicadxml -o .build/mc1.xml mc1.kicad_sch
java -jar "$FREEROUTING_JAR" -da -dct 0 -de .build/mc1.dsn -do .build/mc1.ses -mp 100 -mt 0
"$KICAD_PY" finalize.py
"$KICAD_PY" apply_manual_route.py
python3 test_design.py
python3 render_assembly.py
"$KICAD_CLI" sch erc --format json --output .build/erc.json mc1.kicad_sch
"$KICAD_CLI" pcb drc --format json --output .build/drc.json --schematic-parity mc1.kicad_pcb
```

FreeRouting may leave a route unfinished. A zero-unrouted native DRC result is required; the autorouter's successful exit alone is insufficient. Do not replace the committed routed candidate until the new result passes all checks. The module-level schematic uses passive terminal types and cannot validate power behavior inside the assembled boards; the power and service gates above remain required even when ERC is clean.

The final route includes an explicitly finished `/ZB_RX` centerline in `manual-route.json`. `apply_manual_route.py` applies it once and rejects duplicates. To reproduce the checked candidate rather than run a new search, copy `routing/mc1.ses` to `.build/mc1.ses` after generation, run `finalize.py`, then `apply_manual_route.py`. A new router result may already route that net or occupy the saved centerline; in that case do not apply it blindly. DRC is the release gate.
