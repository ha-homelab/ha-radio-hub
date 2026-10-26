# MC2-D verification record

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
and the XIAO ESP32C6's 14 positions against manufacturer source files. MC2-D
uses pre-soldered **102010636**. TX16/RX17 are U2 pads 7/8; VBUS/GND are 14/13.
The body, USB, U.FL center and underside TP8/TP2 coordinates are pinned in
[the XIAO evidence](cad/xiaoc6-evidence.json). The real carrier access window
makes the two underside recovery joints accessible; J10.1 reaches TP8/EN and
J10.2 reaches TP2/BOOT. Tests reject swapped recovery pad mapping.

The XIAO contains a **5.1 kΩ GPIO8 pull-up** to local 3.3 V. Carrier R3 is removed
and U2 local 3V3 pad12 stays unconnected to the peripheral rail. R4/R5 remain 10 kΩ pull-downs on host GPIO12/SCK and GPIO2/MOSI, preserving
3.3 V VDD_SDIO and serial recovery. WIZ850io v1.1 has no pull-ups on those inputs.
Actual CC1101 modules and warm/cold boot behaviour still require inspection.

## Peripheral power revision PWR1

The [power design](power-design.json) qualifies the RECOM R-78K3.3-1.0 as the
engineering replacement for the former Pololu converter at J2. The new
assembly adds a local 27 µF input capacitor and insulated perfboard mount.
Its budget separates the 3.3 V peripherals from the three controller boards
and radar on the 5 V rail. It records engineering current allowances separately
from manufacturer figures; no physical current or thermal measurement is claimed.

MC2-D has a fresh native layout and export for XIAO and J10; the RECOM PWR1
power circuit and four-wire J2 mapping remain the same. Validate loaded input
headroom, output ripple, startup and temperature on the complete assembly
before using it. Do not power USB or externally drive the peripheral
rail while the assembled converter is unpowered; its output must not be backfed.

## Firmware

The MC2-D migration ran 193 firmware/regression tests with the configured
sanitizers, 20 harness/power contract tests and 13 fabrication guard tests.
These are software checks, not physical hardware acceptance.

Actual build reports are retained for:

- [MC2-D ESP32](../../firmware/external-antenna/build-evidence.json): all 21 application
  GPIO, shared SPI, three legacy BLE4.2 connections, C6 update API and memory layout.
  The report records the actual linked application and partition sizes. Static
  RAM allocation is not a measurement of runtime free heap or simultaneous-load peaks.
  BLE5 extended advertisements and Coded PHY are not supported by this older SoC.
- [C6 RCP](../../firmware/external-antenna/c6-build-evidence.json): 248,560-byte
  application, ESP-IDF 5.5.5, **4 MB flash**, ROM-compatible RX17/TX16 and GPIO8
  high/BOOT9 low entry contract. The image identifies `mc2d-xiaoc6-ext-v1`, drives
  RF enable GPIO3 LOW and antenna select GPIO14 HIGH, and verifies GPIO
  configuration/readback before radio startup. The updater rejects TinyC6 and
  8 MB images rather than assuming all ESP32-C6 boards are interchangeable.
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
All three radios use explicit nominal factory-header mounting planes; XIAO C6
adds its new U.FL endpoint and two service wires. A lower coax approach preserves
the 150 mm cable budget. Mechanical tests check the header gaps, access window,
service-wire clearance and cable length/slack, and reject the former high approach
with the new stack. These heights are engineering allowances until measured; see
[the mounting source ledger](../../mechanical/full-hub/sources.md#factory-header-stack-and-coax-approach).
The 215 × 215 × 78 mm main shell requires no enlargement; existing plastic
geometry is retained and the assembly images/inventory are regenerated.
The [optional carrier-only evidence](../../mechanical/module-carrier/external-antenna-prototype/verification.json)
is also regenerated for MC2-D, but covers only the smaller housing without
the full set of peripheral trays.

Use the [RF commissioning procedure](../../docs/rf-commissioning.md) and
[results sheet](coverage-results.csv) for the 1,000 ft² / about 93 m² requirement.
All physical results remain `not_run`. The next physical checks are module fit,
rail headroom/backpower, recovery, simultaneous traffic, temperature, installed
antenna routing and at least a 72-hour RF soak. No live HA migration has occurred.
