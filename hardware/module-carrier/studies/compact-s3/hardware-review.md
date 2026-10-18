# Compact S3 hardware review

Checked 17 October 2026. This is a component and pin-fit study. It does not replace the active MC1 carrier, establish a new carrier size, or certify RF, thermal, power or firmware operation on an untested board.

**Select the Waveshare ESP32-S3-Nano-M for the next prototype.** It preserves 8 MB PSRAM, increases flash to 16 MB and offers factory male headers. Its 21 non-strapping application pins require shared W5500/CC1101 SPI and careful use of its ROM UART and LED-connected pin. **The LOLIN S3 MINI v1.0.0 remains the lower-software-change comparison:** it can retain both SPI buses and all 24 signals, but reduces flash to 4 MB and PSRAM to 2 MB. Neither requires an Ethernet intermediary MCU. The selection prioritizes capacity and ready headers over retaining separate SPI buses.

The Tiny and Zero names are misleading for this particular mechanical requirement. Their advertised GPIO totals include pads that cannot be connected using only ordinary male headers. The missing pins cannot be recovered by removing the USB socket.

## Counting rule

The present firmware uses 24 distinct application signals: six for W5500, six for CC1101, four for Thread UART/reset/boot, four for the Zigbee UART with hardware flow control, two for radar and two for I2C. Sharing the SPI clock/MOSI/MISO reduces this to 21 without deleting functions. Native USB GPIO19/20 and local boot/reset service are additional requirements. See [firmware review](firmware-review.md) for the implementation audit and build evidence.

Pin counts below are derived from manufacturer schematics and pinout drawings. A PTH GPIO is a signal accessible through a normal header hole; bottom test points, castellated-only extra pads, FPC contacts and the USB differential pair are excluded. GPIO3 is excluded conservatively because it is a boot strap. The Mini additionally reserves GPIO43/44 to avoid ROM-UART traffic. The Nano cannot reserve them while retaining all 21 signals.

## LOLIN S3 MINI v1.0.0

The exact chip is **ESP32-S3FH4R2**, with 4 MB flash and 2 MB Quad PSRAM. The PCB is **34.3 × 25.4 mm**, compared with the current DevKit's 62.74 × 25.4 mm body. That is 45.33% less module-body area, not a 45.33% reduction in the whole carrier. Its printed antenna is opposite the native USB-C connector. The two mounting holes and header pattern are visible in the manufacturer's dimension sheet. [Product](https://www.wemos.cc/en/latest/s3/s3_mini.html), [dimension drawing](https://www.wemos.cc/en/latest/_static/files/dim_s3_mini_v1.0.0.pdf).

There are four eight-pin header rows, 32 positions altogether. They expose GPIO1–18, GPIO21, GPIO33–38 and GPIO43/44: **27 GPIO**. Removing GPIO3 and reserving 43/44 leaves exactly **24 application pins**. USB19/20 and the GPIO47 RGB LED are not consuming those 24 pins. GPIO33–38 are usable on this exact Quad-PSRAM chip; an Octal-PSRAM N8R8 pin rule must not be copied onto it. The complete header-by-header ledger is in [board-candidates.json](board-candidates.json). [Official schematic](https://www.wemos.cc/en/latest/_static/files/sch_s3_mini_v1.0.0.pdf).

The intended assembly uses four ordinary 1×8 male headers and direct soldering into the carrier. No underside signal wires or loose SMD parts are needed. **A factory-installed full-header version was not verified.** If supplied bare, those four header strips must first be soldered to the finished Mini. The nominal 2.54 mm header grid and 22.86 mm outer-row spacing need a sample-fit check before releasing a footprint; the rounded dimension sheet alone does not establish fabrication tolerances or pin protrusion height.

The schematic shows an ME6211C33 LDO, native USB, a local GPIO0 BOOT button and EN reset button, without an active UART bridge. Header VBUS is the same net as USB VBUS. Keep the carrier's source-isolation policy: an attached programming cable must not parallel its 5 V supply with the PoE supply. The Mini's 3.3 V output remains separate from the peripheral regulator output. The ME6211's 500 mA maximum is an IC rating, not proof that a hot enclosed Mini can continuously supply that current. Check rail droop and LDO temperature with the final carrier diode and maximum radio/CPU load. [Schematic](https://www.wemos.cc/en/latest/_static/files/sch_s3_mini_v1.0.0.pdf), [Micro One ME6211 datasheet](https://datasheet.lcsc.com/lcsc/1808092141_MICRONE-Nanjing-Micro-One-Elec-ME6211C33R5G_C235316.pdf).

The firmware agent's proposed assignment retains Ethernet, CC1101, Zigbee and I2C pins, moving only Thread UART/control and radar to GPIO33–38. This is the least architectural change. Capacity remains a real qualification gate: a successful compile establishes image fit, not simultaneous runtime memory margin or long-term OTA headroom.

## Waveshare ESP32-S3-Nano-M

The manufacturer offers a **pre-soldered male-header** version. Its board is **43.18 × 17.78 mm**, with two 15-pin rows, 2.54 mm pitch and 15.24 mm row spacing. Module-body area is 51.82% below the current DevKit. It retains **16 MB flash and 8 MB PSRAM**, native USB-C and a ceramic antenna at the opposite end. [Product and package options](https://www.waveshare.com/product/esp32-s3-nano.htm), [dimensions](https://docs.waveshare.com/assets/images/ESP32-S3-Nano-details-size-d435914d61a0d43a84a1c96664de73b1.webp).

The headers expose GPIO0–14, 17, 18, 21, 38, 43, 44, 46, 47 and 48. Excluding straps 0, 3 and 46 leaves **21**. GPIO19/20 remain on USB. GPIO48 also drives the onboard SCK LED through a MOSFET gate; it is not a free pin with no attached load. There is no active UART bridge on GPIO43/44. These facts permit a plausible complete shared-SPI assignment, but provide no spare non-strapping pin. The bottom test pads for GPIO39–42 are excluded. [Pinout](https://docs.waveshare.com/assets/images/ESP32-S3-Nano-details-inter-1-c806cf5e83bb5f6f6f71fc5bad2239c7.webp), [schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf).

GPIO43 emits ROM UART output during boot. A safe assignment must use it as a transmit signal into a UART receiver that tolerates this startup traffic, with reset/framing recovery demonstrated; do not connect it to another actively driven output or assume it stays silent until application startup. GPIO48's gate load must also suit the selected signal. Sharing SPI must pass cold-start, MISO release, reset ordering and simultaneous Ethernet/RF operation tests. The current stock software path can share the bus; that is not yet a hardware acceptance result.

Its MP2322GQH buck is a **1 A** converter at chip level, with a **3–22 V** operating range. The proposed power path keeps the existing component count: **isolated 5 V → existing carrier branch Schottky → JP1.15 VIN → onboard buck → local 3.3 V**. Leave JP1.12 VBUS and JP1.2 3.3 V unconnected on the carrier. USB separately reaches VIN through onboard D3, so those two diodes OR the inputs and prevent either source feeding the other. This bypasses the second diode drop that a VBUS-fed carrier would introduce. **This is a schematic-level proposal, not an approved supply range:** the board advertises external VIN at 6–21 V, although its own USB input operates this same rail below 5 V through D3. Confirm minimum loaded VIN, output ripple, thermal rise and brownout behavior before adoption. Do not infer a guaranteed 1 A spare peripheral budget or join regulator outputs. [Board overview](https://docs.waveshare.com/ESP32-S3-Nano), [schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf), [MPS MP2322](https://www.monolithicpower.com/en/mp2322.html).

Native USB is the service path; there is no separate USB-UART probe to power. Keep the assembly normally powered during service to avoid powering other controllers through I/O. The Nano has no dedicated BOOT button: expose its existing B1/GPIO0 header and a nearby ground for temporary boot selection, and retain access to RESET.

This is the selected next prototype because preserving 8 MB PSRAM and factory headers outweighs the extra SPI/boot qualification. It is a different pinout and footprint from both the Mini and current DevKit, not a drop-in replacement.

## Waveshare ESP32-S3-Tiny-N8R8

The main board is **23.5 × 18 mm**. The N8R8 product option has 8 MB flash and 8 MB PSRAM. Its USB-C and boot/reset buttons are on a separate **18 × 18 mm** service adapter connected by an eight-contact, 0.5 mm FPC. The main board's 23 edge-hole positions carry power/ground and only **20 GPIO: 1–18, 43 and 44**. The additional advertised GPIO are underside pads. Excluding GPIO3 leaves 19 usable without strap loading. Even counting the strap, 20 is fewer than the required shared-SPI 21. [N8R8 option](https://www.waveshare.net/shop/ESP32-S3-Tiny-N8R8-Kit.htm), [pinout](https://docs.waveshare.com/assets/images/ESP32-S3-Tiny-details-inter-fc4d043c04724600472e4ce8f10429a7.webp), [dimensions](https://docs.waveshare.com/assets/images/ESP32-S3-Tiny-details-1-3cb57dcb7847e1db49d2faee9722d6df.webp).

The manufacturer identifies an ME6217C33M5G LDO with an 800 mA maximum, but also gives an approximate 270 mA output-current answer in its FAQ. Neither establishes this hub's thermal or spare-power budget. The ceramic antenna, FPC insertion access and cable bend would need space beyond the bare-board rectangle. **Reject it under the ordinary-header-only rule.** Using underside pads or repurposing service FPC signals would add the assembly and service complexity this redesign is intended to remove. [Overview](https://docs.waveshare.com/ESP32-S3-Tiny), [FAQ](https://docs.waveshare.com/ESP32-S3-Tiny/FAQ).

## Waveshare ESP32-S3-Zero-N8R8-M

This is also **23.5 × 18 mm**, and the N8R8-M option includes 8 MB flash, 8 MB PSRAM and pre-soldered headers. However, its 18 ordinary header positions expose only **15 GPIO: 1–13, 43 and 44**, plus three supply/ground pins. Excluding GPIO3 leaves 14. Its additional small top/bottom pads cannot be counted for this assembly method. It retains native USB-C, boot/reset buttons and a ceramic antenna; the board uses an ME6217C33M5G regulator, and specifies 3.7–6 V on its 5 V input. **Reject it for the host pin budget**, despite its attractive size and header option. [Product options](https://www.waveshare.com/product/esp32-s3-zero.htm?sku=25081), [pinout](https://docs.waveshare.com/assets/images/ESP32-S3-Zero-Pinout-10a4868b32f9da9005e87b2d9d84574e.webp), [dimensions](https://docs.waveshare.com/assets/images/Esp32-S3-Zero-Size-b56afa84e292cd9d532df8b52376fcb2.webp), [overview](https://docs.waveshare.com/ESP32-S3-Zero).

## Alternatives and decision gates

Two conventional large boards were checked as capacity-preserving fallbacks: Waveshare's S3-DEV-KIT-N8R8-M is **63.3 × 25.4 mm** and the full LOLIN S3 is **65.3 × 25.4 mm**. Neither shrinks the existing module. [Waveshare drawing](https://docs.waveshare.com/assets/images/ESP32-S3-DEV-KIT-N8R8-details-size-de1bb65d3985c613f06a65417479c2c5.webp), [LOLIN S3](https://www.wemos.cc/en/latest/s3/s3.html).

Proceed in this order:

1. Qualify the selected Nano-M with shared SPI. Prove boot-UART recovery, input-power behavior and concurrent RF/Ethernet operation with the complete feature set. Keep its full 8 MB PSRAM capacity and factory header preparation.
2. Retain the Mini comparison as a fallback if separate buses prove preferable. Its full firmware must establish OTA slot fit, internal heap and 2 MB PSRAM margin while all features run; confirm the actual supplied header preparation.
3. After selecting one board, design a new carrier footprint from verified geometry and a physical sample. Keep USB/BOOT access, header soldering access, antenna clearance, and the outward Ethernet socket. A smaller S3 does not automatically establish a smaller safe carrier or allow copper beneath its antenna.

Do not remove USB connectors for this change. Both viable compact candidates already retain a normal native-USB service route. No component was ordered, flashed or desoldered during this review.
