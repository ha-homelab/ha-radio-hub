# HA Radio Hub hardware platform

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

This is the original Pi-based reference. The newer **single-S3** architecture,
custom PCBs and graphical connector maps are in [low-power hardware](low-power/README.md).

Design prototype, revision A. Component selection against documentation was checked on 2026-10-16; combined hardware operation, thermal performance and fit have not yet been measured. This is an assembly of off-the-shelf modules, not a designed or certified PCB.

## Selected architecture

One external Cat5e/Cat6 cable carries Ethernet and power from an **active IEEE 802.3at PoE+** port. An isolated splitter supplies 5 V. Its Ethernet output connects to an internal 100 Mbps switch. Raspberry Pi 4 runs OTBR locally and exposes a separate Zigbee NCP to ZHA over TCP. The Raspberry Pi is not the Home Assistant server: HA stays on the existing server.

- **Zigbee:** SMLIGHT SLZB-07Mg24, a dedicated EFR32MG24 running as a Zigbee NCP, connected to the Pi by USB. Added to HA as a ZHA network adapter. No MultiPAN.
- **Thread:** a separate Nordic nRF52840 Dongle PCA10059 running OpenThread RCP over USB. OTBR runs on the Pi inside the enclosure. HA uses the OpenThread Border Router, Thread and Matter integrations.
- **BLE + Z-Wave + sensors:** Waveshare ESP32-S3-ETH-M with W5500, connected to the switch by Ethernet. ESPHome handles the Bluetooth proxy, ZAC93 UART, LD2450 UART and BME680 I²C together. This is the intended combined configuration; operation under simultaneous load requires bench testing.
- **RF:** the fully wired option uses a second ESP32-S3-ETH-M + CC1101 433.92 MHz on Ethernet port 4, with separate GDO0/TX and GDO2/RX. The firmware ports MQTT/API, RM433 and Dooya from RF Airbridge; hardware testing and migration of private settings remain necessary before replacing the active node. The **compatibility option** retains the old ESP8266 NodeMCU + CC1101 inside the enclosure, but still uses Wi-Fi and does not meet the all-wired requirement. Choose one RF branch; do not install both as identical event sources. See [RF migration](rf-migration.md).
- **LD2450:** a 24 GHz radar on the front wall. The number 2450 is the model name, not a frequency of 2.450 GHz.
- **BME680:** a separate ventilated mini-enclosure on a short I²C cable, outside the hot Pi/switch compartment.

The ESP32-C5 from the original example is not in the baseline BOM: Linux OTBR + a dedicated RCP provide a reproducible route on a documented platform. A Thread radio chip alone does not make a board a border router.

## Parts and dimensions

[Block diagram](wiring.svg) · [BOM CSV](bom.csv) lists exact selected models, fastener/cable requirements, sources and status. BOM prices are budget estimates, not vendor quotations; availability was not researched for entries without a price. Existing ZAC93 and NodeMCU/CC1101 hardware can be reused.

The [procurement and order checklist](procurement.md) defines the fully wired assembly, separate mating connectors and checks for the selected power parts. The BOM is for buying prototype parts: it does not mean that a particular USB-C cable, DC plug or fuse set has already been tested. Adafruit 4536 for the Pi remains a candidate without a published 3 A rating; C10/C11 require mating-connector checks.

Main dimensions for layout:

- Pi 4: 85 × 56 mm PCB; allow for a heatsink and microSD access.
- TL-SF1005D v13: 104 × 70 × 22 mm enclosure; cable plugs extend beyond these dimensions.
- PoE splitter: 102.5 × 29.6 × 24.8 mm, excluding cable bends.
- ESP32-S3-ETH: 72.8 × 21 mm in plan according to the [Waveshare drawing](https://docs.waveshare.com/assets/images/ESP32-S3-ETH-details-size-e17a2432fc60e98e2ed27afcdbea08cc.webp). Measure the height with soldered headers and connected plugs. USB radios, ZAC93 and NodeMCU: reserved spaces include margin; check exact connector heights and mounting pitches on the delivered parts.
- Project enclosure: nominally 240 × 200 × 80 mm, with two levels. Assembly fit has not been verified. Do not print the final enclosure before checking cable fit.

Off-the-shelf alternatives include a desktop ABS/polycarbonate box with at least 240 × 200 × 80 mm of clear **internal** space, or a DIN enclosure with a separate RF compartment. External dimensions do not prove sufficient room: standoffs, the lid and cable entries reduce usable space, so the layout must be checked again. A metal enclosure is suitable only with external antennas; the built-in Nordic and ZAC93 antennas will lose efficiency inside metal. This revision favors a printed PETG/ASA enclosure with a replaceable mounting deck.

## Power and assembly

Follow the [wiring instructions](wiring.md) and [power budget](power.md). Do not infer an unknown module pinout from wire colors. ZAC93 and CC1101 use **3.3 V** power and logic; LD2450 uses **5 V** power and **3.3 V** UART logic. All low-voltage grounds join after the isolated splitter; assembly does not modify the PoE input or network pairs.

Assembly order: splitter and distribution → switch/Pi → separate USB radios → ESP32 Ethernet → LD2450 → ZAC93 → BME680 → RF. At each step, measure voltage at the module itself and test it individually. Connect UART and I²C wiring with power off. During normal operation, each module has only one power source; disconnect its 5 V branch before connecting a USB programmer.

## RF layout

See [antennas and coexistence](antennas.md). Place the enclosure centrally, while ensuring that LD2450 faces the monitored room and BME680 samples ambient air. These requirements can conflict, which is why modular external mounts are provided.

A successful compile is not the readiness criterion: acceptance requires 5 V measurements under load, 24–72 h of combined operation, recovery after a PoE power cycle, Zigbee/Thread traffic, BLE connections, Z-Wave inclusion and RF reception/transmission with a real device.
