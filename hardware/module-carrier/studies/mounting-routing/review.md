# Connector support and free-angle routing review

Baseline: commit `6873b00`, the two-sided 51 × 75 mm MC1 carrier. The selected successor is `nano-flange-angled-passives`, now present in the native CAD. This is a design review, not measured mechanical, thermal or signal-integrity qualification. The local mounting flange and placement changes preserve two copper layers, native plated-hole parts and every firmware interface.

## Recommendation

Add the local support beside the RJ45 before optimizing the five axial components. Permit any useful rotation of D1–D3 and R1–R2, while retaining their native 7.62 mm lead pitch, pin identities, body clearance and accessible solder joints. A diagonal footprint is ordinary plated-hole assembly; it does not require bending the component body diagonally or changing its electrical function.

Optimize the **complete power paths and signal return paths**, then reduce unnecessary signal length and vias. Do not select a layout solely because the sum of its drawn copper centerlines is smaller. Keep the diode bands and resistor references unambiguous in the mirrored back-side assembly drawing.

## RJ45 load path and the selected support row

The baseline RJ45 mouth midpoint is `(39,77)` mm. Its nearest support is H3 at `(24.2,57.5)`: 24.48 mm away, with a 19.5 mm setback and 14.8 mm lateral offset. These are geometry measurements, not a stiffness calculation. Deflection depends on load direction, jack height, laminate properties, support restraint and the enclosure.

The selected layout adds a **6 × 27 mm local right flange**, moves H3 to `(24.2,72)` and adds H4 at `(54,72)`. Their common support row is only **5 mm behind the jack mouth**, bracketing its center almost symmetrically: 14.8 mm left and 15.0 mm right. This gives the connector end a much more direct load path than the previous single offset support. XIAO moves upward by 1 mm to retain physical access. Preserve the specified maximum support-body envelope and verify the actual screws, washers and enclosure posts on both faces.

This fourth support is a deliberate quality improvement, with one additional mounting point and its hardware. It does not prove that the WIZ module's twelve header joints are relieved of insertion loads: a support under the **carrier** controls carrier bending, while a correctly fitted **jack/module cradle** or panel restraint transfers connector loads away from those joints. Provide cable strain relief separately, without obstructing the release latch or pressing on components. Do not preload the WIZ PCB or assume the RJ45 metal shell can accept arbitrary clamping.

Samtec's carrier-board guidance describes board reinforcement and assisted mating as ways to limit damage to boards, connectors and solder joints. It concerns its own board-to-board systems; it supports the general load-path principle, **not an allowable force or support spacing for WIZ850io**. No verified WIZ850io insertion-force value is assumed here. [Samtec carrier-board mating and stiffener guide](https://suddendocs.samtec.com/notesandwhitepapers/samtec-com-hpc-carrier-board-mating-and-stiffener-reference-guide.pdf).

## What the baseline routing actually shows

Direct parsing of the baseline native PCB gives **1,942.523 mm of explicit track centerline, 426 segments and 35 vias**. Ground pours, plated-hole barrels, internal module traces and external harnesses are excluded. The total is a comparison aid, not the physical length traversed by one signal.

- The diode-to-H2 supply net is **80.848 mm with two vias**; the diode-to-XIAO supply net is **69.701 mm with two vias**. Both use 0.80 mm tracks. Relocating D2 near H2's lower power-pin region and D3 near XIAO is worth testing before small angle-only changes.
- The diode-to-Nano supply net is already **18.323 mm without vias**. Shortening another branch by moving all three diodes into a common row could make this one worse. Compare each branch and the shared incoming 5 V network together.
- The branched SPI networks contain **117.708 mm MOSI, 107.072 mm SCK and 91.141 mm MISO**, with one, two and one vias respectively. These are whole-net totals, not individual Nano-to-WIZ or Nano-to-CC1101 path lengths.
- RF GDO0 contains **83.893 mm and five vias**; RF CS contains **66.949 mm and no vias**. Moving the pull-up tap toward its actual signal route may remove a detour. A short resistor supply connection alone does not establish that the driven signal path improved.

The source PCB SHA-256 for those baseline measurements is `87e2dbdd2d7be9daeb703dff1356812abf905cf625409c61e812d707ffb88e39`.

## Selected placement and actual results

The final axial positions, expressed as native post-flip angles, are **D1 `(45,16)` at 250°; D2 `(3,51.5)` at 0°; D3 `(17,67)` at 180°; R1 `(38.5,30)` at 10°; R2 `(38,23.5)` at 90°**. D1 and R1 use non-orthogonal orientations. D2 is clear of front-module bodies. XIAO is now at `(18,56.5)`, and the unpopulated J8/J9 recovery pads move to the front aisle at `(29.5,17)` and `(29.5,25)`.

**D3 now lies behind XIAO, creating a new local height qualification.** Its two solder joints must be inspected before XIAO is installed. Measure the actual XIAO underside components over these joints and require `module gap − underside protrusion − tail/fillet height ≥ 1.0 mm`. Normally seated factory header plastics are retained; the assumed example 3.0 mm gap is not a measured fact. The DRC inventory now has 41 intentional projections: 33 beneath H2, six beneath Nano and two beneath XIAO. Classification of these projections does not establish physical clearance.

The [recorded native routing comparison](../../cad/routing-metrics.json) gives **1,942.5231 → 1,748.9646 mm (−9.964%)**, **35 → 19 vias**, and **426 → 350 track segments**. Independent parsing of the final native PCB matched all lengths within 0.001 mm and exactly matched every via count, segment count and the recorded SHA-256 `7f8296edb0317269f6b094847edeb91a2886d2e1fc220150be1a1db43755d6ea`.

- The post-diode H2 supply improves **80.8480 → 17.8231 mm**, XIAO **69.7010 → 5.1542 mm**, and Nano **18.3235 → 14.8316 mm**. All three final post-diode nets have no vias. RF CS improves **66.9491 → 37.9174 mm**, and RF GDO0 **83.8930 → 62.4593 mm**, with GDO0 vias reduced from five to zero.
- The common supply networks get longer: **5 V 71.4904 → 103.4429 mm** and **3.3 V 112.9799 → 144.4114 mm**. Consequently, post-diode savings alone do not quantify each complete connector-to-load voltage drop.
- All three shared SPI net totals worsen: **MOSI 117.7082 → 123.7659 mm**, **SCK 107.0723 → 113.1223 mm**, and **MISO 91.1410 → 102.9214 mm**. MOSI/SCK vias decrease from one/two to zero/one, but MISO increases from one to two. Ethernet CS also increases **52.8126 → 59.2616 mm**, with one additional via. These are real tradeoffs; the total-length reduction does not demonstrate better SPI signal integrity.

The selected board improves local connector support and substantially shortens the targeted supply branches and several peripheral routes. It is not a globally shortest route, and no performance improvement is inferred without checking the final return paths and testing simultaneous traffic on assembled hardware.

## A useful optimization order

1. **Hard constraints first:** unchanged pin/net identity and diode polarity; two layers; original track-width and clearance rules; RF exclusions on both faces; actual support and connector envelopes; acyclic soldering order; and the existing measured-gap requirement of at least 1.0 mm above opposing metal. Reclassify every intentional opposite-side PTH/body projection after moving components; do not reuse stale DRC identities.
2. **Power:** compare incoming-connector-to-load paths, including common-rail segments, the branch diode, return path and vias. Report branch length and estimated resistance with explicit copper-thickness/current assumptions. Confirm loaded voltage on the real hardware. Do not narrow a power trace simply to win a length metric.
3. **SPI:** minimize unnecessary source-to-receiver path length, branch stubs and layer changes while preserving a nearby, continuous ground return. Inspect the filled copper, not only the intended pour outline. The active W5500 clock is 10 MHz; edge rise time, module traces and the external CC1101 harness still matter. No new length-matching serpentine is justified by this review.
4. **Other signals:** remove obvious detours and excess vias without sacrificing the preceding constraints. Score both the worst relevant path and the per-net change; retain total copper length as a secondary summary.

TI's high-speed layout guidance explains why crossing a reference-plane void makes a high-frequency return detour. The same return-path principle is relevant here, but its interface-specific impedance and matching tables are not automatically requirements for this 10 MHz SPI carrier. [TI, High-Speed Interface Layout Guidelines, section 2.4](https://www.ti.com/lit/an/spraar7i/spraar7i.pdf).

Shorter power copper helps, but it does not remove the diode's forward drop. For scale only, assuming 35 µm copper and approximately `1.72e-8 Ω·m` resistivity, a 0.80 mm-wide trace contributes about **0.61 mΩ/mm**. Removing 50 mm saves about 31 mΩ, or 15 mV at an assumed 0.5 A; this excludes vias and the return path and is not a current-capacity rating. The fitted 1N5819 datasheet specifies a **0.60 V maximum forward drop at 1 A** under its stated pulse-test conditions. It is not a constant 0.60 V drop at every operating point. Supply-headroom and thermal checks remain necessary. [Vishay 1N5817/18/19 datasheet](https://www.vishay.com/docs/88525/1n5817.pdf).

## Cost and verification

The flange changes actual laminate area from **3,825 to 3,987 mm² (+4.24%)**, while the enclosing rectangle becomes **57 × 75 = 4,275 mm² (+11.76%)**. Fabrication or panel packing may use that larger rectangle; the laminate increment is not a price quote. Compare quotations with identical quantity, thickness, copper, finish and shipping. Free-angle component placement adds no electronic parts, but irregular outlines and the fourth mounting operation can affect total assembly cost.

Keep unchanged electrical connectivity, raw/classified DRC and ERC, support clearances, routing metrics and the exact source hash with the selected board. Complete source-to-receiver path/return-path review and physical checks remain necessary. Check plug insertion/removal and cable loading in the intended enclosure, without assigning a percentage stiffness improvement from geometry alone. Firmware need not change or be rebuilt solely for these placement and mounting changes.
