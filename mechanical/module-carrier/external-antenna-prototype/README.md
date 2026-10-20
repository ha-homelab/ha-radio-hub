# MC2-C external-antenna enclosure prototype

**Historical carrier-only option.** For the complete device, including Zooz
ZAC93, power modules, UART bridge, CC1101, LD2450 and an attached BME680 pod,
use the [FH1 full-hub enclosure](../../full-hub/README.md). This smaller housing
does not contain those additional modules.

[Illustrated plan](index.html) · [dimensioned drawing](enclosure.svg) · [actual printable meshes](print-parts.png) · [assembly with antenna envelopes](assembly-preview.png) · [trial parameters](parameters.json) · [digital checks](verification.json)

This package implements three independently labeled external antenna connections for **MC2**: **BLE**, **THREAD** and **ZIGBEE**. Each uses its own 50 Ω cable. The ports are in the fixed base wall, so lifting the cover does not pull on the miniature radio connectors. This enclosure is a printable engineering prototype; physical fit, cable routing, strength, temperature and coverage are not yet qualified.

The nominal carrier shell is **190 × 160 × 58 mm**, plus a **4 mm ceiling spacing frame**. The carrier is 100 × 100 mm; its actual outline and mounting holes are read from the MC2 native KiCad board. The extra width reserves hand/tool access and initial 65 mm spacing between adjacent antenna connectors. That spacing is a starting mechanical layout, **not a demonstrated RF isolation distance or a promise of coverage over 1,000 ft²**.

MC2-C uses the **ESP32-DevKitC-VIE with ESP32-WROVER-IE** host. The four carrier mounting holes, WIZ850io connector position and shell dimensions are retained from MC2-A. The plan now draws each U1–U4 body reservation directly from the current CAD ledger, identifies the selected host, and records those reservations and the electrical revision in `verification.json`. It does not reuse the S3 host outline. The host's single USB connector and the conservative WROVER module overhang are covered by the native carrier ledger; supplied-board dimensions and installed heights still require measurement.

The Thread board is **Unexpected Maker TinyC6[D], TC6D-01**. Its 36.3 × 17.78 mm
nominal PCB is aligned by the header centers, and its U.FL socket position is
read from the revised native CAD. The Series D radio needs the MC2-C RCP
firmware to select that external antenna. The same 150 mm cable and carrier
mounts remain applicable; installed header height and formed coax bends still
require a physical trial.

This remains a **carrier-only housing**. The PoE splitter, converter, DFR0627, ZAC93, CC1101, LD2450 and BME680 remain in their separately allocated housings/locations. No free volume in this shell is permission to move them next to the RF cables. The system still receives one PoE cable from the existing network switch. The carrier's downstream WIZ Ethernet connector carries data after the external splitter; do not connect raw PoE to an ordinary WIZ jack.

## Print files

- [base.stl](base.stl): open tray with three D-shaped bulkhead holes, recessed radio names, four native PCB support positions, three soft-loop cable supports, ventilation and a rear split cable exit.
- [cover.stl](cover.stl): flat cover with four closure holes. Print its outside face on the bed.
- [ceiling-spacing-frame.stl](ceiling-spacing-frame.stl): 4 mm frame to clear base hardware; install it between tray and ceiling.
- [cable-bar.stl](cable-bar.stl): low-voltage rear harness restraint. Two M3 fasteners attach it to the base and soft ties pass through the two center slots. It does not touch or support an RF connector.
- [bulkhead-fit-coupon.stl](bulkhead-fit-coupon.stl): **print this first**. Viewed in its print orientation, left to right the round holes have zero, +0.2 mm and +0.4 mm nominal allowance, identified by one, two and three shallow notches. Select allowance using the actual bulkhead, then set `rf.print_allowance` and regenerate the full shell.
- [assembly.scad](assembly.scad): assembled inspection view only. Do not print the merged assembly.

All STL units are millimetres. The base sits floor-down; other parts are supplied flat on the bed. Side holes and the short soft-loop supports may need local supports or bridging settings specific to the printer. Inspect the slice and remove support debris before inserting electronics. No print material, layer adhesion or mounting load has been certified. Use an electrically insulating, unfilled material suitable for the measured ceiling temperature; conductive/metal-filled prints change the RF environment.

## Connector and antenna fit contract

The current **RF1** reference is **Taoglas CAB.618.E**: standard SMA female
bulkhead to right-angle I-PEX MHF I/U.FL, 50 ohm, 1.13 mm micro-coax. The round
cutout is **6.6 mm project clearance plus 0.2 mm trial print allowance**, with a
3 mm wall and matching 3 mm coupon. This is not a vendor-specified cutout. A
20 mm internal tool envelope remains clear. Fit the supplied washer and nut;
hold the connector shoulder so antenna tightening does not twist the coax.
Check thread engagement on the actual coupon. The former D-hole base is
superseded. MHF4, MHF III and RP-SMA are different interfaces.

The nominal harness is **150 mm**, with a conservative **144 mm project budget**
and 30 mm connector/service allowance for this smaller shell. The grouped
[catalogue drawing](https://www.taoglas.com/datasheets/Taoglas_Cable_Assembly_Catalog.pdf)
shows ±6 mm on a 200 mm sibling, not an explicit tolerance for this 150 mm SKU;
measure delivered usable length. The [cable specification](https://cdn.taoglas.com/specifications/30021F0020000A_Taoglas.pdf)
gives a **6.8 mm minimum bend radius** for the cable family used as our
engineering basis; the exact internal wire SKU of CAB.618.E remains unconfirmed.
Circular guide bends must fit between tangency points while leaving **21 mm**
unbent for the 17 mm reference heatshrink plus up to 4 mm connector flange.
Retainer centres sit 27 mm inward from the wall. These calculations do not replace
formed-route, nut-engagement and strain-relief tests with the actual parts.
See the [RF source ledger](../../full-hub/rf-evidence.json).

The external antenna candidate is **TE ANT-2.4-LCW-SMA / L9000082-01**, normal SMA male, approximately 83.1 mm long and 10 mm diameter. Reserve its external volume and hinge motion at the installed location. Keep all three radiating bodies outside the shell; initially orient them parallel and away from nearby metal, ceiling framework, Ethernet cabling and other antennas. Test different orientations at the actual mounting point. Do not derive swept-body clearance or coverage from a connector-to-connector distance alone. [TE antenna reference](https://www.te.com/en/product-L9000082-01.html).

## Assembly and measurements

1. Print the bulkhead coupon. Fit the purchased connector with its supplied nut, washer and O-ring, check thread engagement and that the D flat resists rotation without cracking plastic. Use the connector maker's applicable torque limit; none is invented for this printed wall. Hold the bulkhead with the appropriate tool when fitting/removing an antenna. Never transfer tightening force through the coax to the radio.
2. Check the native carrier dimensions and support holes against the manufactured board. Mount the bare carrier first. The nominal underside seat is **Z15 mm** above the exterior floor, leaving **12 mm** from inside floor to PCB underside. PCB thickness is assumed **1.6 mm**; the cover inside face is **Z55 mm**, leaving **38.4 mm** above the carrier. Check every real module, solder tail, connector and mated harness. All such measurements remain `null` in `parameters.json` until recorded.
3. Install the M2.5 nylon PCB nuts/retainers and rear M3 cable-bar hardware while the base underside is accessible. Keep all hardware projection below the base within **3 mm**, so the 4 mm spacing frame leaves at least 1 mm clearance. The four PCB screws use only the native holes; no new board holes or sockets are implied. Use suitable case-to-ceiling anchors through the two separate 4.5 mm holes. Select lengths from the printed stack and actual ceiling; no load rating is assigned.
4. Install and secure all three bulkheads **before** snapping the AMC plugs onto the modules. From the exterior front, the order is **BLE — THREAD — ZIGBEE**. Match the same labels on each cable and radio. Seat each miniature plug squarely, pressing its metal shell; do not press sideways, pull its wire or repeatedly reconnect it for normal servicing.
5. Lead each coax straight inward, then pass a **soft, loose restraint loop** through its printed tower. The tower is a strain-relief anchor, not a calibrated clamping jaw. Add a protective sleeve if required; never cinch a hard cable tie directly onto micro-coax. Route from there to its module with a broad bend, keeping clear of the cover seam, screws, sharp pins, Ethernet magnetics and power wiring. The anchor must prevent an external antenna adjustment from loading the board connector. Measure the complete formed path plus service slack before committing to cable length. Routes to the final module connectors must be inspected against the assembled board; the plan does not certify their three-dimensional fit.
6. Restrain the rear Ethernet/low-voltage harness using the separate cable bar before connecting it to the WIZ/header assembly. The rear opening is a generous split pass-through, **not** a precise RJ45 panel mount, cable gland or strain relief by itself. Verify the actual plug latch, boot and bend; no post-assembly USB cable insertion is qualified. Program modules before installation and use documented firmware update paths for routine service.
7. Fit the cover using four M3 closure positions (2.5 mm trial pilots in base, 3.3 mm clearance in lid). Check/tap pilots with the selected screw in an unloaded print before fitting electronics. Close against the case, not against components or PCB screws. Keep the entire coax harness on the base side of the closure seam.
8. Test antenna retention, cable pull isolation, RF connector seating, case closure and sustained temperature on the bench. Then test Zigbee, Thread and BLE concurrently in the closed installed case at the central ceiling position, including the weakest rooms and closed doors. Record actual packet/response performance before declaring a finished enclosure.

The bulkhead's own IP67 component description does **not** give the ventilated printed enclosure an ingress rating. This prototype is for indoor dry use.

## Rebuild

From the repository root, with `mechanical/requirements.txt` installed in the selected Python environment:

```sh
python mechanical/module-carrier/external-antenna-prototype/build.py
python mechanical/module-carrier/external-antenna-prototype/build.py --check
python -m unittest discover -s mechanical/module-carrier/external-antenna-prototype -p 'test_*.py'
```

The tests check native mounting positions, current module-body XY reservations inside the shell, RF guide endpoints against the CAD connector estimates, independent port identities and spacing, nominal PCB clearance, separation of shell/cover, open bulkhead tool envelopes, frame/mount alignment and connected watertight meshes in bed orientation. The portable output check compares source contracts and geometry while tolerating platform-specific mesh ordering or PNG rasterization. Module-body checks cover XY only; they do not certify component height or a collision-free formed coax route. These are digital regressions; they do not turn unspecified hardware measurements into physical fit results.
