# Current MC2 documentation

Updated 20 October 2026. **MC2-D** is the active 100 × 100 mm carrier with separate
external Zigbee, Thread and BLE antennas. The selected ESP32-DevKitC-VIE has 8 MB flash and 8 MB physical
PSRAM (4 MB directly addressable); its Thread radio is XIAO ESP32C6 pre-soldered / 102010636. All components face the same side.
The project is an engineering prototype, with physical and whole-house RF
qualification still outstanding.

**New build: [Start here — the complete MC2-D / FH1 build journey](start-here.md).**
It orders parts verification, loose-board flashing, printing, wiring, first
power and Home Assistant setup, with a checkpoint at each stage and symptom-based
troubleshooting. To view the guide locally as rendered HTML, run
`python3 tools/preview.py` from the repository root and open the printed URL.

## Active build references

- [S1 printed assembly legend, QR, native previews and cost assumptions](pcb-silkscreen.md).
- [Prototype PCB order, quantity and matched revision](pcb-order.md).
- [Exact parts, availability and priced subtotal](mc2-shopping.md).
- [Lower-cost pigtails, connector fit and RF evidence](pigtail-selection.md).
- [Classic ESP32 migration, cost and compatibility](classic-esp32-migration.md).
- [Assembly, exact parts and antenna connections](external-antennas.md).
- [Visual guide with pin-to-pin lookup](../hardware/external-antenna/index.html).
- [Hardware and carrier BOM](../hardware/external-antenna/README.md),
  [RF BOM](../hardware/external-antenna/rf-bom.json),
  [schematic](../hardware/external-antenna/cad/schematic.svg) and
  [connector ledger](../hardware/external-antenna/cad/connectors.json).
- [ESP32/C6/MG24 build and programming instructions](../firmware/external-antenna/README.md)
  and [network updating](../firmware/external-antenna/updates/README.md).
- [MC2-D MG24 external-antenna image: build, program and recover](mc2-zigbee.md).
- [Optional ESP-NOW sensor satellites, wiring and use cases](espnow.md)
  and [firmware configuration](../firmware/espnow/README.md).
- [Full-hub enclosure, exploded layout and printable mounts](../mechanical/full-hub/README.md).
- [Complete assembly, ZAC93 placement and pin-to-pin wiring](full-hub-assembly.md).
- [Full-hub graphical wiring](../hardware/external-antenna/full-hub-wiring.svg).
- [Independent connection audit and I²C address correction](connection-audit.md).
- [Blank power and boot-strap measurement worksheet](../hardware/external-antenna/power-measurements.csv).
- [Coverage acceptance procedure](rf-commissioning.md) and
  [unmeasured results sheet](../hardware/external-antenna/coverage-results.csv).
- [Digital verification record](../hardware/external-antenna/validation.md).
- [Design registry](../hardware/designs.json) and [engineering history](design-history.md).

The PoE switch supplies the isolated splitter and low-voltage rails. MC2 changes
neither the battery installation nor the switch supply. The FH1 enclosure adds
individual mounts for power, UART bridge, Z-Wave and 433 MHz radio, a lid-mounted
radar and an attached ventilated environmental-sensor pod. Its exact selected
modules and unmeasured dimensions are in the [assembly inventory](../mechanical/full-hub/components.json).
The selected 102010636 was in stock at DigiKey on 20 October 2026. Use
the [prototype ordering record](pcb-order.md) and matching MC2-D firmware.

MC1 remains a [historical build](module-carrier.md). Its software checks continue
for regression coverage, but its Nano/H2 pin map, 16 MB flash layout, compact
housing and cost estimate must not be combined with MC2.

## Documentation index

This page is the topic index for `docs/`. The sections below group the build
references by the task they support instead of by the order they were written.

### Get started

- [Start here — the complete MC2-D / FH1 build journey](start-here.md): the
  ordered route with a checkpoint at each stage.
- [Project overview](overview.md) and the [Russian overview](overview.ru.md).
- [Prototype acceptance record](acceptance.md): what passed and what is still
  outstanding.
- [Current validation status](validation.md).

### Install and wire

- [Complete assembly, ZAC93 placement and pin-to-pin wiring](full-hub-assembly.md).
- [Assembly, exact parts and antenna connections](external-antennas.md).
- [Parts catalog and visual assembly reference](parts-catalog.md) and the
  [historical assembly parts gallery](parts-gallery.md).
- [MC2-D pre-fabrication purchase audit — 21 October 2026](pre-fabrication-audit.md).
- [MC2-D MG24 external-antenna image: build, program and recover](mc2-zigbee.md).
- [ESP32/C6/MG24 build and programming instructions](../firmware/external-antenna/README.md)
  and [network updating](../firmware/external-antenna/updates/README.md).

### Configure Home Assistant

- [Connecting to Home Assistant](home-assistant.md): the association and entity
  setup for the hub.
- [Matter-over-Thread devices for the first bench test](thread-devices.md): candidate
  devices, checked against official pages rather than tested here.

### Operate and commission

- [Coverage acceptance procedure](rf-commissioning.md) with the
  [unmeasured results sheet](../hardware/external-antenna/coverage-results.csv).
- [Blank power and boot-strap measurement worksheet](../hardware/external-antenna/power-measurements.csv).
- [Independent connection audit and I²C address correction](connection-audit.md).
- [Continuous integration and automated approval](ci.md) and
  [Terraform ownership](infrastructure.md).

### Manufacturing and enclosure

- [Full-hub enclosure, exploded layout and printable mounts](../mechanical/full-hub/README.md).
- [HA Radio Hub enclosure — historical DRAFT V0](enclosure.md).
- [Low-power enclosure: layout mock-up](low-power-enclosure.md) and the
  [compact minimum-energy hub](low-power.md).
- [Make the low-voltage DIY carrier with toner transfer](diy-pcb.md).
- [Draft RFQ: prototype PCBs and assembly](manufacturing-rfq.md) and
  [manufacturing and selling small batches](manufacturing.md).
- [Versioned engineering build package](releases.md): downloadable design archives.

### Reference

- [Firmware and software](firmware.md): the historical Pi design.
- [Historical build record for MC1](module-carrier.md).
- [Design registry](../hardware/designs.json) and
  [engineering history](design-history.md).
- [Exact parts, availability and priced subtotal](mc2-shopping.md) and
  [lower-cost pigtails, connector fit and RF evidence](pigtail-selection.md).
- [Classic ESP32 migration, cost and compatibility](classic-esp32-migration.md).

### Design review and results

- [Single-carrier and H2 Quartet function audit](h2-quartet-function-audit.md),
  [independent consolidation review](h2-quartet-review.md) and
  [H2 Quartet simplification](h2-simplification.md): the October 17 decision
  trail that led back to the single MC2-D carrier.

The historical MC1 drafts above are kept for provenance. Their pin maps, flash
layouts and cost estimates must not be combined with MC2-D.
