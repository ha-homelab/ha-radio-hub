# MC1 hardware

MC1 is the project's **single current custom PCB**: a carrier for finished
S3, H2, MG24 and WIZ850io modules. Male module pins are soldered directly into
plated holes, with controllers on the room-facing front and Ethernet/male harness
headers on the ceiling-facing back. Female module sockets and hand-soldered bare RF modules are excluded.

Current PCB outline: **51 mm horizontal × 75 mm vertical, two copper layers**.
Two-sided placement reduces area by 21.5% against the preceding 65 × 75 mm carrier,
with the same seven function groups. [Equal-scale comparison](layout-comparison.svg).
The Nano pin map, shared Ethernet/CC1101 SPI and matching active firmware replace
the old full-size S3 assignments. The RJ45 opening remains outward-facing on the ceiling side.
Physical USB shells remain included in the fit checks. Program before soldering;
normal updates use the network. H2 v1.3 requires R7 isolation and RX23/TX24 firmware.
Seven male headers are fitted on the back; J8/J9 remain unpopulated local recovery pads.
The five axial parts also mount on the back. Use both assembly drawings and the
[clearance and soldering study](studies/two-sided/assembly-review.md).

Use the [visual guide](index.html), [assembly instructions](../../docs/module-carrier.md),
[CAD source](cad/), [gallery](images/README.md), and
[matching firmware](../../firmware/module-carrier/README.md) together.

The schematic and PCB remain engineering prototypes. CAD and firmware checks do
not establish hardware operation, EMC/RF behavior, power margin or module fit.
An unverified manufacturing output must not be described as production-ready.

The current design is recorded in [designs.json](../designs.json). Earlier
boards are [historical references](../../docs/design-history.md), not alternative
current BOMs.

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
