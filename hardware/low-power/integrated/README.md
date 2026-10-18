# LP-I0 integrated radio hub PCB

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](../../../docs/module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

LP-I0 is an **engineering prototype, not a fabrication release or a qualified product**. It combines the ESP32-S3-WROOM-1-N16R8 host, ESP32-H2-MINI-1-H4S Thread RCP, MGM240PA22VNA3 Zigbee NCP, W5500 Ethernet, SC16IS752 UART expander and power supply on one board. CC1101, ZAC93, LD2450 and BME680 remain connected through keyed harnesses. The current low-power firmware pin assignments are preserved.

The editable KiCad schematic, PCB, local footprint library and machine-readable connectivity are the electrical design. The Gerber/drill and assembly exports are **review samples**. Do not order a production batch from them until the open items in [release-status.json](release-status.json) have been closed with evidence. A successful ERC/DRC establishes only the rules actually checked; it does not establish RF performance, USB compliance, isolation qualification, impedance or manufacturability.

## Electrical scope

- One PoE cable enters a Bel **0813-1X1T-57-F** 10/100 PoE magjack. Its four cable-side supply taps feed the two input bridges of **Ag97005-FL**, which supplies nominal 5 V across an isolation barrier. This exact 5 V model is rated **9 W**, not the 12 W of the higher-voltage variants. CP1/CP2 remain open for Class 0.
- F1 is a 1.5 A time-delay fuse on the secondary. **Pololu D24V22F3** provides the only 3.3 V supply; PG/EN are unconnected and both grounds are connected. The existing 1.025 A reserved 3.3 V load budget is retained. The 1.5 A / 3.3 V regulator load test is a separate bench qualification test: account for its 5 V input current, fuse temperature derating and PoE limits. A 1 A continuous note is a preliminary operating target, not a declaration that all reserved peaks are below 1 A.
- The W5500 is the **48-pin LQFP** device. The magjack has a common PHY-side center tap, so the receiver uses the 6.8 nF series capacitors and 49.9 Ω termination arrangement from the official W5500 reference. The 25 MHz crystal, 12.4 kΩ EXRES, internal-regulator capacitors and local analogue bypasses are included. Reserved pin23 is grounded as required by the manufacturer. PMODE starts at 111; the existing firmware selects its tested Ethernet mode.
- The SC16IS752 is **IPW, TSSOP-28**, with 3.6864 MHz crystal and TPS3808G33DBVR reset supervision. Its interrupt has the required 1 kΩ pull-up. The shared SPI bus and UARTA feed the existing Z-Wave proxy.
- H2 EN and BOOT remain open-drain signals from S3; H2 GPIO8 is pulled high and GPIO25 low. MGM240P RESET has **no external 3.3 V pull-up**. Its SWD/reset/PA00 boot service connector permits separate programming.
- The USB-C receptacle is a **self-powered native USB service port**. It has CC pull-downs, USBLC6-2SC6 ESD protection and 22 Ω series data resistors. USB VBUS is not connected to either board supply. Current firmware does not gate USB attach using VBUS, so full USB self-powered-device compliance is an explicit open item.
- The two UART service/programming sources must never drive simultaneously. Hold the S3 in reset before driving the H2 service RX line from an external programmer. Service 3.3 V pins are target references, not independent power inputs.

Use [connectors.json](connectors.json) and the [pin atlas](../visual/README.md) for harness wiring. Connector numbering is the **PCB top/component view**. The cable mating face is mirrored. Magjack PCB solder terminals are not RJ45 cable contact numbers. Remote CC1101/LD2450 connector locations depend on the purchased module and are not invented here.

## Board and assembly

The candidate outline is **160 × 142 mm**, with 3.2 mm mounting holes (M3 head envelope up to 6.8 mm diameter) centered at (5,5), (155,23), (5,137) and (155,137) mm. The board uses four copper layers and a provisional 1.6 mm thickness. In1.Cu is a dedicated ground reference plane; signal routing uses the other three copper layers. Surface ground pours connect SMD ground pins to reserved stitching vias. The MDI paths are fixed on F.Cu before the other buses are routed. This outline does **not** fit the existing 160 × 100 mm carrier pocket or its mounting pattern.

The S3/H2/MGM240P have integral antennas. The MGM240P antenna edge is aligned with the top PCB edge. Their local antenna regions and the documented board keepouts must remain free of copper, metal fasteners, cables and enclosure metal. A wider application-specific RF clearance/coexistence review is still required. The PoE module is mounted vertically; its component envelope and the under-module isolation corridor are reserved. The Pololu module is mounted on its verified through-hole pattern with symbolic pad names, not invented numeric pin numbers.

The routing report records measured pad-to-pad planar trace lengths, layers and via counts. CI requires MDI paths to remain on F.Cu without vias, TX/RX trace skew below 2.5 mm and USB trace skew below 3 mm. These are project sanity budgets, not substitutes for stack-up and signal-integrity qualification.

The design retains 0.8 mm power trunks with short 0.2 mm escapes at fine-pitch IC pads. The completion pass locks the existing trunks and reserves local ground returns; final native checks remain mandatory. The design includes 0.5 mm primary PoE routing targets, and a preliminary 2.5 mm clearance rule between named PoE inputs and secondary nets. The Ag97000 under-module corridor is at least 6 mm wide. These settings are not a substitute for the final safety classification and fabrication stack-up. USB and Ethernet pair geometry must be tuned and checked against the selected fabricator's stack-up; do not interpret a routed line width as a verified 90 Ω or 100 Ω impedance.

The manufacturer-recommended S3 land pattern includes 0.2 mm thermal via drills. Confirm filled/tented via and solder-paste treatment with the assembler. The board requires SMT plus through-hole assembly; the PoE module, Pololu module and connectors cannot be treated as ordinary reflow-only parts.

## Reproduce and verify

Use **KiCad 10.0.6**, its Python `pcbnew` bindings, and Python 3.10+ for the validator. `generate.py` itself runs with the macOS KiCad-bundled Python 3.9. All library references are project-relative; `--libraries` is the KiCad SharedSupport/library root containing `footprints/`.

```sh
# Generate schematic and an UNROUTED board; this does not replace the routed PCB.
python-with-pcbnew generate.py --libraries /path/to/kicad/library-root

# Optional routing reproduction. FreeRouting 1.9.0 uses Java 17 and a GUI session.
# It is not a dependency of the read-only CI check. Optimization is disabled for the recorded routing pass.
java -jar /path/to/freerouting-1.9.0.jar -da -dct 0 \
  -de .build/integrated.dsn -do /tmp/integrated.ses -mp 20 -mt 0
python-with-pcbnew finish.py --session /tmp/integrated.ses --prepare-only --kicad-cli kicad-cli
# Preserve wide trunks; complete fine-pitch escapes and reserved ground returns.
python-with-pcbnew complete_route.py
java -jar /path/to/freerouting-1.9.0.jar -da -dct 0 \
  -de .build/completion.dsn -do /tmp/completion.ses -mp 20 -mt 0
python-with-pcbnew finish.py --session /tmp/completion.ses --prepare-only \
  --seed-board .build/completion.kicad_pcb --kicad-cli kicad-cli
# Reroute complete noncritical nets still open in the native report.
# This removes incomplete fragments without moving the protected PHY routes.
python-with-pcbnew complete_route.py --reroute-open
java -jar /path/to/freerouting-1.9.0.jar -da -dct 0 \
  -de .build/completion.dsn -do /tmp/completed.ses -mp 20 -mt 0
python-with-pcbnew finish.py --session /tmp/completed.ses \
  --seed-board .build/completion.kicad_pcb --kicad-cli kicad-cli

# Read-only checks copy the project to a temporary directory.
python3 validate.py --kicad-cli kicad-cli
python3 -m unittest discover -s . -p 'test_*.py'
```

`design.py` is the connection source; `generate.py` creates the schematic, `netlist.json`, `connectors.json`, BOM and portable local footprints. `finish.py` imports an actual router session and exports only after native checks pass. `complete_route.py` and `local_repairs.py` reserve short local returns and complete fine-pitch supply escapes; `trim_stubs.py` trims native-reported dangling tails while preserving internal track junctions. Autorouting is not a proof of completion: any remaining native error requires layout repair before export. The validator compares the firmware/atlas contract, actual schematic netlist and actual PCB pad nets, then runs KiCad ERC/DRC. It never modifies the checked-in PCB or fabrication exports.

Flashing instructions and images remain under [firmware/low-power](../../../firmware/low-power/README.md). No live hardware has been flashed or tested as part of this PCB design.
