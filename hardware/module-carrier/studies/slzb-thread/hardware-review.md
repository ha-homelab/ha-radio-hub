# SMLIGHT SLZB hardware and Thread review

Reviewed 17 October 2026. “ZLB” is interpreted as SMLIGHT **SLZB**. This is a read-only comparison; no active PCB, deployment firmware or hardware was changed.

**The current SLZB-MRxU validates our overall architecture: an ESP32-S3 host, W5500 Ethernet and two independent 802.15.4 radios.** It does not demonstrate that one inexpensive radio can replace the host plus simultaneous Zigbee and Thread radios. The commercial advantage is integration into a finished board, with power, antennas, enclosure and maintenance firmware already assembled. The closest homogeneous-radio reference is **MR5U: S3 + W5500 + two EFR32MG24**. [Current MR5U hardware](https://smlight.tech/products/slzb-mr5u).

A purchased **SLZB-Ultima with appropriate add-ons** could replace much of our assembled hardware, but the reviewed sources do not establish an out-of-box replacement for our complete combination of local Thread border routing, active BLE connections, Zigbee, Z-Wave, CC1101, LD2450 and BME680.

## Model and generation distinctions

The suffix matters. Older non-U products and current U products must not be mixed in a BOM or capability statement.

- **SLZB-06:** CC2652P radio; **06M:** EFR32MG21; **06P7:** CC2652P7. The classic generation uses an ESP32 host, LAN8720 Ethernet and a USB-UART bridge. An official 06M specification identifies ESP32-D0WD-V3, LAN8720 and CP2102N. These are single-radio products: normal operation selects Zigbee or Thread. [06M hardware](https://smlight.tech/zz/slzb-06m), [radio-model matrix](https://smlight.tech/manual/slzb-06/guide/slzb-models-overview).
- **Original MR1/MR2/MR3:** two radios. MR1 pairs CC2652P7 with MG21; MR2 pairs CC2652P with MG21; MR3 pairs CC2674P10 with MG24. The original MR3 documentation describes ESP32, LAN8720 and CP2102. [Original MR1](https://smlight.tech/product/slzb-mr1), [original MR3](https://smlight.tech/product/slzb-mr3), [series matrix](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/slzb-series-overview).
- **06xU:** ESP32-S3 + W5500, one radio. Options include 06U/CC2652P, 06P7U/CC2652P7, 06P10U/CC2674P10, 06MU/MG21, 06Mg24U/MG24 and 06Mg26U/MG26. They still have one Zigbee/Thread radio, not two. [Current 06xU](https://smlight.tech/products/slzb-06xu).
- **MRxU:** ESP32-S3 + W5500, two radios. Pairings are MR1U: P7 + MG21; MR2U: P + MG21; MR3U: P10 + MG24; MR4U: P10 + MG26; MR5U: MG24 + MG24. Separate chips permit concurrent Zigbee and Thread; two advertised protocols on one chip do not imply equivalent simultaneous operation. [Current MRxU](https://smlight.tech/products/slzb-mrxu).

The vendor's “triple/quadruple radio” marketing counts Wi-Fi and Bluetooth capabilities too. For comparison with our BOM, count physical host and 802.15.4 SoCs explicitly.

## Memory and network architecture

The U generation adds **2 MB PSRAM**. Its official ESPHome repository identifies an ESP32-S3R2/Quad-PSRAM design and describes **16 MB flash** for 06xU, MRxU and Ultima. This is useful evidence that 8 MB PSRAM is not intrinsically required merely to transport two radio streams. It does not prove that our larger simultaneous application fits 2 MB. The original ESPHome 06 profile configures 16 MB flash with an ordinary ESP32 and LAN8720; that is a profile fact, not a guarantee about every historical hardware revision. [U-series overview](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/slzb-series-overview), [official ESPHome README](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/README.md), [core configuration](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/packages/core/core.yaml), [classic profile](https://github.com/smlight-dev/slzb-06-fw-esphome/blob/28a212e42980de20a44ac3c30e8d7adb4a6e6d8a/configs/th-bt.yaml).

LAN8720 is a PHY used with the original ESP32 Ethernet MAC. It is not an interchangeable four-wire SPI substitute for W5500 on our S3. The current commercial S3 generation also uses W5500, with the radios connected to the host by UART. No extra MCU is inserted between the host and Ethernet. [MRxU hardware pin definitions](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/hw_defs/mrxu/r1_73.yaml).

## Thread radio transport versus a local border router

SMLIGHT now documents two distinct modes:

1. **Thread to remote OTBR:** available across the coordinator family. The SLZB exposes a radio over USB or serial-over-IP; the border-router application runs on Home Assistant or another host.
2. **Thread + OTBR on device:** available on 06xU, MRxU and Ultima. Thread/IP routing runs locally and Home Assistant uses the device's REST interface. The setup manual labels this an initial **beta** integration.

The local mode is real; describing all SLZBs as merely TCP radio bridges would now be incorrect. Equally, an older 06M with Thread firmware does not thereby acquire the newer on-device router. [Official two-mode setup](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/thread-setup-network-and-usb-connection).

The changelog introduced local OTBR for xU in 3.2.6.dev0 and moved it from experimental to beta in 3.3.3.dev1. The currently listed 3.4.3.dev1 still includes NAT64, mDNS, scheduling and RCP-stability fixes. Treat it as implemented and evolving, not proof that every combined feature configuration is qualified. [SLZB-OS changelog](https://smlight.tech/support/manuals/books/slzb-os/page/changelog-slzb-os).

## Ultima: a credible finished-hardware alternative, with gaps

Ultima uses an ESP32-S3, W5500, two radio paths, optional PoE, optional Z-Wave 800, USB host, IR, and an I2C/GPIO expansion interface. The manufacturer announcement specifies CC2674P10 + EFR32MG24 for Ultima 3. Its Z-Wave add-on is a different controller from our existing ZAC93, so buying it changes hardware rather than merely enclosing our current part. [Ultima product](https://smlight.tech/products/slzb-ultima), [manufacturer announcement](https://t.me/s/smlight_tech), [Z-Wave add-on](https://smlight.tech/de/addon-zw).

The most useful engineering lesson is its **TCA9555 I2C GPIO expander**. In the official r1.04 definition it sits at 0x24 on S3 SDA44/SCL43 and handles radio reset/boot plus other slow controls. The three native UART allocations are CC26, EFR32 and Z-Wave. Fast UART data stays on the S3, while low-rate controls move to the expander. [Ultima pin definitions](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/hw_defs/ultima/r1_04.yaml).

For our remaining peripherals:

- **CC1101:** current SLZB-OS documents an Ultima RF Transceiver add-on with raw OOK/ASK capture, storage and replay on 315/433/868/915 MHz. This is relevant to our 433 MHz requirement, but matching the chip name does not prove parity for every modulation, decoder or waveform we might use. Simultaneous physical slot compatibility with all desired add-ons must be checked. [Official RF module API](https://github.com/smlight-tech/slzb-os-scripts/blob/main/docs/modules/rf.md).
- **BME680:** the presence of a real I2C bus makes attachment plausible. Its normal 0x76/0x77 address does not conflict with Ultima's documented 0x24 expander. However, no complete connector pin-number/voltage assignment or stock BME680 integration was established in this review. A protocol-level fit is not a verified wiring plan.
- **LD2450:** with Zigbee, Thread and Z-Wave all present, Ultima already assigns three UARTs. Radar needs another serial path: a UART bridge, USB-serial path, or a separate peripheral controller. Its GPIO expander is not a buffered UART replacement. The reviewed stock configuration contains no LD2450 parser.
- **Active BLE:** official ESPHome explicitly enables active Bluetooth proxying. That same Ultima profile exposes its radio UARTs through TCP stream servers; it does not establish local OTBR under ESPHome. Stock SLZB-OS forwards BLE advertisements, but explicitly does not support active GATT connections. Its native BLE path requires SLZB-OS 3.3.3.dev7 or newer and Home Assistant 2026.8 or newer. [Native BLE manual](https://smlight.tech/support/manuals/books/slzb-os/page/bluetooth-low-energy), [Home Assistant's independent integration documentation](https://www.home-assistant.io/integrations/smlight/#bluetooth-remote-adapter-proxy). [Active proxy configuration](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/packages/bluetooth/bluetooth.yaml), [Ultima assembled profile](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/devices/ultima_r1_04.yaml).

## What to change in our design

**Keep the S3 + Ethernet + separate Zigbee/Thread architecture.** SMLIGHT's current hardware supports this choice. MR5U demonstrates that two identical MG24 radios are a valid commercial arrangement, but replacing our existing H2 RCP with a second MG24 does not remove a processor, a UART or Ethernet. It introduces firmware/board qualification and is not automatically simpler.

**Do not add TCA9555 just to imitate Ultima.** Our selected Nano already fits 21 application GPIO. Moving only H2 EN/BOOT onto an existing I2C bus would save exactly **two native GPIO, 21 → 19**, while adding a ready expander module, wiring and a reset-time dependency. It would require a new complete pin map and boot-safe implementation. There is no demonstrated net reduction in board area or assembly work.

**Evaluate a bought Ultima only as a deliberate hardware consolidation option.** It can plausibly replace the host, Ethernet, two radio modules, power/enclosure work and a Z-Wave path, and offer a vendor-supported CC1101 add-on. Preserve the outstanding acceptance gates: active BLE together with local OTBR, radar's fourth serial path, BME680 wiring/software, add-on coexistence, and the exact current board revision. Until those are resolved, it is a partial alternative rather than a verified replacement for the complete custom hub.

No pricing, stock availability, power consumption or final carrier-area savings are assumed. Product pages contain historical and generic copy; exact generation and firmware mode are part of the specification.
