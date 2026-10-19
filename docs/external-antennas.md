# MC2-B: three external antennas

MC2-B is the current **100 × 100 mm, two-copper-layer** carrier for finished
modules. It retains the local Thread Border Router, Ember Zigbee, active Bluetooth
proxy, Z-Wave transport, CC1101 RX/TX, LD2450 and BME680. Its change is three
independent external 2.4 GHz radio paths. **This is an engineering prototype**:
builds and CAD checks do not demonstrate house coverage or physical fit.

Start with the [visual guide and pin lookup](../hardware/external-antenna/index.html),
[native hardware](../hardware/external-antenna/README.md),
[firmware instructions](../firmware/external-antenna/README.md), and
[printable enclosure](../mechanical/module-carrier/external-antenna-prototype/README.md).

## Exact module selection

- **U1: Espressif ESP32-DevKitC-VIE / ESP32-WROVER-IE.** Classic ESP32 ECOv3,
  factory external RF connector, 8 MB flash and 8 MB physical PSRAM; two 19-pin
  rows. The application maps 4 MB PSRAM for capability-based allocation at quad 40 MHz.
  It runs Ethernet, the BLE 4.2 proxy and local Thread Border Router. Do not
  substitute WROOM (no PSRAM), VE (onboard antenna), an older WROVER revision,
  or the former S3 board. **MC2-A and MC2-B footprints and binaries differ.**
- **U2: Unexpected Maker TinyC6-U-01.** Factory U.FL variant, 8 MB flash and native
  USB. It runs the dedicated Thread RCP. Its ordinary through-hole headers expose
  RX17, TX16, EN and BOOT9. Fit its supplied **1×12 and 1×11 loose headers** first.
  The carrier adds a 10 kΩ pull-up from the TinyC6 local 3.3 V pin (header 4)
  to its GPIO8 strap (header 10), required for reliable ROM download entry.
  There is no competing USB-UART transmitter and no H2 R7 removal step. Do not
  substitute TinyC6[D], an onboard-antenna TinyC6, or an H2 image.
- **U3: Seeed XIAO MG24.** Retain the same Ember protocol family, with a separately
  built **external-antenna firmware**. PB04=1 and PB05=1 select its U.FL path before
  radio initialization. Its onboard antenna and external path are alternatives,
  not two simultaneous radiators.
- **U4: WIZnet WIZ850io.** Retain the SPI Ethernet module. Its RJ45 is a data port;
  the separate standards-compliant PoE splitter supplies the low-voltage circuit.

Module sources: [Espressif ordering and pin guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html),
[Unexpected Maker design files](https://github.com/UnexpectedMaker/esp32c6),
[Seeed antenna selection](https://wiki.seeedstudio.com/xiao_mg24_getting_started/).

**Procurement caveat, 18 October 2026:** TinyC6-U-01 was not available for immediate
shipment in the checked listings; Mouser 392-TC6-U-01 showed zero stock/backorder
and TinyTronics showed on-request availability. This is an exact-part design,
not a claim that every part can be ordered for next-day delivery. Recheck the
specific U.FL SKU before ordering the carrier. The [RF BOM](../hardware/external-antenna/rf-bom.json)
and [carrier BOM](../hardware/external-antenna/cad/BOM.csv) must be used together
with the retained off-board equipment below. MC1's old price estimate does not
price MC2.

## Three antenna paths

Buy **three TE Connectivity/Linx ANT-2.4-LCW-SMA antennas** and **three Amphenol RF
095-902-545-150 pigtails**. Each 150 mm cable has an AMC/U.FL-compatible right-angle
radio plug and a standard SMA female bulkhead. Each antenna has the matching
standard SMA male plug, 50 Ω impedance, 2400–2485 MHz specification and 2.8 dBi
peak gain. These are **not RP-SMA** connectors. Confirm center contacts and the
exact connector family; MHF III/4 miniature plugs are not interchangeable.

1. WROVER-IE U.FL → its cable → **BLE** bulkhead → antenna.
2. TinyC6-U U.FL → its cable → **THREAD** bulkhead → antenna.
3. XIAO MG24 U.FL → its cable → **ZIGBEE** bulkhead → antenna.

No RF combiner is used. Mate miniature connectors squarely with power removed;
secure the cable away from the connector and leave slack. Connect the antennas
before operating the radios. Inspect the physical cable route before final
assembly. The enclosure's 65 mm adjacent bulkhead pitch is a starting layout,
**not a measured isolation rating**. The 150 mm cable selection still needs a
physical dry fit; do not pull it taut to reach a bulkhead.

Primary specifications: [TE antenna](https://www.te.com/en/product-L9000082-01.html),
[Amphenol 150 mm assembly](https://www.amphenolrf.com/en-us/part/095-902-545-150/8897/).

## Pin connections and initial programming

Use the [generated connector ledger](../hardware/external-antenna/cad/connectors.json)
and [schematic](../hardware/external-antenna/cad/schematic.svg), rather than MC1
pin numbers. Net names such as THREAD_RX and ZB_RX describe the **radio end**:
therefore the host transmitter connects to that RX net.

- ESP32 GPIO26/TX → C6 GPIO17/RX, header 12; C6 GPIO16/TX, header 13 → ESP32 GPIO36/RX.
- ESP32 GPIO27 → C6 EN/RST, header 15; ESP32 GPIO15 → C6 BOOT9, header 11.
  Recovery outputs are open-drain.
- ESP32 GPIO32/TX → MG24 D7/PC07 RX; MG24 D6/PC06 TX → ESP32 GPIO39/RX.
  ESP32 GPIO33/RTS → MG24 D4/PC04 CTS; MG24 D5/PC05 RTS → ESP32 GPIO14/CTS.
- LD2450 TX → ESP32 GPIO18/RX; ESP32 GPIO23/TX → LD2450 RX.
- I²C uses GPIO21/SDA and GPIO22/SCL with 3.3 V logic. Retain the documented
  WK2132 bridge and BME680 address/pull-up configuration; never add 5 V pull-ups.
- Shared SPI: GPIO12/SCK, GPIO2/MOSI, GPIO19/MISO. WIZ850io uses GPIO5/CS,
  GPIO34/IRQ and GPIO4/RESET; CC1101 uses GPIO13/CS, GPIO25/GDO0 TX and
  GPIO35/GDO2 RX. Do not use other breakout boards with unknown strap pull-ups.

GPIO6–11 belong to flash, GPIO16/17 to PSRAM, GPIO1/3 to the board's USB-UART
bridge, and GPIO0 to ROM download entry. GPIO34/35/36/39 are input-only and have
no internal pulls. **Fit the carrier's 10 kΩ pull-downs on GPIO12 and GPIO2**:
GPIO12 must be low at reset for the selected module's 3.3 V flash supply;
GPIO2 must be low for UART download mode. They connect only to SPI peripheral
inputs. Preserve the documented chip-select and C6 boot pull-ups and the C6
local-3.3-V GPIO8 strap. Never apply an eFuse workaround to an unknown module.

The UART0 logger is disabled and the IDF application console is off so UART0 can
serve the radar after boot. Zigbee uses UART1, Thread uses UART2. USB-UART remains
available for ROM programming on GPIO1/3, but is not a running application log
port. The firmware locks the supported silicon to ECOv3 or newer.

Program and verify each controller **while loose**, using the MC2-B classic-ESP32 factory
image, C6 RCP and external MG24 NCP/bootloader. For loose TinyC6 ROM programming,
fit a temporary 10 kΩ pull-up from GPIO8 (header 10) to its local 3.3 V
(header 4): carrier R3 is not connected yet. The BOOT button only pulls GPIO9 low.
Neither an MC1 nor MC2-A S3 OTA image is compatible with this processor.
Flash the new host over its Micro-B USB-UART connection first, under the new
`mc2-classic-hub` identity. Do not reuse an S3 factory image or its boot offset.
Keep physical recovery possible before soldering. All carrier
components face the same side; solder low axial parts and headers first, then
modules from the back. Check pad numbers, diode cathodes, continuity, supply
polarity and clearance before applying power. The C6's loose headers require
ordinary through-hole soldering; no RF resistor relocation is specified.

The [firmware guide](../firmware/external-antenna/README.md) and
[network update instructions](../firmware/external-antenna/updates/README.md)
provide reproducible commands and reject the wrong radio target/antenna mode.
Keep one deployed node with the configured identity. Back up Thread credentials,
Zigbee state and HA configuration before a future physical migration.

## PoE and retained equipment

Power remains **battery-fed PoE switch → Ethernet cable → isolated PoE splitter
→ regulated/fused low-voltage rails**. The splitter's data output feeds WIZ850io;
its DC output feeds the documented regulators. No direct battery connection to
this carrier, new injector or raw PoE-voltage input is introduced. Check the
actual splitter rating, regulator headroom and switch port budget under all
radios' simultaneous load.

Retain the WK2132/DFR0627 UART bridge, existing regional ZAC93, band-matched
433.92 MHz CC1101 and antenna, LD2450, BME680, power converters, fuses and harnesses.
Their exact carrier endpoints are in the connector ledger. ZAC93 retains its
stock antenna; LD2450 retains its 24 GHz printed array. Neither belongs on a
2.4 GHz SMA antenna. Locate BME680 away from the converters and warm electronics,
and keep metal and wires out of the radar's active face.

The new printed housing is **carrier-only**. Its nominal shell is
190 × 160 × 58 mm, with a required 4 mm ceiling frame, giving 62 mm installed
body depth before antenna projection. Power modules, UART bridge, other radios
and sensors need separate accommodation. Do not describe this as a completed
single-box assembly. Bulkheads and coax remain on the fixed base when the lid
is removed. Print the connector fit coupon before the full shell; validate
actual module heights, solder tails, cable bends and attachment strength.

## Bluetooth compatibility and coverage

The classic ESP32 supports BLE 4.2 legacy advertisements and active connections.
The configured three-connection HA proxy is retained, but BLE 5 extended
advertisements and LE Coded PHY are unavailable. External antennas do not add
those features. Confirm any sensor requiring them before changing the host.


External antennas move the radiators away from the carrier ground planes,
Ethernet metalwork and converters. They improve placement options; they do not
guarantee coverage of **1,000 ft² / about 93 m²**. Layout, walls, interference,
end-device transmit power and installed mesh routers still matter. BLE sensors
that are not mesh devices do not gain a Thread/Zigbee mesh route.

Follow the [RF commissioning procedure](rf-commissioning.md), including weak-room
measurements, simultaneous traffic and at least a 72-hour soak. The
[results sheet](../hardware/external-antenna/coverage-results.csv) deliberately
starts with `not_run`. If coverage is inadequate, first adjust placement and
antenna orientation, then add appropriate powered Zigbee/Thread routers or a
second Ethernet BLE proxy. Do not compensate with arbitrary transmit-power
increases. Hardware operation, measured energy use and regulatory compliance
remain separate from compilation and CAD validation.

The [host migration record](classic-esp32-migration.md) explains the exact board
choice, memory budget and limitations.

The [historical MC1 guide](module-carrier.md) remains available for existing
boards. Its Nano/H2 pin map, compact case and onboard MG24 image are not MC2 parts.
