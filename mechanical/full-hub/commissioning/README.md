# ZAC93 cradle first print on the TRONXY XY-3

[Open the editable PrusaSlicer project](FH1-ZAC93-XY3-PLA.3mf) to print one cradle and try the real ZAC93 before spending filament on the enclosure. This trial is for the original XY-3 with a 310 × 310 mm bed, a 0.4 mm nozzle and unfilled 1.75 mm PLA. The estimated print takes **43 min 19 s** and uses **6.71 g**. Physical fit and first-layer adhesion still require a trial.

## Before starting

1. On a cold printer, check that the sheet sits flat and establish physical nozzle clearance around the entire first-layer footprint using the printer's normal leveling procedure. The project commands a 0.35 mm first layer. A Z reading on the display alone cannot confirm the physical gap. Resolve any scraping or raised damage before printing.
2. Open the 3MF as a **project** in PrusaSlicer 2.9.6. Keep the model centered at X100 Y100, flat face down and 100% scale. Select **Slice now** and inspect the skirt, removable supports under the retaining lips and the first-layer path. The actual deposited lines extend from about 79.54 to 120.46 mm on each axis, plus half a line width at their edges.
3. Confirm that the loaded PLA and sheet are suitable for a 200 °C nozzle and an unheated bed. Export plain-text G-code for an attended start. Keep the bed clear of hands and measuring tools. The job homes cold, lifts to Z8 and moves over the skirt entry at X80.216 Y80.457 before heating. After heating it proceeds straight to the first layer. A well-attached line of PLA should remain on the sheet. Stop if the nozzle scores the coating, pushes the sheet or drags loose plastic.
4. Let the cradle cool, remove the skirt and supports, and dry-fit the unpowered ZAC93, connector and mounting hardware. See the [enclosure assembly guide](../README.md) and [Linux printing guide](../../../docs/linux-printing.md).

The [supplied profile](xy3-zac93-pla.ini) uses one skirt 2 mm from the model, 0.20 mm subsequent layers and 2 mm Bowden retraction. The printable project uses zero slicer Z offset. A change to mesh, orientation, scale, placement or skirt can change the first extrusion point. Recheck the raised approach in the preview and generated commands after any such change.

## Rebuild from the STL

From the repository root, run the following with Python 3.8 or newer and PrusaSlicer 2.9.6. Set the output to a local directory outside the checkout.

```sh
python3 mechanical/full-hub/commissioning/build.py \
  --slicer prusa-slicer \
  --output-dir "$HOME/xy3-cradle"
```

On macOS, pass the path to the executable inside the PrusaSlicer application bundle. The script takes the [current cradle STL](../zwave-tray.stl) and the supplied profile, creates an editable 3MF and slices that project into a local `.gcode` file. It checks that reopening the project alone produces the same machine commands as slicing the source STL at X100 Y100 with the explicit profile. It verifies the complete approach through the first skirt extrusion, including the raised heating position and the lowering point. The script runs entirely offline.
