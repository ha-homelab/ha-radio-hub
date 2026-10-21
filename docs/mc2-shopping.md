# MC2-D: parts, availability and observed prices

Updated **20 October 2026** for one MC2-D hub with the **PWR1 power assembly**.
MC2-D replaces the Australian TinyC6[D] order with the **Seeed XIAO ESP32C6
pre-soldered SKU 102010636**. Buy factory-fitted headers/connectors wherever
available. The [carrier BOM](../hardware/external-antenna/cad/BOM.csv),
[RF BOM](../hardware/external-antenna/rf-bom.json) and
[assembly guide](external-antennas.md) describe the same revision.

**Already ordered: ESP32-DevKitC-VIE.** The owner confirmed the Mouser order;
do not order it again. ZAC93 is received and CC1101/433 MHz antenna are already
owned. Other rows remain offers, not purchases. Each offer retains its observation
date in [procurement.json](../hardware/external-antenna/procurement.json).

**Priced components: $147.85**, including the host's historical $9.48 offer,
or **$138.37 still to buy after excluding that ordered host**. With the historical
five-PCB-and-shipping estimate, the corresponding subtotals are **$161.56** and
**$152.08**. These exclude the unpriced assembly materials, electronics delivery,
tax and tariffs below. The actual paid host total was not provided; these are
not a completed order ledger or a delivered total.

The new Thread board costs **$6.38**, $11.62 below the previous $18 board.
The owner's rejected TinyC6 cart also had **$23.95 Australian shipping**
($41.95 total); that shipping is no longer needed. DigiKey lists USPS Ground
Advantage at $4.99, making **$11.37 before tax/tariffs** an indicative standalone
XIAO shipment, subject to checkout. Prefer one combined DigiKey order.
[Published US delivery rates](https://www.digikey.com/en/help-support/delivery-information/delivery-time-and-cost).

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
   This host is already ordered. No exact AliExpress VIE variant has been qualified for MC2-D.
   The previous S3 offer was $15.20 promotional / $22.00 crossed-out price,
   before $5.93 shipping: the observed board-only reduction is $5.72 (37.6%)
   against that promotional price, **not a delivered-cost quote**.
   This purchase requires the **MC2-D** carrier and initial USB-UART flash;
   it is not a drop-in replacement on the older MC2-A PCB.

2. **1 × Seeed Studio XIAO ESP32C6 (Pre-Soldered), SKU 102010636**.
   [DigiKey 1597-102010636-ND](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010636/26553893)
   showed **$6.38 and 21 in stock** on 20 October 2026. Select **102010636**,
   with two factory-soldered 7-pin male headers. Do not substitute the unsoldered
   **113991254**, three-pack **102010574**, or TinyC6. No extra female sockets
   are used in the current direct-solder carrier height.

   This 4 MB board is the dedicated MC2-D Thread RCP. It has native USB and
   a switched external U.FL path. MC2-D firmware sets **GPIO3 LOW, GPIO14 HIGH**
   before Thread starts; TinyC6's I²C-expander firmware is incompatible.
   [Manufacturer pin map and RF switch](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/).

   **Two small solder joints remain on the module:** EN and BOOT are underside
   pads, not header pins. Fit flexible insulated 30 AWG leads from **TP8/EN to
   J10.1** and **TP2/BOOT to J10.2**, with strain relief and the carrier's service
   window. These are required for the existing automatic reset and network RCP
   update/recovery functions. Do not omit them or confuse the bottom view with
   a top view. Follow the [assembly guide](external-antennas.md).
   GPIO8 already has a local pull-up on XIAO; the former carrier R3 is removed.
   No battery connector or battery is needed.

3. **1 × Seeed Studio XIAO MG24, pre-soldered, SKU 102010690**.
   This is a Silicon Labs EFR32MG24 board, **not an ESP32**. It runs our
   external-antenna Ember Zigbee firmware. The Sense variant is not needed.
   [DigiKey exact part](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010690/26553865)
   showed **$8.90 and 16 in stock** on 20 October 2026.
   [AliExpress candidate](https://www.aliexpress.com/item/1005003282607003.html)
   is a mixed XIAO-family listing found in search; its live page failed to load,
   so its MG24/pre-soldered variant, seller, price and stock are **unverified**.
   Prefer the exact DigiKey SKU until those details are checked.

## Factory-assembled connector policy

| Component | Buy this assembly | Work still needed |
| --- | --- | --- |
| ESP32-DevKitC-VIE | Complete 38-pin board with fitted headers; already ordered | Solder factory header tails into carrier |
| XIAO ESP32C6 | **102010636**, factory 2×7 male headers | Two underside EN/BOOT leads, then carrier joints |
| XIAO MG24 | **102010690**, factory 2×7 male headers; not Sense | Carrier joints; use onboard programming probe |
| WIZ850io | Complete WIZnet plug-in module, both 1×6 headers and RJ45 fitted | Carrier joints |
| DFR0627 | Finished Gravity module with fitted connectors | Connect the supplied Gravity cable and prepared UART harness |
| Adafruit BME680 3660 | STEMMA QT revision with fitted JST-SH sockets | Plug in a ready-made QT lead; leave loose 0.1-inch header unused |
| HLK-LD2450 | Complete module with factory connector; order a matching ready-made cable if absent | Connect cable according to pin labels |
| Zooz ZAC93 / CC1101 | Reuse the received/existing modules | Remapped mating harnesses; no duplicate purchase |
| RECOM R-78K3.3-1.0 | Finished SIP-3 converter with integral leads | Solder converter, capacitor and links on the PWR1 perfboard |

Bare carrier PCBs are still ordered without assembly. Their headers, diodes and
resistors, the RECOM perfboard and two C6 recovery leads require a soldering iron.
Factory-soldered module headers reduce work; they do not make the complete hub
solderless. Prefer precrimped mating wires over buying loose crimp contacts.

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

The current engineering selection, with the **FH1-MC2-D-PWR1** enclosure, is:

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
shipping, tax and import charges. C6, MG24, DFR0627 and BME680 US offers were checked
on **20 October 2026**, as were RECOM and Panasonic. The other prices retain their
**19 October** observations. “Orderable” is not a guarantee of immediate dispatch.
The machine-readable record is [procurement.json](../hardware/external-antenna/procurement.json).

| Qty | Exact item and checked seller | Unit price | Line total | Availability observed |
| ---: | --- | ---: | ---: | --- |
| 1 | [ESP32-DevKitC-VIE — Mouser](https://www.mouser.com/en/ProductDetail/Espressif-Systems/ESP32-DevKitC-VIE?mgh=1&qs=vmHwEFxEFR%252B9L5ZhUgeToA%3D%3D) | $9.48 historical | $9.48 historical | Already ordered; actual paid total not provided |
| 1 | [XIAO ESP32C6 pre-soldered 102010636 — DigiKey](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010636/26553893) | $6.38 | $6.38 | 21; US distributor |
| 1 | [XIAO MG24 pre-soldered 102010690 — DigiKey](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010690/26553865) | $8.90 | $8.90 | 16 |
| 1 | [WIZ850io — DigiKey](https://www.digikey.com/en/products/detail/wiznet/WIZ850IO/8789619) | $24.52 | $24.52 | 1,433 |
| 1 | [POE-SPLITTER-25W-5.5-2.1, SKU 27737 — Waveshare](https://www.waveshare.com/poe-splitter-25w-type-c.htm?sku=27737) | $19.99 | $19.99 | Orderable; select the 5 V DC barrel version |
| 1 | [RECOM R-78K3.3-1.0 — DigiKey](https://www.digikey.com/en/products/detail/recom-power/R-78K3-3-1-0/18093033) | $3.98 | $3.98 | 3,242; a separate 989 at factory |
| 1 | [Panasonic EEU-FS1H270, 27 µF input capacitor — DigiKey](https://www.digikey.com/en/products/detail/panasonic-industry/EEU-FS1H270/7381268) | $0.40 | $0.40 | 4,822 |
| 1 | [DFR0627 — DigiKey](https://www.digikey.com/en/products/detail/dfrobot/DFR0627/12091972) | $8.00 | $8.00 | 121 |
| 1 | [BME680 STEMMA QT, 3660 — DigiKey](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3660/7915571) | $18.95 | $18.95 | 388 |
| 1 | [HLK-LD2450 module — Alexnld](https://alexnld.com/product/hi-link-hlk-ld2450-24ghz-motion-target-tracking-radar-sensor-module-distance-angle-measurement-for-smart-hotel-home-led/) | $21.99 | $21.99 | Seller reports In Stock; select the module variant |
| 3 | [ANT-2.4-LCW-SMA — DigiKey](https://www.digikey.com/en/products/detail/te-connectivity-linx/ANT-2-4-LCW-SMA/9607799) | $3.76 | $11.28 | 2,777 |
| 3 | [CAB.618.E — DigiKey](https://www.digikey.com/en/products/detail/taoglas-limited/CAB-618-E/26766261) | $4.66 | $13.98 | 48; US tariff may be added in cart |

**Major-component subtotal: $147.45; with the input capacitor: $147.85.**
After excluding the already ordered host's historical $9.48 offer, **$138.37**
of priced components remain to buy. Adding the historical [five-PCB estimate](pcb-order.md#quantity-and-delivery)
with its shipping gives **$161.56 including the host**, or **$152.08 excluding it**.
The unchanged board size permits a like-for-like calculator comparison, but the
new MC2-D Gerbers require fresh supplier DFM acceptance. These subtotals exclude
received ZAC93 and existing CC1101/433 MHz antenna; new builders must buy them too.
They are **not complete delivered hub prices**.

Also required, and **not yet priced**:

- One 24 × 24 × 1.6 mm isolated-pad perfboard cutoff, insulated wire and
  heat-shrink for the RECOM/capacitor assembly; PWR1 tray restraints.
- Two 1N5819 diodes for D2/D3 and an insulated 22 AWG wire link for D1.
  The submitted order contains three diodes: keep one spare. **Do not fit a
  diode at D1**; its extra drop reduces the host regulator headroom.
- Four axial resistors: one 4.7 kΩ and three 10 kΩ.
- J1–J7 and J10 headers and insulated mating contacts, ZAC93 2×5 mating header,
  BME680 QT lead and module wiring.
- 1.5 A time-delay fuse with insulated holder, 5.5/2.1 mm DC adapter,
  cable restraints, fasteners, insulation and printed parts. The fuse rating is
  a starting selection; verify inrush, wire/contact ratings and derating as
  described in the [assembly guide](full-hub-assembly.md#power-and-ethernet).
- Two flexible insulated 30 AWG recovery leads for XIAO TP8/EN and TP2/BOOT,
  individual joint insulation and strain relief.
- Electronics delivery, tax, duties/tariffs and any PCB checkout/DFM adjustment.

Group the pre-soldered XIAO C6, MG24, DFR0627, BME680, RECOM, Panasonic capacitor,
WIZ850io, three antennas and three pigtails in one DigiKey quote to compare delivery charges at checkout.
The Pololu is no longer in this shopping list. No combined delivery total
to ZIP 94121 has been established. RECOM quantity breaks were $3.83 each at
five and $3.767 at ten; buying extra regulators saves cents per unit but
increases this single-prototype order. Buy one electronics set first.

## Before committing the full parts order

Order the **MC2-D fabrication package**, with **102010636** as U2.
MC2-C used TinyC6[D]; its Gerbers and RCP image are not substitutes for MC2-D. The [revision and ordering record](pcb-order.md)
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
