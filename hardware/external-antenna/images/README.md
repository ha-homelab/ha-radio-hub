# MC2-B appearance concepts

These raster concepts predate the **MC2-C / TinyC6[D]** revision. They illustrate
the general arrangement, not the current module outline or U.FL position.
Use the [current CAD assembly](../cad/assembly-top.svg) and
[full-hub layout](../../../mechanical/full-hub/layout.svg) to build MC2-C.

The current README uses two new **AI-generated appearance concepts**, made on
18 October 2026 with the built-in `image_gen` tool:

- [Assembled MC2-B](mc2b-assembled-concept.png): classic WROVER-IE host at left,
  TinyC6 upper middle, XIAO MG24 upper right, WIZ850io lower right.
- [Bare MC2-B](mc2b-bare-concept.png): illustrative board finish with no parts.

No antennas or pigtails are attached in the assembled view, as requested, so
the board remains visible. All three radios require their respective antennas
for operation. The host uses one Micro-B USB-UART service connector.

These are not photographs, manufacturing artwork or exact module models.
Pin/hole counts, small components, shield shapes, copper and text are approximate.
Use the [native CAD](../cad/README.md), [assembly drawing](../cad/assembly-top.svg)
and [current shopping guide](../../../docs/mc2-shopping.md) for construction.
The first generated image had an incorrect host antenna extension and power
connector; a corrective pass removed those features before publication.

- [Initial assembled prompt](mc2b-assembled-prompt.txt)
- [Corrective prompt](mc2b-correction-prompt.txt)
- [Bare-board prompt](mc2b-bare-prompt.txt)
- [Reference and output hashes](mc2b-provenance.json)

## Full-hub FH1 exploded appearance

[Full-hub illustration](full-hub-exploded-concept.png) was made on 19 October
2026 with the built-in `image_gen` tool. It shows the intended full assembly,
including the separate ZAC93 cradle, the power and peripheral trays, a raised
radar/lid and the attached BME680 pod. Antennas, coax and most signal harnesses
are omitted so the modules remain visible. They are required in the real build.

This is a presentation image, **not a photograph, measured assembly, exact
mount model or pinout**. The small board features, proportions, retention and
connector details remain illustrative. Use [source-driven exploded CAD](../../../mechanical/full-hub/exploded-preview.png),
[print files](../../../mechanical/full-hub/README.md) and
[pin-to-pin wiring](../../../docs/full-hub-assembly.md) for construction.
Never drill a module or copy apparent wiring from this image.

The initial image was corrected to put the radar parallel to the lid and to
remove invented through-board fasteners from the ZAC93, CC1101, UART bridge and
radar. The regulator has two diagonal fasteners. Fine details are not a claim
that the delivered boards or connectors have those exact shapes.

- [Initial prompt](full-hub-exploded-prompt.txt)
- [Placement and mount correction](full-hub-correction-prompt.txt)
- [Final mount correction](full-hub-mount-correction-prompt.txt)
- [Provenance and output hash](full-hub-provenance.json)

## Historical MC2-A appearance concepts

These originals and their provenance refer to the
[MC2-A snapshot](https://github.com/ha-homelab/ha-radio-hub/tree/fee52fb67c3286e3f22925347ef7a35a720c2a55).

These older S3 images were made on 18 October 2026 with the built-in `image_gen`
tool for the project README. They are **AI-generated concept illustrations**,
not photographs, deterministic CAD renders, fabrication artwork or evidence of
physical assembly. Green solder mask and gold pad finish are presentation choices.

![Assembled appearance concept](mc2-assembled-concept.png)

The assembled image shows the intended general arrangement: S3 at left,
TinyC6 at upper center, XIAO at upper right and Ethernet at lower right.
Small component positions, module internals, connector shapes, pin counts and
traces are approximate. In particular, apparent chip/shield/antenna features
must not be used to identify a purchasable module. Cables and antennas are
omitted for visibility; all three radios require their selected antennas during use.

![Bare-board finish concept](mc2-bare-concept.png)

The bare image illustrates the finish and general hole groups. Its generated
silkscreen labels, pad counts and routing are not electrically authoritative.
Use the [native PCB](../cad/mc2.kicad_pcb),
[actual front copper](../cad/board-top.svg),
[assembly drawing](../cad/assembly-top.svg) and
[shopping list](../../../docs/mc2-shopping.md) for the build.

The reference inputs were rasterizations of `cad/assembly-top.svg` and
`cad/board-top.svg`. The initial assembled attempt had ambiguous coax routing
and was rejected for publication. The corrective image removes the coax and
antennas rather than presenting that routing as correct.

- [Initial prompt](initial-prompt.txt)
- [Assembled-image corrective prompt](assembled-prompt.txt)
- [Bare-carrier prompt](bare-prompt.txt)
- [Source and output hashes](provenance.json)

These images belong to the historical MC2-A S3 revision and must not be used
to identify the depicted MC2-B parts, not the later MC2-C revision.
