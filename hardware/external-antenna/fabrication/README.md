# MC2-D prototype fabrication package

Upload **MC2-D-prototype-gerbers.zip** for a bare-board prototype order.
This revision adds a **6 × 10.9 mm internal routed opening with R1.5 mm corners** for XIAO recovery-pad access. The old TinyC6 MC2-C archive is incompatible and is retained only in its historical release. Obtain the manufacturer's DFM acceptance and a new checkout quote including this opening; the previous five-board price is a reference, not a binding quote for this revision.
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

An enclosure or off-board RF accessory change does not require a new Gerber
export when the native PCB and firmware are unchanged. First regenerate and
validate the mechanical reports and print package, then run:

```sh
python3 hardware/external-antenna/fabrication/package.py --refresh-assembly-evidence
python3 hardware/external-antenna/fabrication/package.py --check
```

This explicit operation checks the existing ZIP, all ten member hashes, and the
same native/firmware/mechanical evidence guards as `--check`. It only permits
source changes under `mechanical/full-hub/` and the exact off-board
`hardware/external-antenna/rf-bom.json` file, plus the exact shared mechanical
helper `mechanical/module-carrier/external-antenna-prototype/build.py`. Mechanical
source paths are resolved to their canonical repository paths before binding.
A changed, added or removed native
CAD or firmware source binding requires a fresh export instead. It updates only
the manifest's assembly evidence binding and records that no new native export
or ERC/DRC run took place. The archive and its original native export timestamps
remain untouched. `--check` still rejects any unrefreshed source difference.

The four mounting holes are non-plated. The separate plated drill file contains
component holes and vias. The selected finish is **lead-free HASL**; no assembly
or stencil is needed. A small prototype order does not certify the design or
replace the physical checks in the assembly guide.
