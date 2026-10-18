# Antennas, radar and coexistence

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](../docs/module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

The basic principle is a separate radio for each protocol and a separate location for each radiator. The distances below are initial design targets, **not measured isolation**.

## Selected antennas

- Zigbee SLZB-07Mg24: the supplier's stock 2.4 GHz antenna. Do not replace it with a 433/868/915 MHz antenna. Preserve the factory RF path and regional power limit. SMLIGHT changes its product range; before buying, verify the Mg24 marking, RF connector type and actual package contents.
- Thread PCA10059: built-in PCB antenna. The selected dongle has no stock external SMA path. Place the antenna end beside a plastic wall, away from the Pi ground plane and not under a metal deck. Reposition it with a USB extension rather than soldering coax to an unidentified point.
- BLE ESP32-S3-ETH: the built-in ceramic antenna is active by default. [Waveshare](https://www.waveshare.com/wiki/ESP32-S3-ETH) states that enabling IPEX Gen 1 requires moving a resistor. An external antenna is an additional hardware modification, not just a cable connection. This option requires a matched 50 Ω 2.4 GHz path and RF verification after rework.
- Z-Wave ZAC93: stock PCB antenna. Do not convert it to SMA or solder on an arbitrary wire. Verify that the module's region matches the installed Z-Wave network and country of operation.
- RF CC1101: retain the existing matched **433.92 MHz** antenna. The CC1101 chip's frequency ranges do not mean that one module/antenna works equally well at 433 and 915 MHz. If a new module is needed, select one with a matching network for the required band.
- LD2450: built-in 24 GHz printed antennas, no external antennas. Keep metal, shields, screws and wires out of the space in front of the active face.

Provide a mechanical blanking plug for an unused replaceable RF entry. SMA and RP-SMA differ in their center contact; matching threads alone do not establish compatibility. Check connector gender before ordering a pigtail. Long coax losses can offset the benefit of moving an antenna; extending the radio's USB connection is usually more predictable.

ZAC93 modular-approval conditions cannot automatically be applied to this enclosure. The [Zooz manual, page 2, §2.7 and §2.9](https://www.getzooz.com/downloads/zooz-z-wave-800-series-long-range-gpio-module-zac93-LR-manual.pdf) separately restricts co-location with other transmitters and describes evaluation of a device with multiple radios. This prototype deliberately contains several transmitters: the distances below and a functional RF test do not demonstrate compliance with those conditions. The complete assembly is not certified under this project.

## Initial layout

Reserve the lower level for the Pi, switch and PoE DC/DC, and the upper level for radio modules. Aim for 100 mm between active 2.4 GHz antennas; given the enclosure dimensions, some antennas will need to be near opposite walls or outside. Initially leave at least 15–20 mm of clear space around built-in antennas, away from cables, metal and fasteners; final keep-outs come from each board's documentation. Distance is not a substitute for desensitization testing.

Connect USB radios to USB 2.0 through short shielded extensions, with no USB 3.0 drive near the antennas. Route twisted power pairs below. DC/DC converters and RJ45 connectors must not sit directly under the RF end of the boards.

On the bench, test each radio individually first. Then repeat with simultaneous BLE, Zigbee, Thread, Z-Wave and RF loads. Compare packet loss, latency and reconnection counts. Good RSSI alone does not prove the absence of collisions or loss.

## Channels

Zigbee and Thread use 2.4 GHz IEEE 802.15.4; BLE hops across channels in the same band. Separate radios do not eliminate blocking between nearby transmitters and receivers. The initial hypothesis is Zigbee channel 15 and Thread channel 25, subject to device compatibility and the actual Wi-Fi environment. This is **not a universal setting**. Do not change an existing network's channel without a migration plan and backup; first record the actual Wi-Fi/Zigbee/Thread channels. Reducing unnecessary TX power can be more useful than increasing antenna gain.

For BLE, Ethernet removes network traffic from the ESP32 Wi-Fi radio. [ESPHome](https://esphome.io/components/bluetooth_proxy/) recommends wired proxies and warns about nearby EMI sources. This combined enclosure is deliberately a compromise: if BLE suffers, move the proxy/antenna or split the enclosure rather than assuming every layout will perform like separate devices.

## LD2450 and BME680

Aim the radar into the room; verify positive/negative coordinates by walking from left to right. The initial model has a **1.2 mm** non-metallized PETG window (`radar_skin` in the [enclosure parameters](../mechanical/parameters.json)); leave an air gap, then compare the exposed board with the lid closed. At 24 GHz, thickness, pigment, plastic moisture and ribs in front of the antenna affect performance; the selected thickness is not a validated RF lens. Do not use carbon-fiber/metal-filled filament. Do not position the enclosure so the radar sees only a wall or closed door.

LD2450 is optimized for tracking moving targets; a `still target` indication does not guarantee sustained detection of a stationary person. Configure zones and test the intended lighting scenarios. BME680 sits in a separate ventilated pod, protected from direct heating and drafts from the main enclosure. Assess humidity/temperature after stabilization; the gas channel measures sensor resistance, not CO2 selectively.
