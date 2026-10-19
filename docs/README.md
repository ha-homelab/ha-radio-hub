# Current MC2 documentation

Updated 18 October 2026. **MC2-B** is the active 100 × 100 mm carrier with separate
external Zigbee, Thread and BLE antennas. The selected ESP32-DevKitC-VIE has 8 MB flash and 8 MB physical
PSRAM (4 MB directly addressable); its Thread radio is TinyC6-U-01. All components face the same side.
The project is an engineering prototype, with physical and whole-house RF
qualification still outstanding.

- [Classic ESP32 migration, cost and compatibility](classic-esp32-migration.md).
- [Assembly, exact parts and antenna connections](external-antennas.md).
- [Visual guide with pin-to-pin lookup](../hardware/external-antenna/index.html).
- [Hardware and carrier BOM](../hardware/external-antenna/README.md),
  [RF BOM](../hardware/external-antenna/rf-bom.json),
  [schematic](../hardware/external-antenna/cad/schematic.svg) and
  [connector ledger](../hardware/external-antenna/cad/connectors.json).
- [ESP32/C6/MG24 build and programming instructions](../firmware/external-antenna/README.md)
  and [network updating](../firmware/external-antenna/updates/README.md).
- [Carrier-only printed enclosure and fit coupon](../mechanical/module-carrier/external-antenna-prototype/README.md).
- [Coverage acceptance procedure](rf-commissioning.md) and
  [unmeasured results sheet](../hardware/external-antenna/coverage-results.csv).
- [Digital verification record](../hardware/external-antenna/validation.md).
- [Design registry](../hardware/designs.json) and [engineering history](design-history.md).

The PoE switch supplies the existing splitter and low-voltage rails. MC2 changes
neither the battery installation nor the switch supply. Off-board power, UART
bridge, Z-Wave, 433 MHz radio and sensors still require separate accommodation.
TinyC6-U-01 was a backorder/on-request part when checked; verify availability of
the exact external-antenna SKU before ordering the carrier.

MC1 remains a [historical build](module-carrier.md). Its software checks continue
for regression coverage, but its Nano/H2 pin map, 16 MB flash layout, compact
housing and cost estimate must not be combined with MC2.
