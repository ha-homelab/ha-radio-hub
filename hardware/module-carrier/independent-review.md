# MC1 independent integration review

Reviewed 17 October 2026. Scope: carrier design/pin ledger versus manufacturer sources and the actual firmware contract, antenna geometry, WK2132 forwarding, and public presentation claims. The review was independent of the carrier generator; the reviewer authored the XIAO firmware adaptation, so this is not a separate audit of that firmware's implementation.

## Confirmed electrical interface

- XIAO **U3.7 / D6 / PC06 / TX** reaches **S3 GPIO18 / RX**; **U3.8 / D7 / PC07 / RX** reaches **GPIO17 / TX**.
- XIAO **U3.5 / D4 / PC04 / CTS** reaches **S3 GPIO16 / RTS**; **U3.6 / D5 / PC05 / RTS** reaches **GPIO21 / CTS**. NCP and bootloader both use **115200 8N1 hardware RTS/CTS**.
- **U3.1 / D0 / PC00** reaches **J8.1**; **J8.2** is ground. The local recovery jumper remains open normally and does not consume an S3 GPIO. The onboard XIAO reset button and USB CMSIS-DAP service path remain available.
- **U3.14** receives the diode-isolated 5 V branch, **U3.13** is ground, and **U3.12 / 3V3 output** is unconnected. The XIAO, H2 and S3 regulator outputs are not paralleled with the peripheral 3.3 V supply. D3 cathode faces the XIAO branch, as required by [Seeed's external-power guidance](https://wiki.seeedstudio.com/xiao_mg24_getting_started/#hardware-overview).
- These are schematic/pin-ledger checks, not measured voltage, isolation or continuity results. Supply diodes do not isolate signal pins: avoid USB-powering one controller while its connected peers are unpowered. Follow the complete carrier's powered-service/VBUS-blocking procedure.

## Antenna issue found and corrected in the design source

The initial XIAO placement was described as an antenna overhang. That was inaccurate: at U3 anchor **(143,18), rotation 180°**, its PCB tip extends only **0.034 mm** beyond the carrier edge. The original 1.2 mm strip also did not cover the entire antenna body.

The [Seeed native board](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip) places the inner D0 hole at **(116.0177,65.256)** and ANT1 center at **(98.9838,76.5556)**. Transforming through the carrier footprint places the ceramic body at **x=129.1004–134.3004 mm, y=−0.0339–1.9661 mm**. The interim **x=130–141 mm** keepout still missed part of it; this was reported to the hardware author. The corrected generator now uses **x=128.8–141 mm, y=0–5 mm**, with copper, tracks and vias excluded on both layers. The source rectangle was checked after this correction. This covers the projected ceramic body with a margin between the header rows; it is not a manufacturer-qualified host-board RF clearance.

Firmware selects this ceramic antenna with **PB04 low and PB05 high** before stack startup. Final RF range/coexistence, enclosure clearance and antenna detuning require measurements.

## WK2132 forwarding review

The current implementation retains the Z-Wave proxy interface and uses a dedicated worker. Source review found handling for 256-byte hardware-FIFO count wrap, bounded 64-byte I2C transfers, TX free-space limits, queued writes, UART errors and configuration loss. An ambiguous failed FIFO write is not replayed; faults disconnect the stream rather than reporting successful delivery. Flush completion accounts for queued data and wire idle state. The obsolete application-loop description was reported and corrected in the firmware README.

No new concrete transport defect was found in that review. The nominal **2 ms** polling interval is not a worst-case bound: the hardware RX FIFO holds approximately **22.22 ms** of continuous 115200-8N1 traffic. Tests of the software transport do not establish scheduler latency, I2C electrical integrity or reliable simultaneous radio operation. A detected fault requires a hub restart, as documented.

## Claim and presentation review

`docs/module-carrier.md` correctly frames the seven function groups as requirements/contracts and separates them from bench qualification. It does not establish completed migration, equal RF performance, guaranteed lower power or zero engineering effort. The ambiguous USB-service wording identified during review was corrected: later USB service uses the normally powered complete carrier and a verified VBUS-blocking data cable; disconnecting PoE alone does not isolate controllers.

The earlier H2 visual inventory remains a historical planning snapshot; its proposed actions are not evidence that the final MC1 migration was applied. The final MC1 migration manifest, not that older inventory, should identify current and archived visual entrypoints.

## Final native-CAD inspection

An independent parser compared **145 native PCB pad entries** with the carrier ledger; every assigned net matched. The corrected XIAO all-layer rule area is present in the final native board. The exported KiCad 10.0.6 reports show **zero ERC violations, zero DRC violations, zero unconnected items and zero schematic-parity issues**. These reports were inspected, not independently regenerated by this reviewer. The evidence hashes match the final files:

- PCB: `4f1212c357125ec8af6b329a3761bcc34dcf14eb5bff9f75ebb48233c33307a0`.
- Schematic: `0d3b6aa1c8d2a7f7fd4460c0119052c7ba7d5cc6e864dd6b67d66e7716c53af1`.

Native top and bottom copper exports, the full A3 schematic and the assembly view were opened in Chrome. The four mounted modules, direct through-hole connections, antenna-edge copper exclusions and local recovery header agree with the design reviewed above. The schematic is a module-interconnection drawing; its generic terminals do not prove the electrical behavior inside the vendor modules.

None of these software, geometric or visual checks establishes physical fit, solderability, power margin, USB backpower isolation or RF performance. MC1 remains an engineering prototype, not a fabrication release.

## Final presentation inspection

The page's architecture, assembly explanation and wiring filter were exercised in Chrome before the final image insertion; filtering for `U3.` returned the expected **7 of 33 nets**. Final HTML was then inspected as source, without competing with the primary reviewer's final browser session. It includes the actual assembly SVG, native top/bottom renders, a separately labeled generated concept and populated verification results. All **seven image paths** and all verification-evidence paths resolve to local files. The native-render image and source-PCB hashes match their provenance manifest.

Both final native PNG renders and the generated concept were visually inspected. The concept conveys the four mounted modules and direct male-header assembly, but its connector geometry is approximate: for example, its RADAR header has two visible pins rather than the required four, and an extra unlabeled header is illustrated. Its caption and provenance correctly exclude it as a pin map or fit reference; use the native CAD, assembly SVG and connector manifest for construction. No claim of pin-for-pin visual accuracy is made for that image.

The final verification summary explicitly records `hardware_tested: false` and separates software/CAD evidence from commissioning. No additional material protocol or carrier-net discrepancy was found in this review.
