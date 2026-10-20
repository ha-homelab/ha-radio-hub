# MC2-C: exact radio and antenna shopping list

Updated **19 October 2026** for one MC2-C hub. This is the radio/antenna purchase
list, not the complete hub BOM. The [carrier BOM](../hardware/external-antenna/cad/BOM.csv),
[RF BOM](../hardware/external-antenna/rf-bom.json) and
[assembly guide](external-antennas.md) remain the engineering references.
No order has been placed. Prices below are observed offers, not checkout totals;
discount eligibility, tax, delivery and stock can change.

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
   was indexed at **$9.48 for one** on 18 October 2026. Its live page blocked
   automated rechecking, so confirm the current offer, stock and delivery at
   checkout. No exact AliExpress VIE variant has been qualified for MC2-C.
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

## Three antennas and three pigtails

The exact existing MC2 engineering selection is:

- **3 × TE Connectivity / Linx ANT-2.4-LCW-SMA**
  ([manufacturer](https://www.te.com/en/product-L9000082-01.html),
  [DigiKey listing](https://www.digikey.com/en/products/detail/te-connectivity-linx/ANT-2-4-LCW-SMA/9607799)).
  2400–2485 MHz, 50 Ω, 2.8 dBi peak gain, 83.1 mm long,
  standard SMA male with a center pin. One each for BLE, Thread and Zigbee.
- **3 × Amphenol RF 095-902-545-150**
  ([manufacturer](https://www.amphenolrf.com/en-us/part/095-902-545-150/8897/),
  [Mouser listing](https://www.mouser.com/ProductDetail/Amphenol-RF/095-902-545-150?qs=DRkmTr78QASFS985qeOImw%3D%3D)).
  150 mm, 50 Ω, 1.13 mm coax, AMC/U.FL-compatible right-angle board plug
  to straight standard SMA female bulkhead with a center socket.
  These are the specific bulkhead dimensions used by the enclosure fit coupon.

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

## Before committing the full parts order

Order the **MC2-C fabrication package**, with **TC6D-01** as U2. MC2-B is the
previous fixed-antenna TinyC6 assembly. The [revision and ordering record](pcb-order.md)
ties the current PCB, firmware and enclosure together. Start with five bare
PCBs and components for one complete prototype; the extra PCBs are spares, not a
reason to buy five untested sets of electronics.

Also retain or source **1 × WIZ850io**, the isolated PoE splitter, regulated
5 V/3.3 V supplies, fuses, DFR0627, regional ZAC93, CC1101, LD2450, BME680 and
harnesses described in the assembly guide. They are not included in the radio
prices above. The [FH1 full-hub inventory](../mechanical/full-hub/components.json)
and [assembly guide](full-hub-assembly.md) select the finished Waveshare
POE-SPLITTER-25W-5.5-2.1 and specify the modules, power accessories and mounts
for the complete enclosure. The ZAC93 has been received; do not order a second
one for this build. Existing CC1101 and other delivered-part dimensions still
need to be checked against the reserved envelopes.

Connect antennas before powering the radios; the README's assembled concept
omits cables to show the board. Actual pinout and routing come from CAD, not
the generated images.
