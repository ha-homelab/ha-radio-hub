# MC1 split-rail mounting and fit study

[Open the illustrated study](index.html). The carrier sits on selected lower edge ledges, then the second case half closes retaining lips over those edges. **H3 is the only PCB retainer; the case has its own attachment system.** The populated carrier is lowered into the open frame, not pushed through continuous grooves.

This directory provides a native-derived contact plan, an interface section, assembly sequence, historical comparison, editable SCAD and three **fit-coupon STL files**. It does **not** provide a complete printable enclosure. Final case height, front/rear component clearances, closure fasteners, locating stops, H3 support depth, jack restraint and ceiling attachment are unset until measured.

## Contact and movement contract

The current CAD defines maximum contact envelopes on **both faces**:

- Left: `x=0…0.85`, `y=15…54.5 mm`.
- Right: `x=46.3…47.5`, `y=8…74 mm`.
- H3: `(18,52.03) mm`, 2.7 mm hole for the existing nylon M2.5 retainer. Its clearance is not a zero-play locating system.

The contact bands are maximum inward reach **from the actual board edge**, not nominal lip dimensions. The SCAD example reserves a ±0.2 mm in-plane displacement budget at every contact point, including translation, rotation, manufacturing error and assembly play. Its centered lips therefore reach only **0.65 mm left / 1.0 mm right**, and their Y endpoints are inset by 0.2 mm. At the assumed extreme position, contact does not exceed 0.85 / 1.2 mm. Minimum engagement under that example is only 0.45 / 0.8 mm; load capacity remains untested.

That movement budget is not yet physically enforced. The example's 0.2 mm side clearance already consumes the entire 0.2 mm X allowance; it leaves **no additional allowance for board/print error or rotation**. Actual side clearance and maximum edge excursion remain null. Set the final budget from the measured board-edge seats and case locating features. If actual excursion exceeds it, revise the fit and lip dimensions. Do not let positive XY clearance move a lip into a solder joint. The nominal independent geometric review leaves only about 0.32 / 0.33 mm after an explicit 0.5 mm solder-growth allowance, so an unaccounted 0.3 mm shift is significant.

The larger CAD copper exclusions provide flat edge regions; they are not permission to extend the lips. Walls and the eventual lid must also stay clear of module bodies and antennas. The left band starts at y15 to improve H2 antenna separation; that alone does not qualify a full surrounding case. Espressif recommends at least 15 mm antenna clearance in all directions inside the housing, followed by finished-product range testing. Apply that review to the full wall and lid, not only the contact land. [H2 housing guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board).

## Fit coupons before a case

`parameters.json` keeps `pcb_actual_thickness_mm`, `pcb_actual_width_mm`, `selected_slot_height_mm`, front/rear component projections and final case height **null**. The illustrated 1.6 mm PCB and 2.0 mm slot are nominal examples.

JLCPCB publishes ±10% thickness tolerance for boards at least 1 mm thick: a nominal 1.6 mm board may be **1.44–1.76 mm**. Measure the purchased board at the intended contact lands, including local finish and bow. [Manufacturer capability table](https://jlcpcb.com/capabilities/pcb-capabilities/).

Print the coupons with the material, nozzle, orientation and slicer settings intended for the case:

- [1.8 mm slot](fit-gap-1p8.stl): one identifying edge notch.
- [2.0 mm slot](fit-gap-2p0.stl): two notches.
- [2.2 mm slot](fit-gap-2p2.stl): three notches.

The STL orientation places the coupon's outer wall on the bed. Use an unpopulated offcut or unobstructed board edge; do not force the populated assembly into the test part. These coupons have 1.2 mm engagement and test vertical clearance only, not the left rail's final contact width or rail strength. At 1.76 mm board thickness the three nominal gaps leave only 0.04 / 0.24 / 0.44 mm total clearance before printing errors. A larger gap may rattle; a smaller one may bind. Neither is selected automatically.

Prusa advises positive fit clearance, test prints and material/orientation-specific iteration; there is no universal tolerance. Its guidance also treats layer direction and environmental conditions as mechanical design inputs. A successful coupon therefore does not qualify heat resistance, creep, rail retention or installation loads. [Prusa modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).

## Assembly and interfaces still required

1. Program and prepare loose modules. Fit **all 13 rear components first**, including WIZ; solder, trim and inspect from the front. Fit and solder the **three front controllers** afterward.
2. Measure actual edge thickness and opposing solder/module clearance. Select and document a coupon fit; establish a bounded in-plane location before dimensioning the lips.
3. With the upper case half removed, lower the assembled carrier onto the lower ledges. Contact only the allowed lands. Check antennas, wiring and solder tails.
4. Retain H3 without bending or crushing the board. Close the second half against case hard stops, not by squeezing the PCB. Case screws and ceiling/wall attachments must transmit their loads through the case structure independently of the PCB.
5. Add a measured WIZ jack stop/cradle and cable strain relief. PCB edge grooves do not automatically unload the WIZ module's header solder joints. Qualify insertion/removal, cable loading, thermal behavior and radio operation in the completed assembly.

Rear cavity depth must clear the tallest measured rear feature, the mating plugs and wire bends; front depth must clear the front modules. Neither depth is inferred from the WIZ catalog's ambiguous 18 mm overall dimension. The SCAD deliberately shows isolated interface segments, with no invented full lid, closed perimeter or fastening bosses.

## Reproduce and inspect

Use the repository's pinned `mechanical/requirements.txt` environment. From the repository root:

```sh
python mechanical/module-carrier/rail-mount/build.py
python mechanical/module-carrier/rail-mount/build.py --check
python -m unittest discover -s mechanical/module-carrier/rail-mount -p 'test_*.py'
```

`build.py` reads the active native PCB plus `design.json`; `native-inputs.json` records their hashes and contact regions. [verification.json](verification.json) records source/output hashes and digital checks, with physical tests explicitly unperformed. It uses the existing `mechanical/build.py` CSG helpers. The three coupons are checked for a closed, consistently oriented, single positive-volume solid; tests probe the actual slot void and its bearing faces, and check lip reach at the assumed displacement extremes. Those checks establish mesh geometry, not fit or strength. `rail-interface.scad` is parametrically editable; `fit-coupons.scad` and the STL outputs regenerate from `parameters.json`.

The immutable [c3c8107 four-support baseline](baseline/README.md) supplies the historical side of the mounting comparison. The current board becomes narrower because edge support replaces three PCB mounting points, while enclosure attachment remains necessary. No fabrication price or stiffness improvement is inferred from area alone.
