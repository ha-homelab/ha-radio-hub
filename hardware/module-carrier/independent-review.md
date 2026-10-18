# MC1 independent integration review

Reviewed 17 October 2026 (final CAD evidence dated 18 October UTC). Current scope: **compact-100x90-right-edge**, replacing the former 160 × 100 mm placement. This review checks native carrier geometry and pin assignments independently of the generator, retained firmware contracts, and the current visual guide. The reviewer authored the XIAO firmware adaptation, so this is not an independent audit of that firmware's implementation. No assembled hardware was tested.

## Confirmed electrical interface

- XIAO **U3.7 / D6 / PC06 / TX** reaches **S3 GPIO18 / RX**; **U3.8 / D7 / PC07 / RX** reaches **GPIO17 / TX**.
- XIAO **U3.5 / D4 / PC04 / CTS** reaches **S3 GPIO16 / RTS**; **U3.6 / D5 / PC05 / RTS** reaches **GPIO21 / CTS**. NCP and bootloader both use **115200 8N1 hardware RTS/CTS**.
- **U3.1 / D0 / PC00** reaches **J8.1**; **J8.2** is ground. The normally open local recovery jumper does not consume an S3 GPIO. The onboard reset button and USB CMSIS-DAP service path remain available.
- **U3.14** receives diode-isolated 5 V, **U3.13** is ground, and **U3.12 / 3V3 output** is unconnected. The XIAO, H2 and S3 regulator outputs are not paralleled with the peripheral 3.3 V supply. D3's cathode faces XIAO, consistent with [Seeed's external-power guidance](https://wiki.seeedstudio.com/xiao_mg24_getting_started/#hardware-overview).
- Supply diodes do not isolate signal pins. **Correction from the square-layout service review:** the earlier blanket USB VBUS-blocker recommendation was wrong for XIAO. Its SAMD11 regulator U10 is supplied and enabled by USB VBUS; the header powers VIN behind onboard D1, so header power with VBUS blocked does not provide the probe's intended supply. XIAO service requires USB VBUS with the complete carrier normally powered, after checking the actual diode-isolated rails, backfeed and enumeration. Do not USB-power XIAO alone while its connected peers are unpowered. Qualify S3/H2 service against their own port circuits. The [service review](studies/square-layout/service-review.md#xiaos-programming-probe-needs-usb-vbus) records the official-netlist evidence; this reviewer independently confirmed the U4.14, D1, U10 and SAMD11 supply connections.

The compact layout preserves all **145 carrier pad assignments**, the four mounted modules, eight harness/service headers, three diodes and two resistors. It does not change firmware pin assignments or application protocols. These are native-net and source checks, not measured continuity, voltage or isolation results.

## Compact placement and practical access

The selected carrier is **100 × 90 mm, two layers**, with all parts on top and factory male module pins soldered from below. The 100 × 80 mm candidate would have placed the axial parts underneath the permanently mounted S3 and restricted mounting. The extra 10 mm preserves single-side component placement and access without adding sockets or small surface-mount parts.

Final module origins/rotations are U1 S3 **(5,3), 0°**; U2 H2 **(64,84), 180°**; U3 XIAO **(97,18), 180°**; and U4 WIZ850io **(92.9,67), 270°**. Harnesses occupy the two aisles between modules. Three **2.7 mm** mounting holes at **(35,13), (35,72), (70.7,61)** accommodate nylon M2.5 supports with bodies no larger than **5 mm**.

An independent native-PCB parser found no overlaps between the declared mating housings, USB service envelopes, support bodies and other component courtyards. Relevant minimum margins are:

- J4's reserved mating housing to D1 courtyard: **0.65 mm**.
- J3's reserved mating housing to H2 courtyard: **2.18 mm**.
- J2's reserved mating housing to XIAO courtyard: **0.272 mm diagonally**; clearance to the actual board outline is approximately **0.97 mm**. This is a tight fit, not permission to substitute a bulky housing.
- XIAO's USB service envelope to the axial parts: **1.729 mm**.
- Axial-part courtyards to WIZ850io courtyard: **2.19 mm**.

The drawing assumes **5.5 mm-wide narrow mating housings** and **30 mm axial USB service envelopes**. Wires must leave the headers upward and bend above the modules; flat right-angle harnesses and arbitrary connector shells are not covered. XIAO's USB end is about **44.74 mm** from the WIZ board, but the intervening axial parts limit low-level cable routing. Actual USB shells, wire bend height, underside module components, pin fit and solder access require a dry fit. Review moved the axial bank 1 mm right and relocated two supports to eliminate earlier housing and USB-envelope conflicts.

## RJ45 opening

The [WIZnet dimension drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png) and [pin map](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png) put the opening toward local negative Y. In the current native placement it faces **right / positive X**, at **x=102 mm**, spanning **y=69.11–85.21 mm**: **2 mm beyond the carrier edge**. The module PCB remains at **x=74.3–99.3, y=65.66–88.66 mm**, with all factory header holes on the carrier.

The reserved plug/latch corridor is **x=99.3–139, y=63–90 mm**. It is an engineering allowance, not a manufacturer-specified universal boot or bend envelope. The enclosure cutout and support under insertion loads require physical verification. The carrier's 100 × 90 mm outline is not an enclosure dimension: the jack and antennas extend beyond it, before cables or external modules are included.

## Antenna geometry

All five declared copper/track/via exclusion regions are present in the native PCB. The [Seeed native board](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip) places XIAO's ceramic body, after the current transform, at **x=83.1004–88.3004, y=−0.0339–1.9661 mm**. The **x=82.8–95, y=0–5 mm** carrier exclusion covers its projection. XIAO's PCB tip barely overhangs the carrier; it must not be described as having its whole antenna outside the carrier. Firmware selects the ceramic antenna with **PB04 low / PB05 high**.

The opposed H2 orientation places its antenna at the bottom. Its projected antenna outline is approximately **x=45.97–59.17, y=85.575–90.975 mm**; WIZ's PCB begins **15.13 mm** to its right. Top and bottom edge exclusions also cover the antenna projections of the development boards. These are geometric provisions, not a manufacturer's qualification of the assembled host board or enclosure.

Compared with the previous placement, approximate antenna-center separations change from **42 to 97 mm** for S3–H2, **34 to 93 mm** for H2–XIAO, and **76 to 69 mm** for S3–XIAO. Opposing H2 increases two separations, but does not prove equal range, immunity or coexistence. Follow the [H2 antenna layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html), keep enclosure metal and harnesses away, and measure simultaneous radio performance.

## WK2132 and integration claims

The retained Z-Wave forwarding implementation uses a dedicated worker. Source review found handling for 256-byte FIFO count wrap, bounded 64-byte I2C transfers, TX free space, queued writes, UART errors and configuration loss. Ambiguous failed FIFO writes are not replayed; faults disconnect the stream. Flush completion accounts for both queued data and wire idle. No new concrete transport defect was found in this review.

The nominal **2 ms** polling interval is not a worst-case scheduling guarantee: the RX FIFO holds approximately **22.22 ms** of continuous 115200-8N1 traffic. Software tests do not establish physical I2C integrity, scheduling latency or reliable simultaneous radio activity. A detected fault requires the documented hub restart.

`docs/module-carrier.md` correctly distinguishes retained functions, compiled software and physical qualification. Ember/EZSP keeps the ZHA/Zigbee2MQTT integration path, subject to supported firmware versions and actual commissioning; successful pairing, migration and backup restoration are not established by compilation. No material protocol or native-net discrepancy was found. Lower total power, lower delivered cost and equal RF performance remain unmeasured.

## Final native and visual evidence

The independent parser matched **145 native pad entries**, net assignments and positions to the ledger. All **100 module pads** are **1.80 mm copper / 1.10 mm drill**, giving a nominal **0.35 mm annular ring**. This preserves hole centers and improves routing clearance between adjacent 2.54 mm pads; manufacturing tolerances and actual male-pin fit still require checking. The **12 mechanical/pin/project-rule tests passed**. Exported KiCad 10.0.6 reports show **zero ERC violations, zero DRC violations, zero unconnected items and zero schematic-parity issues**. This reviewer inspected those reports; the hardware author separately reproduced them from a clean temporary source copy, recorded in `cad/checks/reproduction.json`.

All eleven hashes in `cad/verification.json` match the reviewed files, including `mc1.kicad_pro`. The final root review caught native-board saving resetting project rules. The shared restore helper now preserves the Default class (0.25 mm track), Power class (0.8 mm track), 0.2 mm clearance, 0.8/0.4 mm vias and all six power-net assignments after native writes. The actual saved project and new regression test were checked; the helper changes no severity or exclusion settings. Fresh native and clean-reproduction checks remain zero, and the PCB bytes are unchanged. Final PCB SHA-256:

`bed9b495f92728f6f0cc000be6d5a8b31b15fdbefcee779d9cb0fd12e771e165`

The current assembly PNG and both native PCB renders were visually inspected. Their provenance hashes match this PCB; HTML image references resolve and show the current compact placement. The generated compact concept was rejected because it invents antenna bodies, omits USB ports and misrepresents connector geometry and RJ45 projection. It is retained only in explicitly rejected history and is absent from the current guide. Use the dimensioned assembly SVG, native CAD and connector ledger for construction; the native board renders do not depict the complete mounted assembly.

The guide's verification summary records `hardware_tested: false`. No fit, thermal, power, USB-backfeed, radio-coexistence or network-migration bench test was performed by this review. MC1 remains an engineering prototype, not a fabrication release.
