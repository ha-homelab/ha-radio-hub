# MC2-C prototype fabrication package

Upload **MC2-C-prototype-gerbers.zip** for a bare-board prototype order.
Use the [ordering instructions](../../../docs/pcb-order.md) for finish,
dimensions and the five-board recommendation. `manifest.json` records the
native source and evidence hashes, fabrication settings and every archive member.

Verify before upload:

```sh
python3 hardware/external-antenna/fabrication/package.py --check
```

This fails if a source, bound build/geometry report or archive member changed.
It is also required in CI. After changing the design, regenerate and validate
the native CAD, firmware and mechanical evidence first, then export with
official KiCad **10.0.6**:

```sh
python3 hardware/external-antenna/fabrication/package.py --cli /path/to/kicad-cli
```

Export performs fresh native ERC/DRC/parity checks before writing the archive.
Native Gerbers and Excellon drill files are not geometrically edited.
Export timestamps are retained. Every export therefore produces a new manifest.
Do not mix an old archive with a newer source checkout.

The four mounting holes are non-plated. The separate plated drill file contains
component holes and vias. The selected finish is **lead-free HASL**; no assembly
or stencil is needed. A small prototype order does not certify the design or
replace the physical checks in the assembly guide.
