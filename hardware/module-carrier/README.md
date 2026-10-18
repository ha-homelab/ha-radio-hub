# MC1 hardware

MC1 is the project's **single current custom PCB**: a carrier for finished
S3, H2, MG24 and WIZ850io modules. Male module pins are soldered directly into
plated holes. Female module sockets and hand-soldered bare RF modules are excluded.

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
