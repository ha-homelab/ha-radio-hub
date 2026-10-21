# MC2-D pre-fabrication purchase audit — 21 October 2026

**Conclusion: the confirmed purchased component variants match the corrected
MC2-D carrier contract. Order five bare prototype PCBs from the current
fabrication package, then qualify the first assembled hub.** No purchased
module needs replacement. This is a document/electrical/mechanical audit,
not a claim that delivered hardware has been measured or powered.

## Purchase evidence and exact variants

The 28 DigiKey line items below were read from the submitted-order confirmation,
not merely a saved cart. The Mouser order email separately confirms one
**356-ESP32DVKTC32VIE / ESP32-DevKitC-VIE**. The owner has confirmed receipt of
**Zooz ZAC93**, purchase of **five LD2450** modules, and the existing CC1101/RF
hardware. Allocate one radar to this hub. Private order identifiers, addresses
and payment details are intentionally absent from the public repository.

| Qty | DigiKey part number | Manufacturer part / description | Unit USD | Line USD |
|---:|---|---|---:|---:|
| 1 | 1597-102010636-ND | Seeed 102010636 — XIAO ESP32C6, factory-soldered headers, Thread RCP | 6.38 | 6.38 |
| 1 | 1597-102010690-ND | Seeed 102010690 — XIAO MG24, factory-soldered headers, Zigbee | 8.90 | 8.90 |
| 1 | 1278-1043-ND | WIZnet WIZ850IO — Ethernet module | 24.52 | 24.52 |
| 1 | 945-R-78K3.3-1.0-ND | RECOM R-78K3.3-1.0 — 3.3 V regulator | 3.98 | 3.98 |
| 1 | 1738-DFR0627-ND | DFRobot DFR0627 — I²C dual UART | 8.00 | 8.00 |
| 1 | 1528-2444-ND | Adafruit 3660 — BME680 with STEMMA QT | 18.95 | 18.95 |
| 3 | ANT-2.4-LCW-SMA-ND | TE/Linx ANT-2.4-LCW-SMA — 2.4 GHz SMA antennas | 3.76 | 11.28 |
| 3 | 931-CAB.618.E-ND | Taoglas CAB.618.E — 150 mm U.FL/MHF I to SMA female bulkhead | 4.66 | 13.98 |
| 1 | P122402-ND | Panasonic EEU-FS1H270 — 27 µF, 50 V radial input capacitor | 0.40 | 0.40 |
| 3 | 1801-1N5819CT-ND | Taiwan Semiconductor 1N5819 — D2/D3, DO-41 Schottky; two used, one spare | 0.32 | 0.96 |
| 1 | CF14JT4K70CT-ND | Stackpole CF14JT4K70 — R1, 4.7 kΩ, 5%, ¼ W | 0.10 | 0.10 |
| 1 | S1011EC-40-ND | Sullins PRPC040SAAN-RC — 1×40 breakaway, 2.54 mm male header | 1.23 | 1.23 |
| 1 | 35-PRPC005DAAN-RC-ND | Sullins PRPC005DAAN-RC — 2×5, 2.54 mm male header, ZAC93 harness | 0.20 | 0.20 |
| 1 | 1528-4397-ND | Adafruit 4397 — STEMMA QT to individual 0.1-inch female leads, 150 mm | 0.95 | 0.95 |
| 1 pack | 1528-1961-ND | Adafruit 1950 — 20 female/female 150 mm, 28 AWG signal jumpers | 1.95 | 1.95 |
| 1 pack | 1528-1964-ND | Adafruit 1954 — 20 male/female 150 mm, 28 AWG jumpers | 1.95 | 1.95 |
| 1 | 1528-1386-ND | Adafruit 368 — 5.5×2.1 mm female DC jack to screw terminals | 2.00 | 2.00 |
| 10 | CF14JT10K0CT-ND | Stackpole CF14JT10K0 — 10 kΩ, 5%, ¼ W; three used, seven spare | 0.027 | 0.27 |
| 1 | 4526-PAD1-ND | BusBoard PAD1 — 80×50×1.6 mm isolated-pad FR4, cut for regulator module | 8.15 | 8.15 |
| 1 | 952-2227-ND | Harwin M20-1060200 — 2-position power connector housing | 0.13 | 0.13 |
| 1 | 952-2229-ND | Harwin M20-1060400 — 4-position power connector housing | 0.22 | 0.22 |
| 10 | 952-M20-1160042CT-ND | Harwin M20-1160042 — gold crimp contacts, 22–30 AWG; six used, four spare | 0.086 | 0.86 |
| 1 spool | 1568-08867-ND | SparkFun 08867 — 22 AWG stranded black wire, 25 ft | 5.59 | 5.59 |
| 1 spool | 1568-08865-ND | SparkFun 08865 — 22 AWG stranded red wire, 25 ft | 5.59 | 5.59 |
| 10 | 298-1020-ND | Panduit PLT1M-C — 2.5 mm × 99 mm cable ties | 0.229 | 2.29 |
| 1 spool | 1528-1734-ND | Adafruit 3166 — 30 AWG blue silicone wire, 50 ft, C6 EN/BOOT | 4.95 | 4.95 |
| 1 length | A116B-4-ND | Alpha F221B1/16 BK100 — 1/16-inch heat shrink, black, 4 ft | 2.88 | 2.88 |
| 1 length | A332B-4-ND | Alpha F221B3/32 BK100 — 3/32-inch heat shrink, black, 4 ft | 3.57 | 3.57 |
| | | **Merchandise subtotal** | | **140.23** |

Prices are the observed component line prices; this audit does not reconstruct
shipping, tax or the final charged total. An order record confirms a variant,
not the dimensions or condition of the item ultimately delivered.

## Compatibility findings

- **U1:** the ordered VIE is the 38-pin, 25.4 mm row-spacing WROVER-IE host with external antenna, 8 MB flash and PSRAM. It is not a generic 30-pin ESP32. The firmware reserves the PSRAM pins and uses the classic ESP32 target.
- **U2/U3:** the exact factory-header XIAO SKUs match the 2×7, 2.54 mm pitch, 15.24 mm row-spacing footprints. Solder them directly to MC2-D; additional female sockets change the enclosure and coax geometry. C6 still needs its two fine wires from underside TP8/EN and TP2/BOOT to J10.
- **U4:** WIZ850io matches the actual 12 pad assignments, its 20.32 mm row spacing and the reserved RJ45 opening. Power it from the peripheral 3.3 V rail.
- **Power:** RECOM pin 1=VIN, 2=GND, 3=3.3 V; the 27 µF capacitor and PAD1 belong on the separate PWR1 assembly, not a footprint on MC2-D. J2 carries 5 V/GND/3.3 V/GND. Do not join any controller's local 3.3 V output to this peripheral rail.
- **External modules:** DFR0627, ZAC93, CC1101, LD2450 and BME680 connect by the documented remapped harnesses. DFR0627 must be set to A1=1/A0=0 (0x50–0x57); BME680 remains 0x77. ZAC93 uses 3.3 V and its five-wire adapter, not a straight-through Raspberry Pi cable.
- **RF:** all three CAB.618.E pigtails are U.FL/MHF-I to standard SMA female; the three ANT-2.4-LCW-SMA antennas have the matching SMA mating side. The nominal cable route and slack budget fit. Firmware must select each XIAO's external RF path.
- **Connectors:** the Sullins 0.64 mm square posts and Harwin M20 contacts/housings are compatible. The 40-pin strip provides 35 fitted carrier pins. Ten crimp contacts provide six installed contacts plus four spares. The two jumper packs suffice using the [explicit allocation](full-hub-assembly.md#allocate-the-purchased-harness-parts).
- **Assembly materials:** the 30 AWG wire is nominally 0.79 mm OD, within the specified 0.8 mm underside-wire limit. PAD1 must be cut to 24×24 mm with the prescribed copper-free rim. Cable ties restrain wiring; they do not replace the case's module retention hardware.

## Corrections made before fabrication

**D1 is an insulated 22 AWG wire link, not a 1N5819.** An additional Schottky drop
before the DevKitC's AMS1117 unnecessarily reduced voltage headroom. The link
keeps the same hole centres, pads and copper connections. Its symbol, footprint,
silkscreen, BOM and assembly instructions now identify it as a wire link.
D2/D3 remain 1N5819; use two purchased diodes and keep the third as a spare.
Splitter tolerance and loaded cable/contact losses still require measurement.

Flash loose boards before assembly. **Do not connect powered USB to the assembled
hub**, including with PoE off: host USB can feed the whole 5 V bus through D1,
and signals can backpower other rails. Assembled operation uses PoE and OTA.

**ZAC93 adapter:** insert the purchased 2×5 header's 5.84 mm long mating posts
into ZAC93. Solder and individually insulate the five harness wires on its
3.05 mm short tails. Those tails are not a reliable socket-mating interface.
See the [five-wire pin map](full-hub-assembly.md#install-the-zac93).

The previous CI failure was traced to stale prototype-enclosure evidence after
a native design metadata change. Regeneration binds the enclosure reports to
the corrected carrier; it is not evidence of a firmware compile failure.

## Verification and order handoff

The final native [verification report](../hardware/external-antenna/cad/verification.json)
and [reproduction report](../hardware/external-antenna/cad/checks/reproduction.json)
record **ERC 0, DRC 0, unrouted 0 and schematic parity 0**, with a passing clean reproduction check. The new archive passed its complete source/evidence and ten-file integrity check.
The independent initial comparison of all 131 numbered PCB pads to the design
contract found no pad/net discrepancies. The D1 correction preserves connected
copper topology; the generated package must pass its source/evidence hash guard.

Use only [MC2-D-prototype-gerbers.zip](../hardware/external-antenna/fabrication/MC2-D-prototype-gerbers.zip)
with its accompanying [manifest](../hardware/external-antenna/fabrication/manifest.json).
Follow the [PCB ordering settings](pcb-order.md): five pieces, 100×100 mm,
two layers, 1.6 mm FR-4, 1 oz copper, green mask, white legend, lead-free HASL,
no assembly or stencil. Confirm the MC2-D marking, D1 **NO DIODE** legend,
four NPTH mounting holes and rounded opening under U2 in the supplier preview.
Old MC2-C releases and the earlier MC2-D archive with D1 shown as a diode are superseded.

Audited archive SHA-256: `5898031673d14b154e9d25f597b3b8dc522e52fdb28e6391236c0a5b4490a7fe`.

## Remaining physical work

Before soldering the delivered modules, dry-seat them and check header height,
USB shell/tail clearance, at least 2.5 mm under C6, recovery-wire insulation and
coax engagement without tension. Nominal drawings do not guarantee delivered
header heights. Check the exact existing CC1101 variant and LD2450 cables.

The DigiKey order does not include the PCB, case prints, a confirmed exact
1.5 A time-delay fuse/holder, or all final fasteners/retention straps. Purchase
of the selected Waveshare 27737 5 V barrel-output PoE splitter was not confirmed
by this audit. The adapter and fuse-holder enclosure envelopes still need
physical fitting. These are completion/fit tasks, not a discovered carrier
pinout incompatibility.

After assembly, measure rails under simultaneous load, qualify thermal behavior,
RF coverage, BLE/Thread/Zigbee coexistence and recovery before switching Home
Assistant. The host supports legacy BLE 4.2, not BLE 5 extended advertisements.
Do not treat five prototype boards as a qualification for a production batch.
