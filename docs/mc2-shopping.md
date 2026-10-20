# MC2-B: exact radio and antenna shopping list

Checked **18 October 2026** for one MC2 hub. This is the radio/antenna purchase
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
   checkout. No exact AliExpress VIE variant has been qualified for MC2-B.
   The previous S3 offer was $15.20 promotional / $22.00 crossed-out price,
   before $5.93 shipping: the observed board-only reduction is $5.72 (37.6%)
   against that promotional price, **not a delivered-cost quote**.
   This purchase requires the **MC2-B** carrier and initial USB-UART flash;
   it is not a drop-in replacement on the older MC2-A PCB.

2. **1 × Unexpected Maker TinyC6 with fixed U.FL, order code TC6-U-01**.
   Project documents call this **TinyC6-U-01**. It is the original board with
   8 MB flash, native USB and supplied loose 1×12 + 1×11 headers.
   It runs the dedicated Thread RCP. **AliExpress supply was not found and
   immediate availability remains unconfirmed.**
   [Mouser exact-part listing](https://www.mouser.com/en/ProductDetail/Unexpected-Maker/TC6-U-01?qs=Z%252BL2brAPG1IKH7BFgNUR0g%3D%3D)
   was previously on backorder; its live stock page could not be rechecked.
   The fresh [Kamami listing](https://kamami.pl/en/retired-products/1201003-tinyc6-esp32-c6-development-board-with-esp32-c6-module-ufl-connector-5902186336612.html)
   now redirects into retired products. Old search snippets showing stock are
   not a purchase confirmation. Secure an actual TC6-U-01 before ordering
   carriers. Do not substitute TC6-01, TinyC6[D]/TC6D-01, XIAO ESP32C6,
   ESP32-C6 SuperMini or an H2 board: the present carrier and firmware are
   tied to this layout. [Original manufacturer design files](https://github.com/UnexpectedMaker/esp32c6)
   document the original board; the newer
   [Series D antenna selection](https://unexpectedmaker.com/getting-started.php?mcu=esp32c6)
   uses a different software-controlled RF path.

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

The unresolved item is **the original TC6-U-01**. The board design is digitally
checked, but that does not establish supply. If the original cannot be sourced,
the next engineering step is to qualify an available C6 board and update the
carrier, recovery wiring and firmware together. Ordering a lookalike first does
not resolve this dependency.

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
