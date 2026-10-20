# FH1 — complete MC2-B radio-hub enclosure

This package adds physical accommodation for the **whole hub**: the MC2-B
carrier, Zooz ZAC93, DFR0627 UART bridge, CC1101, isolated PoE splitter, 3.3 V
regulator, DC adapter, fuse, LD2450 and an attached BME680 pod. It supersedes the
smaller carrier-only housing for a complete assembly. It is an **engineering
prototype**, with digital checks and explicitly unmeasured fit assumptions.

[Open illustrated layout](index.html) · [Electrical assembly](../../docs/full-hub-assembly.md) ·
[Component inventory](components.json) · [Sources](sources.md) ·
[Parameters](parameters.json) · [Digital verification](verification.json)

![Exploded geometry](exploded-preview.png)

The exploded drawing separates parts for visibility. The component shapes are
simplified envelopes, not detailed supplier STEP models. Use the numbered plan
for locations and the electrical guide for signal names; a render is not a
mating-side connector diagram.

![Numbered component layout](layout.svg)

## ZAC93 location and attachment

**The ZAC93 is beside the carrier in its own removable cradle.** Its factory
2×5 socket faces downward into the opening, leaving space for a wired mating
header. The five-wire cable goes to carrier **J4**, not directly to the ESP32.
The adjacent **DFR0627 / WK2132 connects to J3**. Its UART1 provides the ZAC93's
serial link. The [full wiring drawing](../../hardware/external-antenna/full-hub-wiring.svg)
shows the pin remapping.

Orient the ZAC93's stock antenna toward the outer plastic wall. Keep the
antenna area free of straps, wires and metal; the lid-mounted radar is placed
away from that area. Do not drill mounting holes in the ZAC93. The printed
cradle uses edge support and nonconductive retention. Trial socket/board
heights must be compared with the actual delivered revision before tightening
or plugging in the harness.

## Print package

Print each STL separately in its supplied bed orientation, in **millimetres**.
The assembly and exploded SCAD files are inspection models; do not print either
as a single solid.

- [Base](base.stl) and [lid](lid.stl): main housing, carrier supports, fixed-base
  RF bulkheads, cable passages and mounting points.
- [Z-Wave cradle](zwave-tray.stl): ZAC93 support with underside socket space.
- [UART-bridge tray](wk2132-tray.stl) and [CC1101 tray](cc1101-tray.stl).
- [PoE-splitter tray](poe-splitter-tray.stl), [buck-regulator tray](buck-tray.stl)
  and [DC-adapter/fuse utility tray](power-utility-tray.stl).
- [Radar holder](radar-holder.stl): LD2450 support behind the lid's room-facing
  window. Retention must not cross the active antenna face.
- [BME680 pod](bme680-pod.stl), [pod lid](bme680-pod-lid.stl) and **two**
  [pod arms](pod-arm.stl): an attached ventilated compartment outside the warm
  main shell.
- [Fit coupon](fit-coupon.stl): print first to check fastener pilots and the
  selected SMA bulkhead against actual hardware.
- [CC1101 port blank](cc1101-port-blank.stl): optional closure for an unused
  trial feed opening. It is not an RF connector or antenna adapter.
- [Assembled SCAD](assembly.scad) and [exploded SCAD](exploded.scad).

The main body is **215 × 215 × 78 mm**. The attached pod increases body width to
**277 mm** before antenna and cable projection. The largest individual print
is 215 × 215 mm. The selected **TRONXY XY-3 (original)** has a nominal
310 × 310 × 330 mm print volume, leaving room for a brim. A generic 220 × 220 mm
bed leaves only 2.5 mm per edge; inspect the slicer's printable region and brim
before trying it on that smaller machine.

Use electrically insulating, unfilled material and validate it at the actual
operating temperature. Metal/carbon-filled filament is unsuitable around the
radio/radar apertures. The initial radar window is 0.8 mm thick, with a nominal 12.4 mm gap
from the antenna face to its inner surface. These follow the Hi-Link radome
guide as a starting point; actual material, board height and detection still
need a test. Inspect bridging/supports around horizontal openings,
remove debris, and check the slice before inserting any electronics. This
ventilated enclosure has no ingress-protection or structural-load rating.

## Fasteners and retention

The initial hardware schedule is:

- 4 × M2.5 carrier bolts with nonconductive nuts and suitable washers.
- 4 × M3 lid screws for the tested printed pilots.
- 24 × M2 screws: four for each of the six removable trays.
- 2 × M2 fasteners for the Pololu's two native mounting holes.
- 4 × M2 radar-holder screws.
- 2 × M3 through-bolts and nuts for the pod arms at the main wall.
- 2 × M2 bolts and nuts for the pod-to-arm connection; 2 × M2 pod-lid screws.
- At least eight soft nonconductive module-retention straps: two for the
  splitter, one each for ZAC93, DFR0627, CC1101, DC adapter, fuse and BME680.
  Add the radar's board-end restraints and separate loose cable-restraint loops.

Select screw length from the actual printed stack and the mount records in
[verification.json](verification.json). Check pilots with the coupon first.
Fasteners must not bottom out, crack a boss, contact a circuit or intrude into a
cable/antenna space. Nuts, washers and real screw heads occupy space too; verify
those during the unpowered dry fit.

## Fit the complete assembly

1. Print the coupon and ZAC93 cradle first. Test the actual ZAC93 socket,
   mating header, antenna clearance and soft retention, with power disconnected.
   Confirm fastener pilots and bulkhead engagement before printing the base.
2. Install the carrier on its four native mounting holes. The separate U1–U4
   modules remain soldered to that carrier. Check the underside solder tails,
   board height and Ethernet-jack support/access with the actual populated PCB.
3. Secure the peripheral trays to the base, then retain each module in its own
   tray. Place insulation only at component-free contact points. Keep buck
   underside components, inductors and radio antenna regions clear. A cable
   connector alone is not retention.
4. Install the **Waveshare POE-SPLITTER-25W-5.5-2.1** finished isolated splitter
   with its original case intact. This bay is not designed for the historical
   Silvertel EvalPoE arrangement. Secure the DC adapter and fuse in their
   utility tray. Route its data-only RJ45 tail to WIZ850io; route fused 5 V to J1
   and the Pololu converter to J2 as the electrical guide specifies.
5. Install the three fixed-base SMA bulkheads and route their separate
   150 mm coax leads to BLE, Thread and Zigbee. Use loose, protective soft loops
   at the restraint points; never tighten a cable tie directly onto micro-coax.
   Keep the existing CC1101's separate 433.92 MHz feed matched to its actual
   connector. The trial side opening is not proof that an unknown adapter fits.
6. Fit the ZAC93's remapped J4 harness, the J3 bridge harness and J5 RF harness.
   Leave all connectors accessible and restrain wires away from antenna areas,
   screw tips and the closure seam. Follow the actual module's labels.
7. Attach the BME680 pod using both arms. Its air gap and ventilation reduce
   heating but do not establish temperature accuracy. Route the I²C harness
   through the reserved passage; check bus rise time and reliability with the
   final cable. Mount the LD2450 to the lid holder facing the room and connect
   J6. Leave service slack and unplug this lead before fully removing the lid.
8. Dry-fit the closed enclosure. Check that nothing is compressed and the
   input Ethernet plug, internal RJ45 latch, fuse and module connectors can be
   serviced. Test rails, firmware and each radio with the lid open, then repeat
   under simultaneous load with the lid closed. Follow the
   [RF commissioning procedure](../../docs/rf-commissioning.md).

## Evidence and remaining physical checks

The generator reads the current native MC2-B carrier geometry and
`components.json`, rather than assuming that all boards are interchangeable.
`verification.json` records the modelled component bounds, keepouts, mount
positions, cable-route allowances, print-part dimensions and source hashes.
These checks are against declared geometry, not measurements of your parts.

ZAC93's nominal plan dimensions are sourced, but its delivered revision and
socket stack need inspection. CC1101's existing vendor variant is unknown.
DC-adapter and fuse-holder dimensions are allocations until exact parts are
selected. The splitter's actual captive tails, plug boots, connector heights,
coax bending and retention force need a dry fit. No digital pass resolves those
unknowns. Use the parameters to revise the affected tray/clearance before
printing if a delivered part differs.

The main case is intended to present LD2450's face toward the room. Follow the
sensor manufacturer's mounting/orientation guidance; a ceiling installation
requires its own detection test. Compare BME680 to an independent ambient
reference after thermal equilibrium. Record physical results separately;
`fit_verified: false` must remain false until those checks are actually done.

## Rebuild and check

Install the pinned `mechanical/requirements.txt` in a Python virtual environment,
then run these commands from the repository root:

```sh
python mechanical/full-hub/build.py
python -m unittest discover -s mechanical/full-hub -p 'test_*.py'
python mechanical/full-hub/build.py --check
python hardware/external-antenna/render.py --check
python tools/check.py
```

The CI checks the full-hub package alongside the retained carrier-only and
firmware regression targets. AI appearance images are separate presentation
assets; rebuilding the CAD does not regenerate them.
