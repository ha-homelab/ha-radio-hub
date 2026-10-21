# MC2-B: previous-generation ESP32 host

This records the earlier host migration. The active **MC2-D** retains this
ESP32-DevKitC-VIE host but uses **XIAO ESP32C6 pre-soldered / 102010636** for Thread,
with a new carrier footprint and matching RF-switch firmware. See the
[current shopping list](mc2-shopping.md) and [assembly guide](external-antennas.md).

MC2-B replaces **ESP32-S3-DevKitC-1U-N8R8** with **Espressif ESP32-DevKitC-VIE**,
using the **ESP32-WROVER-IE** module. This is a cost-focused host migration;
TinyC6-U-01, XIAO MG24, WIZ850io, CC1101, ZAC93/WK2132, LD2450 and BME680 keep
their existing roles. The PoE source remains the battery-fed switch, followed
by the isolated splitter and regulated low-voltage supplies.

## Why this exact board

The VIE has a factory external antenna connector, two 19-pin male headers,
8 MB flash and 8 MB physical PSRAM. These are the specifications of the
**complete board**, not an assumption based on the WROVER module family.
[Espressif's ordering table](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html#ordering-information)
identifies this exact configuration. An unqualified “ESP32 DevKit” listing is
not sufficient: the WROOM variants lack the selected PSRAM, and VE uses a
printed antenna.

The original ESP32 has three hardware UART controllers. They serve the radar,
Zigbee NCP and Thread RCP; the existing I²C UART bridge still serves Z-Wave.
Ethernet and CC1101 share SPI with separate chip selects. Keeping these
interfaces avoids adding another controller or dropping an existing service.
The module uses ECOv3 silicon; the build requires revision 3 or newer.

We retain PSRAM because this is a combined OTBR, Ethernet and BLE application,
not a minimal single-purpose BLE proxy. A no-PSRAM WROOM or a smaller C3 is not
a qualified replacement for this full build. Moving Z-Wave, Thread or radar to
another processor would be a different architecture, not a cheaper host swap.

## Cost and limits

The [shopping guide](mc2-shopping.md) records the exact source and verification
level. The indexed one-board VIE offer was **$9.48**, versus the previously
inspected S3 promotion at **$15.20**: **$5.72 / 37.6% less for the host board**.
Shipping, taxes, promotions and stock can change. This is not a claim that the
whole hub costs 37.6% less; antennas, radios and the other modules remain.
If an MC2-A board has already been manufactured, replacing that carrier adds
cost and can erase the saving on a single unit.

Tradeoffs are explicit:

- **BLE 4.2:** legacy advertisements and three active HA proxy connections are
  configured. BLE 5 extended advertising and LE Coded PHY are unavailable.
  An external antenna does not add those capabilities or guarantee the same
  coverage as another radio. [Module datasheet](https://documentation.espressif.com/esp32-wrover-e_esp32-wrover-ie_datasheet_en.html).
- **4 MB directly addressable PSRAM:** the module physically contains 8 MB, but the classic
  ESP32's direct memory mapping covers 4 MB. We do not count the rest as
  available heap. PSRAM is set to **quad 40 MHz** to avoid the additional SPI
  host reservation needed at 80 MHz. [ESP-IDF memory restrictions](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32/api-guides/external-ram.html).
- **Different carrier:** VIE is a 38-pin board; the previous S3 board was
  44-pin with a different row spacing. MC2-B adds explicit boot-strap biasing.
  Never insert VIE into the MC2-A footprint or reuse the old pin map.
- **Different binary and first flash:** the new host uses the `esp32` target,
  new factory image and `mc2-classic-hub` node identity. S3 firmware is not an
  OTA migration path. The USB-UART bridge programs the loose board; runtime
  UART logging is disabled to reserve all three hardware UARTs.
- **Power is unmeasured:** an older or cheaper processor is not evidence of
  lower energy consumption. Keep the simultaneous-load and 72-hour tests.

## Assembly and verification

Use only the current [pin-to-pin assembly guide](external-antennas.md),
[generated connector ledger](../hardware/external-antenna/cad/connectors.json)
and [firmware instructions](../firmware/external-antenna/README.md).
The 10 kΩ pull-downs on GPIO12/SCK and GPIO2/MOSI are part of the design, not
optional accessories. GPIO12 must be low at reset for the selected module's
3.3 V flash domain, and GPIO2 low for UART download entry. Preserve the
separate local 3.3 V rails and all other documented straps.

The authoritative digital results are the [firmware build record](../firmware/external-antenna/build-evidence.json),
[hardware checks](../hardware/external-antenna/validation.md) and
[enclosure verification](../mechanical/module-carrier/external-antenna-prototype/README.md).
The compiled MC2-B application is **1,708,944 bytes**, leaving **2,223,216 bytes**
in each 3,932,160-byte OTA slot. The final image header identifies classic
ESP32 and minimum revision 3.0. KiCad reports zero ERC, DRC, unconnected-item
and schematic-parity errors. The 15 enclosure tests pass; its five printable
meshes remain byte-identical because the outline and supports did not move.

Compilation and routing checks do not prove free runtime heap or reliable
simultaneous traffic. Before deployment, record internal free/largest heap,
PSRAM availability, reset/recovery behavior, BLE connections, RF RX/TX,
Zigbee flow control, Thread routing, Z-Wave and radar traffic together.

The device has not been flashed or switched in Home Assistant as part of this
source migration. Back up credentials and network state before a later
physical migration. The [MC2-A snapshot](https://github.com/ha-homelab/ha-radio-hub/tree/fee52fb67c3286e3f22925347ef7a35a720c2a55)
retains the original S3 design and its build evidence.
