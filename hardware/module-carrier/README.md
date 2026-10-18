# MC1 hardware

> **Historical MC1 revision.** The current [MC2 external-antenna build](../../docs/external-antennas.md) uses different modules, pins, flash layout and housing. Keep this material with MC1 boards only.


MC1 is the project's **single current custom PCB**: a carrier for finished
S3, H2, MG24 and WIZ850io modules. Male module pins are soldered directly into
plated holes, with controllers on the room-facing front and Ethernet/male harness
headers on the ceiling-facing back. Female module sockets and hand-soldered bare RF modules are excluded.

Current PCB envelope: **47.5 mm horizontal × 75 mm vertical, two copper layers**.
H3 is the sole PCB retention hole. Split enclosure rails support the long edges;
a separate jack stop and cable restraint protect the WIZ header joints.
Actual area is 6.9% below the preceding four-hole board and 26.9% below the historical 65 × 75 mm carrier,
with the same seven function groups. [Equal-scale comparison](layout-comparison.svg).
The Nano pin map, shared Ethernet/CC1101 SPI and matching active firmware replace
the old full-size S3 assignments. The RJ45 opening remains outward-facing on the ceiling side.
Physical USB shells remain included in the fit checks. Program before soldering;
normal updates use the network. H2 v1.3 requires R7 isolation and RX23/TX24 firmware.
Seven male headers are fitted on the back; J8/J9 remain unpopulated local recovery pads.
The five axial parts also mount on the back. Solder the entire back first,
including WIZ, inspect its joints, then fit and solder front U1–U3. Use both assembly drawings and the
[clearance and soldering study](studies/two-sided/assembly-review.md).

Use the [carrier enclosure prototype](../../mechanical/module-carrier/enclosure-prototype/README.md),
[single-anchor rail study](../../mechanical/module-carrier/rail-mount/README.md),
[visual guide](index.html), [assembly instructions](../../docs/module-carrier.md),
[CAD source](cad/), [gallery](images/README.md), and
[matching firmware](../../firmware/module-carrier/README.md) together.

The enclosure prototype has four printable parts: base, cover, trial jack stop
and required 4 mm ceiling spacing frame. Its shell is **84.3 × 121.8 × 57.4 mm**;
installed depth is **61.4 mm**. Fit floor hardware on the bench before ceiling
attachment and verify underside projection is no greater than 3 mm. Actual
module heights, jack contact and printed fit remain to be measured.

The schematic and PCB remain engineering prototypes. CAD and firmware checks do
not establish hardware operation, EMC/RF behavior, power margin or module fit.
An unverified manufacturing output must not be described as production-ready.

The current design is recorded in [designs.json](../designs.json). Earlier
boards are [historical references](../../docs/design-history.md), not alternative
current BOMs.

The [cost review](cost-review/README.md) records the provisional **$5.20 / five
bare boards** and **$55–57 populated-carrier materials** references. They exclude
shipping, tax, labor, enclosure and external modules; they are not a complete-hub
quotation. The [circuit schematic](cad/schematic.svg), [pin wiring](wiring.json) and
[connector ledger](cad/connectors.json) complement the front/back drawings.

Regenerate the presentation with `python3 hardware/module-carrier/render.py`.
The CAD and firmware directories document their separate validation commands.

Current evidence: [native checks](cad/verification.json),
[combined summary](verification-summary.json),
[independent review](independent-review.md), and
[visual migration](visual-migration.json).

Run `python3 -m unittest discover -s hardware/module-carrier -p "test_*.py"`
for the cross-file interface contract and `python3 hardware/module-carrier/render_board.py --check`
to verify native-render provenance.

The [square-layout](studies/square-layout/index.html),
[compact-host](studies/compact-s3/index.html) and
[SMLIGHT](studies/slzb-thread/index.html) studies are historical decision records.
Their selected direction is implemented here; their old build artifacts are not
substitutes for the active firmware or routed CAD.
