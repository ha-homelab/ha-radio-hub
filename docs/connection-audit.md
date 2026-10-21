# MC2-D connection audit

Review date: **20 October 2026**. Scope: the active MC2-D carrier, factory-header
modules, PWR1 supply, external harnesses and matching firmware. Three independent
reviews covered power/boot behavior, firmware/protocols and connector/mechanical
orientation. The initial revision was `f3ad9fe`; the corrections below are included
in the current files.

**Two problem areas were found and corrected:** the DFR0627 UART bridge's
I²C address block overlapped BME680, and the RF shared data line could suffer
output contention during initialization or a failed radio-mode transition.
No swapped carrier pins, reversed supply
diodes or missing routed connections were found. Physical operation remains
unmeasured; this is a design review, not a test of an assembled hub.

## Required correction: DFR0627 switch A0

With power disconnected, set **A1=1, A0=0** on DFR0627. Use the current firmware
with UART1 register address **0x50** and FIFO address **0x51**. Keep BME680 at
**0x77**. Reserve the entire **0x50–0x57** block for the bridge.

The previous A1=1/A0=1 setting selected 0x70–0x77. WK2132 uses address bits for
channel and FIFO selection and acknowledges the matching eight-address block;
checking only 0x70 and 0x71 missed the collision. Both BME680 choices, 0x76 and
0x77, were inside that old block. Disabling the second UART does not free its
addresses. This follows the [DFRobot protocol reference](https://wiki.dfrobot.com/dfr0627/docs/20907)
and [manufacturer driver](https://github.com/DFRobot/DFRobot_IICSerial).

The fix updates both MC2 and the maintained MC1 firmware profile. Configuration
validation now rejects a second I²C device within the bridge's decoded block
on the same bus. Frozen historical MC1 drawings retain their old annotations;
their reference pages explicitly override those annotations. No PCB traces,
connector pin order, printed mounts or additional purchased parts are needed.

This was independently tested through the actual pinned ESPHome 2026.9.1
configuration validator: **0x50 + BME680 0x77/0x76 passes** and
**0x70 + BME680 0x77/0x76 is rejected**. A separate regression compares the
switch positions and addresses in the public wiring diagram, harness lookup
and CAD ledger with the firmware setting.

## RF startup and handoff corrections

The CC1101 GDO0 line is shared with the host's open-drain transmitter, GPIO25
on MC2-D. The radio can drive GDO0 during reception. Merely configuring the
host pin as open-drain does not make every LOW safe: it must remain released
until the radio changes to transmit mode.

In the pinned ESPHome/ESP-IDF combination, RMT channel creation used a default
LOW idle level and connected its output before enabling open-drain mode.
ESPHome released the line later in setup. Independent source reviews confirmed
that this leaves a startup contention window; it is not hidden by the channel
being disabled for transmission.

The shared RF package now includes a small local initialization guard. It
prepares the configured RF pin in its released state and supplies HIGH as the
RMT channel's initial level before the driver connects the output. Other
transmitter pins retain their normal behavior. The guard wraps the allocation
call without changing the cached SDK or copying the upstream transmitter.
The RF protocols, carrier resistors and connector assignments remain unchanged.

The transmit sequence also needs an explicit handoff. The upstream CC1101
driver does not propagate a failed IDLE wait to its caller, so calling
`set_idle()` alone did not prove it was safe for the host to drive LOW. The
shared RF helper now releases the host, configures and reads back GDO0 as
high-impedance (`IOCFG0=0x2E`), and confirms IDLE. Only then may the host pull
LOW and request TX; it confirms TX before sending the waveform. A failed
check releases the host and skips the waveform. This sequence also avoids
asserting an unintended OOK carrier while entering TX with a pulled-up input.
GDO0 becomes the asynchronous serial input in TX regardless of its output
selection; GDO2 continues to provide RX data. Completion releases the host
before restoring and checking RX.

Native regression tests cover the original startup behavior, the corrected
ordering, GPIO/allocator failures, rejected mode changes and failed RX
restoration. The build verifier also checks that the actual linked transmitter
calls the startup wrapper. These checks guard the software assumptions; they
do not measure the electrical waveform.

Use a current rebuilt host image to receive this correction. On the bench,
scope GDO0 through power-up, host reset and RX→TX→RX transitions, including
failed mode changes. Source review
and compilation do not replace that waveform check.

Sources: [ESPHome 2026.9.1 RMT transmitter](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/remote_transmitter/remote_transmitter_rmt.cpp),
[ESP-IDF 5.5.5 RMT driver](https://github.com/espressif/esp-idf/blob/v5.5.5/components/esp_driver_rmt/src/rmt_tx.c),
and [TI CC1101 datasheet](https://www.ti.com/lit/ds/symlink/cc1101.pdf).

## Verified signal paths

Directions below are electrical directions, not matching text labels. For
example, `THREAD_RX` names the radio's receiver and therefore connects to the
host transmitter. Carrier pin numbers refer to the component-side drawing.

| Function | Verified path and setup |
| --- | --- |
| Thread UART | Host GPIO26 TX → U2 pad8 / D7 / C6 GPIO17 RX. U2 pad7 / D6 / GPIO16 TX → host GPIO36 RX. 460800 baud, no flow-control wires. |
| C6 recovery | Host GPIO27 → J10.1 → underside TP8 / EN; host GPIO15 → J10.2 → TP2 / GPIO9 BOOT. Both host outputs are open-drain. C6-local GPIO8 has its factory pull-up. |
| Zigbee UART | Host GPIO32 TX → U3 pad8 / PC07 RX; U3 pad7 / PC06 TX → host GPIO39 RX. Host GPIO33 RTS → U3 pad5 / PC04 CTS; U3 pad6 / PC05 RTS → host GPIO14 CTS. 115200 baud. |
| Shared SPI | Host GPIO12 SCK → U4.J1.4 and J5.3. GPIO2 MOSI → U4.J1.3 and J5.4. U4.J2.6 and J5.5 MISO → GPIO19. Each slave has its own chip select. |
| Ethernet control | GPIO5 CS → U4.J1.5; U4.J1.6 IRQ → GPIO34; GPIO4 RESET → U4.J2.5. WIZ850io provides pull-ups on CS/IRQ/RESET, not on SCK/MOSI. |
| CC1101 | GPIO13 → J5.6 CSn; GPIO25 open-drain → J5.7 GDO0 transmit; J5.8 GDO2 receive → GPIO35. R1 pulls GDO0 up; R2 keeps CSn inactive. Module-end pins must be identified by signal name on the retained board. |
| Shared I²C | GPIO21 SDA → J3.3 / DFR D and J7.3 / BME SDA. GPIO22 SCL → J3.4 / DFR C and J7.4 / BME SCL. 400 kHz, 3.3 V pull-ups. DFR block 0x50–0x57; BME 0x77. |
| Z-Wave transmit | DFR UART1 T/TX1 → J3.5 → J4.4 → ZAC93 physical pin8 RX. |
| Z-Wave receive | ZAC93 physical pin10 TX → J4.5 → J3.6 → DFR UART1 R/RX1. 115200 8N1. |
| Radar | GPIO23 TX → J6.3 → LD2450 RX; LD2450 TX → J6.4 → GPIO18 RX. 256000 baud, 3.3 V logic despite the radar's 5 V supply. |
| Service pads | J8 temporarily shorts MG24 D0/PC00 to GND. J9 temporarily shorts host GPIO0 to GND. Both remain open in operation. |
| RF | U1 BLE, U2 Thread and U3 Zigbee each use their own U.FL/MHF I cable to a standard SMA female bulkhead and standard SMA male antenna. C6 GPIO3 LOW/GPIO14 HIGH and MG24 PB04/PB05 HIGH select the external paths. |

Primary pin sources: [Espressif DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html),
[Seeed C6 native design](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH&PCB_260114.zip),
[Seeed MG24 native design](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip),
[WIZ850io schematic](https://docs.wiznet.io/assets/files/wiz850io_sch_v110-3fcc19fc2acaf16f15c5f08f9c8330cb.pdf),
[DFRobot](https://wiki.dfrobot.com/dfr0627),
[Zooz installation guide](https://www.support.getzooz.com/kb/article/1215-zac93-800-gpio-module-installation-guide/),
[Adafruit native PCB](https://github.com/adafruit/Adafruit-BME680-PCB).
The current Zooz pinout image could not be freshly retrieved; verify the received
board's labels before mating its socket. Existing CC1101 and radar cable pin
orders are likewise not inferred from wire colors or generic listing photos.

## Verified power paths

- The battery-fed switch supplies the isolated active PoE splitter. Only its
  regulated 5 V output reaches the fuse and J1.1; J1.2 is the return. The
  splitter's data-only RJ45 tail plugs into WIZ850io.
- J2.1 → RECOM pin1 VIN; J2.2 and J2.4 → pin2 GND; pin3 VOUT → J2.3.
  The input capacitor is positive to VIN and negative to GND. This input is
  before the controller diodes. [RECOM pinout](https://recom-power.com/pdf/Innoline/R-78K-1.0.pdf).
- D1/D2/D3 anodes connect to fused 5 V; their banded cathodes feed U1/U2/U3
  respectively. Controller-local 3.3 V outputs U1.J2.1, U2.12 and U3.12 remain
  unconnected to carrier power. [Diode polarity](https://www.vishay.com/docs/88525/1n5817.pdf).
- Peripheral 3.3 V feeds both WIZ850io supply pins, DFR0627, CC1101, BME680's
  input and ZAC93 pin1. ZAC93 pins6 and9 are returns; pins2/3/4/5/7 remain NC.
  LD2450 alone uses direct fused 5 V on J6.1.
- R4/R5 hold host GPIO12/GPIO2 low at reset. Flash/PSRAM and USB-UART pins are
  not borrowed. Firmware disables the application serial console and remaps
  UART0 to the radar; UART1 and UART2 serve Zigbee and Thread.

## Evidence and remaining measurements

The reviewers compared manufacturer native designs and pinouts with the actual
KiCad schematic/PCB, not only generated JSON. All **131 component pad/net
assignments** agreed between native schematic and board; **31 connected nets**
and **30 intentionally unconnected pads** were accounted for. Fresh KiCad
10.0.6 checks reported **0 ERC violations, 0 DRC violations, 0 unrouted items
and 0 schematic-parity errors**. The I²C correction changes external switch
setup and firmware; the native PCB, schematic and routed copper are unchanged.

The C6 underside TP8/TP2 coordinates and both 14-pin module rows were checked
against Seeed's design. Adafruit's native PCB confirms the QT connector order
GND / power input / SDA / SCL. Factory header height, actual cable bends and
ZAC93 socket seating still require a dry fit. The C6 service leads need the
specified clearance and strain relief; the window is accessed with the carrier
removed from the case.

Copy the [blank power worksheet](../hardware/external-antenna/power-measurements.csv)
for the physical build. It covers RECOM input/output, ZAC93 supply, each local
controller rail, the host's input after D1, and reset-time GPIO12/GPIO2 levels.
U1's regulator needs its own dropout/headroom check; RECOM's 4.5 V minimum is
not a pass threshold for U1. All worksheet measurements are still `not_run`.

Before calling the assembled connections qualified, verify:

1. Actual J1/J2 wire gauge, contact current rating and loaded voltage drop;
   these are not established by an unspecified generic jumper lead.
2. Continuity and polarity of all **35 external wires**, especially the
   remapped ZAC93 socket and C6's two small underside pads.
3. Shared I²C rise time/reliability with the real BME pod cable and the corrected
   DFR switch setting; shared SPI with the actual CC1101 harness.
4. Cold starts, all services active together, local rail transients, closed-case
   temperature, RF coverage and recovery after PoE loss. Scope CC1101 GDO0 at
   startup/reset and during RX→TX→RX transitions to verify the released state.

Use the [pin-by-pin assembly instructions](full-hub-assembly.md),
[searchable connector lookup](../hardware/external-antenna/index.html#harness)
and [commissioning procedure](rf-commissioning.md) for those physical tests.
