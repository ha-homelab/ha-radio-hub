# Prototype procurement

For photographs, identification drawings and AliExpress search links, use the
[illustrated parts catalog](../docs/parts-catalog.md). It keeps the original Pi
build, C0 + M0, I0 and the bench reference in separate inventories. The quantities
below apply to the original Pi-based build, not the single-S3 alternatives.

Use the [BOM CSV](bom.csv) or equivalent [BOM JSON](bom.json). A fully wired assembly needs the `common` and `wired_rf_only` rows: **two** ESP32-S3-ETH-M boards in total, three separate internal Ethernet patch cables, two USB radio extensions and three USB-C power harnesses. Exclude `compatibility_wifi_only` rows. `injector_only` is needed only with a separate PoE injector; `optional` is not part of the baseline assembly.

The main board models have been selected, but several order items are still defined by technical requirements. The `select_after_connector_check` field means that a part number cannot be selected before inspecting the relevant board. A blank price means no quote is available, not that the part is free. Do not treat the main-module prices alone as the complete order total.

## What to buy and what to reuse

- PSE: an existing active IEEE 802.3at port with 30 W available, or an external [Omada POE160S / TL-POE160S](https://www.omadanetworks.com/us/business-networking/omada-accessory-poe-adapter/poe160s/). The injector includes a mains cable. Its LAN cable C16 and the PoE cable to the enclosure C15 are separate from the three internal C1/C8 cables. Do not buy a PoE HAT as a substitute for a PoE source.
- PS1: on the shared Waveshare product page, select **DC Port / POE-SPLITTER-25W-5.5-2.1**, not the USB-C version. Its captive male RJ45 lead plugs directly into switch port 1; no fourth separate patch cable is needed. The male DC lead requires female mating lead C10. SW1 must be the 5 V TL-SF1005D v13; another revision requires a new power and enclosure check.
- U4/U10: two **ESP32-S3-ETH-M, SKU 34882** boards with soldered male headers, no camera and no PoE module. [Waveshare](https://docs.waveshare.com/ESP32-S3-ETH) lists separate SKUs for these variants. Do not install microSD cards in the ESP32 boards; SD1 is only for the Pi.
- U5: move the existing ZAC93 itself, not the entire previous ESP32 board. Keep the old board for rollback. Retain the regional variant and stock antenna; do not replace the controller while physically moving the network without a separate migration plan.
- U9/A2: the existing CC1101 and its matched 433.92 MHz antenna. The wired version requires accessible **GDO0 and GDO2**. If GDO2 is not on the connector, identify a documented connection point or compatible module before buying the remaining RF accessories; the presence of a CC1101 chip does not guarantee this.
- U2/A1: SLZB-07**Mg24** with its antenna. U3: Nordic **PCA10059**, not a development kit. The baseline does not require buying external antennas for Nordic, ZAC93, LD2450 or the main S3. When routing the existing RF antenna through a wall, match the SMA/RP-SMA type and gender to its actual connector; no universal pigtail has been selected.
- U7/C6: Adafruit **3660 + 4397**. BME680 does not include a QT cable; 4397 provides a 150 mm JST-SH → female-socket cable that fits the S3 male headers. Its length counts toward the total 200 mm I²C harness limit. The QT board outline in the [official EagleCAD](https://github.com/adafruit/Adafruit-BME680-PCB/blob/master/Adafruit%20BME680.brd) is 25.4 × 17.78 mm; the plug and cable bend extend beyond it.

## Power harness — before applying power

J1 must have one input pair and **five** output pairs. C10 connects the splitter DC output to the common fuse and then the 5 V bus. Five separate fuses feed the Pi, switch, main S3, RF S3 and radar from this bus. GND is common, with no series fuse. F1 therefore comprises six insulated holders with selected DC fuses, not one holder for the entire assembly. Ratings and the total-current limit are in [power.md](power.md).

Before ordering C10 and C11, record connector gender, outer/inner diameter, insertion length and polarity. The splitter specifies 5.5/2.1 mm; that is **not** the TP-Link input specification. For C10, the rating of at least 5 A must cover the whole connector and wire, not just the terminal. Arbitrary CCTV adapters and breadboards do not establish that rating.

The following power parts have been selected:

- **C4/C9 — two DFRobot FIT0993**, one per S3. The manufacturer specifies terminal input, USB-C output, **5 V / 2 A**, 300 mm length and 4 mm cable diameter. Connect each 1 A fused branch with `+` to 5 V and `−` to GND; leave terminals `D+`, `D−` and `S` unused and insulated. Secure the terminal block against strain. [DFRobot](https://www.dfrobot.com/product-2831.html).
- **C3 — Adafruit 4536**, DC socket → USB-C, with **C17 — Same Sky PP3-002A** and a short 20 AWG pair from C7. C17 has 5.5/2.1 mm outer/inner diameters: after the Pi fuse, connect 5 V to the center contact and GND to the outer contact, and insulate the solder joints. [Adafruit](https://www.adafruit.com/product/4536) explicitly lists Pi 4 compatibility, but **does not publish a separate 3 A current rating**. The 6 A rating applies only to [plug C17](https://www.sameskydevices.com/product/resource/pp3-002a.pdf), not to the complete adapter or harness. C3 is therefore a prototype candidate: before connecting the Pi, load-test the complete harness up to 3 A, measure output voltage and heating, then test under actual Pi load. Reject this option if voltage drop or heating is excessive.

C3 has no PD negotiation or wrong-voltage/polarity protection: use only verified 5 V. A USB-C PD trigger cannot replace the selected source adapter. During fit checks, allow for the rigid projection of C3 plus C17 beyond the Pi USB-C connector and the loops in the 300 mm C4/C9 cables. Until the power harness, C10/C11 and fuses are verified, the kit is not a physically tested assembly.

Do not simultaneously connect the switch's stock mains supply or computer USB to a module already powered by J1. Do not join the local 3V3 regulator outputs of the two S3 boards. Detailed connections are in [wiring.md](wiring.md).

## Other connectors and consumables

- C12: a ZAC93 2×5 mating header and four secured conductors to the S3. Check pitch, gender and pin 1 orientation on the actual module; route pins 1/6/8/10 according to [wiring.csv](wiring.csv). Do not bridge contacts “by default.”
- C13: a matching LD2450 four-wire cable; order separately only if it is absent from the U6 package. Wire colors do not replace the radar's `5V/GND/TX/RX` labels.
- C14: eight CC1101 conductors with a secured connector; R1 4.7 kΩ goes between GDO0/GPIO4 and the **RF S3's local 3V3**. Insulate the resistor leads.
- C7/M3: appropriately sized wire, heat-shrink tubing, labels, cable ties, insulating standoffs/screws, grommets and strain relief. Grommet dimensions depend on the actual harness outer diameter and enclosure opening; purchased grommets are not included in the enclosure model. Match board supports to its holes.
- Flashing also requires a working **USB data** cable for the S3 and a computer; the BOM power harness may not carry data. Acceptance requires a multimeter, current meter/5 V load, oscilloscope and temperature measurement equipment. These are tools, do not remain inside the enclosure and are excluded from component prices.

After receiving the parts, first check the fit of the boards, both sides of every plug, cable bends and height below the lid. Then test the power harness and individual modules on the bench. Final printing and 24–72 h of continuous combined operation complete physical validation; a successful firmware compile does not replace them.
