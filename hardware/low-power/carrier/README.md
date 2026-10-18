# LP-C0 low-voltage module carrier

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../../../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

**This is a routed, electrically connected prototype PCB, not a production release.** The native KiCad 10 project includes a schematic, a two-layer PCB, a machine-readable connector map, assembly data and prototype Gerbers. The board passes native ERC, DRC, the unconnected-item check and schematic parity. It has not been fabricated, populated, powered or RF-tested. No radio pairing, PoE interoperability, long-run reliability or 3 W AC energy target is established by these CAD checks.

Open [carrier.kicad_pro](carrier.kicad_pro) in KiCad 10. The ready-to-review [schematic PDF](outputs/schematic.pdf), [assembly drawing](outputs/assembly-top.svg) and [top copper drawing](outputs/board-top.svg) are generated from the native files. The [validation summary](outputs/validation/summary.json) states the actual check results. [Prototype fabrication files](outputs/prototype-gerbers.zip) are for engineering review and a first article only.

## What this board does

LP-C0 is a **160 × 100 mm, 1.6 mm, two-layer low-voltage backplane**. SC16IS752, its 3.6864 MHz crystal, its TPS3808G33 reset supervisor, bypass capacitors, pull-ups and unused-input terminations are on the board. Radios, controller modules, the radar and the regulator are wired through keyed connectors. The CPU assignment remains the existing LP-P0 firmware contract: one S3 host, H2 Thread RCP, MG24 Zigbee NCP, ZAC93, CC1101, LD2450 and BME680.

The carrier contains no Ethernet magnetics or PoE primary circuitry. An independently reviewed isolated PoE front end supplies **regulated 5 V** at J1. A separately mounted Pololu D24V22F3 at J2 generates the sole 3.3 V rail. WIZ850io at J4 supplies the Ethernet controller, PHY, magnetics and RJ45. Do not connect raw PoE pairs or a 48 V source to this PCB.

This partition is useful for a bench build with accessible, replaceable modules. It is not a finished plug-together kit: the actual S3/H2 development-board revision must be checked for pin access, regulator backfeed and UART/LED conflicts. The included [LP-M0 daughterboard](mg24-adapter/README.md) provides the exact MGM240PA22VNA3 footprint, power/ground lands and service access. One populated M0 is required per C0 hub; its PCB, assembly and cable end must be included in procurement. No undocumented DevKit header, CC1101 header or radar connector footprint is claimed to fit.

## Connectors and harnesses

[connectors.json](connectors.json) is the complete pin-by-pin wiring list. It contains actual PCB pad centres, connector rotation, voltage domain, remote signal name and verified module-pad/header positions where available. [assembly-bom.csv](assembly-bom.csv) lists populated PCB parts; [harness-bom.csv](harness-bom.csv) lists the mating housings, contacts and off-board assembly items.

The board is viewed **from the component side**, with its origin at the upper-left corner and positive Y down. Every connector's square pad is pin 1. The J3 IDC header uses odd and even columns, not a single left-to-right sequence. A cable socket viewed into its mating face is mirrored relative to the PCB. Use moulded circuit numbers and the manufacturer drawing, then continuity-test every conductor. The pin numbers in this project belong to the **carrier connector**; they are not development-board header numbers. J3 is emphatically **not a Raspberry Pi header**.

- J1: 2-position JST XH, isolated 5 V input and return.
- J2: 3-position JST XH, buck VIN = fused 5 V, GND, buck VOUT = 3.3 V. Check this order before power.
- J3: 40-position keyed Würth IDC, S3 GPIO, duplicate 3.3 V and ground contacts. No 5 V.
- J4: 10-position JST XH, WIZ850io power and SPI. The official WIZ850io **J2.1 is GND; J2.2/3 are 3.3 V; J2.4 is NC**. The WIZ header J2 is distinct from carrier J2.
- J5: 7-position JST XH, H2 power, UART, EN and BOOT. EN/BOOT are open-drain controls with external pull-ups.
- J6: 6-position JST XH, MG24 power and UART with RTS/CTS.
- J7: 8-position JST XH, CC1101 power, SPI and GDO0/GDO2. GDO0 is shared open-drain TX with a 4.7 kΩ pull-up.
- J8: 5-position JST XH, ZAC93 3.3 V, both ground contacts and UART. SC16 TXA goes to ZAC93 RX; SC16 RXA receives ZAC93 TX.
- J9: 4-position JST XH, LD2450 5 V supply and 3.3 V UART. The radar is the only 5 V module on these peripheral harnesses.
- J10: JST SH STEMMA QT, 1 GND / 2 3.3 V / 3 SDA / 4 SCL. BME680 stays in a ventilated external pod. Its breakout provides the I²C pull-ups.

Use 22 AWG conductors on J1/J2 and 26 AWG on signal harnesses. The selected XH contact supports 28–22 AWG; the connector's 3 A rating is specified with 22 AWG. The selected IDC **mating socket is rated 1 A per contact**, regardless of the larger header rating. Keep SPI harnesses short: start at **100 mm maximum**, route a nearby ground return, and scope the actual edges before increasing length. This is a prototype layout constraint, not a measured signal-integrity guarantee. The 10 MHz W5500 and 4 MHz SC16 bus settings have not been validated through these cables.

## Module-side prerequisites

The required module-side wiring is described in [the LP-P0 hardware contract](../README.md). In particular:

1. Power S3/H2 modules only from the regulated 3.3 V rail after verifying that their development-board regulator and USB circuitry cannot backfeed it. Never connect another live 3.3 V supply. Isolate the S3 GPIO48 LED and UART0 USB bridge connections as required by the chosen board. Native S3 USB remains on GPIO19/20 and is not routed through J3.
2. H2 requires its documented GPIO8 pull-up and GPIO25 pull-down, EN timing and GPIO9 BOOT state. J5 does not expose those two strap pins; they must exist on the H2 module adapter. The carrier supplies EN/BOOT pull-ups and EN capacitance; account for any duplicate parts on a DevKit.
3. Use the included M0 adapter for MG24: its all-ground connection, VDD bypassing, antenna keepout, PA00 boot service, SWD PA01/PA02, reset and 3.3 V reference are part of the design. Connect C0 J6 to M0 J1 straight number-to-number. Do not add a 3.3 V pull-up to its reset pin. Flash the exact [MGM240P NCP build](../../../firmware/low-power/mg24/README.md), not an unrelated USB-dongle image.
4. ZAC93 and CC1101 connections terminate in harnesses because the physical revision and mounting dimensions of the user's boards are not verified. Check pin 1 and trace continuity at the actual board before attaching power.
5. The WIZ850io **data-only Ethernet RJ45 is not itself a PoE PD**. The separate verified front end must provide a data path and isolated 5 V; the carrier does not implement that external cable assembly.

## Power and assembly limits

F1 is Littelfuse **044901.5MR**, a 1.5 A time-delay fuse. It does not provide reverse-polarity protection, overvoltage protection or active current limiting. Use an isolated, current-limited 5 V source for first power. Start with only the external regulator, then measure J2.3 before connecting modules. The provisional continuous input criterion is **at most 1.0 A at 5 V**; re-evaluate the fuse and thermal derating against measured duty cycles. A fuse rating is not a measured current draw.

The shared 3.3 V rail uses a 0.8 mm routing class and a front copper pour; ground uses a rear pour. The SC16's small local supply escape is 0.25 mm. General signal traces are 0.25 mm, minimum clearance 0.20 mm, and routed vias are 0.8 mm with 0.4 mm drills. Copper is specified as 1 oz nominal per layer. Verify voltage at the furthest module during simultaneous radio activity; an unloaded 3.3 V reading is insufficient.

The PCB has hand-solderable 0805 passives, 1206 bulk capacitors, a TSSOP-28 UART bridge and SOT-23-6 supervisor. The JST SH connector is the finest-pitch part. Assemble low components first, inspect bridges under magnification, and measure resistance between rails before power. Three ground pads (J3.8, J4.2 and J4.9) have direct plane connections to avoid isolated thermal islands; they need more soldering heat or board preheat than the other connector pads.

The initial crystal load capacitors are 22 pF and 33 pF. Their values follow the existing design contract and remain a measured-frequency/drive-level gate. The crystal traces are short local front-layer routes reserved before global routing. Do not infer oscillator start-up margin from DRC. The SC16 64-byte receive FIFO still requires firmware stress testing with all radios active.

Mounting holes are 3.2 mm NPTH at **(5,5), (155,5), (5,95), (155,95) mm**. Use insulating M3 supports and protect the underside from conductive hardware. This hole pattern and the off-board harness layout **do not match the existing low-power enclosure mock-up**. Three support positions differ; do not print the old case expecting this board to fit. Harness bend radius, module antenna clearance, PoE isolation and BME/radar placement require an enclosure revision after a physical first article.

## Reproduce and verify

KiCad 10.0.6 was used locally. `generate.py` and `finalize.py` require the Python interpreter bundled with KiCad or a Python environment providing the matching `pcbnew`. The committed PCB is the routed result; regenerating only the schematic and placement does not recreate routing.

```sh
python3 generate.py --libraries /path/to/KiCad/SharedSupport
kicad-cli sch export netlist carrier.kicad_sch --format kicadxml -o .build/carrier.xml
java -jar /path/to/freerouting-1.9.0.jar -da -dct 0 -de .build/carrier.dsn -do .build/carrier.ses -mp 40 -mt 0
python3 finalize.py
python3 -m unittest test_contract -v
python3 validate.py --kicad-cli kicad-cli --out .build/validation
python3 export.py --kicad-cli kicad-cli
python3 validate.py --kicad-cli kicad-cli --check-hashes --out .build/recheck
```

Run from this directory. FreeRouting 1.9.0 needs a graphical display even in its command-line mode; a headless Linux reroute needs a virtual display. **CI does not need to reroute.** It checks the committed native PCB with KiCad and the independent netlist/connector validator. `-mt 0` avoids the old router's multithreaded optimization problems. `-da` disables its analytics. The intermediate DSN/SES and unrouted board live under ignored `.build/`.

Validation compares schematic-exported connectivity, native PCB pad nets and the canonical design; verifies all part positions/rotations, checks actual connector pad centres; and compares external endpoints against the independently sourced visual module atlas. Native DRC includes unconnected items and schematic parity. The script parses the JSON report as well as checking process status, because an observed KiCad CLI run returned success despite reporting errors.

No electrical violation is excluded. The reports list KiCad's default ignored non-electrical checks: missing courtyard (the four board-only mounting holes have no component courtyard), track-to-via centring, tuning geometries and unused symbol footprint filters/type metadata. There are no tuned differential pairs. The five explicitly unused SC16/supervisor output/control pins are marked with no-connect flags as required by the circuit; unused SC16 input/GPIO pins are terminated. See [NOTICE.md](NOTICE.md) for library provenance and licenses.

## Before a production order

Review the prototype Gerbers and drill map with the fabricator, then make a small first-article run. Inspect the pin-1 markings and connector fit before making cables. Validate the input fuse, rail droop, regulator temperature, oscillator frequency, reset/start-up sequence, SPI integrity, all radio traffic, antenna isolation, radar window and continuous operation. The off-board PoE front end and every module adapter need their own electrical/mechanical review. Production PCBA/test fixtures, enclosure design, RF/regulatory work and a saleable product release remain separate engineering steps.

The SHA256 manifest binds source files and exported artifacts, including the fabrication ZIP. Both C0 and M0 use descriptive `.gbr` Gerber filenames. J10 has two isolated solder hold-down tabs, represented as separate NC pins MP1/MP2; they are not extra cable contacts. The full named-pad check covers these tabs as well as numbered electrical pads.
