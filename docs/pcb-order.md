# Order the MC2-C prototype PCB

**Order MC2-C with TinyC6[D] / TC6D-01 as U2.** The older MC2-B build used
TC6-U-01, which is obsolete/restricted in the checked US supplier listing.
The user has not bought that old board. MC2-C brings the module selection,
carrier drawing, firmware antenna switch and FH1 enclosure into one revision.

Start with **five bare PCBs and components for one complete hub**. This is a
prototype fabrication package. Digital checks do not establish physical fit,
RF coverage, power headroom or long-term reliability; test the first assembly
before purchasing electronics for a larger batch.

## Files to send

Upload only
[MC2-C-prototype-gerbers.zip](../hardware/external-antenna/fabrication/MC2-C-prototype-gerbers.zip)
to the PCB manufacturer's Gerber uploader. The accompanying
[manifest](../hardware/external-antenna/fabrication/manifest.json) binds its
contents to the native PCB and verification evidence.

Do not upload the previous private `MC2-B-614c0cd-GERBERS-HOLD.zip`, a drawing
SVG, the repository ZIP or an AI-generated board image.

The archive contains front/back copper, solder mask and silkscreen, the outline,
separate plated/non-plated drill files and a Gerber job file. Open both sides in
the manufacturer's preview and confirm the **MC2-C** board marking and four
mounting holes before submitting. This is a **bare board** order; it does not
include mounted modules, headers or assembly.

## Fabrication settings

- One design, single boards, **100 × 100 mm**, **two copper layers**.
- **FR-4, 1.6 mm**, **1 oz copper**, ordinary green solder mask and white silkscreen.
- **Lead-free HASL**, tented vias, no edge plating, no castellations, no impedance control.
- No stencil and no PCBA service. All carrier assembly uses ordinary through-hole soldering.
- Preserve separate **PTH and NPTH** drill files. Do not plate the four 2.7 mm mounting holes.
- The design uses 0.25 mm signal tracks, 0.20 mm clearance and 0.40 mm via drills;
  standard 6/6 mil fabrication capability is sufficient.

Use the supplied outline and drill data without scaling. Supplier DFM review
may still identify manufacturing-specific requirements; resolve any question
against the native KiCad source before approving a changed CAM preview.

## Quantity and delivery

The live [PCBWay calculator](https://www.pcbway.com/orderonline.aspx), checked on
19 October 2026 with the settings above and United States delivery, returned:

- **5 boards:** $5.00 boards + $8.71 shipping = **$13.71**.
- **10 boards:** $18.18 + $12.04 = **$30.22**.
- **20 boards:** $51.36 + $17.71 = **$69.07**.

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
- **U2:** Unexpected Maker **TinyC6[D] / TC6D-01**, supplied male headers soldered on,
  no battery connector fitted. The manufacturer showed 48 available at $18 each
  on 19 October; [check the exact SKU](https://unexpectedmaker.com/shop.html#!/TinyC6-D/p/865880851)
  when purchasing.
- **U3:** XIAO MG24, pre-soldered **102010690**, with the external-antenna NCP image.
- **U4:** WIZ850io; data-only Ethernet from the isolated 5 V PoE splitter.
- **Firmware:** current MC2-C host and TinyC6[D] RCP. The latter verifies the
  FXL6408-controlled external antenna before starting Thread. An old TinyC6
  RCP image lacks this step.
- **Enclosure:** [FH1-MC2-C print package](../mechanical/full-hub/FH1-MC2-C-print-package.zip),
  generated against the updated module body and U.FL endpoint.

The [full shopping list](mc2-shopping.md), [carrier BOM](../hardware/external-antenna/cad/BOM.csv)
and [full-hub inventory](../mechanical/full-hub/components.json) cover the remaining
parts. The received Zooz ZAC93 remains in its separate insulated cradle. Its
five-wire remapped connection to J4 does not change.

After fabrication, follow [Start here](start-here.md): verify loose parts and
program the controllers, dry-fit the case, continuity-check the unpowered carrier,
then test regulated power and each service before switching Home Assistant.
