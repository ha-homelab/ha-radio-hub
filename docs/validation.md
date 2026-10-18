# Validation status

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

The current MC1 evidence is the [verification summary](../hardware/module-carrier/verification-summary.json), [independent CAD audit](../hardware/module-carrier/independent-review.md), [firmware build record](../firmware/module-carrier/build-evidence.json) and [enclosure prototype checks](../mechanical/module-carrier/enclosure-prototype/README.md). Current physical acceptance is in the [MC1 assembly guide](module-carrier.md#assembly-acceptance). The dated results below describe earlier targets.

Initial design reviewed on **2026-10-16**. This record separates software evidence
from hardware acceptance; it is not a declaration that the appliance works in a home.

## Single-host low-power variant, 2026-10-17

The separate [low-power design](low-power.md) now has a full compiled S3 profile,
not just a proposed consolidation of the older YAML files.

- ESPHome 2026.9.1 / ESP-IDF 5.5.5 compiled and linked `firmware/low-power/hub.yaml`
  with BLE, RF, radar, BME680, SC16 Z-Wave UART, Zigbee TCP and H2-backed OTBR
  together. Application/OTA binary: 1,716,944 bytes; static RAM: 161,127 / 341,760
  bytes (47.1%). Nineteen required SDK settings were checked against the actual
  generated configuration. Runtime heap, task stacks and concurrent throughput
  are not established by these numbers.
- The matching ESP-IDF 5.5.5 H2 UART RCP compiled: 208,928 bytes, 4 MB flash,
  UART0 RX23/TX24 at 460800 baud. The source is the pinned SDK example with its
  build configuration prepared by `prepare_h2.py`; no radio was flashed.
- MGM240PA22VNA3 Ember NCP and UART-XMODEM bootloader compiled from Simplicity
  SDK 2025.6.3 / Zigbee 8.2.3. Generated UART pins, flow control and module clocks
  were inspected. Commander created the bootloader CRC, GBL update and merged
  initial image; address ranges, vectors and GBL roundtrip were checked. See the
  [MG24 evidence](../firmware/low-power/mg24/build-evidence.json). This establishes
  a build for the selected module, not physical startup or pairing.
- The complete native/Python suite passed 77 tests with C++ AddressSanitizer and
  UndefinedBehaviorSanitizer enabled. New coverage includes seven SC16 register
  scenarios, eight actual Zigbee TCP-worker scenarios, and lifetime-energy
  arithmetic/measurement boundaries. The Zigbee tests use real loopback sockets
  and a modeled UART; restoring the old FIFO/timeout defects makes them fail.
- Two offline REST contract tests passed using the exported Espressif C handlers
  and `python-otbr-api` 3.0.0. They reproduce the upstream HTTP-200 dialect-probe
  problem and verify the HTTP-404 correction. They do not exercise an on-device
  web server, radio commissioning or Thread routing.
- Low-power CAD regeneration and nine geometry tests passed. Five printable
  solids, the GLB assembly and layout views match their source. The dimensions
  are allocation envelopes for a concept carrier, not a fabricated PCB or
  verified module mounting pattern.
- The hardware validator checked 26 unique S3 GPIO assignments, UART ownership,
  supply/IRQ constraints, pin agreement with the YAML, and AC/DC/kWh arithmetic.
  This does not replace schematic ERC, PCB DRC, isolation or signal-integrity tests.

The 3 W AC objective remains unmeasured. An absent/incompatible H2 can trigger
an upstream OpenThread panic and restart the shared S3. Full acceptance therefore
includes radio fault recovery as well as the normal concurrent workload. Existing
Home Assistant services were not switched to this unassembled variant.

## Graphical wiring and custom PCB evidence

The [connection atlas](../hardware/low-power/visual/README.md) is generated from
an independently checked pin/net model. It distinguishes module pads, GPIO
numbers and unverified reused-board headers; NC and mechanical pads remain
visible. Its tests cover firmware-pin agreement, supply domains, open-drain
signals, handshake directions, ground coverage and export freshness. Separate
contact drawings check physical geometry and viewing orientation against their
recorded sources. Browser checks cover offline use, connector selection,
pin highlighting and layouts at 375, 760 and 1360 pixels.

The [LP-C0 backplane](../hardware/low-power/carrier/), its
[LP-M0 MG24 daughterboard](../hardware/low-power/carrier/mg24-adapter/) and the
[LP-I0 integrated PCB](../hardware/low-power/integrated/) have separate native
KiCad sources and revision-specific connector manifests. Their validators
compare the circuit contract with the actual schematic netlist and PCB pad
nets, including unused contacts, and run native ERC/DRC. Fabrication exports
must match their recorded source/output hashes. The required CI gate includes
these checks in the pinned KiCad 10.0.6 container.

The 2026-10-17 local native runs returned zero ERC violations, DRC violations,
unconnected items and schematic-parity errors for C0, M0 and I0. The PCB
contract suites passed 39 tests; the connection/atlas and physical-reference
suites passed 23 tests. The browser smoke check covered all three boards,
20 connectors and 19 available net-trace links, with no page errors or missing
images. I0 critical Ethernet and USB routes stay on F.Cu with no vias; recorded
track-length skew is 1.925 mm TX, 1.731 mm RX and 0.795 mm USB. These are
geometry measurements, not impedance or signal-integrity measurements.

These checks do not establish controlled impedance, insulation qualification,
EMC, radio coexistence, assembly yield or physical operation. Read each board's
own status and open items before making first articles. Neither custom PCB
assembly fits the earlier concept case as a complete product; the
[mechanical compatibility review](../hardware/low-power/visual/physical/README.md)
records the differences. No production batch or sales release has been authorized
by a passing software or CAD check.

## Local evidence

### Illustrated parts and DIY carrier, 2026-10-17

The README gallery is rendered from the native C0, M0, I0 and D0 PCB files.
Source and image hashes, tool version and image dimensions are checked offline.
These are bare-board CAD views, not photographs of assembled hardware.

The parts catalog covers all 341 canonical BOM rows in 223 cards, preserving
quantities, packages and notes for each build. It includes a GitHub-readable image gallery and a
filterable HTML version. Manufacturer images have source/credit metadata;
offline fallbacks are explicitly labelled original illustrations. AliExpress
links are unverified searches, not approved seller listings. Browser checks
cover filtering, search, missing remote images and layouts at 375, 760 and
1360 pixels. The updated wiring atlas passed browser checks for all four
boards, 30 connectors and 29 available net-trace links.

The separate D0 toner-transfer design has 636 bottom-copper tracks and 54
insulated wire links, including one connection to the exposed U1.11 adapter
pin at a documented height. Native KiCad ERC, DRC, unconnected-item and
schematic-parity checks returned zero violations. An independent geometry
and wire-union check verified 195 component pins across 44 logical nets, with
a minimum copper clearance of 0.500 mm. There are no top-layer tracks, plated
vias or copper zones. Removing a wire, cutting a track or changing a connector
assignment is covered by connectivity regressions.

The matching vector print package provides transfer copper, bottom inspection
and drilling, component-side assembly with wire schedules, and calibration
coupons. Its checks cover source/output freshness, PDF scale and orientation,
including the raised-pin joint without inventing an extra drilled hole. The
adapter footprints are independently checked against pinned manufacturer CAD.
The relevant suites passed 26 D0, 14 catalog, 18 atlas, 6 contact-reference and
8 print-export tests. All eight pages of the four print PDFs were rendered and
visually inspected; the drilling set contains 299 real holes.
These checks do not establish printer accuracy, etching quality, mechanical
clearance in a real assembly, signal integrity or powered operation. D0 still
needs factory-made fine-pitch adapters and the populated M0 radio board.

### Modular reference and shared tooling

- Main ESPHome 2026.9.1 configuration: schema validation and full ESP-IDF 5.5.5
  compilation passed. It includes W5500 Ethernet, active BLE proxy, ZAC93 UART,
  LD2450 UART and BME680 I²C. Static RAM 104,319 / 341,760 bytes; application
  942,199 bytes. Runtime heap and simultaneous load remain unmeasured.
- RF Airbridge Ethernet port: ESPHome 2026.9.1 / ESP-IDF 5.5.5 schema validation
  and full compilation passed for the **real importer's migrated fixture with
  15 legacy binary sensors**, custom source/topics, an RM433 slot and exact-width
  RF codes. Static RAM: 72,991 / 341,760 bytes (21.4%); application: 699,707 /
  8,126,464 bytes (8.6%). The standalone template also compiled. The port includes
  legacy MQTT payloads, RM433 native events, RC-Switch/Dooya actions and the pinned
  RMT receiver patch. Runtime heap, waveform timing and physical I/O remain unmeasured.
- Native RF regressions exercise golden payloads, exact bit widths, RM433
  quiet-time behavior, offline publishing, actual RMT lifecycle code with driver
  doubles, and the YAML TX worker under delayed completion/faults. AddressSanitizer
  and UndefinedBehaviorSanitizer runs passed: 53 RF/migration tests in the local
  suite, including 24 importer tests. Eight additional release-package tests verify
  committed-source selection, checksums, private-path rejection and archive use.
  These tests do not measure physical
  pulse timing, interrupt races on silicon, RF range or analog pin contention.
- Offline migration tests passed for private output permissions, secret handling,
  quoted RF codes, entity definitions, identity substitution resolution, rejected
  custom lifecycle hooks, and receiver-filter normalization. The private wrapper
  includes a credential-free base package so secret lookups stay beside that
  wrapper. Schema and full compilation of that imported output passed as noted
  above. A subsequent read-only inventory also retrieved the actual installed
  RF configuration and its 15 sensors into an ignored private directory. Its
  upstream package and three helper headers matched the canonical source. The
  importer now preserves its explicit API/OTA authentication settings, web server
  and supported radio overrides while rejecting conflicting secret aliases.
  The actual private migrated configuration also passed ESPHome 2026.9.1 schema
  validation and full compilation: 15 legacy RF sensors, static RAM 73,247 bytes
  (21.4%), application 697,435 bytes (8.6%). Ten configuration-mapping checks
  passed. Its source, credentials and binaries remain in ignored private storage.
  No board was flashed and HA was not switched; the new controller is not ready.
  HA registry identity is deliberately not claimed to transfer.
- Linux config renderer: four tests passed, including custom output paths,
  private atomic replacement and rejection of linked output files. Docker Compose
  parsed the rendered configuration and selected its actual generated bind source.
  No local Docker daemon or
  USB hardware was available for service runtime validation.
- CAD: eight exported STL files were re-imported and checked for watertightness,
  consistent winding, positive volume and one connected body. See the generated
  [mesh report](../mechanical/generated/mesh-report.json). Seven CAD regression tests
  cover source/artifact consistency, geometry changes and rigid assembly placement.
  CI regenerates in a temporary directory and compares the committed STL/GLB solids
  and SCAD source before packaging. These are geometry checks.
- Original source and documentation: the repository provides an offline checker
  for local links, Python/shell/JSON syntax, required assets, pin-map collisions
  and common credential patterns. This is not an exhaustive security audit.
- Release packaging reads committed Git objects, excludes private/generated
  installation material, rejects symlinks and records per-file SHA-256 hashes.
  Its inventory lets the checker run in an extracted build package without
  traversing local private configuration. This is separate from physical tests.

## Reproducible CI

[Prototype validation](https://github.com/ha-homelab/ha-radio-hub/actions/workflows/check.yml)
runs offline checks, renderer tests, RF contract/migration regressions, ESPHome
builds, CAD regeneration and a Linux ser2net image build. RF compilation also
uses a synthetic migration fixture with 15 legacy binary sensors rather than
checking only the empty public template. [Thread RCP build](https://github.com/ha-homelab/ha-radio-hub/actions/workflows/thread-rcp.yml)
builds the pinned PCA10059 USB firmware with an Arm toolchain. Read the actual
workflow result; the existence of a workflow is not evidence it passed.

The [Thread RCP run on source revision `31cca5e`](https://github.com/ha-homelab/ha-radio-hub/actions/runs/38992347499)
successfully built the pinned PCA10059 firmware on Linux. The RCP build script
has not changed since that run. This is compiler evidence; no Nordic dongle was
flashed and no Spinel exchange was tested.

Reproduce RF validation in the pinned environment:

```sh
RF_CPP_SANITIZERS=1 python -m unittest discover -s tests -p 'test_*.py'
python firmware/validate.py --config rf-ethernet.yaml
python firmware/validate.py --config rf-ethernet.yaml --migration-fixture --compile
```

The fixture uses generated credentials and synthetic codes, creates an isolated
snapshot, invokes the real importer, compiles its result and discards the binary.
It does not load private household configuration or contact HA, MQTT or a radio.
The migration-fixture command completed successfully locally; generated binaries
were removed without flashing a board.

## Still requires hardware

No boards were flashed or commissioned. Component/cable fit, FDM tolerances,
insert strength, PoE startup/peak margin, temperatures, radio coexistence,
range, correct RF waveforms, commissioning, restart recovery and sensor accuracy
have not been measured. The cooperative 30 s TX wait requires a running event
loop; stock RMT completion can block in `rmt_tx_wait_all_done(-1)`, so the software
tests do not establish a maximum driver-hang or watchdog recovery time. The
full [acceptance checklist](acceptance.md) is the next step on a physical prototype. Existing household services were not changed.
