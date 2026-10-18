# MC1 square-layout study

**Historical study snapshot.** The selected Nano design is now implemented in [current MC1](../../index.html#pcb). Findings and build evidence below refer to the pre-implementation revision `177a547c70bba11d5f48dee0bdc8595670a4fafb`. Reproduce the old study from that Git revision; use the active firmware instructions for the new board.

This study checks a **100 × 100 mm** arrangement with XIAO MG24 horizontal at the left and WIZ850io below the vertical H2. It does not replace the active **100 × 90 mm** design. Open the [visual comparison](index.html), [same-scale drawing](comparison.svg), and [current results](result.json).

The solution also moves S3 to the right. H2's USB ports face upward; MG24's USB port faces into the space between H2 and Ethernet. WIZ's RJ45 opening points down, 2 mm beyond the carrier. All factory USB connectors are retained. Desoldering a connector removes its body, but does not shrink a module's substrate or preserve its programming connection automatically.

The main tradeoff is the H2 antenna inside the carrier outline. Its copper-free area must remain free of permanent wiring and nearby metal. The MG24 USB service envelope passes through part of this area, so a temporarily connected programming cable is not a qualified radio-operating configuration. The stock 14 × 30 mm envelope also has only 0.18 mm to the WIZ courtyard: actual shell dimensions, tolerances and vertical cable exit need a dry fit.

The square has 11.11% more area than 100 × 90 mm, while both fit the advertised 100 × 100 mm prototype size ceiling. This establishes the same size class, not an equal delivered quote. See the [JLCPCB ordering guide](https://jlcpcb.com/help/article/how-do-i-place-an-order) and [PCBWay offer](https://m.pcbway.com/activitypcb.aspx), checked 17 October 2026.

## Files

- [Candidate CAD source and evidence](cad-candidate/README.md).
- [USB and radio review](usb-rf-review.md).
- [Firmware, programming and recovery review](service-review.md).
- [Machine-readable results](result.json).

Run `python3 render.py` to regenerate the comparison and study page from the active and candidate placement ledgers. `python3 render.py --check` verifies those generated outputs.

## Independent service correction

The review found that XIAO's SAMD11 programmer needs USB VBUS. The earlier universal VBUS-blocker advice was incorrect for this circuit; its 5 V header is on VIN behind the onboard diode. The [service review](service-review.md#xiaos-programming-probe-needs-usb-vbus) records the manufacturer-netlist evidence. The active documentation and direct-solder diagram have been corrected too. This finding is independent of carrier size and does not change the runtime pin map.
