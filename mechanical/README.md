# HA Radio Hub mechanical source

DRAFT V0: 240 × 200 × 80 mm two-level enclosure, plus an external ventilated
45 × 36 × 20 mm BME680 pod. STL geometry is validated; physical fit, print,
thermal and RF tests remain open.

Full instructions, assembly allocation, fasteners, material and print orientation:
[docs/enclosure.md](../docs/enclosure.md).

- Edit `parameters.json`; run `python build.py` with `requirements.txt` installed.
- `generated/*.stl`: individual printable parts, all in their print orientation.
- `generated/*.scad`: CSG source emitted by the same model as each STL.
- `generated/assembly.scad` and `generated/assembly.glb`: assembled visualization only.
  GLB uses metres as required by glTF; all STL files use millimetres.
- `generated/mesh-report.json`: re-import validation and SHA-256 checksums.
- `generated/fit_coupon.stl`: print first to select clearances and insert pilot.
- `generated/exploded-preview.png`, `generated/layout-plan.png`: geometry preview
  and planning envelopes. The latter are not exact models of commercial PCBs.

Do not uniformly scale exported STL to fit a smaller bed. Main base and lid do not
fit a 220 × 220 mm printer. The minimum is 246 × 206 mm including a 3 mm brim.
