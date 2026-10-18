# Power and thermal testing

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](../docs/module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

This document describes the power reserve for the **modular Pi design**; the wattages
below are not predictions of average consumption. A [separate single-S3 design](../docs/low-power.md)
is being developed to minimize energy use over years of operation.
Its power system and pinout must not be mixed with this design.

## Power chain

**802.3at PSE → Cat5e/6 → Waveshare POE-SPLITTER-25W-5.5-2.1 → 5 V distribution with individual fuses.** Splitter data out → TL-SF1005D v13 port 1. This is an active isolated splitter, not a passive PoE adapter. There is no 48 V on the low-voltage side. Do not install a PoE HAT on the Pi or a separate PoE module on an ESP32 alongside this wiring.

If no active PoE+ port is available, the selected external injector is [TP-Link Omada POE160S (TL-POE160S)](https://www.omadanetworks.com/us/business-networking/omada-accessory-poe-adapter/poe160s/): IEEE 802.3af/at, up to 30 W. Connect LAN to DATA IN and the single enclosure cable to POWER+DATA OUT. The injector and its supplied mains cable stay outside the enclosure; its own consumption is not part of the 5 V load calculation.

[Waveshare](https://www.waveshare.com/product/accessories/power-heat-sinks/poe-splitter-25w-type-c.htm) specifies 5 V 5 A **maximum**, 37–57 V input and af/at support. The complete enclosure uses 802.3at. The stated 25 W output is not treated as a guarantee of sustained 25 W operation inside a closed printed enclosure. The design test limit is **no more than 20 W / 4 A at the splitter output**, subject to voltage-drop and temperature checks.

## Preliminary budget — design assumptions

These are neither measurements nor the sum of all datasheet maxima:

- Pi 4 with microSD, no SSD: 8 W for normal OTBR/serial-bridge operation, plus 2 W of transient reserve.
- Two USB radios together: 1 W.
- TL-SF1005D v13: 2 W reserve. [TP-Link](https://www.tp-link.com/us/home-networking/5-port-switch/tl-sf1005d/v13/) specifies 5 V/0.6 A and maximum consumption of 1.9 W. Check the label on the actual revision. A 100 Mbps switch was selected: bandwidth is sufficient for the radio protocols, and consumption is lower than the initial Gigabit option.
- ESP32-S3-ETH + ZAC93: 2.5 W reserve.
- LD2450: 0.75 W reserve.
- BME680 with its heater: 0.25 W reserve.
- NodeMCU + CC1101 in the compatibility branch: 1 W reserve. When replacing it with a separate RF S3-ETH + CC1101, provisionally reserve 2 W.
- Fan/wiring losses: 0.5 W reserve.

The working assumption for the compatibility RF branch is 16 W, or about 18 W with the Pi transient reserve. For the wired RF branch it is about 17 W, or about 19 W with the same reserve. Both estimates are below the 20 W design limit, but require measurement. **The simultaneous datasheet maxima of the Pi and all modules do not fit this budget.** Do not run the HA server, compilation, SSD/NVMe or other heavy services on the Pi. If measured consumption exceeds 20 W, undervoltage occurs or the splitter overheats, the configuration fails acceptance: use a documented 802.3bt splitter with more headroom, a lower-power switch/SBC or separate enclosures. A higher-rated fuse does not solve this limit.

## Low-voltage harness

Use enclosed distribution with terminals and wire rated for at least 5 A. The 5 V/GND trunk is a short 18–20 AWG pair. The selected Pi path is C17 (a short 20 AWG pair and Same Sky PP3-002A) → Adafruit 4536 → USB-C. The manufacturer recommends 4536 for Pi 4, but publishes no 3 A current rating: it is a prototype candidate whose complete harness must be load-tested up to 3 A before connecting the Pi. S3 branches use DFRobot FIT0993, rated 5 V / 2 A, with a 1 A fuse. Connections and limits are in the [procurement checklist](procurement.md). Other branches use 22–24 AWG as appropriate for current and length. JST-SH/STEMMA QT is only for the low-current sensor, not the shared 5 V bus.

Suggested initial branch fuse ratings: Pi 3 A; switch 1 A; main ESP32 1 A; RF ESP32 1 A **or** NodeMCU 0.75 A; LD2450 0.25–0.5 A. There are five branches and six holders including the common input fuse. These are starting selections; verify I²t, heating and inrush current. Select the common DC fuse at no more than the lower of 5 A and the rating of the weakest splitter/cable/contact section; individual fuses protect wiring rather than regulate consumption. The sum of branch fuse ratings is not the permitted total current. The distribution enclosure isolates exposed copper from radio modules.

ZAC93 is powered from ESP32-S3-ETH 3V3; BME680 uses the same 3V3 through a separate connector. Check the JW5060/3V3 headroom of the actual board and measure 3.3 V during BLE + Z-Wave TX. LD2450 connects to a separate 5 V branch, not 3V3. Every external connector needs strain relief; Dupont wires are suitable for bench work, while the final harness must be mechanically secured.

When flashing, disconnect the module's normal 5 V branch before connecting the computer's USB. Radios on the Pi USB ports must not receive parallel 5 V power. Never join regulator outputs to “boost” the supply.

## Air temperature at the modules

Published operating-temperature limits for the selected modules are: [SLZB-07Mg24](https://smlight.tech/products/slzb-07mg24) **+5…+35 °C**, [ZAC93](https://www.getzooz.com/downloads/zooz-z-wave-800-series-long-range-gpio-module-zac93-LR-manual.pdf) **0…+40 °C**, and [TL-SF1005D v13](https://www.tp-link.com/us/home-networking/5-port-switch/tl-sf1005d/v13/) **0…+40 °C**. Once enclosed, their ambient air is the air inside the enclosure, not the room reading from the external BME680. Measure it beside these modules with the lid closed. Pi die temperature and outer-wall temperature are separate measurements; no throttling and a wall below 50 °C do not prove compliance with the Zigbee adapter's +35 °C limit. The maximum allowable room temperature for the complete assembly has not been established before testing.

## Bench measurements

1. Check polarity and 5 V at the unloaded splitter output; verify that no 5 V appears on 3V3.
2. Connect branches one at a time through a current meter. Record startup and steady-state current.
3. Monitor Pi undervoltage/throttling; the target range at its 5 V input is **4.85–5.15 V**. This is a design criterion, not a quoted tolerance for every module. Respect any stricter datasheet limits at each module.
4. Load the BLE proxy, Zigbee/Thread and Z-Wave simultaneously; separately perform a short known RF transmission. Use an oscilloscope to check 5 V and 3V3 dips and noise. A multimeter cannot detect short dips.
5. Run for 2 h at the expected room temperature, first on the bench and then with the lid closed. Check the splitter, Pi, switch, ESP32, plastic around connectors and, separately, air beside the radio modules against the limits above. The printed enclosure surface target is <50 °C; it does not replace module limits or thermal derating.
6. Repeat with the actual PoE cable length, after several PSE power interruptions and after 24–72 h of operation. Record measurements separately; this revision does not yet include them.

BME680 will not represent room temperature if placed in the warm Pi enclosure. The complete I²C harness, including its internal section and service loops, is initially limited to 10–20 cm. Place the pod beside or below the enclosure with an air gap, not above hot vents. Assess initial temperature offset against an independent thermometer after thermal equilibrium. Do not apply an arbitrary fixed correction before that measurement.
