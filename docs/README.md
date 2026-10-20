# Current MC2 documentation

Updated 19 October 2026. **MC2-C** is the active 100 × 100 mm carrier with separate
external Zigbee, Thread and BLE antennas. The selected ESP32-DevKitC-VIE has 8 MB flash and 8 MB physical
PSRAM (4 MB directly addressable); its Thread radio is TinyC6[D] / TC6D-01. All components face the same side.
The project is an engineering prototype, with physical and whole-house RF
qualification still outstanding.

**New build: [Start here — the complete MC2-C / FH1 build journey](start-here.md).**
It orders parts verification, loose-board flashing, printing, wiring, first
power and Home Assistant setup, with a checkpoint at each stage and symptom-based
troubleshooting. To view the guide locally as rendered HTML, run
`python3 tools/preview.py` from the repository root and open the printed URL.

## Active build references

- [Prototype PCB order, quantity and matched revision](pcb-order.md).
- [Classic ESP32 migration, cost and compatibility](classic-esp32-migration.md).
- [Assembly, exact parts and antenna connections](external-antennas.md).
- [Visual guide with pin-to-pin lookup](../hardware/external-antenna/index.html).
- [Hardware and carrier BOM](../hardware/external-antenna/README.md),
  [RF BOM](../hardware/external-antenna/rf-bom.json),
  [schematic](../hardware/external-antenna/cad/schematic.svg) and
  [connector ledger](../hardware/external-antenna/cad/connectors.json).
- [ESP32/C6/MG24 build and programming instructions](../firmware/external-antenna/README.md)
  and [network updating](../firmware/external-antenna/updates/README.md).
- [MC2-C MG24 external-antenna image: build, program and recover](mc2-zigbee.md).
- [Full-hub enclosure, exploded layout and printable mounts](../mechanical/full-hub/README.md).
- [Complete assembly, ZAC93 placement and pin-to-pin wiring](full-hub-assembly.md).
- [Full-hub graphical wiring](../hardware/external-antenna/full-hub-wiring.svg).
- [Coverage acceptance procedure](rf-commissioning.md) and
  [unmeasured results sheet](../hardware/external-antenna/coverage-results.csv).
- [Digital verification record](../hardware/external-antenna/validation.md).
- [Design registry](../hardware/designs.json) and [engineering history](design-history.md).

The PoE switch supplies the isolated splitter and low-voltage rails. MC2 changes
neither the battery installation nor the switch supply. The FH1 enclosure adds
individual mounts for power, UART bridge, Z-Wave and 433 MHz radio, a lid-mounted
radar and an attached ventilated environmental-sensor pod. Its exact selected
modules and unmeasured dimensions are in the [assembly inventory](../mechanical/full-hub/components.json).
The current TC6D-01 was in stock at the manufacturer on 19 October 2026. Use
the [prototype ordering record](pcb-order.md) and matching MC2-C firmware.

MC1 remains a [historical build](module-carrier.md). Its software checks continue
for regression coverage, but its Nano/H2 pin map, 16 MB flash layout, compact
housing and cost estimate must not be combined with MC2.
