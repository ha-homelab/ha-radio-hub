# Physical contact references

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../../../../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

Reviewed on 2026-10-17. These drawings locate real module contacts using cited
manufacturer drawings or library footprints. They are not photographs, Gerbers,
drill templates, or a fabrication release. The adjacent [connection atlas](../)
describes the electrical nets; these references clarify the physical orientation.

Open the drawings:

- [ESP32-S3-WROOM-1](generated/s3-contacts.svg)
- [ESP32-H2-MINI-1](generated/h2-contacts.svg)
- [MGM240P built-in antenna variant](generated/mg24-contacts.svg)
- [WIZ850io headers](generated/wiz850io-contacts.svg)
- [Pololu D24V22F3](generated/pololu-contacts.svg)

[contacts.json](generated/contacts.json) contains the source-derived coordinates,
dimensions and pad identities. [catalog.json](catalog.json) records source URLs,
versions and limitations. [manifest.json](generated/manifest.json) hashes the
source inputs and generated outputs.

## Read the view correctly

Every drawing is labelled **PCB footprint top view; module view requires
datasheet**. The origin is the upper-left corner of the nominal module body, x
increases rightward and y downward. Coordinates are millimetres. Red marks the
first contact or an orientation reference. Module pad numbers are not ESP GPIO
numbers, and neither is a development-board header number.

The S3, H2 and MGM drawings show carrier land patterns. WIZ850io shows header
contact centres only: no carrier drill or pad size is claimed. Pololu shows the
module's own holes, with symbolic contact names because the manufacturer drawing
does not assign numeric pin identities. Actual mating headers determine the
carrier drill, annular ring and assembly height.

Yellow antenna regions are orientation references. They are not a complete
manufacturer keep-out, an enclosure clearance, or evidence of RF performance.
Do not place copper, cables, screws, other modules or metal housing using this
drawing alone. Unknown existing CC1101, LD2450 and DevKit header geometry is
deliberately not invented here.

## Sources and orientation checks

### ESP32-S3-WROOM-1

The unmodified source footprint is from the libraries bundled with KiCad 10.0.6
for macOS. Its SHA256 is recorded in the manifest; a matching Git tag is not
assumed. Library distribution and licensing are documented by
[KiCad](https://www.kicad.org/libraries/download/).

Numbering was checked against Figure 3-1, page 10 of the
[Espressif datasheet v1.8](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf):
1-14 left, 15-26 bottom and 27-40 right, with exposed ground 41. Repeated 41
contacts are the common thermal land and its vias. The actual source footprint
retains more information than the illustration, including mask/paste layers and
its antenna rule area.

### ESP32-H2-MINI-1

The unmodified footprint comes from
[Espressif's library at dd76561812ab300351234ba6e0ec1295641796f0](https://github.com/espressif/kicad-libraries/blob/dd76561812ab300351234ba6e0ec1295641796f0/footprints/Espressif.pretty/ESP32-H2-MINI-1.kicad_mod).
The [datasheet v1.6](https://documentation.espressif.com/esp32-h2-mini-1_mini-1u_datasheet_en.pdf)
Figure 11 on page 38 confirms the 13.2 x 16.6 mm body, 0.8 mm pitch and land
pattern. Contact 49 repeats across the exposed-ground array; 50-53 are the corner
ground pads. Contact 1 is below corner pad 53. MINI-1U and development boards
require their own physical drawings.

### MGM240P

The [Silicon Labs datasheet](https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf)
was retrieved as a manufacturer-authored Rev 1.0 PDF through a
[distributor mirror](https://download.kamami.pl/p1186191-MGM240P-Datasheet.pdf).
Figure 8.3, page 49 is the carrier land pattern: contact 1 is upper left, 36 is
upper right, side pads are 2.4 x 0.6 mm at 1 mm pitch, and bottom pads are
0.6 x 2.4 mm. Figure 8.2 is a **bottom** view and must not be copied without
reflection. The built-in-antenna keep-out shown in Figure 8.3 is 8.8 x 4.8 mm.

The current manufacturer revision must still be checked before fabrication.
A second [LCSC-hosted copy](https://datasheet.lcsc.com/datasheet/pdf/911a9a099db30fdfaac073fef611e4e0.pdf?productCode=C19740261)
also identifies itself as Rev 1.0; it does not close that revision check.

### WIZ850io

The [official product documentation](https://docs.wiznet.io/Product/ioModule/WIZ850io),
[dimension drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png)
and [labelled top photograph](https://docs.wiznet.io/img/products/wiz850io/wiz850io_pinmap.png)
were compared. The mechanical drawing gives a 23 x 25 mm PCB, 20.32 mm row
spacing and 2.54 mm pitch. The documentation's separate feature summary says
20 x 25 mm; this reference follows the dimension drawing. Confirm the purchased
revision before manufacturing a mating board.

With the RJ45 mouth facing upward, J1 is left and J2 is right, with contact 1
at the top of both rows. J2 is **1 GND, 2 3V3D, 3 3V3D, 4 NC, 5 RSTn, 6 MISO**.
The RJ45 mouth projects 2.7 mm past the PCB. These headers do not expose PoE
transformer taps.

### Pololu D24V22F3

The [reg19a dimension drawing, 12 November 2015](https://www.pololu.com/file/0J1031/d24v22fx-step-down-voltage-regulator-dimension-diagram.pdf)
was compared with the [labelled top photograph](https://a.pololu-files.com/picture/0J6802.1200.jpg)
from [product 2857](https://www.pololu.com/product/2857/pictures).
The dimension PDF's labelled connector view is the bottom view. In this top
view the five-contact row is along the bottom, left to right: PG, EN, VIN, GND,
VOUT. The extra ground hole is near the left edge above the row.

The six electrical holes are 1.02 mm diameter; two mounting holes are 2.18 mm.
Mount centres are (2.3,2.3) and (15.5,15.5) relative to the rounded nominal
17.8 x 17.8 mm body. Published positional tolerance is +/-0.1 mm and board-edge
tolerance +/-0.3 mm. The drawing gives 6.0 mm maximum component height above
the board, 1.02 mm PCB thickness and 1.1 mm underside component height. Header
height, solder joints and electrical clearance are additional assembly inputs.

### Independent integrated-board checks

The current integrated generator's MGM240P, Pololu and Bel contact positions
were compared with their source drawings. The
[Bel 0813-1X1T-57-F drawing](https://www.belfuse.com/media/drawings/products/magjack%20ICMs/dr-mag-0813-1x1t-57-f.pdf)
Rev F sheet 4 explicitly says **COMPONENT SIDE VIEW**. Its two locating holes
are x +/-6.35 mm about the chosen origin; shield holes are x +/-8.0645,
y -3.175 mm. Signal rows are y 15.24 and 17.78 mm. Missing positions 3, 4 and 12
are intentional. No additional mirroring of that drawing is required. This
check establishes orientation and nominal contact locations, not routing,
isolation, insertion fit or manufacturing tolerances.

## Enclosure compatibility with the actual PCB candidates

The earlier [low-power concept](../../../../mechanical/low-power/parameters.json)
has a 190 x 145 x 45 mm exterior, 2.4 mm walls and a 160 x 100 mm carrier blank
at (15,12,10). Its mounting centres relative to the blank are (5,3.5),
(155,3.5), (5,95), (120.5,95). This is a concept model, not the mechanical
definition of either new electrical PCB.

- **Modular carrier C0:** the current [carrier](../../carrier/) is 160 x 100 mm,
  with 3.2 mm mounting holes at (5,5), (155,5), (5,95), (155,95). Three centres
  differ from the concept: two by 1.5 mm in y, and the lower-right by 34.5 mm
  in x. It is not a drop-in fit. The hardware design deliberately retains its
  corner-hole pattern. Its off-board S3, radios, Ethernet and power modules
  also need separate mounts and cable volumes; fitting this PCB rectangle
  alone would not prove that the whole modular assembly fits.
- **Required modular [MGM adapter M0](../../carrier/mg24-adapter/):** this separate board is 60 x 40 mm,
  with 2.2 mm M2 mounting holes at (3,3), (57,3), (3,37), (57,37), relative
  to its own upper-left corner. There is one M0 per C0-based hub. Its module
  antenna edge aligns with its top edge; the 60 mm width follows the
  datasheet ground-plane recommendation. Neither these mounts nor the
  UART/service connector volumes exist in the earlier case model. M0 is
  not used by the integrated design, which mounts MGM240P directly.
- **Integrated I0:** the current [integrated candidate](../../integrated/)
  is 160 x 142 mm, with 3.2 mm mounting holes at (5,5), (155,23), (5,137),
  (155,137). The old case's inner depth is only 140.2 mm even before its
  bosses. The PCB is 1.8 mm deeper than this cavity and cannot fit in the
  original orientation; rotating it in-plane does not solve the mismatch.
  Its holes and connector positions also differ. Do not print the old case
  as an enclosure for I0.

The I0 upper-right hole is intentionally lower than the upper-left hole:
moving it from (155,5) to (155,23) avoids the MGM240P body and keeps a nominal
6.8 mm fastener-head envelope below the antenna. With the module at (139,0),
that head's upper edge is y=19.6 mm, 14.8 mm below the antenna region's lower
edge y=4.8 mm. Other conductive hardware and cables still require their own
clearance check; this is a planar nominal-envelope comparison, not a completed
assembly test.

A concrete **next-revision envelope to investigate**, not a new validated CAD
release, is 210 x 190 x 55 mm exterior with 2.4 mm walls. For I0, place the
PCB upper-left at (25,18), underside z=10 mm. This yields mount centres
(30,23), (180,41), (30,155), (180,155), using four insulating M3 standoffs.
The nominal rectangular cavity is 205.2 x 185.2 mm: this placement leaves
22.6 mm on each side of the PCB, 15.6 mm above its top edge and 27.6 mm below
its bottom edge, before lid bosses and other mounts are added.

The current I0 MagJack and USB service connector face the PCB's left edge.
That 22.6 mm margin is a starting cable/adapter reservation, not a validated
plug bend radius. Use measured plugs to decide between wall access, recessed
access and an internal extension. The right-side CC1101, ZAC93 and radar
harnesses need routes to separately mounted modules. An isolated BME680 pod
still belongs outside the warm main volume, with a measured internal-plus-
external I2C lead length. Those remote radio and sensor mounts have not been
placed in this new envelope.

Choose actual standoff, insert and screw lengths after the underside solder
envelope and board thickness are fixed. Check the upright PoE module, Pololu
headers, connector insertion paths, all antenna clearances, radar field of
view, lid bosses and strain relief in a full assembly before generating new
print files. The 210 x 190 x 55 mm proposal is intentionally not claimed to
contain every off-board module, or to be the minimum possible case size.
Existing STL/SCAD assets have not been silently changed.

## Reproduce and verify

From the repository root, using Python 3 and its standard library:

```sh
python3 hardware/low-power/visual/physical/build.py
python3 hardware/low-power/visual/physical/build.py --check
python3 -m unittest discover -s hardware/low-power/visual/physical -p 'test_*.py'
```

Checks cover contact-identity coverage, known orientation/row transitions,
WIZ850io's power order, the Pololu top/bottom distinction, source hashes,
SVG XML validity and generated-file freshness. The SVGs were also rendered
and visually reviewed. None of these checks substitutes for a 1:1 print
comparison, real parts, PCB assembly inspection, DRC or RF testing.

## Attribution and license boundaries

The S3 and H2 source footprints remain under their upstream library license:
[CC BY-SA 4.0 with the KiCad electronic-design exception](source/LIBRARY-LICENSE.md).
The S3 footprint is attributed to the KiCad library contributors; the H2
footprint to the Espressif KiCad library contributors at the pinned revision.
Generated illustrations using those footprints retain these source and
license references. The drawing renderer and manually transcribed factual
coordinate data use this repository's license; that does not relicense the
vendor libraries, logos, photographs or PDF artwork. Manufacturer photos and
PDFs are linked, not redistributed in this directory.
