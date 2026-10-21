# Order the MC2-D prototype PCB

**Order MC2-D with Seeed XIAO ESP32C6 (Pre-Soldered), 102010636, as U2.**
The previously selected TinyC6[D] costs $41.95 delivered in the owner's cart.
The new US-stocked C6 is $6.38 before shipping and tax, with factory male headers.
MC2-D replaces its footprint, recovery wiring, antenna driver and enclosure model.
Do not mix MC2-B/MC2-C carrier files or TinyC6 firmware with this build.

Start with **five bare PCBs and components for one complete hub**. This is a
prototype fabrication package. Digital checks do not establish physical fit,
RF coverage, power headroom or long-term reliability; test the first assembly
before purchasing electronics for a larger batch.

## Files to send

Upload only
[MC2-D-prototype-gerbers.zip](../hardware/external-antenna/fabrication/MC2-D-prototype-gerbers.zip)
to the PCB manufacturer's Gerber uploader. The accompanying
[manifest](../hardware/external-antenna/fabrication/manifest.json) binds its
contents to the native PCB and verification evidence.

Do not upload the previous private `MC2-B-614c0cd-GERBERS-HOLD.zip`, a drawing
SVG, the repository ZIP or an AI-generated board image.

The archive contains front/back copper, solder mask and silkscreen, the outline,
separate plated/non-plated drill files and a Gerber job file. Open both sides in
the manufacturer's preview and confirm the **MC2-D** board marking and four
mounting holes **plus the rounded service window beneath U2** before submitting. This is a **bare board** order; it does not
include mounted modules, headers or assembly.

## Fabrication settings

- One design, single boards, **100 × 100 mm**, **two copper layers**.
- **FR-4, 1.6 mm**, **1 oz copper**, ordinary green solder mask and white silkscreen.
- **Lead-free HASL**, tented vias, no edge plating, no castellations, no impedance control.
- No stencil and no PCBA service. Carrier joints use through-hole soldering; two fine wires must also be soldered to XIAO underside test pads.
- Preserve separate **PTH and NPTH** drill files. Do not plate the four 2.7 mm mounting holes.
- The design uses 0.25 mm signal tracks, 0.20 mm clearance and 0.40 mm via drills;
  standard 6/6 mil fabrication capability is sufficient.

Use the supplied outline and drill data without scaling. Supplier DFM review
may still identify manufacturing-specific requirements; resolve any question
against the native KiCad source before approving a changed CAM preview.

## Quantity and delivery

The historical [PCBWay calculator](https://www.pcbway.com/orderonline.aspx), checked on
19 October 2026 for the previous MC2-C 100 × 100 mm board with these settings and United States delivery, returned:

- **5 boards:** $5.00 boards + $8.71 shipping = **$13.71**.
- **10 boards:** $18.18 + $12.04 = **$30.22**.
- **20 boards:** $51.36 + $17.71 = **$69.07**.

**Re-quote the MC2-D ZIP before payment:** the new service window must pass supplier DFM; these are budget references, not a fresh MC2-D checkout.

The selected service was **Global Direct Shipping**, quoted at **6–12 business
days** in addition to manufacturing. These are country-level calculator quotes,
not a paid order or an address-specific total. Tax, duties and later DFM or
delivery adjustments are not included. Five boards have both the lowest total
and the lowest per-board cost among these checked offers.

JLCPCB showed $5.30 for five boards with lead-free HASL, but its shipping-country
selector did not provide a usable delivery quote. That incomplete price is not
a demonstrated cheaper delivered alternative. The observed values are stored in
[procurement.json](../hardware/external-antenna/procurement.json).

## What must match the board

- **U1:** ESP32-DevKitC-VIE / WROVER-IE, 38 pins, 8 MB flash and 8 MB physical PSRAM.
- **U2:** Seeed **XIAO ESP32C6 (Pre-Soldered), 102010636**, with two factory 1×7 male headers. [DigiKey](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010636/26553893) showed 21 at $6.38 on 20 October. Solder its two underside recovery leads: TP8/EN → J10.1 and TP2/BOOT9 → J10.2. The onboard GPIO8 pull-up replaces carrier R3.
- **U3:** XIAO MG24, pre-soldered **102010690**, with the external-antenna NCP image.
- **U4:** WIZ850io; data-only Ethernet from the isolated 5 V PoE splitter.
- **Power:** RECOM R-78K3.3-1.0 and its 27 µF input capacitor, on the
  off-board PWR1 mount. J2 remains 5 V / GND / 3.3 V / GND; see
  [the exact connection](full-hub-assembly.md#power-and-ethernet).
- **Firmware:** current MC2-D host and **4 MB XIAO ESP32C6 RCP**, with GPIO3 LOW and GPIO14 HIGH for the external antenna. The updater rejects TinyC6/8 MB images; use the matched build instructions.
- **RF accessories:** three **Taoglas CAB.618.E** pigtails and three
  **TE ANT-2.4-LCW-SMA** antennas; see the [selection record](pigtail-selection.md).
- **Enclosure:** [FH1-MC2-D-PWR1 print package](../mechanical/full-hub/FH1-MC2-D-PWR1-print-package.zip),
  with round SMA cutouts, a wall-thickness-matched coupon and shorter coax routes.
  The RECOM power mount remains. MC2-D revises the XIAO height, coax route and
  underside service-wire clearance; check the new assembly detail before fitting.

The [full shopping list](mc2-shopping.md), [carrier BOM](../hardware/external-antenna/cad/BOM.csv)
and [full-hub inventory](../mechanical/full-hub/components.json) cover the remaining
parts. The received Zooz ZAC93 remains in its separate insulated cradle. Its
five-wire remapped connection to J4 does not change.

After fabrication, follow [Start here](start-here.md): verify loose parts and
program the controllers, dry-fit the case, continuity-check the unpowered carrier,
then test regulated power and each service before switching Home Assistant.
