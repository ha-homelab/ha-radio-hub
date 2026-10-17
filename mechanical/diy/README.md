# DIY print exporter

Requires KiCad 10.0.x CLI, Python 3.9+ and the pinned packages in `requirements.txt`. CairoSVG additionally needs the Cairo native library (for example `brew install cairo` on macOS). If the Python loader cannot find Homebrew Cairo, prefix the build command with `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"`. The exporter only accepts the intentionally restricted LP-D0 geometry: zero-origin rectangular outline, top-side through-hole components, bottom tracks, round drilled holes, and no vias or zones.

```sh
python3 -m venv /tmp/ha-diy-print-venv
/tmp/ha-diy-print-venv/bin/python -m pip install -r mechanical/diy/requirements.txt
/tmp/ha-diy-print-venv/bin/python mechanical/diy/build.py --kicad-cli kicad-cli
/tmp/ha-diy-print-venv/bin/python mechanical/diy/build.py --check
/tmp/ha-diy-print-venv/bin/python -m unittest discover -s mechanical/diy -p 'test_*.py'
```

`--paper a4` is the default. To use US Letter, regenerate into a separate output directory with `--paper letter --output /tmp/ha-diy-letter` and use those PDFs as a matching set. Never let a print driver fit one paper size to another.

The copper SVG is plotted by KiCad at scale 1 with mirror disabled. Every electrical through-hole pilot centre is checked against native pad coordinates, so a mirrored, shifted or unexpectedly cropped plot is rejected. The physical SVG viewport is converted to vector PDF without scaling; the converter's resulting MediaBox is independently checked in points (72/25.4 per millimetre). Copper-only sheets have no assembly labels or dimension lines near the etch area. External crop marks align with the nominal outline, starting 2 mm outside the board; remove them when trimming.

The drilling PDF has a hole-symbol sheet and a copper inspection sheet, both in the *bottom view*, mirrored once from board coordinates. The assembly PDF is the *component view*. The calibration PDF contains independently checked 100 mm X/Y baselines, a 50 mm square and 2.54 mm pitch marks, plus a sacrificial line/space coupon. `drill-map.json` reports component-view coordinates and actual drill diameters. Virtual `adapter_pin` endpoints resolve to their explicit `physical_pin` and add no hole. Their raised-joint height and assembly instructions have a separate page; cut lengths include the routing plan's vertical allowance.

The manifest hashes the native board, exporter, pinned dependency file, output files and optional jumper schedule. `--check` catches stale/modified outputs without running KiCad. It does not assert that a board was physically built or that a printer preserves scale. Those are separate acceptance gates in [the build guide](../../docs/diy-pcb.md).
