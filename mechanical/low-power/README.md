# Low-power concept enclosure

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

**CONCEPT MOCK-UP ONLY — not a fabrication-ready PCB or validated enclosure.**

Separate 190 × 145 × 45 mm enclosure study for a 160 × 100 mm single carrier.
It does not replace the older Pi-based enclosure or claim that the complete
single-host firmware, radio coexistence or power target has been validated.

- [Assembly instructions and limitations](../../docs/low-power-enclosure.md)
- [Parameters and allocation status](parameters.json)
- [Allocation plan](generated/layout-plan.png)
- [Printable geometry preview](generated/exploded-preview.png)
- [3D assembly, metres](generated/assembly.glb)
- [Mesh/interference report](generated/mesh-report.json)

Use the existing Python environment from `mechanical/requirements.txt`:

```sh
python mechanical/low-power/build.py
python mechanical/low-power/build.py --check
python -m unittest discover -s mechanical/low-power -p 'test_*.py'
```

Each new STL is one closed printable solid in millimetres. `carrier_fit_blank.stl`
is a plastic fit template with designer-selected mounting holes, **not a PCB
fabrication file**. `assembly.scad` and `assembly.glb` also contain rectangular
allocation boxes; those are not supplied as printable electronic parts.

The generator reuses boolean, mesh and semantic comparison functions from
`mechanical/build.py`; both source hashes are recorded. `--check` regenerates
into a temporary directory and compares inventory, inputs, checksums, CSG,
STL/GLB geometry and the allocation report without rewriting saved artifacts.
No installed OpenSCAD renderer is required or claimed to have been tested.
