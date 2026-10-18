# MC2-A external-antenna carrier

MC2 is a **100 × 100 mm, two-layer, all-through-hole engineering prototype**. All 17 fitted components face the room; two additional recovery footprints are unpopulated. There are no controller bodies above another component's solder tails and no carrier RF traces. Three independent factory RF connectors feed three external 2.4 GHz antennas through 50 Ω coax. This is not a fabrication release or a claim of measured coverage.

## Exact controller boards

- **U1: Espressif ESP32-S3-DevKitC-1U-N8R8**, 8 MB flash / 8 MB octal PSRAM. Buy the **1U** external-antenna version. It has **44 pins, two rows of 22**, 2.54 mm pitch and 22.86 mm row spacing. The [official dimension drawing](https://dl.espressif.com/dl/schematics/esp_idf/DXF_ESP32-S3-DevKitC-1_V1.1_20220429.pdf) specifies a 25.40 × 62.74 mm PCB and 8.00 mm from the last header row to the lower board edge; the resulting first-row offset is 1.40 mm. Micro-USB socket bodies extend beyond that PCB. Header facts and reserved GPIOs come from the [official user guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html).
- **U2: Unexpected Maker TinyC6-U-01**, the original fixed-U.FL version, 8 MB flash. Its native USB does not add a competing UART bridge. **Do not substitute TinyC6[D]**, which has different RF selection hardware. The supplied **1×11 and 1×12 male headers must be soldered to the finished module** before carrier assembly. This is ordinary through-hole work; no RF rework is needed. The carrier's independently generated footprint transcribes pad coordinates and body bounds from [manufacturer CAD revision 7c313796](https://github.com/UnexpectedMaker/esp32c6/tree/7c3137962e469be55a295d0eb7ccebed2a6354d1/TinyC6). These reference files are not redistributed here. On 2026-10-18, [Mouser 392-TC6-U-01](https://www.mouser.com/ProductDetail/Unexpected-Maker/TC6-U-01?qs=Z%252BL2brAPG1IKH7BFgNUR0g%3D%3D) listed zero stock and accepted backorders with an estimated two-week factory lead time. Confirm availability before buying the PCB; this is not a shipping promise.
- **U3: Seeed XIAO MG24, presoldered 102010690**. The module's U.FL RF path must be selected by the matching firmware: PB04 and PB05 high. A connected antenna alone does not switch the RF path. [Manufacturer board source](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).

All three use **U.FL / MHF1** mating coax, not MHF3 or MHF4. SMA bulkheads and antennas are offboard mechanical parts; their exact connector/gain/cable choices are in the [RF BOM](../rf-bom.json). No antenna is shared between radios.

## Electrical changes and connections

`pin-plan.json` is the S3 firmware contract. Host Thread TX/RX moves to **GPIO15 / GPIO16**, reset remains GPIO47, boot moves to GPIO39; radar RX moves to GPIO40. GPIO43/44 remains dedicated to the factory USB-UART bridge. Both GPIO38 and GPIO48 are left unused because Espressif moved its RGB LED between these pins across board revisions. GPIO35/36/37 remains reserved for octal PSRAM.

TinyC6 carrier pad12 is GPIO17/ROM RX, pad13 is GPIO16/ROM TX, pad15 is EN/RESET, pad11 is GPIO9/BOOT, pad3 is 5 V, and pads2/14 are GND. Thus host TX15 reaches C6 RX17, and C6 TX16 reaches host RX16. The original H2 bridge-resistor removal is not applicable. **R3 (10 kΩ) is required** from TinyC6 local3V3 (pad4) to GPIO8 (pad10): the C6 ROM downloader requires GPIO8 high together with GPIO9 low. The TinyC6 schematic leaves GPIO8 without a board pull-up; its C6-local rail must not be joined to the peripheral 3.3 V rail. Inspect the tiny board's printed labels before insertion; left and right row lengths differ.

The remaining external harnesses preserve MC1's function: J1 isolated/fused 5 V input; J2 offboard D24V22F3 buck; J3 DFR0627 UART expander; J4 ZAC93; J5 CC1101; J6 LD2450; J7 BME680. [Connectors and exact pad coordinates](connectors.json) and [net membership](../wiring.json) are generated from the same `design.py` as the native schematic and PCB. J8 is XIAO PC00-to-GND recovery; J9 is S3 GPIO0-to-GND recovery. Leave both unpopulated/open in operation.

The existing network PoE switch feeds an **active, isolated, regulated 5 V splitter** upstream of J1. Neither battery voltage nor raw PoE enters this board. J2 connects an external 3.3 V buck only to WIZ850io and peripheral harnesses. Controller 3.3 V outputs are **not joined** to that rail. Each controller receives 5 V through a separate 1N5819: cathode/banded pad1 toward the controller, anode pad2 toward the common 5 V input. Measure rail voltage at maximum simultaneous load: splitter/cable/diode losses must leave adequate local-regulator headroom. Diodes do not prevent signal-pin backpower. Use one intended power source while programming, and power down before connecting harnesses.

## Mechanical contract

`design.json` is the geometry authority. Four 2.7 mm NPTH holes are at (4,4), (96,4), (4,96), (96,96) mm, front-view origin at the top left. Use insulating M2.5 supports no wider than 5 mm at the PCB. The WIZ850io front-facing footprint is rotated180°: its RJ45 mouth is at y102 mm, x62.45–78.55 mm, 2 mm beyond the carrier. Support its jack with the enclosure cradle so cable insertion force does not rely on header joints.

The ledger retains physical USB shells, short USB service approaches and harness-mating envelopes. The three RF socket points are **explicitly labelled planning estimates**, not exact manufacturer coordinates; use sufficient pigtail slack and verify engagement, bend radius and strain relief with delivered boards. Never press a mismatched miniature coax connector into place. Carrier fit, connector height, printer tolerances and simultaneous-radio performance remain unmeasured. [MC2 enclosure](../../../mechanical/module-carrier/external-antenna-prototype/README.md).

## Checks and reproduction

Native ERC, DRC, unrouted items and schematic parity must all be **zero**; there are no intentional warning/overlap exemptions. The carrier has 33 connected nets. `test_design.py` also checks controller pin numbers, reserved GPIOs, supply separation and all module body/pad projections. Passive module symbols model connections, not the boards' internal power circuits.

Run with KiCad10's Python and libraries. Keep environment variables local to the task:

```sh
"$KICAD_PY" generate.py --libraries "$KICAD_LIBRARIES"
"$KICAD_CLI" sch export netlist --format kicadxml -o .build/mc2.xml mc2.kicad_sch
cp routing/mc2.ses .build/mc2.ses
"$KICAD_PY" finalize.py
"$KICAD_CLI" sch erc --severity-all --exit-code-violations --format json --output checks/erc.json mc2.kicad_sch
"$KICAD_CLI" pcb drc --severity-all --exit-code-violations --format json --schematic-parity --output checks/drc.json mc2.kicad_pcb
"$KICAD_PY" record_verification.py
python3 test_design.py
python3 render_assembly.py
python3 reproduce_check.py --python "$KICAD_PY" --cli "$KICAD_CLI" --libraries "$KICAD_LIBRARIES"
```

The checked-in Specctra session was routed with Freerouting1.9.0, one optimization thread. It includes every connection, including the required C6 boot pull-up. Import it with `finalize.py`, which also refills ground. Track/via dimensions and clearance are unchanged from MC1: 0.25 mm signal, 0.80 mm power, 0.80/0.40 mm vias, 0.20 mm clearance and 0.50 mm copper-to-edge minimum. No production manufacturing release is claimed. The native KiCad board can be used for a small prototype after the BOM, power and assembly review; physical qualification then gates a larger run.
