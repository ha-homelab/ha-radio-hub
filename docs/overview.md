# Home Assistant radio hub with a single PoE input

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

This page introduces the original modular Pi-based reference. For the current
MC1 implementation, start with the [documentation index](README.md) and
[assembly guide](module-carrier.md). The [single-S3 study](low-power.md) and
[earlier wiring atlas](../hardware/low-power/visual/README.md) are intermediate
historical work, not MC1 build instructions.

This project provides a prototype build: software and models are checked separately
from physical acceptance tests. The complete electronics have not been assembled
or measured as part of this development. Verify part numbers before purchasing
and dimensions before the final print.

## Design

A single Ethernet cable from a **PoE+ 802.3at** switch enters the enclosure.
An isolated splitter provides 5 V and standard Ethernet. Ethernet feeds a small
internal switch, while five separately protected power branches supply the switch,
Raspberry Pi 4, two ESP32-S3-ETH-M boards and LD2450. The two S3 boards serve as the
main sensor node and RF gateway. This is a modular assembly: the first version
does not require ordering a custom multilayer PCB.

The Raspberry Pi runs OTBR inside the device. Its USB Thread radio connects
locally; IPv6 traffic and the OTBR API reach HA over the network. A separate
MG24 USB radio provides Zigbee over TCP. ZHA and Zigbee2MQTT are alternative
owners of the same coordinator; never connect both at the same time.

The ESP32-S3 connects to the same internal switch by Ethernet. It handles the
Bluetooth proxy, LD2450 radar, existing ZAC93 module and BME680. Keep the ZAC93's
factory firmware and supply **3.3 V only**. Z-Wave JS is required between ESPHome
and HA: adding the ESPHome device alone does not create a Z-Wave network in HA.

RF Airbridge with CC1101 moves to the second S3-ETH-M over Ethernet. The port
preserves MQTT payloads, RM433 events and the RC-Switch/Dooya API; private codes
and sensor definitions must be transferred separately. The new board has a
different MAC address, so the HA registry does not migrate automatically. The
[migration procedure](../hardware/rf-migration.md) includes entity mapping and
rollback to the old ESP8266. Software tests and compilation are separate from
the hardware tests that are still required.

## Sensors and the I²C bus

LD2450 uses UART and tracks moving targets. It is useful for zones and motion;
detection of a stationary or sleeping person is not guaranteed. Test the plastic
window in front of its antenna separately from the uncovered radar.

BME680 uses GPIO1/SDA and GPIO2/SCL, with 3.3 V power and logic levels. The bus
runs at 100 kHz; a four-wire connector supports a short connection. For additional
sensors, check that I²C addresses are unique and account for total bus capacitance
and pull-up resistors. A cable running across a room requires a separate interface
design, rather than simply extending I²C.

The BME680 sits in a small ventilated pod outside the warm main enclosure. It
measures temperature, humidity, pressure and gas-sensor resistance. Measuring CO₂
requires a separate CO₂ sensor. Before relying on temperature readings, compare
them with an independent thermometer after the assembly reaches thermal equilibrium.

## Available deliverables

- [Components and antennas](../hardware/README.md), [connections](../hardware/wiring.md).
- [Parametric enclosure and printing](enclosure.md), with sources in `mechanical/`.
- [Firmware and connection instructions](firmware.md), [HA setup](home-assistant.md).
- [Matter-over-Thread device selection](thread-devices.md).
- [Acceptance tests before migrating the home network](acceptance.md).

First check power and assembly on the bench. Then test each interface separately,
followed by simultaneous operation and temperature inside the closed enclosure.
Migrate existing Zigbee, Z-Wave and Thread networks only after making backups and
checking that the recovery procedures are compatible. A new radio alone does not
transfer an existing network.
