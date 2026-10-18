# MC1 — one carrier, finished modules, preserved protocols

The current carrier uses **Waveshare ESP32-S3-Nano-M, ESP32-H2-DevKitM-1,
Seeed XIAO MG24 and WIZ850io**. It implements the compact-host direction from
the [SMLIGHT comparison](../hardware/module-carrier/studies/slzb-thread/index.html)
while keeping the seven existing function groups and their Home Assistant interfaces.

**Engineering prototype:** CAD checks and firmware builds are recorded separately
from physical acceptance. No assembled board, radio range, power margin or enclosure
fit has been validated. Use the current drawings and matching firmware together;
the former full-size S3 pin map is not interchangeable.

## Construction

The carrier is **80 mm horizontal × 90 mm vertical, with two copper layers**.
All fitted components are on top. Factory male module pins enter plated holes
and are soldered underneath; **no female module sockets or castellated-side soldering**.

The loose circuit parts remain **two resistors and three axial diodes**. There
are four mounted finished modules and nine harness/service headers. J9 is the
new two-pin Nano recovery contact, not another interface board. The Nano has 30
header pins instead of the former S3 board's 44: the four modules require **86
header solder joints**, down from 100. Factory-fitted regulator, RF matching and
decoupling parts remain on their finished modules.

The selected parts are:

- **Waveshare ESP32-S3-Nano-M:** factory male headers, ESP32-S3R8, 16 MB flash,
  8 MB octal PSRAM, 43.18 × 17.78 mm. The generic ESPHome S3 build descriptor is
  not the physical module model: explicit memory and GPIO settings define this board.
- **ESP32-H2-DevKitM-1:** independent Thread RCP. RX4/TX5 avoid its USB-UART
  bridge; host-controlled reset and boot are retained.
- **Seeed XIAO MG24 Pre-Soldered, SKU 102010690:** independent Ember Zigbee NCP,
  PC06/PC07 UART and PC04/PC05 flow control. Use the XIAO-specific firmware,
  not an old M0 adapter image.
- **WIZ850io:** finished Ethernet module with magnetics, sharing SPI with CC1101.
  It is powered from the peripheral 3.3 V rail; it does not extract PoE.
- External finished **isolated 5 V PoE splitter, D24V22F3 3.3 V supply,
  DFR0627/WK2132 UART bridge**, plus the existing CC1101, ZAC93, LD2450 and BME680.
  These still need space outside the quoted carrier outline.

## Functions and implementation

1. **Thread:** local S3 border router, dedicated H2 RCP, IPv6/multicast and Home
   Assistant REST integration. No added Linux host or inter-processor Ethernet bridge.
2. **Zigbee:** separate MG24 Ember/EZSP transport with hardware flow control for
   the ZHA/Zigbee2MQTT ecosystem. Pairing and network backup/restore need bench tests.
3. **Bluetooth:** ESPHome active proxy with three connection slots, as well as
   advertisements. Concurrent performance is not established by compilation.
4. **433 MHz RF:** existing RF Airbridge MQTT contracts and CC1101 receive/transmit.
5. **Z-Wave:** existing regional ZAC93 via checked WK2132 byte forwarding.
6. **Presence:** LD2450 native UART, measurements and control actions.
7. **Environment:** BME680 temperature, humidity, pressure and gas resistance in
   an external ventilated pod. Gas resistance is not a direct CO2 measurement.

W5500 and CC1101 share **SCK13, MOSI11 and MISO12**, with separate chip selects
and unchanged interrupt/control roles. This releases three GPIOs without an
extra controller or expander. Normal SPI transactions use the driver bus lock.
The initial CC1101 setup precedes Ethernet; unreviewed runtime CC1101 reset or
reconfiguration is rejected by firmware validation. Keep the CC1101 harness short
and qualify it under simultaneous Ethernet traffic.

Three native UARTs remain assigned to Thread, Zigbee and radar. GPIO43 is now H2
TX, so boot-time ROM chatter is cleared by resetting H2 before Spinel startup.
GPIO48 drives the slow open-drain H2 BOOT control and also sees the Nano's onboard
LED MOSFET gate. Native USB19/20 are reserved. J9 reaches GPIO0 through Nano
**JP1.13**, permitting manual recovery without soldering a wire onto a test pad.
The Nano's JP2 pin numbers run opposite to its physical top-to-bottom row order;
follow the numbered native footprint and wiring ledger.

## Compact placement and fabrication cost

PCB area changes from **90 cm² to 72 cm²: 20% less than the preceding 100 × 90 mm
carrier**, and 55% less than the original 160 × 100 mm outline. This is an area
calculation, not a claim of a 20% reduction in delivered price. The previous and
current boards both fit within a 100 × 100 mm fabrication size class; quantities,
finish, drill rules, shipping and taxes determine an actual quotation.

![Previous and current carrier at equal scale](../hardware/module-carrier/layout-comparison.svg)

Harness headers occupy the bands between modules. USB sockets remain fitted and
accessible. Module antennas face board edges with copper exclusions on both
layers. H2 is shifted outward by 4.5 mm: its antenna lies nominally outside the
carrier, with a 5.475 mm maximum overhang. Keep the manufacturer-recommended
surrounding space free of enclosure metal and wire loops; verify real tolerances. The assembly drawing marks the reserved USB, connector housing and RF
areas; these are not spare space for wiring. Ceiling mounting does not eliminate
the antenna's near-field interaction with copper or wires.

At MG24, the larger exclusion from copper pours is preserved while a narrow
required PC07 signal escape is permitted beside the header. This is an explicitly
reviewed routing exception, not a claim of manufacturer-qualified antenna clearance.
The antenna maker's evaluation-board geometry is not a universal carrier rule for
a finished XIAO; assembled RF range and coexistence must still be measured.

The dimensions describe the carrier PCB, not an 80 × 90 mm enclosure. Projecting
antenna ends, RJ45, plugged cables, harness bend height, underside solder joints
and external modules require additional space. The narrow connector housings,
nylon supports and service envelopes are explicitly checked in the CAD; verify
the actual purchased mating shells before permanent assembly.

## Ethernet and board sides

WIZ850io is at the lower-right with its **RJ45 opening facing the bottom edge**.
The jack mouth projects **2 mm beyond that edge**. Its factory holes remain on
the carrier. Keep the plug, latch and boot corridor clear and support the board
against connector insertion loads.

Use the [dimensioned assembly](../hardware/module-carrier/cad/assembly-top.svg),
[top copper/silk](../hardware/module-carrier/cad/board-top.svg) and
[bottom copper/silk](../hardware/module-carrier/cad/board-bottom.svg).
The gallery includes native KiCad views of both sides. These are generated from
the routed board, not a photograph of manufactured hardware. Old generated
illustrations remain labeled as history and are not used for construction.

## Power and USB service

The fused isolated 5 V bus reaches each controller through its own axial Schottky
diode. **Nano D1 branch → VIN JP1.15**. Its **VBUS JP1.12 and 3V3 JP1.2 stay
unconnected to carrier rails**. The onboard USB-to-VIN diode and carrier branch
diode form a supply OR; the separate 3.3 V buck serves Ethernet and peripherals.
Do not parallel the Nano, H2, XIAO and peripheral regulator outputs.

The Nano vendor documents external VIN at 6–21 V. This design uses the regulated
5 V bus minus the branch diode, below that published external range, based on the
onboard converter and USB power circuit. **Loaded VIN/3V3 operation is therefore
an explicit bench acceptance requirement**, including cold start, USB insertion,
radio bursts and simultaneous traffic. A firmware build cannot validate this path.

For USB service, keep the whole interconnected carrier powered normally and use
a board-specific, measured procedure. A universal VBUS blocker is not appropriate:
the XIAO SAMD11 programming probe needs USB VBUS. Merely removing PoE and powering
one controller over USB can backfeed unpowered peers through signals; the supply
diodes do not isolate those signals. Check backfeed, rail voltages and enumeration.
Before USB-flashing H2, activate **Pause Thread for H2 Service**, allow the hub to
restart, and verify **Thread State = maintenance** and **Thread Guard Durable = on**.
Only then program H2; automatic RCP resets are disabled in that state. Use
**Retry Quarantined Thread** after programming to resume. The maintenance pause
does not count as a radio fault.

See the [XIAO service review](../hardware/module-carrier/studies/square-layout/service-review.md).

## Thread failure containment

The active firmware probes H2 before starting OpenThread and connects actual reset
and terminal-failure callbacks. An absent RCP can enter **persistent Thread
quarantine** while the other services continue. A terminal fault after startup
records the fault and permits **one controlled whole-host restart**; the next boot
leaves Thread stopped until the explicit retry action. This avoids a repeating
RCP-triggered boot loop. It is not seamless radio isolation: every S3 service is
briefly interrupted during that restart.

A persisted armed marker also covers SDK panic/watchdog exits. An unrelated host
crash while Thread is armed can therefore conservatively quarantine Thread; the
reported reset/fault state and explicit retry distinguish this from deleting the
network. The Thread dataset is kept separately and is not erased by quarantine.
Ordinary lack of a dataset or Ethernet link is not itself a terminal RCP failure.
If a fault-time NVS write fails, RTC retention protects a warm restart but not
complete power removal; check **Thread Guard Durable** before relying on persistent
quarantine or entering maintenance.

Home Assistant diagnostics expose Thread state, last fault, quarantine, fault and
retry counters, RCP resets, device role, internal heap, largest free block, PSRAM,
loop time, uptime and reset reason. **Retry Quarantined Thread** is the deliberate
recovery control. See [firmware instructions](../firmware/module-carrier/README.md)
for exact behavior, source tests and hardware acceptance.

## Firmware installation and existing networks

The Nano factory image uses a 16 MB partition layout. Its NVS location differs
from the historical 8 MB image, so export network datasets/backups before factory
installation or any partition migration. Dataset-preserving quarantine refers
to operation within the installed Nano layout; it is not an automatic migration
of old NVS data. An application-only OTA normally retains the installed partition
table, so verify that table instead of assuming an OTA expands flash partitions.
No physical device has been flashed as part of this redesign.

## Assemble and commission

1. Match module revisions, header numbering and actual mating shells to the CAD.
   Program all three controllers before permanent assembly and dry-fit everything.
2. Fit the five axial parts and harness headers, then solder the factory male
   module pins underneath. Inspect bridges, orientation and every power net.
3. Verify isolated 5 V, peripheral 3.3 V and each controller input under load.
   Leave local regulator outputs and Nano VBUS isolated as specified.
4. Check Ethernet, USB service and J9 manual recovery. To invoke Nano ROM recovery,
   temporarily short J9 GPIO0 to GND while resetting the Nano; remove the short for
   normal operation. Do not leave either boot-service header permanently shorted.
5. Commission each radio/sensor separately, then run Thread, three BLE connections,
   Zigbee, Z-Wave, RF traffic and radar together. Record minimum heap, largest free
   block, stack margin, errors, power and temperature.
6. Exercise absent/stalled H2, explicit retry, power cycling, unplugged Ethernet,
   updates and network backup/restore. Confirm bounded recovery and dataset retention.
7. Choose the permanent enclosure and migrate household networks only after the
   assembled prototype passes these checks. Old enclosure images are not fit evidence.

The [verification summary](../hardware/module-carrier/verification-summary.json),
[independent audit](../hardware/module-carrier/independent-review.md), and
[build evidence](../firmware/module-carrier/build-evidence.json) distinguish completed
checks from physical work. There is one current hardware path; old layouts remain
[engineering history](design-history.md).

## Primary sources

- [Waveshare Nano documentation](https://www.waveshare.com/wiki/ESP32-S3-Nano)
  and [schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf)
- [Espressif H2 DevKitM-1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html)
- [Seeed XIAO MG24](https://wiki.seeedstudio.com/xiao_mg24_getting_started/)
- [WIZnet WIZ850io](https://docs.wiznet.io/Product/ioModule/WIZ850io)
- [DFRobot DFR0627](https://wiki.dfrobot.com/dfr0627)
