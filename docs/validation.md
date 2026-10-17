# Validation status

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

## Local evidence

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
