# Revision A wiring

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

This page describes the original **Pi + two S3 boards** assembly. For the
**single-S3 low-power design**, use the [visual wiring atlas](low-power/visual/README.md)
and its PCB connector maps. The GPIO assignments differ between these designs.

[Machine-readable signal list](wiring.csv). The list specifies **signal names**, not the front view of a connector: the back of the board is mirrored. Before assembly, check the markings and the [Waveshare schematic](https://files.waveshare.com/wiki/ESP32-S3-ETH/ESP32-S3-ETH-Schematic.pdf). GPIO refers to an ESP32 pin number, not a Pico header contact number.

## Ethernet and USB

- External PoE cable → splitter input. Splitter's captive male RJ45 Ethernet output → TL-SF1005D v13 port 1 directly, with no separate patch cable.
- Switch port 2 → Pi 4 RJ45; port 3 → main ESP32-S3-ETH RJ45; port 4 → second ESP32-S3-ETH RJ45 for RF. Port 5 is free. In the old Wi-Fi RF board option, port 4 is also free.
- Pi USB 2.0 → short shielded USB extension → SLZB-07Mg24 (Zigbee).
- Second Pi USB 2.0 → short extension → Nordic PCA10059 (Thread).
- Five 5 V distribution branches → Pi USB-C, switch DC input, main S3 USB-C, RF S3 USB-C and LD2450 5V. In the Wi-Fi option, the fourth branch powers NodeMCU micro-USB instead of the RF S3. The splitter output must be 5 V only; check the exact switch DC plug dimensions/polarity on the actual unit. Do not rely on a matching outer diameter. Connectors and harness parts are listed in the [procurement checklist](procurement.md).

Power leads C4/C9 are DFRobot FIT0993: terminal `+` receives 5 V from its fused branch, `−` receives GND; `D+`, `D−` and `S` are not connected. C3 is Adafruit 4536 with power plug C17 (Same Sky PP3-002A, center +5 V, outer GND). Testing the complete Pi harness up to 3 A is mandatory: no such current rating is published for 4536. Do not connect computer power in parallel with this wiring.

The S3 board is **ESP32-S3-ETH-M**, 16 MB flash + 8 MB PSRAM, with no camera, microSD card or additional PoE module. Hardware UARTs are used to avoid sharing the processing load of bit-banged UARTs with BLE.

## Built-in W5500

These connections are already on the board and need no external wires: SCLK GPIO13, MOSI GPIO11, MISO GPIO12, CS GPIO14, INT GPIO10, RESET GPIO9. GPIO19/20 are assigned to native USB; GPIO21 is the RGB LED. These pins are not used for expansion.

## ZAC93

Check the module revision and markings. The [Zooz manual](https://www.getzooz.com/downloads/zooz-z-wave-800-series-long-range-gpio-module-zac93-LR-manual.pdf) specifies **3.3 V DC**. On the compatible 2×5 header:

- ZAC93 pin 1 `3V3` ← S3 `3V3`.
- ZAC93 pin 6 `GND` ↔ S3 GND; pin 9 is also ground.
- ZAC93 pin 8 `RX` ← S3 GPIO17 TX.
- ZAC93 pin 10 `TX` → S3 GPIO18 RX.
- Leave the remaining pins unconnected. Hardware v2 uses pin 7 for reset; the older revision labeled it PC01. Do not copy another reset circuit without checking the revision.

UART 115200, 8N1. Logic is 3.3 V; MAX232/RS232 levels are unsuitable. Move the ZAC93 itself from the previous ESP32 board; retain the previous ESP32 firmware for rollback. Before moving it, privately back up the Z-Wave NVM/keys and stop the previous serial/controller owner. Two Z-Wave servers must not operate one controller simultaneously.

## LD2450

Use the connector supplied with **HLK-LD2450**, not an LD2410 cable. Read the pinout from the module itself:

- `5V` ← separate fused 5 V branch.
- `GND` ↔ common S3 ground.
- `TX` → S3 GPIO5 RX.
- `RX` ← S3 GPIO4 TX.

UART 256000, 8N1, 3.3 V levels. GPIO4/5 are also connected to the microSD slot, so **no microSD card may be installed**. The camera must also be absent. The minimum radar firmware for ESPHome is V2.02.23090617 according to [ESPHome](https://esphome.io/components/sensor/ld2450/).

## BME680 and I²C expansion

The selected board is Adafruit BME680 STEMMA QT, product 3660. Order [Adafruit 4397](https://www.adafruit.com/product/4397) separately: JST-SH 4-pin/1.0 mm → female sockets, 150 mm. The female sockets fit the male headers on the selected S3-ETH-M; the BME680 does not include this cable. Follow the manufacturer's markings, not visual guesses:

- VIN/V+ → S3 **3V3**.
- GND → S3 GND.
- SDA/SDI → S3 GPIO1.
- SCL/SCK → S3 GPIO2.

I²C 100 kHz. The default Adafruit address is **0x77**; `SDO→GND` changes it to 0x76. The breakout already has pull-ups; check their parallel resistance when using several modules. GPIO1/2 are shared with the camera, so a camera cannot be connected. Initially limit the I²C harness to 10–20 cm; longer distances require edge/capacitance checks or a differential I²C extender, not just a longer cable.

The second STEMMA QT connector can support another **3.3 V-compatible** I²C sensor with a different address. An unused address does not guarantee power headroom. The supplied firmware configures BME680; additional sensors require explicit ESPHome components. Do not use this connector for hot-plugging, 5 V pull-ups, long outdoor wiring or heavy loads.

## RF Airbridge — original board

The existing NodeMCU v2/ESP8266 is retained with CC1101 433.92 MHz. According to the public [RF Airbridge](https://github.com/ha-homelab/rf-airbridge) project: SCLK GPIO14/D5, MOSI GPIO13/D7, MISO GPIO12/D6, CS GPIO15/D8, GDO0 GPIO4/D2, VCC 3V3 and common GND. GDO0 is shared for RX/TX; the radio is half-duplex. GDO2 is unused. Power NodeMCU with 5 V through micro-USB; CC1101 receives 3.3 V from its own NodeMCU. Do not join this 3V3 rail to the S3 regulator output.

The original board uses Wi-Fi. An internal Ethernet switch alone does not change the ESP8266 transport. Actual RF codes, MAC/IP addresses, keys and Wi-Fi credentials are not copied into the public project.

## RF Ethernet — replacing NodeMCU with ESP32-S3

The second ESP32-S3-ETH-M receives a separate 5 V branch and Ethernet port 4. The main BME680/ZAC93/LD2450 board is not used for these connections. The new firmware map is CLK GPIO7, MOSI GPIO8, MISO GPIO6, CS GPIO15; **GPIO4 TX → GDO0**, **GDO2 → GPIO5 RX**; CC1101 VCC3V3/GND. No microSD card or camera is installed. GDO0/GDO2 are deliberately separate; this differs from the existing single-wire NodeMCU pinout. If GDO2 is not exposed on the module, first select a suitable module or solder connection based on its schematic; do not substitute another pad.

Add **R1 = 4.7 kΩ between GPIO4/GDO0 and the second S3's local 3V3**. The transmitter uses open-drain and releases the line during reception: CC1101 can itself drive GDO0 in asynchronous mode. A pull-up to 5 V is prohibited. The firmware holds the line low during gaps between repeats, then releases it before returning to RX. GDO2 connects directly to GPIO5. The basis is [TI CC1101, §27.1 and Table 41](https://www.ti.com/lit/ds/symlink/cc1101.pdf); check signal edges on the assembled harness.

Check the shared supply load with this branch against [power.md](power.md). Migrate private RF codes and settings using the [migration instructions](rf-migration.md). A new MAC requires HA identity checks; a matching node name alone does not preserve the device record. Testing on physical hardware remains mandatory.

## Local Zigbee USB settings

The baseline SLZB-07Mg24 profile is 115200 baud, 8N1 and hardware RTS/CTS. [SMLIGHT setup](https://smlight.tech/support/manuals/books/slzb-07pxmgx/page/zigbee2mqtt-setup) specifies RTS/CTS for SLZB-07/MGx; its [benchmark](https://smlight.tech/blog/zigbee-over-ethernet-vs-usb-latency-test) uses 115200. Check against the installed NCP version; the ZHA TCP-side setting does not change the physical UART configuration in ser2net on the Pi. With modified firmware, update UART parameters on the Pi itself.
