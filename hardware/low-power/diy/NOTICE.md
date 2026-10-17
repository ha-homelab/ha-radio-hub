# LP-D0 source and library notices

JST XH footprint bodies originate from the library bundled with official KiCad 10.0.6. This is a bundled-library version statement, not a claim that the library has a matching Git tag. The final D0 pads are enlarged to 2 mm and represented as normal through-hole pad stacks in KiCad. Only their bottom annuli are manufactured; all holes are drilled manually and remain unplated. Upstream metadata remain in the local files. The KiCad library license and exception are in [KICAD-LIBRARY-LICENSE.md](KICAD-LIBRARY-LICENSE.md).

The Würth 61204021621, axial/radial parts and wire terminal footprints are project-authored geometry. Adafruit adapter mating footprints are project-authored transcriptions of mechanical dimensions and pin connectivity from Adafruit's published Eagle CAD at commit `dbd7a1928c2b668a9edf3d53277063eac4c3e938`: `28-pin SOIC+TSSOP.brd` and `6-pin SOT-23.brd`. The original adapter boards are not distributed or modified here. Source: https://github.com/adafruit/Adafruit-SMT-Breakout-PCBs/tree/dbd7a1928c2b668a9edf3d53277063eac4c3e938 . Those original files carry CC BY-SA 3.0. Adafruit does not endorse this board.

No manufacturer product photographs are redistributed in this directory. The PCB and assembly drawings depict actual generated geometry. All third-party names identify compatible parts only.

The Adafruit adapter bodies sit 6 mm above D0. Their D0-level courtyards describe the two header strips; the full elevated daughterboard outlines remain on assembly layers. This deliberate height-dependent clearance requires the stated standoff and manual inspection. Wire-terminal reference labels are on F.Fab.
