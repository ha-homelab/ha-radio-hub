# HA Radio Hub mechanical source

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](../docs/module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

DRAFT V0: 240 × 200 × 80 mm two-level enclosure, plus an external ventilated
45 × 36 × 20 mm BME680 pod. STL geometry is validated; physical fit, print,
thermal and RF tests remain open.

Full instructions, assembly allocation, fasteners, material and print orientation:
[docs/enclosure.md](../docs/enclosure.md).

- Edit `parameters.json`; run `python build.py` with `requirements.txt` installed.
- Run `python build.py --check` before committing or packaging. It regenerates
  into a temporary directory and verifies the saved exports without replacing
  them: exact CSG, geometrically equivalent STL/GLB, inventory, input provenance
  and file checksums. Triangle ordering and renderer-specific PNG bytes may vary
  between systems. This does not replace a physical fit or print test.
- From the repository root, run the disposable regression fixtures with
  `python -m unittest discover -s mechanical -p 'test_*.py'`.
- `generated/*.stl`: individual printable parts, all in their print orientation.
- `generated/*.scad`: CSG source emitted by the same model as each STL.
- `generated/assembly.scad` and `generated/assembly.glb`: assembled visualization only.
  GLB uses metres as required by glTF; all STL files use millimetres.
- `generated/mesh-report.json`: re-import validation, generator/parameter
  provenance and SHA-256 checksums of the exported artifacts.
- `generated/fit_coupon.stl`: print first to select clearances and insert pilot.
- `generated/exploded-preview.png`, `generated/layout-plan.png`: geometry preview
  and planning envelopes. The latter are not exact models of commercial PCBs.

Do not uniformly scale exported STL to fit a smaller bed. Main base and lid do not
fit a 220 × 220 mm printer. The minimum is 246 × 206 mm including a 3 mm brim.
