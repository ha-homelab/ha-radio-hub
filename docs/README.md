# Current MC1 documentation

Updated 18 October 2026. The single active design is **MC1, revision
`nano-single-anchor-rails`**: a **47.5 × 75 mm, two-copper-layer** carrier for
finished modules. Controllers face the room; Ethernet, male harness headers and
the five axial parts face the ceiling. H3 is the only PCB retention hole; split
case rails provide edge support. Factory male pins are soldered directly into
the carrier, with the entire back completed before the front.

## Build and inspect

- [Assembly guide](module-carrier.md): exact module selection, H2 R7 preparation,
  first programming, power, antennas, soldering order and physical acceptance.
- [Interactive visual guide](../hardware/module-carrier/index.html): current
  architecture, PCB views, connection lookup and update paths.
- [Fitted BOM](../hardware/module-carrier/cad/BOM.csv): sixteen fitted electronic
  references; J8/J9 remain unpopulated recovery pads.
- [Circuit schematic](../hardware/module-carrier/cad/schematic.svg) and
  [schematic PDF](../hardware/module-carrier/cad/schematic.pdf).
- [Front assembly](../hardware/module-carrier/cad/assembly-top.svg) and
  [back assembly](../hardware/module-carrier/cad/assembly-bottom.svg): use the
  physical pad numbers; the back view is mirrored.
- [Wiring ledger](../hardware/module-carrier/wiring.json) and
  [connector map](../hardware/module-carrier/cad/connectors.json): authoritative
  pin-to-net references alongside the native schematic.
- [Native KiCad source and checks](../hardware/module-carrier/cad/README.md).

## Firmware and recovery

Use the [MC1 firmware target](../firmware/module-carrier/README.md), its
[GPIO plan](../firmware/module-carrier/pin-plan.json) and
[XIAO MG24 Ember image](../firmware/module-carrier/zigbee/README.md). The H2 is a
Thread RCP with **RX23/TX24**, paired with the host using those same pins. Check
the actual DevKit revision and remove its specified R7 before connecting the
host transmitter. Initial programming happens while the modules are loose.

The [update guide](../firmware/module-carrier/updates/README.md) covers S3 OTA,
H2 ROM programming through S3 and MG24 application updating over the existing
serial bridge. [Thread recovery](../firmware/module-carrier/thread-recovery.md)
describes bounded restart/quarantine behavior. No USB cable space is reserved
inside the carrier layout; network updating does not guarantee recovery from
every damaged bootloader or inaccessible host.

## Printed housing and cost

The [carrier enclosure prototype](../mechanical/module-carrier/enclosure-prototype/README.md)
provides housing source, printable parts and inspection views. Its trial outside
shell envelope is **84.3 × 121.8 × 57.4 mm**; the required 4 mm ceiling spacing
frame makes installed depth **61.4 mm**. The four print parts are base, cover,
spacing frame and trial jack stop. Install floor hardware before mounting the
base on the ceiling, with measured underside projection no greater than 3 mm.
First use the
[split-rail coupons](../mechanical/module-carrier/rail-mount/README.md) to check
actual board thickness and printer fit. The housing is for the carrier; the
isolated PoE splitter, buck, UART bridge, other radios and sensors remain outside.
Dimensions based on assumed component heights require physical confirmation.

The [17 October cost review](../hardware/module-carrier/cost-review/README.md)
records a provisional JLCPCB website estimate of **$5.20 for five bare boards**.
Four onboard modules, headers and axial parts give an allocated material cost
of **$55–57 per carrier**, before delivery, taxes and labor. That figure excludes
the enclosure and off-board equipment; it is not the complete hub cost.

## What has been verified

The [verification summary](../hardware/module-carrier/verification-summary.json),
[independent CAD review](../hardware/module-carrier/independent-review.md),
[firmware build evidence](../firmware/module-carrier/build-evidence.json) and
[mechanical instructions](../mechanical/module-carrier/enclosure-prototype/README.md)
separate automated checks from physical qualification. Source consistency,
compilation, mesh validity and simulated faults do not establish measured module
clearance, electrical startup, antenna performance, cooling or connector-load
capacity. The build remains an engineering prototype.

## Earlier designs

[Design history](design-history.md) explains C0/M0, I0, D0, the Pi assembly,
all-H2 experiment and earlier MC1 layouts. Pages labeled historical are retained
for reproducibility. Their old BOMs, pin maps, prices and enclosures are not
additional choices or parts to combine with the current MC1 build.
