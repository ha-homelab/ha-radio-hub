# MC1 printable enclosure prototype

> **Historical MC1 revision.** The current [MC2 external-antenna build](../../../docs/external-antennas.md) uses different modules, pins, flash layout and housing. Keep this material with MC1 boards only.


[Open the illustrated plan and section](index.html) · [dimensioned SVG](enclosure.svg) · [3D print-parts view](print-parts.png) · [trial dimensions](parameters.json) · [digital verification](verification.json)

This is a **complete carrier-only shell prototype**, with a printable base, retaining cover, ceiling spacing frame and separate adjustable jack-stop trial. It replaces the absence of a shell; it does not replace physical measurements or claim a finished product. The earlier [split-rail study and fit coupons](../rail-mount/README.md) remain the starting point for selecting the board fit.

The PCB is **47.5 × 75 mm, two layers**. The default outer case is **84.3 × 121.8 × 57.4 mm**. Installed depth is **61.4 mm including the 4 mm ceiling spacing frame**. Its width and length reserve space around the radio modules and cable entry rather than increasing the PCB footprint. Its height uses explicit **26 mm rear / 25 mm front cavity assumptions**. These are not measured module heights and are not a claim that this is the smallest possible enclosure.

## Print files and orientation

- [base.stl](base.stl): ceiling-side tray, lower edge seats, H3 support, case closure bosses, vents, cable openings and two separate case mounting holes. Exterior floor lies on the bed.
- [cover.stl](cover.stl): room-side cover and downward retaining bridges. Exterior face lies on the bed; retaining bridges print upward. This holds the PCB edges without three additional PCB holes.
- [ceiling-spacing-frame.stl](ceiling-spacing-frame.stl): 4 mm spacer frame, printed flat. It holds the base away from the ceiling and leaves an open underside region for floor fasteners. Its two 4.4 mm mounting holes align with the base.
- [jack-stop-trial.stl](jack-stop-trial.stl): removable slotted bracket, with its flat foot on the bed. This is a **fit-development part**; its default contact position and height are arbitrary adjustable parameters, not approved contact points on WIZ850io.
- Matching `.scad` files preserve the generated printable geometry. [assembly.scad](assembly.scad) shows the four parts in assembled coordinates; do not print that merged preview. Edit `parameters.json` and regenerate to change the design.

STL units are millimetres. The base is a tall open tray. Inspect support placement beneath the lower edge bridges and RJ45 opening; the files have not been sliced or test-printed. Remove supports completely before fitting electronics. Do not infer universal printer settings or material strength from watertight meshes. Print the existing rail coupons with the intended printer, material and orientation first. [Prusa's modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) explains why fit and load direction require testing.

## What is fixed, and what is provisional

The generator reads the active native KiCad board and `design.json`: outline, module XY bounds, the sole H3 location `(18, 52.03)`, and legal contact lands. It uses subsets of those lands: left `x=0…0.65, y=27…54.3`; right `x=46.5…47.5, y=27…73.8 mm`. The narrower nominal lips reserve the existing trial ±0.2 mm movement budget. Moving their starts to y27 avoids placing the new support bridges immediately beside the top antenna region.

A 2.0 mm trial rail gap accepts a nominal 1.6 mm board in the digital model. The actual slot choice, board thickness/bow, print error and **pointwise XY excursion including rotation** remain unmeasured. The 0.2 mm side clearance alone does not establish a production tolerance stack. H3 clearance is not a precision locating feature. Add or adjust nonconductive edge shims only after measuring the populated assembly, while keeping all actual contacts inside the legal lands. Never tighten the lid to remove PCB play by bending it.

The rear PCB face is at Z28.4 mm, the nominal front at Z30.0, and the cover inner face at Z55.0. The support-to-retaining-lip gap ends at Z30.4. Case closure is against the tray's hard stops at Z55, independently of the PCB. **The first assembly must show that the 26 mm rear cavity exceeds the tallest rear component, mated header housing and wire bend by the required margin.** It must also show that the front cavity clears all module parts. Existing opposing solder-tail and module-underside clearance requirements still apply.

The WIZ port opens through the bottom edge of the case in plan view. Its modeled cable corridor is x18…48 mm, beginning at the native jack face y77, with a case opening from Z3 to Z28.4. That opening is intentionally broad. The actual plug boot, latch access and cable bend are not modeled. The x-side opening serves external low-voltage harnesses; it is not a USB service bay. Initial module programming remains before soldering, with normal post-assembly service through firmware pathways.

## Radio and thermal limits

The shell is intended for an electrically insulating, nonconductive print. Do not use conductive fill, metal coating or foil near the radio antennas. The upper inner wall is at y−21 mm. The native H2 antenna extends to y−5.475 mm, giving **15.525 mm antenna-to-end-wall clearance**; this includes the antenna projection beyond the module PCB. That specific distance is regression-tested. The outer walls are set back from the board, and the supports use only selected edge regions. However, the complete housing has not been checked against measured three-dimensional antenna volumes or tested for RF range. Espressif recommends at least 15 mm clearance around the H2 PCB antenna within the housing and testing the finished product. This design does **not** certify that recommendation at every support, fastener, cable and installed ceiling surface. [Official H2 housing guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board).

The side and face slots provide air openings; no airflow rate or temperature reduction is predicted. Measure the closed case at sustained workload and the hottest intended ceiling environment. This prototype is for an indoor, dry location; it has no sealing or ingress rating.

## Assembly and hardware

1. Program loose modules and perform the documented board preparation. Fit and solder **all 13 rear parts first**, including WIZ, headers, diodes and resistors. Trim and inspect. Fit and solder the **three front controllers** afterward. Use the existing local solder-tail/underside clearance checks; opposite-side overlap is allowed only where the measured stack clears.
2. Test a rail coupon against a bare board edge or offcut. Measure the actual board width, thickness and bow. Enter measurements in the manifest and revise trial geometry as required. Check the full tray and cover without electronics.
3. Work on the bench with both sides of the base accessible. Trial-fit the H3 nylon nut in its underside recess and place it before mounting the base; retain it temporarily so it cannot fall or turn. Install and adjust the jack-stop hardware now, as described in step 4. **Do not attach the base to the ceiling until all floor fasteners and stop adjustments are complete.**
4. If using the jack stop, adjust its contact coordinates and height to the **metal jack cage**, with no contact against exposed circuitry and no preload on WIZ or the carrier. The two 3.2 ×18 mm floor slots permit longitudinal adjustment. The printable stop's foot has slots for two M3 fasteners. Install screw heads from below the floor and secure the bracket with nuts above its foot. Select heads no greater than 6 mm diameter and **measure total projection beneath the base: no more than 3 mm**, including any washer. The supplied 4 mm spacing frame then leaves at least 1 mm nominal clearance to the ceiling. The bracket's default crossbar can collide with an actual module: leave it out of a powered assembly until the contact is measured. The stop primarily addresses insertion load; the case opening is not itself cable strain relief. Add a separately verified cable clamp so a cable pull does not load the header solder joints.
5. Route and restrain external harnesses through the side opening. Connect them while the rear face remains accessible. Do not place the external PoE splitter, buck, DFR0627, ZAC93, CC1101 or sensors into unallocated free space around the antennas. Their modules stay in separate housings or mounting locations.
6. Place the 4 mm spacing frame between the base and ceiling, then attach the open base using its two 4.4 mm mounting holes. The frame prevents the preinstalled floor hardware from contacting the ceiling. Keep it installed: the base is **not a flush-mount design**. The 9 mm driver-access bores through the edge bridges reach the case mounting screw heads before loading the carrier. Select anchors and fasteners for the actual substrate and added 4 mm stack; no ceiling load rating is assigned. After checking all floor hardware, lower the populated carrier normal to its plane onto the lower edge seats. Do not slide it through a closed groove. Install the sole **nylon M2.5 H3 retainer**. The support is 5 mm in diameter with a 2.7 mm through-hole and a trial hex recess beneath the floor. Select screw length/nut fit from the printed stack; the recess is not a verified fit to every commercial nylon nut. Retain without crushing or bending the PCB.
7. Lower the cover onto the case hard stops. Four nominal M3 closure positions use 3.2 mm lid holes and 2.5 mm trial pilot holes in the base; select/tap/test the intended fasteners before loading the PCB. They fasten only the case. No sockets are added to any module or PCB connector.
8. Before ceiling use, demonstrate PCB retention, non-interference, jack insertion/removal, cable pull isolation, thermal behavior and radio operation on the complete assembly. Inspect for support debris and trimmed conductive tails. Record results rather than treating CAD clearance as a physical test.

## Rebuild and digital checks

Use the environment pinned by `mechanical/requirements.txt`, from repository root:

```sh
python mechanical/module-carrier/enclosure-prototype/build.py
python mechanical/module-carrier/enclosure-prototype/build.py --check
python -m unittest discover -s mechanical/module-carrier/enclosure-prototype -p 'test_*.py'
```

The eleven checks cover one native H3, unknown measurements remaining unknown, nonintersecting case halves, legal nominal rail contact, nominal PCB clearance, the modeled jack tunnel, ceiling-screw driver access, connected bed-oriented meshes, the H2 end-wall antenna setback, floor-fastener clearance within the spacing frame, and aligned ceiling-mounting holes. The report records the native source hashes. These checks deliberately do not assert measured module/cable fit, force capacity, printed tolerances or thermal/RF performance.

The default `--check` is portable between macOS and Linux: recorded file hashes still protect checked-in exports, native/source contracts and SVG/SCAD text must match, and changed STL bytes are compared as solids with tight numerical tolerance. The case PNG must retain its recorded integrity and expected decoded size; a platform's different font rasterization does not fail the check. Use `--check --exact` to additionally require every exported byte to match on the same rendering platform. The four portability regression tests in `rail-mount/test_portability.py` accept reordered triangles/render metadata and reject changed geometry, stale source contracts and unrecorded image edits.
