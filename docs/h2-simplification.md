# H2 Quartet: assemble finished modules, not an integrated PCB

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

**Decision, 2026-10-17:** prototype a hub from four identical, assembled **Waveshare ESP32-H2-Zero-M** boards and one assembled W5500 Ethernet module. Optimize the number of parts the builder must solder, the number of different spare modules, and the wiring. Additional firmware work is acceptable. This is an architectural experiment, **not a complete working firmware or a fabrication release**.

[Visual comparison and assembly plan](../hardware/h2-quartet/index.html) · [Block diagram](../hardware/h2-quartet/architecture.svg) · [Machine-readable assessment](../hardware/h2-quartet/assessment.json) · [Successful component build](../firmware/h2-quartet/README.md).

## The important simplification

The C0 and I0 documents describe custom board assembly. Their resistors, decoupling capacitors, crystals and support chips become the builder's assembly work. In this variant, those functions come already assembled inside development boards, an Ethernet module and power modules. Do not reproduce those circuits on another PCB.

Use a **through-hole interconnect carrier** carrying conductors and off-board connectors. The modules' factory-fitted male pins enter plated holes directly and are soldered from the underside: **no female sockets**. Extra height is accepted, but extra socket cost is not. Buy the **-M version with pre-soldered headers**. It has 4 MB flash and native USB, without a USB-to-UART transmitter competing for GPIO23. The board includes its regulator, crystal, RF matching, antenna, boot/reset controls and decoupling. Its published schematic exposes the GPIOs needed below. [Manufacturer documentation](https://docs.waveshare.com/ESP32-H2-Zero), [schematic](https://files.waveshare.com/wiki/ESP32-H2-Zero/ESP32-H2-Zero-Schematic.pdf).

This approach also reduces manual assembly if a later experiment retains an S3. The reduction in soldering comes primarily from **finished modules**; using the same H2 board additionally standardizes spares and programming.

## Proposed hardware

- **A — gateway H2:** W5500 Ethernet, the host software, and CC1101 RF control/timing. One shared hardware SPI bus serves W5500, CC1101 and the peripheral H2, each with a separate chip-select. Two native UARTs connect the two radio H2 boards.
- **B — radio H2:** Thread RCP in the first software layout. Its radio is independent of A's Bluetooth.
- **C — radio H2:** Zigbee ZBOSS NCP, with a separate TCP endpoint forwarded by A to one Zigbee2MQTT client.
- **D — peripheral H2:** hardware SPI slave upstream, one UART for LD2450, one UART for Zooz ZAC93, and I²C for BME680. Its 2.4 GHz radio is off. It can parse radar reports locally and buffer Z-Wave serial traffic.

The fourth H2 avoids an SC16IS752, its external oscillator/support circuit, and the main controller's shortage of native UARTs. A fourth board connected upstream through UART would consume one of the UARTs we want to use; **SPI slave is the deliberate choice**. D cannot simultaneously be a hardware SPI slave and an independent hardware SPI master on H2's sole general-purpose SPI controller, so CC1101 stays on A.

Retain the existing ready-made CC1101, ZAC93, LD2450 and BME680 boards. H2 does not replace the sub-GHz RF front ends in CC1101 or ZAC93. There is **one external Ethernet/PoE cable, one W5500, no internal Ethernet switch, no Orange Pi, no MG24 daughterboard and no SC16** in this target.

## Finished-module shopping scope

1. Four **ESP32-H2-Zero-M**, same revision, 4 MB flash, pre-soldered headers.
2. One finished **WIZ850io** or equivalently documented W5500 module with its RJ45/magnetics, clock and decoupling assembled. Prefer the already specified WIZ850io to an unidentified breakout. WIZ850io uses 3.3 V; it is not a PoE power extractor.
3. One **assembled, isolated, active 802.3af/at PoE splitter with regulated 5 V output**, rated for the measured full load. This is a procurement requirement; no new splitter SKU has been electrically qualified here. The existing fitted Silvertel evaluation assembly can serve for bench work. Do not buy an empty evaluation PCB or a passive splitter as its replacement.
4. A finished 5 V-to-3.3 V converter, such as the existing D24V22F3 assembly, for the 3.3 V peripheral rail; fused power distribution, short labeled off-board harnesses and mounting hardware. No board-to-carrier sockets.
5. Existing CC1101, ZAC93, LD2450 and BME680 assemblies.

At the user's **$5 per H2 assumption**, the four controllers cost **$20 before shipping/tax**. This is not a quote for the whole hub. Ethernet, power, peripherals and interconnect are additional. Do not derive a wattage or a total cost saving from that subtotal.

The target is **no hand-soldered fine-pitch ICs or decoupling-capacitor array**. A small number of harness-level parts may remain: the existing 4.7 kΩ CC1101 GDO0 pull-up, chip-select idle pull-ups if absent on the selected modules, a fuse and possibly bulk capacitance justified by measurement. Factory-fitted capacitors are not counted as manual assembly. The final loose-part count is pending the exact splitter and breakout revisions.

For comparison, the committed assembly BOMs contain **17 capacitors + 17 resistors on C0**, **3 capacitors + 1 resistor on M0**, and **44 capacitors + 35 resistors on I0**. C0+M0 and I0 are alternatives, not additive purchases. The goal is to remove these *manual assembly tasks*, not to claim the finished modules contain fewer total electronic components.

### The new carrier is an interconnect, not another integrated hub PCB

Solder the four H2 boards' factory male pins directly through matching plated holes in the carrier. Do not add female sockets and do not solder the modules by their castellated side pads. Replacement will require desoldering; the user accepts this tradeoff for inexpensive boards.

Apply the same approach to the Ethernet and power modules where their manufacturer-defined headers permit it. Use keyed connectors or terminal blocks for off-board power and sensors. Place module antenna ends over the carrier edge or its verified copper-free regions; the extra vertical height does not remove antenna keepout requirements. Retain access to native USB and BOOT/RESET.

Header pitch alone does not define a footprint: row spacing, orientation, pin numbering, protruding USB/RJ45 connectors and underside components must be measured from the exact boards. WIZ850io uses two 1×6 headers at 2.54 mm pitch; row spacing still needs its revision-specific drawing. This report does **not** release carrier Gerbers. Freeze those footprints after a physical fit check; the existing C0/I0 Gerbers do not match these modules. [WIZnet documentation](https://docs.wiznet.io/Product/ioModule/WIZ850io).

## Power and physical assembly

For the first modular prototype, feed the four H2 boards through their documented **5 V inputs and onboard regulators**. Supply LD2450 at 5 V. Use the separate assembled 3.3 V converter for WIZ850io, CC1101, ZAC93 and the specified BME680 breakout, with a common secondary ground. Do not parallel the four boards' 3.3 V regulator outputs. This deliberately favors straightforward assembly over a speculative efficiency improvement.

The Zero schematic connects USB VBUS and its 5 V input: disconnect that board's external power before USB-powered programming, or use a verified data-only/service arrangement. Do not join the computer's USB 5 V to the splitter output. A later common-3.3 V optimization requires checking regulator reverse-current behavior and every USB path first.

Keep SPI inside the enclosure with short ground-referenced harnesses; an initial routing target is at most about 10 cm per branch, not a guaranteed electrical limit. Put radio antennas at the enclosure perimeter and verify concurrent operation. Keep the BME680 in its ventilated external pod. A mounting layout, connector orientation and signal-integrity check are still required before cutting final harnesses.

## Candidate GPIO allocation

**These are GPIO labels, not physical connector-pin numbers.** They are based on the Zero-M schematic and are not instructions for a generic H2 clone. The schematic's P8 numbers must not be interpreted as a single physical 18-pin row.

Gateway A uses all 14 exposed non-strapping GPIO:

| Connection | Gateway GPIO |
| --- | --- |
| Shared SPI clock / MOSI / MISO | 4 / 5 / 0 |
| W5500 CS / interrupt | 1 / 10 |
| CC1101 CS | 13 |
| CC1101 GDO0 transmit / GDO2 receive | 2 / 3 |
| Peripheral D CS / READY input | 14 / 11 |
| Radio B UART TX / RX | 24 / 23 |
| Zigbee C UART TX / RX | 12 / 22 |

No harness function uses GPIO8 (RGB LED), GPIO9 (BOOT), GPIO25 (strap), or GPIO26/27 (native USB). No LED removal or USB-UART isolation is required on the selected Zero-M board. The two-wire Zigbee link is **115200 8N1 without RTS/CTS**, matching the selected firmware's configurable serial transport. Buffer overflow must be detected and reported; this differs from the original MG24 flow-control contract.

Peripheral D allocation:

| Connection | Peripheral GPIO |
| --- | --- |
| SPI slave clock / MOSI / MISO / CS | 4 / 5 / 0 / 1 |
| READY output | 10 |
| LD2450 UART TX / RX | 24 / 23 |
| ZAC93 UART TX / RX | 12 / 22 |
| BME680 SDA / SCL | 2 / 3 |

D has GPIO11/13/14 available. Remote reset control is optional and only usable if the selected remote module exposes its reset input. The Zero-M main header does not expose EN as a normal header pin; the first prototype therefore retains local RESET/BOOT buttons and native USB service. Do not add fine-pitch reset wiring merely to claim fully automatic recovery.

H2 provides two hardware UARTs, one general-purpose SPI controller and two transmit/two receive RMT channels. UART GPIO routing is configurable. The candidate preserves one RMT transmit and one receive channel for RF Airbridge. [H2 datasheet](https://documentation.espressif.com/esp32-h2_datasheet_en.html).

## What was actually built

A minimal **H2 + W5500 + ESPHome active Bluetooth proxy with three connections** compiled successfully with ESPHome 2026.9.1 and ESP-IDF 5.5.5. The linker reports **106,302 / 258,000 bytes of static RAM (41.2%)**; the application binary is **1,061,120 bytes**. The denominator is the linker's available static region, not a new claim about total chip SRAM. Runtime heap, packet buffers and stack peaks have not been measured.

This probe intentionally excludes Thread, Zigbee, RF, sensors, API encryption and the OTA service. Its GPIOs are compilation placeholders and **differ from the candidate harness map**. The successful build proves that Ethernet and active BLE can coexist in a software build for H2; it does not prove that the full hub fits or that the board works. Exact config and hashes are preserved in [the build evidence](../firmware/h2-quartet/README.md).

## Thread: the real software work

The public ESP-IDF 5.5.5 build links a target-specific `libopenthread_br.a`. Its published library set has **no H2 target**. Our current S3 integration also explicitly depends on PSRAM and S3-specific assignments. Changing `board:` to H2 is not sufficient. [Build rule](https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/CMakeLists.txt), [pinned library tree](https://github.com/espressif/esp-thread-lib/tree/33209823e559560f54dcd41cbf3dbdd27f46d569).

OpenThread itself is open source. The missing integration includes IPv6 routing, ICMPv6/neighbor discovery, multicast, MeshCoP discovery and service-discovery/SRP forwarding; some builds also add upstream DNS and NAT64. W5500 must be driven as a raw Ethernet interface into the network stack, not through its IPv4 hardware sockets.

Two software layouts fit this modular concept:

1. **Protocol-reuse layout:** A runs Ethernet, BLE and the Thread host/BR; B runs standard Thread RCP. This reuses ESPHome BLE, Spinel and ZBOSS interfaces but concentrates memory on A. Moving only the radio to B does not move the Thread host's RAM there.
2. **Distributed layout:** A runs native Thread and Ethernet/BR; B runs the full BLE proxy. A forwards B's API stream over a framed UART connection. This follows the user's proposal and distributes memory, but requires a real stream/socket transport, connection lifecycle, backpressure and service flashing. HCI alone leaves the BLE host on A, so it does not achieve the same memory split.

Both remain experiments. For a fully open BR implementation, evaluate **Zephyr's OpenThread border-router sample** before writing platform glue from scratch. Zephyr supports an H2 board and W5500 separately, and has an open BR implementation with a REST overlay. However, its tested ESP border-router overlay targets S3 and uses PSRAM; H2 needs its own configuration, device-tree overlay and memory proof. Switching to Zephyr does not automatically retain ESPHome's BLE API. [H2 board](https://docs.zephyrproject.org/latest/boards/espressif/esp32h2_devkitm/doc/index.html), [W5500 binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/ethernet/wiznet,w5500.html), [BR source/sample](https://github.com/zephyrproject-rtos/zephyr/tree/main/samples/net/openthread/border_router).

Running OTBR on the existing HA server with a remote RCP is a possible bench fallback, but changes the local-BR requirement. HA's own app documentation warns about TCP-RCP timing and stale routes after failure. It is not silently substituted for the local design. [Official app documentation](https://github.com/home-assistant/addons/blob/master/openthread_border_router/DOCS.md).

## Zigbee: avoid hiding the migration cost

`tostmann/esp-coordinator` supports H2 from v1.5.0; version.txt read during this review was 1.5.77. Its author reports H2 hardware pairing and restart-persistence tests. We did not repeat those tests. It uses the ZBOSS NCP protocol and the older Espressif/ZBOSS SDK line; upgrading to the newer, different Zigbee stack is not automatic. [Firmware](https://github.com/tostmann/esp-coordinator).

Stock Zigbee2MQTT labels ZBOSS experimental and lacks its normal backup/restore, install-code and Inter-PAN features. The author's fork adds NVRAM recovery, at the cost of another maintained software dependency. Test restoring an erased spare H2 before migrating the real network. The custom ZHA adapter currently warns of an incompatibility with HA 2026.7+; do not downgrade production HA dependencies to force it. Keep the existing coordinator available until this is resolved or a Zigbee2MQTT migration is deliberately chosen. [Z2M support](https://www.zigbee2mqtt.io/guide/adapters/zboss.html), [custom ZHA warning](https://github.com/tostmann/zha-zboss-esp).

## Peripheral transport and implementation order

D is a programmable peripheral processor, not a transparent wire. Use a versioned frame header, boot/session epoch, channel, sequence number, bounded payload length, integrity check and per-channel queue credits. Queue a DMA-compatible SPI transaction before asserting READY. Apply backpressure; explicitly fault the Z-Wave channel after unrecoverable byte loss. Coalesce old radar states instead of delaying control traffic. RF actuation remains on A and must not be replayed after uncertain resets.

At 256000 and 115200 baud with 8N1, the two UARTs can produce at most **37,120 bytes/s in one direction combined** before protocol framing. A proposed 4 MHz SPI link has 500,000 raw bytes/s per direction; that is only a sizing check, not an achieved throughput. W5500 and CC1101 share arbitration. Bound each transfer and measure worst-case latency, not just average throughput. [H2 SPI slave requirements](https://docs.espressif.com/projects/esp-idf/en/stable/esp32h2/api-reference/peripherals/spi_slave.html).

Implement in this order:

1. Assemble only a gateway H2 and W5500; verify supply, Ethernet and the already compiled BLE probe on hardware. Add API encryption/OTA and record runtime heap before expanding scope.
2. Prove a **local H2 BR** with Ethernet, IPv6 routing, discovery, REST compatibility and reboot recovery. Select the protocol-reuse or distributed layout from real memory measurements.
3. Add D's SPI transport, both UARTs and BME680; test overflow, stale sessions and independent resets.
4. Add the second radio as Zigbee NCP on an isolated test network; test backup/recovery on a spare board.
5. Integrate existing RF behavior, active BLE connections, concurrent radio traffic, power loss and Ethernet loss. Measure peak/average power at the actual PoE port.
6. Freeze the harness and mounting layout only after those gates. No integrated PCB or enclosure based on guessed fit is needed for these experiments.

**Result:** a concrete, connector-based four-H2 hardware target with a successful Ethernet/BLE component build, a feasible GPIO ledger and an explicit software work plan. Full local Thread BR operation, total power, radio coexistence and complete firmware remain unverified.
