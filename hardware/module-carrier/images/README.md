# MC1 image provenance

This is the gallery for the project's single current module carrier. It must not
be confused with the [historical board gallery](../../gallery/README.md).

## Native CAD views

![MC1 top](mc1-board-top.png)

![MC1 underside](mc1-board-bottom.png)

The top and bottom board renders are produced by KiCad from `../cad/mc1.kicad_pcb`.
They represent the actual native carrier layout. Any absent module body or
connector model is not evidence that the physical part can be omitted.

The native render manifest records the PCB and image hashes, KiCad version,
viewpoint and pixel dimensions. Renderer colors are presentation choices, not a
fabrication finish specification.

## Current assembly views

The current version uses the S3-Nano-M host on a 51 × 75 mm main body with a right mounting ear (57 × 75 mm overall), with
controllers facing the room and Ethernet/male harness pins facing the ceiling.

The [room-facing drawing](../cad/assembly-top.svg) shows the three controllers.
The [ceiling-facing drawing](../cad/assembly-bottom.svg) shows Ethernet and the
male harness headers; it is mirrored as seen from the back. Both are generated
from native CAD geometry with physical pad numbers. The
[same-scale comparison](../layout-comparison.svg) shows the area reduction, and
[section principle](../direct-solder.svg) explains the opposing-tail clearance.

## Historical and rejected illustrations

The preceding 65 × 75 mm single-sided layout is archived under
[single-sided-65x75](history/single-sided-65x75/). Its original reports and images
retain their historical meaning.

The preceding 80 × 90 mm USB-service layout is archived under
[usb-service-80x90](history/usb-service-80x90/). Its large cable corridors are no
longer part of the current assembly.

The preceding full-size-S3 renders and browser captures are archived under
[pre-nano](history/pre-nano/). They describe the former 100 × 90 mm board, not the current assembly.

The earlier [160 × 100 mm concept](history/mc1-160x100-concept.png) is retained
only as history, with its [provenance](history/mc1-160x100-provenance.json).
It must not be used for the compact board.

A new image made with the built-in image_gen tool from the compact assembly
drawing was **rejected**: it invented antenna bodies, misrepresented connector
details and exaggerated the RJ45 overhang. The
[rejected image](history/mc1-100x90-rejected-concept.png),
[prompt](compact-layout-prompt.txt) and
[review record](history/mc1-100x90-rejected-review.json) are retained for traceability,
but the image is not shown as a current assembly view. No manufactured-board
photograph is available. No manufacturer photography is redistributed here.

## Screenshots

Browser screenshots show the rendered current MC1 visual guide. They are UI
verification artifacts and must be refreshed when the visible guide changes.
They do not replace the source SVGs or native PCB files.

Captured views: [current PCB](ui-pcb.jpg), [assembly drawing](ui-assembly.jpg),
[ceiling-facing assembly](ui-assembly-back.jpg), [assembly section](ui-stack.jpg),
[size comparison](ui-comparison.jpg), [net search](ui-wiring.jpg), [module architecture](ui-architecture.jpg), and
[Thread recovery](ui-recovery.jpg), and [network updates](ui-updates.jpg). The [screenshot record](screenshot-provenance.json)
records the source hash, viewport and successful search check.
The [migration manifest](../visual-migration.json) accounts for current and
historical visual assets.

## Mounting and routed-length revision

The current layout adds the right mounting ear and a fourth support beside RJ45.
D1 and R1 use non-cardinal angles; the native mirrored assembly view remains the
authority for polarity and pad identity.

- [Support comparison](../studies/mounting-routing/mounting.svg) and [browser capture](ui-mounting.jpg).
- [Measured routing comparison](../routing-comparison.svg) and [browser capture](ui-routing.jpg).
- [Historical three-support baseline](../studies/mounting-routing/baseline/README.md).
