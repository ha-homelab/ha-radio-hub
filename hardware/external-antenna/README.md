# MC2-C — three external 2.4 GHz antennas

The current engineering prototype uses an ESP32-DevKitC-VIE (WROVER-IE, 8 MB flash / 8 MB quad PSRAM) host, a TinyC6[D] / TC6D-01 Thread RCP, and a XIAO MG24 Zigbee NCP. Each radio has its own external antenna. The previous MC1 Nano and MC2-A S3 remain historical and are not pin or binary compatible. All 21 application signals remain; R4/R5 constrain the classic ESP32 boot straps. Bluetooth uses legacy BLE4.2 advertising and connections, not BLE5 extended advertisements or Coded PHY.

- [Visual assembly and antenna guide](index.html)
- [Full device assembly and ZAC93 pin map](../../docs/full-hub-assembly.md)
- [Exploded enclosure, all component mounts and print files](../../mechanical/full-hub/README.md)
- [Full-hub wiring drawing](full-hub-wiring.svg)
- [Exact shopping list and AliExpress checks](../../docs/mc2-shopping.md)
- [Historical MC2-A appearance concepts and provenance](images/README.md)
- [Editable carrier, exact pinout, assembly and checks](cad/README.md)
- [Front assembly drawing](cad/assembly-top.svg)
- [Schematic](cad/schematic.svg), [PDF](cad/schematic.pdf)
- [PCB copper front](cad/board-top.svg), [back](cad/board-bottom.svg)
- [Controller/peripheral BOM](cad/BOM.csv), [RF parts](rf-bom.json)
- [Net wiring](wiring.json), [physical connector coordinates](cad/connectors.json)

This is a routed design package, not a claim of measured RF coverage or approved hardware. The MC2-C selection replaces the obsolete original TinyC6 with the available TC6D-01 and matching antenna-switch firmware. See the [prototype ordering record](../../docs/pcb-order.md). Fit and RF acceptance must be completed on the physical assembly.
