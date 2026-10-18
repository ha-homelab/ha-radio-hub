# Two-sided MC1 assembly review

Reviewed against the 65 × 75 mm single-sided reference and the requested arrangement: S3, H2 and MG24 on the **room-facing front**; WIZ850io and male cable headers on the **ceiling-facing back**. This is an assembly study, not physical qualification. No firmware or pin assignment change is required if the native bottom-side footprints retain their electrical pad numbers.

The two-sided arrangement is practical in principle and can reduce board area. The limiting condition is not simply whether the component rectangles overlap: plated-hole leads pass through the board, and every joint must remain accessible at the stage when it is soldered. A smaller layout that cannot be soldered, inspected or mounted without contact is not an improvement.

## Verified dimensions and dimensions still to measure

- **Nano-M:** manufacturer plan view gives 43.18 × 17.78 mm, 15.24 mm row spacing and 2.54 mm pin pitch. The 40.64 mm horizontal dimension spans corner holes, not the fifteen-pin row's 35.56 mm pin span. The product page identifies the `-M` version as having pre-soldered headers. Neither cited drawing establishes the purchased header spacer height or the remaining pin length below that spacer. [Waveshare dimensions](https://docs.waveshare.com/ESP32-S3-Nano), [variant identification](https://www.waveshare.com/product/esp32-s3-nano.htm).
- **H2 DevKitM-1:** official plan view gives 25.40 × 48.26 mm board body, 22.86 mm row spacing and 2.54 mm pitch, with the antenna extension dimensioned separately. It does not provide a complete vertical stack of factory headers, board underside and carrier. [Espressif dimension drawing](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.2_dimension.pdf).
- **XIAO MG24:** the specific pre-soldered SKU is 102010690; the vendor states approximately 21 × 17.8 mm. Existing inspection of the official native CAD gives 20.955 × 17.78 mm and 15.24 mm row spacing. The exact pre-soldered header's stand-off and tail length remain sample measurements. The older general XIAO mechanical guide predates MG24 and must not be treated as its factory assembly drawing. [SKU](https://www.seeedstudio.com/Seeed-Studio-XIAO-MG24-Pre-Soldered-p-6381.html), [MG24 guide](https://wiki.seeedstudio.com/xiao_mg24_getting_started/), [native CAD](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip), [older family guide](https://www.seeedstudio.com/blog/wp-content/uploads/2022/08/Seeed-Studio-XIAO-Series-Package-and-PCB-Design.pdf).
- **WIZ850io:** the manufacturer catalog lists **23 × 25 × 18 mm** and two 1×6 pin rows. Its plan view gives 20.32 mm row spacing, 2.54 mm pitch, a 16.10 mm jack width and 2.70 mm jack projection beyond the PCB. The catalog's 18 mm dimension lacks a vertical datum/tolerance explaining pin inclusion; it is not a verified height above the assembled carrier. [Catalog](https://docs.wiznet.io/Product/Modules/Ethernet-Module), [dimension drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png).
- **Cable headers:** specify an exact part and mating housing before accepting a vertical stack. For example, Samtec TSW-106-07-G-S documents a 0.635 mm square post, 2.54 mm pitch, 5.842 mm post and 10.922 mm overall length. Those values demonstrate why “a 2.54 mm header” is insufficient to specify height; they do not identify the headers fitted by Waveshare, Espressif or Seeed. [Exact header example](https://www.samtec.com/products/tsw-106-07-g-s).

## Opposing pin tails and underside clearance

Use the actual assembled carrier surface as the datum on each side. Define:

- `t`: carrier thickness.
- `L`: free pin length entering the carrier, measured from its seated spacer to the tip.
- `p = L − t`: untrimmed projection out of the opposite carrier face.
- `s`: distance from that opposite carrier face to the opposing module PCB underside.
- `u`: tallest opposing underside component, solder joint or metal feature extending toward the carrier at the overlap.
- `c = s − u − p`: remaining mechanical clearance.

The required clearance is positive **after tolerances, board bow and lead/solder variation**. The current CAD stack selects a residual clearance of **at least 1.0 mm** at every permitted overlap. This is a provisional engineering acceptance limit for this low-voltage prototype, not a vendor dimension, a cited electrical safety standard or a replacement for inspecting the actual assembly. Factory module gaps remain unknown until measured.

An illustration, not vendor data: a 6.0 mm free male pin through a 1.6 mm carrier projects 4.4 mm. It will collide with an opposing PCB whose underside is only 2.5 mm from the carrier. If that tail is trimmed to 1.0 mm and the opposing underside feature is 0.8 mm tall, the resulting clearance is `2.5 − 0.8 − 1.0 = 0.7 mm`, which **fails the current 1.0 mm limit**. That combination would require at least a 2.8 mm measured gap before adding any dimensional tolerance allowance. Different purchased parts can invalidate this example.

Specify a measured maximum protrusion where overlap is permitted. “Trim to no more than 1.0 mm” is an initial target under review, not a universal release dimension: it must leave an acceptable through-hole solder joint and satisfy `s − u − p ≥ 1.0 mm` after tolerances. Measure the maximum of the remaining lead and solder fillet, not only the clipped lead tip. Do not clip pins flush with the plated hole to achieve a drawing, force a module onto tall tails, or rely on solder mask/tape to compensate for physical interference. Inspect for cut fragments, sharp burrs and stressed joints before the opposing module hides them.

Cable-header **short solder tails** project toward the room-facing modules; factory controller **long breadboard posts** project toward the ceiling-facing parts. These are different lengths and must be modeled separately. Header plastic, module PCB undersides, existing factory solder fillets and underside components all count as obstacles. Moving a symbol to the bottom copper layer does not remove any of them.

## Solder-access dependency graph

For every pair of opposite-side components, add the rule **A must be soldered and inspected before B is fitted** when B's body blocks the tool approach to A's solder lands. Use pad plus iron-tip/inspection clearance, not pad center alone. The resulting ordering must have no cycle.

A direct full overlap between H2 and WIZ is particularly problematic. H2's 25.40 mm body is wider than WIZ's 20.32 mm pin rows, while WIZ's 23 mm body is approximately as wide as H2's 22.86 mm rows. If their longitudinal spans also overlap, each can obstruct the other's required solder side. Increasing height may permit an angled tool, but that is a new assembly assumption and should not be the default plan.

WIZ behind Nano is more promising geometrically because its pin rows lie outside the 17.78 mm Nano body when centered. However, the margin from each 1.8 mm carrier pad edge to that body is only `(20.32 − 17.78)/2 − 0.9 = 0.37 mm`. This proves neither comfortable iron access nor inspection. Require a wider working corridor or demonstrate the actual tool approach during dry fitting.

Back-side cable headers placed **between** a front module's rows are usually the straightforward case: solder the cable headers from the front first, inspect and trim their tails, then fit the front module and solder its rows from the back where no header housing blocks them. This is a placement rule, not permission to hide uninspected joints. The exact current layout should publish its own acyclic order after overlap checks.

## Suggested assembly sequence

1. Program and bench-test loose modules. Perform the already required H2 v1.3 R7 isolation and verify continuity. Preserve the established firmware pins and update paths.
2. Dry-fit all factory male pins in an unpowered carrier. Measure actual board-to-board gaps, tail projections, underside features and mating housings; mark every overlap and soldering dependency.
3. Install small through-hole parts and whichever back-side headers will be hidden first. Solder, inspect and trim their front-side tails while those joints are visible. Keep J8/J9 recovery pads unpopulated as specified by the active design.
4. Fit front controller modules in the verified order. Solder and inspect their back-side joints, trimming any tails that will lie below WIZ or cable housings. Use a holder that supports the assembly rather than resting it on antennas, switches or USB shells.
5. Fit WIZ only when its required front-side solder lands remain accessible. If the graph requires WIZ earlier, change the order only after verifying access to every remaining controller joint. A mutual obstruction requires a placement change.
6. Inspect both faces before power-up, including concealed-space clearance with the modules seated. Verify rails and all connections before attaching harnesses. Then verify host/network updating and the retained local recovery operations.

No female module sockets, added interposer, underside flying wires or replacement factory headers are required by this recommendation. Tail trimming, two-sided handling and staged inspection are additional assembly work compared with the previous one-sided layout.

## Ceiling-side depth, Ethernet access and retention

Measure the furthest assembled back-side projection `H_back` from the carrier's back face, including the WIZ jack, cable-header housing and cable exit. Set the ceiling/enclosure stand-off to at least `H_back + clearance`; use a measured cable bend/latch envelope separately. A provisional **20–25 mm ceiling-side allocation** is reasonable for visualization around the catalog's 18 mm WIZ module, but it is **not a released spacer length**. The assembled projection may differ because that 18 mm figure can include parts of the header pins.

The RJ45 must still accept a real plug, allow the latch to be released and allow the cable to bend without pressing the carrier against the ceiling. An edge-facing jack is preferable to a trapped opening between board and ceiling. Connector insertion loads require nearby nonconductive support or enclosure support; the WIZ's twelve soldered signal/power pins should not be the only path carrying repeated cable leverage. Nylon supports and an insulating back enclosure must leave the antenna ends unobstructed. WIZ metal, permanent harness wires and their connectors must stay outside antenna exclusion volumes on **both** board faces.

## Cost and quality tradeoff

Moving components between faces does not itself require more than the existing two copper layers. Bare-board area can decrease without adding electronic parts or losing functions. It does introduce a second assembly orientation, more opportunities for lead interference, a stricter solder sequence and extra inspection. DIY cost moves partly from laminate to labor; an outsourced assembly quotation may change even when the bare-PCB stack-up stays the same. Smaller area does not guarantee an equal percentage saving in delivered price.

Keep the two-sided design if its native footprint parity, copper checks, acyclic assembly order, measured lead clearance and final ceiling mounting all pass. Do not trade those conditions for a few additional millimeters of board reduction.

## Section illustration review

The current `assembly()` illustration seats the factory header plastics against the carrier and the module PCB, rather than implying unsupported adjustable gaps. Its WIZ and controller footprints are separate in section; only the rear cable header lies below the front controller. That permits the stated header-first soldering order in this illustration. The ceiling label explicitly says insulating mounting posts are not shown. The drawing remains qualitative: its pixel heights do not establish factory spacer dimensions or the assembled 1.0 mm residual clearance. The native layout needs its own overlap and assembly-order checks.

## Reference commit CI

The completed validation run for commit `9215e4b25b9819d096b4467a415c8d08944fd780` passed all jobs: current MC1 S3/H2 builds, native carrier/CAD checks, modular prototype, historical single-host prototype, MG24 builds and the aggregate check. No failure was found. [Validation run](https://github.com/ha-homelab/ha-radio-hub/actions/runs/39096897594). This result describes the prior single-sided commit, not qualification of a newly modified two-sided board.
