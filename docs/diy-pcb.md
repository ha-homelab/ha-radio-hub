# Make the low-voltage DIY carrier with toner transfer

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

This is a separate single-sided carrier for home fabrication, not a simplified print of the factory boards. Its copper artwork, drilling and assembly sheets are generated from its native KiCad board. The design has not been etched, drilled, assembled or powered in hardware; CAD checks and a correct PDF cannot establish toner adhesion, drill accuracy or electrical performance.

The LP-D0 board outline is **190 x 145 mm**. This is the PCB size, not an enclosure size. It does not fit the existing 190 x 145 mm outer-size concept enclosure; the adapters, headers, wire loops and external modules also need a new placement and clearance check.

The DIY carrier keeps fine-pitch devices and radios on separately manufactured adapters. Use the factory-made LP-M0 MGM240P board and the specified breakout modules. [Adafruit 1208](https://www.adafruit.com/product/1208) and [1230](https://www.adafruit.com/product/1230) are breakout PCBs, not populated SC16IS752/TPS3808 modules: the specified ICs still need fine-pitch soldering onto those adapters, or an assembly service. The LP-M0 radio board likewise needs its specified module assembled. Keep the isolated PoE power front end outside this home-etched board: only its regulated low-voltage output enters the carrier. Never apply Ethernet PoE voltage directly to a 5 V or 3.3 V connector.

This remains a substantial hand build: the current print set has **299 drilled holes and 54 insulated wire links**, including 100 dedicated wire-terminal holes and one raised connection to an existing adapter pin. It also needs the component leads and external harnesses. Use the generated drill and wire schedules for the exact locations; intermediate router exports are not an assembly release.

## Why the other boards are not the iron-transfer artwork

LP-C0 uses two copper layers, plated interconnections and fine-pitch SC16IS752/TPS3808 circuitry. Reproducing it at home would require a different interconnection and assembly process; simply omitting one layer disconnects the circuit. LP-I0 additionally uses four copper layers, internal planes, fine-pitch radio/Ethernet parts and the PoE isolation layout. It cannot be manufactured as designed by single-sided toner transfer. The DIY board instead uses through-hole terminations and documented insulated wire links on the component side.

## Download the matching print set

All four files are vector PDFs on A4 pages at true 1:1 geometry. Use the PDF files rather than a preview image.

- [Toner-transfer copper](../hardware/low-power/diy/print/toner-transfer.pdf): the only sheet to transfer onto the copper; no additional mirror.
- [Drilling and bottom-side inspection](../hardware/low-power/diy/print/drilling.pdf): actual hole centres and a drill-symbol legend, viewed from below.
- [Assembly and wire schedule](../hardware/low-power/diy/print/assembly.pdf): component view and actual insulated-link endpoints.
- [Printer calibration and sacrificial etch coupon](../hardware/low-power/diy/print/calibration.pdf): verify the printer and process before the full board.

The [native KiCad board](../hardware/low-power/diy/diy.kicad_pcb), [wire list](../hardware/low-power/diy/jumpers.csv) and [print manifest](../hardware/low-power/diy/print/manifest.json) identify the same build. If the board changes, regenerate the entire set.

## Print orientation: read this before using transfer film

KiCad normally shows the board from its component side, including when B.Cu is selected. Its **Flip board view** command changes that to a mirrored bottom view. The native export command's `--mirror` option similarly changes the plotted orientation. [KiCad 10 PCB editor documentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#_the_appearance_panel), [CLI documentation](https://docs.kicad.org/10.0/en/cli/cli.html).

For this **bottom-copper-only** board, the toner-transfer sheet uses **B.Cu with no export mirror**. Place the toner against the copper. That face-down transfer reverses the printed image once, producing the bottom view of the designed circuit. The separate bottom inspection/drilling view is mirrored relative to the transfer sheet; do not use the drilling or assembly sheet as an etching mask. The transfer-film manufacturer specifies image-side-down contact; its instructions do not replace this board-specific orientation check. [Techniks instructions](https://www.techniks.com/how_to.htm).

A concrete board landmark is **J1 pin 1 at (15, 12) mm in component-view coordinates**. On the bottom inspection sheet it is at **(175, 12) mm**, measured from the bottom view's upper-left corner. The four mounting-hole centres are (5, 5), (185, 5), (5, 140) and (185, 140) mm; their symmetry alone cannot detect a mirror error. Use J1 and its adjacent fuse holes, not the mounting holes alone. Confirm these values against the generated `drill-map.json` when using a later revision.

Before committing a full blank, use the asymmetric orientation marks and the calibration coupon. Hold the printed sheet against the component-side assembly sheet and look through the paper: the pad positions must coincide. Then turn the print face down, keeping the designated top edge at the top, and compare it with the bottom-side inspection view. A screenshot, browser preview or gallery thumbnail is not a scale drawing.

## Calibrate the physical printer

Use a laser printer or toner photocopier compatible with the selected transfer medium; an inkjet print is not a toner resist. Set **Actual size / 100%**, one page per sheet, and disable fit, shrink, poster tiling, booklet, duplex and printer-driver mirror modes. Disable toner-saving modes. Choose the paper size printed in the PDF metadata. The PDF generator does not compensate for an inaccurate printer.

First print the calibration sheet on ordinary paper. Measure both 100.00 mm axes, the 50.00 mm square and the 25.40 mm ten-pitch connector span with a reliable ruler or caliper. The recommended project acceptance is within 0.20 mm on each 100 mm axis; this is a process target, not a measured capability of your printer. Check an actual header against the pitch marks too. If either axis fails, correct the driver/paper configuration and reprint. Do not accept an X-axis correction as proof that Y is also correct. Repeat the check on the actual transfer medium before etching a complete board.

## Transfer and etch a coupon first

The selected blank is single-sided FR4, 1.6 mm thick with 35 um copper, large enough for the 190 x 145 mm outline plus a handling margin. Use a flat, deburred blank and clean copper without touching the active area afterwards. Use a dedicated heat-resistant work surface and transfer film approved for your printer. For Press-n-Peel Blue specifically, Techniks suggests starting at 275-325 F (135-163 C), without steam; transfer time depends on board size, thickness, iron and toner. These are the manufacturer's starting conditions, not a validated recipe for this carrier. Follow the current instructions for the film actually used. [Techniks process and printer compatibility notice](https://www.techniks.com/).

Transfer the line/space and pad coupon first. Under magnification, check for broken tracks, spread toner, bridges, pinholes and a complete resist around every drill centre. Use the same blank, toner, temperature and etch process intended for the board. Only proceed if the coupon's line and gap dimensions relevant to the final board survive the complete transfer and etch process. This is a large 190 x 145 mm transfer: a small successful coupon does not establish even heating or registration across the entire board. Inspect the centre and all corners after transfer and reject any incomplete resist before etching.

Use a commercial PCB etchant according to its label and safety data sheet; protect eyes and skin, ventilate the workspace, and contain splashes. Collect used copper-bearing etchant for the applicable local waste route, not a household drain. This guide does not prescribe mixing chemicals. Remove resist according to the film/etchant instructions, then wash and dry the board before inspection.

## Drill, assemble, then apply power

1. Inspect every copper path against the bottom inspection sheet before drilling. Small white centres in the copper artwork are pilot marks, not the final hole diameters.
2. Support and clamp the board. Use the generated drill schedule and sharp PCB drills; wear eye protection and control glass-fibre dust. All holes on the home-etched board are **unplated**, even where the KiCad library represents a through-hole pad on both copper layers.
3. Fit the documented top-side insulated jumpers and low-profile parts first. A drawn crossing is not a connection. Strip only the wire ends and verify each link against the endpoint schedule.
4. The `E1` endpoint is a top-side solder joint on the exposed **U1.11 (MOSI)** adapter lead, **not an additional drill hole**. Other wire endpoints use their designated through-hole terminals and are soldered on the bottom. Follow the assembly PDF's physical pin and height: keep 6 mm below the adapter PCB, make the indicated joint 4 mm above the carrier, and keep the first/last 3 mm of wire above the header before descending. Make and inspect the joint before seating the adapter. Strip only the specified end length; cover the exposed wire joint with suitable thin insulation so it cannot touch U1.10, U1.12 or another header pin. Under magnification check for solder bridges, loose strands and insulation trapped in the joint, then verify continuity to U1.11 and isolation from adjacent pins. Cut lengths include the corresponding vertical allowance.
5. Solder all regular through-hole leads and T-terminal wire ends to the bottom copper; the explicitly documented raised E1 joint is the exception. A top-side annulus in an assembly illustration does not create electrical continuity on a single-sided blank. Fit headers with the exact pin-1 orientation shown, then check every adapter's actual pinout before insertion.
6. With all modules unplugged, continuity-test every named link and check the power rails against ground and each other. A visual inspection alone cannot detect all opens or shorts.
7. Apply the documented regulated low-voltage input from a current-limited supply. Verify the rails and polarity at every empty module connector before installing the modules. Power off before adding or moving a module or cable.
8. Complete the project firmware and functional acceptance tests. A working power LED is not a passed UART, Ethernet, radio or PoE test.

## Reproduce and inspect the print package

The generator, pinned Python dependencies and regression checks are in [mechanical/diy](../mechanical/diy/). They use KiCad's native copper plot rather than reconstructing a circuit from a screenshot. The output manifest records input hashes, layer/orientation settings, physical dimensions and drill information. Regenerate the print package whenever the native board or jumper schedule changes; do not mix revisions.

The transfer artwork uses small pilot openings generated by KiCad's small-drill-mark mode; the drill schedule, rather than these white dots, defines final hole sizes.

The current KiCad 10.0.6 print set contains eight visually checked A4 pages: one transfer page, two drilling/inspection pages, four assembly/schedule pages and one calibration page. Native pad-coordinate checks, vector dimensions and the print regression tests verify the exported geometry. The final build report distinguishes those source/plot checks from physical tests. Printing, transfer, etching, drilling, module clearance, soldering, powered operation and enclosure fit remain unverified until a prototype is built.
