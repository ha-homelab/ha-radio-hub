# MC2-C verification record

Review date: 20 October 2026. This record describes **digital verification of an
engineering prototype**. No assembled MC2 board was powered, flashed or connected
to Home Assistant during this work. Physical acceptance is outstanding.

## Circuit and geometry

The [native CAD evidence](cad/verification.json) records KiCad 10.0.6 ERC, DRC,
unconnected-item and schematic-parity results. All four categories must be zero,
without waived overlap findings. The [clean reproduction result](cad/checks/reproduction.json)
compares the generated connector/BOM ledgers and native copper/pad topology after
regenerating from source and the frozen routing session. Source hashes bind the
record to the tested revision; object UUIDs are not treated as geometry.

Independent review checked the ESP32-DevKitC-VIE's 38 physical header positions
and TinyC6[D]'s 23 positions against manufacturer source files. MC2-C uses
**TC6D-01**. Its connected pads preserve RX17/TX16, EN, BOOT9, power and the
GPIO8 strap; unused pad17 is now GPIO10. The updated body and USB envelopes and
U.FL center come from the pinned Series D STEP model. The exact source hashes,
transformation and pin ledger are in [the C6[D] evidence](cad/c6d-evidence.json).

**R3, 10 kΩ**, connects GPIO8 to the C6's own local 3.3 V rail, separate from
peripheral 3.3 V. Loose-module programming requires the temporary equivalent
pull-up. R4/R5 remain 10 kΩ pull-downs on host GPIO12/SCK and GPIO2/MOSI, preserving
3.3 V VDD_SDIO and serial recovery. WIZ850io v1.1 has no pull-ups on those inputs.
Actual CC1101 modules and warm/cold boot behaviour still require inspection.

## Peripheral power revision PWR1

The [power design](power-design.json) qualifies the RECOM R-78K3.3-1.0 as the
engineering replacement for the former Pololu converter at J2. The new
assembly adds a local 27 µF input capacitor and insulated perfboard mount.
Its budget separates the 3.3 V peripherals from the three controller boards
and radar on the 5 V rail. It records engineering current allowances separately
from manufacturer figures; no physical current or thermal measurement is claimed.

The native MC2-C copper and firmware sources remain unchanged. Their existing
evidence is retained, not represented as a new native export. Validate loaded
input headroom, output ripple, startup and temperature on the complete PWR1
assembly before using it. Do not power USB or externally drive the peripheral
rail while the assembled converter is unpowered; its output must not be backfed.

## Firmware

Actual build reports are retained for:

- [MC2-C ESP32](../../firmware/external-antenna/build-evidence.json): all 21 application
  GPIO, shared SPI, three legacy BLE4.2 connections, C6 update API and memory layout.
  The report records the actual linked application and partition sizes. Static
  RAM allocation is not a measurement of runtime free heap or simultaneous-load peaks.
  BLE5 extended advertisements and Coded PHY are not supported by this older SoC.
- [C6 RCP](../../firmware/external-antenna/c6-build-evidence.json): 257,552-byte
  application, ESP-IDF 5.5.5, 8 MB flash, ROM-compatible RX17/TX16 and required
  GPIO8 high/BOOT9 low entry contract. The MC2-C image identifies TC6D-01, initializes
  the FXL6408 antenna selector before radio startup, and fails closed on I²C,
  device-identity or configuration-register readback errors. Input-status registers
  do not report driven outputs and are deliberately excluded from this check.
- [External MG24](../../firmware/module-carrier/zigbee/build-evidence-external.json)
  and [onboard MG24](../../firmware/module-carrier/zigbee/build-evidence-onboard.json):
  both builds and bootloader/application conversions passed. The regenerated
  onboard application matches the earlier onboard image, preserving the MC1 path.

The host checks include wrong-target rejection, wrong-antenna rejection, missing
strap metadata, generated pin assignments, update transport behavior and historical
MC1 regressions. See [test results](../../firmware/external-antenna/test-results.json).
These tests do not prove RF connectivity, electrical reset timing or on-device OTA.

## Enclosure and RF acceptance

The [FH1 mechanical evidence](../../mechanical/full-hub/verification.json)
binds the full-hub printable parts to native carrier geometry and the
[component inventory](../../mechanical/full-hub/components.json). The new
package includes mounts for ZAC93, DFR0627, CC1101, isolated power modules,
LD2450 and the attached BME680 pod. Its checks cover the modelled envelopes,
mounts, mesh validity and print-bed dimensions; read the report for the exact
scope. Physical measurements remain unverified: nominal or allocated heights,
unselected accessory SKUs and routing allowances are not measurements of the
delivered assembly. STL validity does not prove a successful print, load
capacity, connector engagement, radar-window performance or thermal accuracy.
For MC2-C, the corrected TinyC6[D] U.FL endpoint gives a modelled Thread coax
route of 100.203 mm, or 125.203 mm with the 25 mm slack allowance. The selected
150 mm cable remains within budget. The 215 × 215 × 78 mm main shell and its
module mounts need no enlargement.
The [earlier carrier-only evidence](../../mechanical/module-carrier/external-antenna-prototype/verification.json)
remains tied to the smaller historical housing.

Use the [RF commissioning procedure](../../docs/rf-commissioning.md) and
[results sheet](coverage-results.csv) for the 1,000 ft² / about 93 m² requirement.
All physical results remain `not_run`. The next physical checks are module fit,
rail headroom/backpower, recovery, simultaneous traffic, temperature, installed
antenna routing and at least a 72-hour RF soak. No live HA migration has occurred.
