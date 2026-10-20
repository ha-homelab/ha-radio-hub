# Sources and generated artifacts

Custom MC2 module footprints are original carrier drill patterns derived from the manufacturer mechanical dimensions linked in README.md, not modified chip/module SMT land patterns. They are provided for engineering review. The ESP32, C6, XIAO and WIZnet products remain their respective manufacturers' designs.

The vendored standard THT pin-header, resistor and diode footprints originate from the installed KiCad 10.0.6 library, licensed under CC-BY-SA 4.0 with the KiCad Libraries Exception. Upstream: https://gitlab.com/kicad/libraries/kicad-footprints. License and exception: https://www.kicad.org/libraries/license/ . Their original footprint metadata is retained; optional 3D-model path references were removed for portability.

`routing/mc2.ses` was generated locally with FreeRouting 1.9.0; the executable is not redistributed. Native KiCad checks apply to the complete resulting PCB. The renderer-generated assembly drawing is a placement visualization, while native copper SVGs reflect the actual saved PCB.

TinyC6[D] interface facts come from Unexpected Maker `um-series-d` commit `70a46b4c649ec0f8b1087ffb1bebe6ff5ff450e3`. `c6d-evidence.json` records file hashes and the independent coordinate transcription. No manufacturer STEP, schematic PDF or pinout artwork is redistributed.
