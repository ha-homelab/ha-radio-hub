# MC2-B verification record

Review date: 19 October 2026. This record describes **digital verification of an
engineering prototype**. No assembled MC2 board was powered, flashed or connected
to Home Assistant during this work. Physical acceptance is outstanding.

## Circuit and geometry

The [native CAD evidence](cad/verification.json) records KiCad 10.0.6 ERC, DRC,
unconnected-item and schematic-parity results. All four categories must be zero,
without waived overlap findings. The [clean reproduction result](cad/checks/reproduction.json)
compares the generated connector/BOM ledgers and native copper/pad topology after
regenerating from source and the frozen routing session. Source hashes bind the
record to the tested revision; object UUIDs are not treated as geometry.

Independent review checked the ESP32-DevKitC-VIE's 38 physical header positions and the original
TinyC6's 23 positions against manufacturer drawings. The C6 review found a missing
GPIO8 boot strap: **R3, 10 kΩ, now connects GPIO8 to the C6's own local 3.3 V rail**.
That rail is separate from peripheral 3.3 V. Loose-module programming requires
the temporary equivalent pull-up before carrier assembly. The XIAO RF connector's
estimated cable endpoint was also checked against the actual connector location;
these estimates still require measurement on delivered modules. MC2-B adds R4/R5, 10 kΩ pull-downs on GPIO12/SCK and GPIO2/MOSI. The former preserves 3.3 V VDD_SDIO; the latter permits serial recovery. WIZ850io v1.1 has no pull-ups on those two input nets. Actual CC1101 modules and warm/cold boot behavior still require inspection and testing.

## Firmware

Actual build reports are retained for:

- [MC2-B ESP32](../../firmware/external-antenna/build-evidence.json): all 21 application
  GPIO, shared SPI, three legacy BLE4.2 connections, C6 update API and memory layout.
  The report records the actual linked application and partition sizes. Static
  RAM allocation is not a measurement of runtime free heap or simultaneous-load peaks.
  BLE5 extended advertisements and Coded PHY are not supported by this older SoC.
- [C6 RCP](../../firmware/external-antenna/c6-build-evidence.json): 235,456-byte
  application, ESP-IDF 5.5.5, 8 MB flash, ROM-compatible RX17/TX16 and required
  GPIO8 high/BOOT9 low entry contract.
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
The [earlier carrier-only evidence](../../mechanical/module-carrier/external-antenna-prototype/verification.json)
remains tied to the smaller historical housing.

Use the [RF commissioning procedure](../../docs/rf-commissioning.md) and
[results sheet](coverage-results.csv) for the 1,000 ft² / about 93 m² requirement.
All physical results remain `not_run`. The next physical checks are module fit,
rail headroom/backpower, recovery, simultaneous traffic, temperature, installed
antenna routing and at least a 72-hour RF soak. No live HA migration has occurred.
