# MC2-C: parts, availability and observed prices

Updated **20 October 2026** for one MC2-C hub with the **PWR1 power assembly**.
The RECOM regulator and its input capacitor were checked on 20 October; other
module offers and the PCB estimate retain their **19 October 2026** observations.
The priced list covers major modules, RF accessories and the input capacitor;
remaining assembly materials are listed separately and still need pricing. The [carrier BOM](../hardware/external-antenna/cad/BOM.csv),
[RF BOM](../hardware/external-antenna/rf-bom.json) and
[assembly guide](external-antennas.md) remain the engineering references.
No order has been placed. Prices below are observed offers, not checkout totals;
discount eligibility, tax, delivery and stock can change.

**Current priced components: $159.47** — $159.07 for the 11 major component
lines plus $0.40 for the input capacitor — or **$173.18 including the five-PCB
quote and PCB shipping**. Smaller assembly
materials, electronics shipping, taxes and import charges remain additional.
The received ZAC93 and existing CC1101/433 MHz antenna do not need to be bought
again. [Jump to all prices and availability](#major-component-cost-and-availability).

## The two ESP boards and the Zigbee board

1. **1 × Espressif ESP32-DevKitC-VIE**, complete development board with
   **ESP32-WROVER-IE**, male headers, 8 MB flash and 8 MB physical PSRAM.
   The original ESP32 maps 4 MB of that PSRAM for capability-based allocation; this
   project uses quad PSRAM at 40 MHz. The **IE** module has the factory external
   antenna connector. Buy the 38-pin board (two 19-pin rows), not a loose module,
   WROOM board, onboard-antenna VE or an S3 board. It runs Ethernet, the active
   BLE 4.2 proxy and Thread Border Router.
   [Espressif's exact ordering table](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html#ordering-information)
   confirms the memory and antenna variant.
   [Mouser exact-part listing](https://www.mouser.com/en/ProductDetail/Espressif-Systems/ESP32-DevKitC-VIE?mgh=1&qs=vmHwEFxEFR%252B9L5ZhUgeToA%3D%3D)
   showed **$9.48 for one and 488 in stock** on its live US page on
   19 October 2026. Confirm the offer and delivery at checkout.
   No exact AliExpress VIE variant has been qualified for MC2-C.
   The previous S3 offer was $15.20 promotional / $22.00 crossed-out price,
   before $5.93 shipping: the observed board-only reduction is $5.72 (37.6%)
   against that promotional price, **not a delivered-cost quote**.
   This purchase requires the **MC2-C** carrier and initial USB-UART flash;
   it is not a drop-in replacement on the older MC2-A PCB.

2. **1 × Unexpected Maker TinyC6[D], order code TC6D-01**.
   Buy the finished development board with 8 MB flash, native USB and its
   supplied loose 1×12 + 1×11 male headers. The
   [manufacturer's exact product](https://unexpectedmaker.com/shop.html#!/TinyC6-D/p/865880851)
   showed **USD $18.00 and 48 in stock on 19 October 2026**. It ships from
   Melbourne, Australia; delivery, tax and any import fees are additional and
   have not been quoted. Stock is an observation, not a reservation.
   Leave the extra female-header and antenna options unchecked: this carrier
   uses direct-solder male headers and the specified SMA pigtail/antenna below.
   Do not fit the supplied battery connector or a LiPo.

   This is the **MC2-C** Thread RCP target. Its onboard antenna is selected at
   reset; our matching firmware selects and verifies the external U.FL path
   through **FXL6408 XIO0**, on the C6's own I²C bus (SDA6/SCL7, address 0x43),
   before starting Thread. This bus is separate from the host's sensor bus.
   Use the [MC2-C firmware instructions](../firmware/external-antenna/README.md);
   an original TinyC6 RCP binary is not an acceptable substitute.
   [Pinned manufacturer files](https://github.com/UnexpectedMaker/um-series-d/tree/70a46b4c649ec0f8b1087ffb1bebe6ff5ff450e3)
   define this board. The old **TC6-U-01** is no longer the shopping target:
   Mouser's US listing now marks it obsolete and unavailable in the region.
   XIAO ESP32C6, ESP32-C6 SuperMini and H2 boards are not pin-compatible substitutes.

3. **1 × Seeed Studio XIAO MG24, pre-soldered, SKU 102010690**.
   This is a Silicon Labs EFR32MG24 board, **not an ESP32**. It runs our
   external-antenna Ember Zigbee firmware. The Sense variant is not needed.
   [Seeed exact part](https://www.seeedstudio.com/Seeed-Studio-XIAO-MG24-Pre-Soldered-p-6381.html)
   shows **$8.90** and in-stock status in the checked product page.
   [AliExpress candidate](https://www.aliexpress.com/item/1005003282607003.html)
   is a mixed XIAO-family listing found in search; its live page failed to load,
   so its MG24/pre-soldered variant, seller, price and stock are **unverified**.
   Prefer the exact Seeed part until those details are checked.

## Power parts: retain the splitter, replace the expensive buck

Buy **1 × RECOM R-78K3.3-1.0** and **1 × Panasonic EEU-FS1H270** input capacitor.
The RECOM costs **$3.98** instead of the previous Pololu's $26.95; the capacitor
adds **$0.40**, so the replacement power parts total **$4.38**. The observed
reduction is **$22.57 including the new capacitor**, before mounting materials,
shipping and tax. Do not buy the old D24V22F3 as well.

The existing **Waveshare POE-SPLITTER-25W-5.5-2.1, SKU 27737** remains the selected
isolated **5 V DC-barrel** splitter. Its fused 5 V output supplies the controller
boards and LD2450 directly, and also feeds the RECOM through J2. The RECOM supplies
**3.3 V peripherals**: WIZ850io, DFR0627, ZAC93, CC1101 and BME680. The development
boards use their own regulators; their local 3.3 V outputs must remain separate.

- **RECOM R-78K3.3-1.0**, DigiKey **945-R-78K3.3-1.0-ND**: 4.5–36 V input,
  3.3 V / 1 A output, SIP-3, 11.5 × 7.55 × 10.2 mm body. Its exact input range
  includes the splitter's 5 V output. Do not substitute **R-78E3.3-0.5**, which
  needs at least 6 V. See the [RECOM datasheet](https://recom-power.com/pdf/Innoline/R-78K-1.0.pdf).
- **Panasonic EEU-FS1H270**, DigiKey **P122402-ND**: 27 µF, 50 V, ±20%, radial
  electrolytic, 105 °C, FS-A series. The 50 V marking is the capacitor's rating;
  this assembly still receives **5 V only**. Body is nominally Ø5 × 11 mm,
  with Ø5.5 × 12.5 mm reserved for tolerance, and 2 mm lead spacing.
  Its 5,000-hour rating at 105 °C is an endurance specification, not a promise
  about the lifetime of the complete hub.
  [Panasonic datasheet](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1255.pdf).
- **1 × 24 × 24 × 1.6 mm isolated-pad perfboard cutoff**, 2.54 mm pitch,
  plus insulated hookup wire, individual heat-shrink sleeves and the printed
  PWR1 tray/restraints. Suitable workshop stock can be reused; these materials
  are not priced below. Use the actual PWR1 pad/wire layout, not uncut stripboard.

The capacitor is fitted close to **VIN and GND** for the datasheet's hard-plugging
condition: positive to VIN, negative to GND. J2 remains the four-wire carrier
interface: **J2.1 → VIN, J2.2/J2.4 → GND, J2.3 ← VOUT**. The RECOM itself has only
three pins; pin **1 = VIN, 2 = GND, 3 = VOUT**. Follow the
[assembly drawing](full-hub-assembly.md#power-and-ethernet) for orientation,
lead insulation, polarity checks and the initial load test. This is an
engineering assembly selection; physical startup and thermal tests remain due.

## Three antennas and three pigtails

The current engineering selection, with the **FH1-MC2-C-PWR1** enclosure, is:

- **3 × TE Connectivity / Linx ANT-2.4-LCW-SMA**
  ([manufacturer](https://www.te.com/en/product-L9000082-01.html),
  [DigiKey listing](https://www.digikey.com/en/products/detail/te-connectivity-linx/ANT-2-4-LCW-SMA/9607799)).
  2400–2485 MHz, 50 Ω, 2.8 dBi peak gain, 83.1 mm long,
  standard SMA male with a center pin. One each for BLE, Thread and Zigbee.
  DigiKey showed **$3.76 each, 2,777 available**; three total **$11.28**.
- **3 × Taoglas CAB.618.E**
  ([manufacturer](https://www.taoglas.com/product/cab-618-e-i-pex-mhf-i-u-fl-to-150mm-1-13mm-coax-black-cable-smaf-bulkhead-straight/),
  [DigiKey 931-CAB.618.E-ND](https://www.digikey.com/en/products/detail/taoglas-limited/CAB-618-E/26766261)).
  150 mm, 50 Ω, 1.13 mm coax, I-PEX MHF I/U.FL-compatible right-angle board plug
  to straight standard SMA female bulkhead with a center socket.
  DigiKey showed **$4.66 each, 48 available**; three total **$13.98**.
  This saves **$74.43** against the previous three Amphenol cables at $88.41.
  Use the RF1 round-hole coupon and revised cable routing. The
  [selection record](pigtail-selection.md) explains the length allowance,
  bend radius and physical checks; the supplier's shared drawing does not
  guarantee the exact 150 mm SKU's length tolerance.

AliExpress options for a lower-cost **sample**, not qualified BOM replacements:

- [BEVOTOP pigtail listing](https://www.aliexpress.com/item/1005001480408807.html)
  was inspected live. Select exactly **Color: SMA F to RF1 F** and
  **Pins: 15CM**, quantity **3**. The selected variant displayed **$3.84**;
  the listing displayed **$1.68** shipping before checkout. This selection
  describes standard SMA and first-generation miniature coax, not RP-SMA
  or RF4/MHF4. Seller naming of miniature plug gender is inconsistent:
  verify the mating geometry against U.FL, not the word “female” alone.
  Its loss, bulkhead dimensions and physical mating fit have not been measured;
  repeat the connector coupon/dry-fit checks before adopting it.
- [ALLiSHOP 2.4 GHz, 3 dBi SMA male (pin) antenna candidate](https://www.aliexpress.com/item/32612052358.html).
  A matching title was found in search, but the live page stopped at CAPTCHA.
  Its currently selected variant, dimensions, stock, price and RF performance
  are **not verified**. Do not treat this as the TE antenna or order from the
  title alone. The exact TE antenna above remains the preferred selection.

The target chain is **radio U.FL → dedicated 150 mm pigtail → SMA female
bulkhead → SMA male 2.4 GHz antenna**. Repeat it three times. There is no combiner.
Do not buy RP-SMA, IPEX4/MHF4, 433 MHz or 868/915 MHz antennas for these three paths.
The existing CC1101 still needs its separate matching 433.92 MHz antenna;
ZAC93 keeps its original regional antenna and LD2450 its printed radar array.

## Major-component cost and availability

These are observed USD offers for the exact selections, before electronics
shipping, tax and import charges. RECOM and Panasonic observations are dated
**20 October 2026**; every other row is dated **19 October 2026**. “Orderable” means the page offered Add to Cart
without an explicit stock count; it is not confirmation of immediate dispatch.
The machine-readable record is [procurement.json](../hardware/external-antenna/procurement.json).

| Qty | Exact item and checked seller | Unit price | Line total | Availability observed |
| ---: | --- | ---: | ---: | --- |
| 1 | [ESP32-DevKitC-VIE — Mouser](https://www.mouser.com/en/ProductDetail/Espressif-Systems/ESP32-DevKitC-VIE?mgh=1&qs=vmHwEFxEFR%252B9L5ZhUgeToA%3D%3D) | $9.48 | $9.48 | 488 |
| 1 | [TinyC6[D] TC6D-01 — manufacturer](https://unexpectedmaker.com/shop.html#!/TinyC6-D/p/865880851) | $18.00 | $18.00 | 48; ships from Australia |
| 1 | [XIAO MG24 pre-soldered 102010690 — Seeed](https://www.seeedstudio.com/Seeed-Studio-XIAO-MG24-Pre-Soldered-p-6381.html) | $8.90 | $8.90 | In stock |
| 1 | [WIZ850io — DigiKey](https://www.digikey.com/en/products/detail/wiznet/WIZ850IO/8789619) | $24.52 | $24.52 | 1,433 |
| 1 | [POE-SPLITTER-25W-5.5-2.1, SKU 27737 — Waveshare](https://www.waveshare.com/poe-splitter-25w-type-c.htm?sku=27737) | $19.99 | $19.99 | Orderable; select the 5 V DC barrel version |
| 1 | [RECOM R-78K3.3-1.0 — DigiKey](https://www.digikey.com/en/products/detail/recom-power/R-78K3-3-1-0/18093033) | $3.98 | $3.98 | 3,242; a separate 989 at factory |
| 1 | [Panasonic EEU-FS1H270, 27 µF input capacitor — DigiKey](https://www.digikey.com/en/products/detail/panasonic-industry/EEU-FS1H270/7381268) | $0.40 | $0.40 | 4,822 |
| 1 | [DFR0627 — DFRobot](https://www.dfrobot.com/product-2001.html) | $8.00 | $8.00 | Orderable |
| 1 | [BME680 STEMMA QT, 3660 — Adafruit](https://www.adafruit.com/product/3660) | $18.95 | $18.95 | In stock |
| 1 | [HLK-LD2450 module — Alexnld](https://alexnld.com/product/hi-link-hlk-ld2450-24ghz-motion-target-tracking-radar-sensor-module-distance-angle-measurement-for-smart-hotel-home-led/) | $21.99 | $21.99 | Seller reports In Stock; select the module variant |
| 3 | [ANT-2.4-LCW-SMA — DigiKey](https://www.digikey.com/en/products/detail/te-connectivity-linx/ANT-2-4-LCW-SMA/9607799) | $3.76 | $11.28 | 2,777 |
| 3 | [CAB.618.E — DigiKey](https://www.digikey.com/en/products/detail/taoglas-limited/CAB-618-E/26766261) | $4.66 | $13.98 | 48; US tariff may be added in cart |

**Major-component subtotal: $159.07; with the input capacitor: $159.47.**
The previous set with the same RF cables and the Pololu was $182.04. Adding the
[five-PCB quote with its quoted shipping](pcb-order.md#quantity-and-delivery)
of $13.71 gives **$173.18 in priced items**. This is **not the complete delivered
hub price**. The received ZAC93 and existing CC1101/433 MHz antenna are excluded
from this owner's additional purchase cost; a new builder must buy them too.

Also required, and **not yet priced**:

- One 24 × 24 × 1.6 mm isolated-pad perfboard cutoff, insulated wire and
  heat-shrink for the RECOM/capacitor assembly; PWR1 tray restraints.
- Three 1N5819 diodes and five axial resistors: one 4.7 kΩ and four 10 kΩ.
- J1–J7 headers and insulated mating contacts, ZAC93 2×5 mating header,
  BME680 QT lead and module wiring.
- 1.5 A time-delay fuse with insulated holder, 5.5/2.1 mm DC adapter,
  cable restraints, fasteners, insulation and printed parts. The fuse rating is
  a starting selection; verify inrush, wire/contact ratings and derating as
  described in the [assembly guide](full-hub-assembly.md#power-and-ethernet).
- Electronics delivery, tax, duties/tariffs and any PCB checkout/DFM adjustment.

Group the RECOM, Panasonic capacitor, WIZ850io, three antennas and three
pigtails in one DigiKey quote to compare delivery charges at checkout.
The Pololu is no longer in this shopping list. No combined delivery total
to ZIP 94121 has been established. RECOM quantity breaks were $3.83 each at
five and $3.767 at ten; buying extra regulators saves cents per unit but
increases this single-prototype order. Buy one electronics set first.

## Before committing the full parts order

Order the **MC2-C fabrication package**, with **TC6D-01** as U2. MC2-B is the
previous fixed-antenna TinyC6 assembly. The [revision and ordering record](pcb-order.md)
ties the current PCB, firmware and enclosure together. Start with five bare
PCBs and components for one complete prototype; the extra PCBs are spares, not a
reason to buy five untested sets of electronics.

Also retain or source **1 × WIZ850io**, the isolated PoE splitter, regulated
5 V output plus the RECOM 3.3 V assembly, fuses, DFR0627, regional ZAC93, CC1101, LD2450, BME680 and
harnesses described in the assembly guide. Use the priced lines and explicit
exclusions above together. The [FH1 full-hub inventory](../mechanical/full-hub/components.json)
and [assembly guide](full-hub-assembly.md) select the finished Waveshare
POE-SPLITTER-25W-5.5-2.1 and specify the modules, power accessories and mounts
for the complete enclosure. The ZAC93 has been received; do not order a second
one for this build. Existing CC1101 and other delivered-part dimensions still
need to be checked against the reserved envelopes.

Connect antennas before powering the radios; the README's assembled concept
omits cables to show the board. Actual pinout and routing come from CAD, not
the generated images.
