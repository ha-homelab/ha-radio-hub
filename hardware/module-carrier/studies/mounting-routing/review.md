# Rectangular carrier and rear-first assembly

The current native layout is **`nano-centered-rear-first`**: a rectangular **51 × 75 mm** carrier, with no mounting ear. WIZ moves 6 mm left from the preceding layout, XIAO rotates into the lower-left position, and a support fits between H2 and XIAO. All firmware pin assignments, two copper layers and the direct-solder factory male headers are retained. This is a geometric and routing review; hardware strength, clearances and signal integrity remain unmeasured.

The immediate comparison is the [ear layout saved from `af287e4`](ear-baseline/README.md). The [older three-support `6873b00` layout](baseline/README.md) remains a separate historical reference. The [equal-scale mounting drawing](mounting.svg) compares the ear baseline with the current native board.

## Current placement and assembly order

Native post-flip coordinates and rotations are WIZ **`(22.84,67.9)`, 0° on the rear**, and XIAO **`(1.5,58.3)`, 0° on the front**. D2 moves to `(3,50.8)`, 0°; D3 to `(12.5,65)`, 180°. D1 remains `(45,16)`, 250°; R1 `(38.5,30)`, 10°; R2 `(38,23.5)`, 90°. Free-angle axial placement uses the unchanged native 7.62 mm lead pitch; diode pin identities and band orientation remain explicit.

The required order now applies to **every fitted rear component**, including WIZ:

1. Fit all **13 rear parts**: WIZ, J1–J7, D1–D3 and R1–R2. Solder from the front, trim as permitted, and inspect every joint before covering it.
2. Fit the **three front controllers**: Nano, H2 and XIAO. Their rear solder lands must remain accessible with all rear parts already installed.

The native placement passes the geometric rear-first access checks, including the modeled physical USB bodies and harness housings. The earlier sequence that fitted WIZ last is historical and must not be used for this revision. Tool access and actual module fit still require a dry assembly check; no female sockets, flying wires or unsupported floating modules are introduced.

**D3 remains behind XIAO.** At each opposing joint require `measured module gap − local underside protrusion − tail/fillet height ≥ 1.0 mm`. The tentative 1 mm tail/fillet limit must preserve a sound plated-hole joint. Factory gaps remain unknown; the 3 mm example is not a measured spacer height. The raw DRC report has 41 classified projections: 33 rear header pins beneath H2, six axial pins beneath Nano and two D3 pins beneath XIAO. Classification does not prove their vertical clearance.

## Support geometry: an explicit tradeoff

The four support centers are **H1 `(29.5,8)`, H2 `(29.5,44)`, H3 `(18,52.03)`, H4 `(48,72)`**. H3 occupies the gap between H2 and XIAO; H4 remains near the right side of the RJ45 end. The mouth midpoint moves from `(39,77)` to **`(33,77)`**. Use the prescribed maximum 5 mm nylon support/head envelope and verify the actual hardware on both faces.

The ear baseline had H3/H4 on one horizontal row, both 5 mm behind the mouth. The new supports are **staggered**:

- H3 is 29.13 mm from the new mouth midpoint and 24.97 mm behind it along the insertion axis. The previous ear-layout H3 distance was 15.62 mm, with a 5 mm setback.
- H4 is 15.81 mm from the new midpoint and 5 mm behind it, essentially retaining the previous right-side geometry.

Removing the ear reduces the outline and meets the requested assembly order, but it gives up the symmetric near-mouth support row. These distances do **not** establish equal or improved stiffness. Deflection also depends on load direction, jack height, laminate properties, post restraint and enclosure support.

Supporting the **carrier** does not automatically unload the WIZ module's twelve header joints. A fitted insulating **jack/module cradle or enclosure stop**, plus cable strain relief, provides a separate load path. It must not preload the WIZ PCB, obstruct the latch or assume an arbitrary allowable clamping force on the metal shell. Samtec's carrier-board guidance supports the general use of reinforcement and assisted mating to limit board, connector and solder-joint damage; it does not specify a WIZ850io force rating or support spacing. [Samtec carrier-board mating and stiffener guide](https://suddendocs.samtec.com/notesandwhitepapers/samtec-com-hpc-carrier-board-mating-and-stiffener-reference-guide.pdf).

## Current routing, compared with the ear baseline

The [native routing ledger](../../cad/routing-metrics.json) records **1,748.9646 → 1,736.7132 mm of explicit track centerline (−0.7005%)**, **19 → 18 vias**, and 350 segments in both revisions. These totals exclude filled copper, plated-hole barrels, internal module wiring and external harnesses. Branched-net totals are not individual source-to-receiver path lengths.

- MOSI falls **123.7659 → 103.3592 mm**, but gains a via: zero → one. SCK falls **113.1223 → 107.9386 mm**, with one → zero vias. MISO is nearly unchanged at **102.9214 → 102.9058 mm**, while its vias rise from two to three.
- Ethernet CS falls **59.2616 → 55.3097 mm**, with two → zero vias. The total-length improvement therefore does not mean every SPI metric improves.
- Post-diode H2 supply falls **17.8231 → 17.1231 mm**, Nano **14.8316 → 14.4240 mm**; XIAO rises **5.1542 → 8.4563 mm**. All three retain zero vias. The common 5 V network grows **103.4429 → 105.0399 mm** and gains one via, while 3.3 V falls **144.4114 → 115.4374 mm**.

The current PCB SHA-256 is `b33c3ff2b299e826cb11e783f835361635d544eda4c71ba62e85cb6318bb2857`. No globally shortest routing or signal-integrity improvement is claimed. Preserve nearby ground returns, inspect the filled copper around layer changes and compare complete supply/return paths rather than only post-diode branches. The W5500 remains configured at 10 MHz; edge rates and the external CC1101 harness still matter. [TI, High-Speed Interface Layout Guidelines, section 2.4](https://www.ti.com/lit/an/spraar7i/spraar7i.pdf).

## Historical result retained: three-support board to ear layout

The older `6873b00` board had **1,942.5231 mm of tracks, 35 vias and 426 segments**. The ear revision reduced these to **1,748.9646 mm, 19 vias and 350 segments**, a **9.964%** track-length reduction. Its main gains were the post-diode H2 supply **80.8480 → 17.8231 mm** and XIAO supply **69.7010 → 5.1542 mm**. All three shared SPI net totals increased in that iteration: MOSI **117.7082 → 123.7659**, SCK **107.0723 → 113.1223**, MISO **91.1410 → 102.9214 mm**.

Those figures describe the two historical boards, not a fresh baseline for the current drawing. Their native sources remain available for reproduction. They illustrate why a smaller total trace length alone is not evidence that every interface improved.

## Cost and remaining qualification

Relative to the immediate ear baseline, the enclosing rectangle drops from **57 × 75 to 51 × 75 mm (−10.53%)**. Actual laminate drops from **3,987 to 3,825 mm² (−4.06%)**. The larger percentage applies to the bounding rectangle, not removed laminate or a guaranteed delivered-price saving. Four mounting points, two copper layers and the electronic part count remain unchanged. Compare fabrication quotes with identical quantity, thickness, copper, finish and shipping.

Shorter supply copper does not remove the series diode drop. For scale only, 0.80 mm-wide, 35 µm copper at approximately `1.72e-8 Ω·m` contributes about 0.61 mΩ/mm; this is an assumption, not an assembled-board measurement or current rating. The fitted 1N5819 specifies 0.60 V maximum forward drop at 1 A under its stated pulse-test conditions, not a constant drop at every operating point. [Vishay 1N5817/18/19 datasheet](https://www.vishay.com/docs/88525/1n5817.pdf).

Keep the native connectivity, classified/raw DRC, ERC, rear-first access checks and source hashes with this revision. Qualify the actual module gaps, solder access, enclosure restraint, loaded rails and simultaneous interface traffic before treating it as a proven assembly. Firmware is unchanged by this placement revision.
