# MC2 — three external 2.4 GHz antennas

The current engineering prototype uses an ESP32-S3-DevKitC-1U-N8R8 host, a TinyC6-U-01 Thread RCP, and a XIAO MG24 Zigbee NCP. Each radio has its own external antenna. The previous MC1 Nano remains historical and is not pin compatible.

- [Visual assembly and antenna guide](index.html)
- [Exact shopping list and AliExpress checks](../../docs/mc2-shopping.md)
- [Generated appearance concepts and provenance](images/README.md)
- [Editable carrier, exact pinout, assembly and checks](cad/README.md)
- [Front assembly drawing](cad/assembly-top.svg)
- [Schematic](cad/schematic.svg), [PDF](cad/schematic.pdf)
- [PCB copper front](cad/board-top.svg), [back](cad/board-bottom.svg)
- [Controller/peripheral BOM](cad/BOM.csv), [RF parts](rf-bom.json)
- [Net wiring](wiring.json), [physical connector coordinates](cad/connectors.json)

This is a routed design package, not a claim of measured RF coverage or approved hardware. Verify TinyC6 supply before ordering parts: the selected original U.FL SKU was on backorder when checked. Fit and RF acceptance must be completed on the physical assembly.
