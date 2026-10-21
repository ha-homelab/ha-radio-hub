# Full-hub mechanical source ledger

Thread-board and power assembly updated 2026-10-20; other evidence reviewed 2026-10-19. The user confirmed the delivered Z-Wave board is a **Zooz
ZAC93**. No board, connector or enclosure has been physically measured in this
work. [components.json](components.json) separates published nominal dimensions
from the larger engineering envelopes used for layout. Envelopes include the
allocated installed pins/socket height, while cable insertion and bend space is
listed separately. They are not manufacturer tolerances or a fit certificate.

## Selected parts and mounting evidence

### Carrier and its four fitted modules

The current carrier is MC2-D, with ESP32-DevKitC-VIE / ESP32-WROVER-IE,
Seeed Studio XIAO ESP32C6 pre-soldered SKU 102010636, Seeed XIAO MG24 and WIZnet WIZ850io. Its authoritative
outline, four mounting holes and fitted-part plan geometry are in the project
[CAD manifest](../../hardware/external-antenna/cad/design.json). The bare PCB is
100 x 100 mm with four 2.7 mm holes at (4,4), (96,4), (4,96), (96,96).
WIZ850io's jack reaches y=102 mm and needs a plug/latch corridor to y=138 mm in
carrier-local coordinates. The populated height is an allocation, not a measured
stack. Individual modules are retained by their soldered headers; the case
supports the carrier and the Ethernet jack. Do not add screws through module
PCBs. The wiring authority remains the
[connector ledger](../../hardware/external-antenna/cad/connectors.json).

### Factory-header stack and coax approach

U1 ESP32-DevKitC-VIE, U2 XIAO ESP32C6 102010636 and U3 XIAO MG24 102010690
are purchased with male headers and soldered directly into the carrier.
No female module sockets or raised stand-offs are specified. The model uses a
**2.54 mm header-plastic gap as an engineering allocation**, placing each radio
PCB underside 4.14 mm above the carrier underside. This is not a measured or
manufacturer-certified spacer height: the
[Espressif dimension drawing](https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_dimensions.pdf)
and [Seeed MG24 guide](https://wiki.seeedstudio.com/xiao_mg24_getting_started/)
establish plan geometry but do not qualify the delivered header stack in Z.
The existing 8 mm allowance above each radio PCB plane is retained for its PCB,
components and connector envelope. Check the delivered boards against it.

The former generic 9 mm U1/U3 PCB plane made the last Zigbee coax leg look
shorter. The current model lowers that plane and its connector endpoint,
and routes the three coax cables through **z=32 mm**, rather than z=40 mm,
before the final connector approach. With the nominal direct-header stack,
the longest guide is 117.141 mm plus 25 mm service allowance, within the 144 mm
project cable budget. The generator checks the full rounded sweeps against
printed parts and all module envelopes. Confirm actual header height, socket
height, the estimated U1/U3 socket XY and the formed 150 mm cables before
final assembly; these calculations do not certify physical fit.

### XIAO ESP32C6 revision change

MC2-D selects **Seeed Studio XIAO ESP32C6 with factory-soldered headers,
SKU 102010636**, replacing the TinyC6[D] fitted to historical MC2-C boards.
The [manufacturer hardware guide](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/)
gives a nominal 21 × 17.8 mm PCB and links the manufacturer's KiCad sources.
The current [native CAD ledger](../../hardware/external-antenna/cad/design.json)
records the footprint, USB shell and external-antenna connector location.
The bare 113991254 board and bundles without installed headers are not the
selected purchase. A pre-soldered header does not eliminate the two underside
EN and BOOT service connections required by this carrier; make those fine
wire joints before seating the board. Keep the separate battery pads empty.

Neither the public PCB dimensions nor a generic product picture establish
factory-header height. The model retains an explicit engineering allowance
for the installed stack and underneath service wires, which must be checked
on the delivered board. Factory male headers solder directly into the carrier;
no extra female sockets are specified. The nominal 2.54 mm header plastic puts
the C6 PCB underside 4.14 mm above the carrier underside (1.6 + 2.54 mm).
The native carrier includes an access window under the EN/BOOT pads. Keep
each insulated fine wire at most 0.8 mm in outer diameter and underside solder
joints within 1.5 mm of the module PCB. Header pitch is 2.54 mm, with two seven-pin rows;
check the pin-one orientation and full seating before applying power.

The enclosure generators consume the current native-CAD U.FL endpoint when
checking the three separate 150 mm coax routes. A fitted AMC plug, header
stack and formed cable bend still need a dry fit. The full enclosure retains
its 215 × 215 × 78 mm outer dimensions and 30 mm populated-carrier reservation.
Program the loose board over USB first; routine assembled updates use the
documented host-to-RCP path. USB insertion into the assembled stack is not a
qualified service route. Only the **MC2-D RCP firmware** selects the XIAO's
external antenna using GPIO3 low and GPIO14 high. TinyC6[D] firmware is not
interchangeable.

### Zooz ZAC93

The [Zooz manual](https://www.getzooz.com/downloads/zooz-z-wave-800-series-long-range-gpio-module-zac93-LR-manual.pdf)
lists a 1.1 x 1.1 inch body, equivalent to 27.94 x 27.94 mm. This rounded figure
does not define PCB-edge tolerances, total socket height or a mounting-hole
pattern. The [manufacturer installation guide](https://www.support.getzooz.com/kb/article/1215-zac93-800-gpio-module-installation-guide/)
shows the underside connector fitted to a host header and cautions against
forcing it. This enclosure therefore uses a nonconductive cradle with clearance
for that connector and a wired mating header, not an invented screw pattern.
Keep the stock antenna at the outer plastic wall, with no cable, metal fastener
or strap over its active region. The 10 mm antenna-side reservation is our
provisional layout rule, not a published Zooz guarantee. Inspect the delivered
antenna edge and mating orientation before installing retention hardware.

### DFRobot DFR0627 / WK2132

The [manufacturer wiki](https://wiki.dfrobot.com/dfr0627/) specifies 32.5 x 27 mm.
Its [dimension drawing](https://dfimg.dfrobot.com/wiki/20531/DFR0627_i2c-to-uart-module_dimension_V1.0.pdf)
shows a 1.6 mm PCB and two holes on the same side at 20 mm center spacing.
That drawing does **not** dimension their diameter or their x offset. The wiki's
“Mounting Hole Size 20mm” describes that spacing; it must not be interpreted as
a 20 mm hole diameter. The full-hub design uses an adjustable tray rather than
inferring the missing dimensions. Leave room for the Gravity plug, UART1 header,
address switches and reset access. Header height must be checked on the actual
board with its cables fitted.

### Power splitter and buck regulator

This layout explicitly selects the finished **Waveshare
POE-SPLITTER-25W-5.5-2.1**, the DC-output version. Its
[manufacturer page](https://www.waveshare.com/product/accessories/power-heat-sinks/poe-splitter-25w-type-c.htm)
specifies an isolated 5 V output and a 102.5 x 29.6 x 24.8 mm metal body. The
body dimensions exclude captive tails and plugs. Keep its factory housing
intact and retain it using insulated straps without obstructing heat transfer.
The cable bay is part of the design, not spare space. This selection supersedes
the earlier Silvertel EvalPoE option **for this enclosure**; ownership of the
Waveshare splitter has not been confirmed. Check its actual tail lengths,
exit orientation and input-plug access before printing the main case.

PWR1 selects **RECOM R-78K3.3-1.0**. The
[manufacturer datasheet, Rev. 6-2025, page 7](https://recom-power.com/pdf/Innoline/R-78K-1.0.pdf)
gives a nominal 11.5 × 7.55 × 10.2 mm body, three 0.64 ± 0.1 mm pins on
2.54 mm pitch, 4.1 mm nominal exposed leads and a 1.7 g typical weight.
Dimensions with one decimal have ±0.5 mm tolerance; two decimals have
±0.25 mm tolerance. The model conservatively reserves the full tolerance
range around the planned pad position. The package has no mounting holes.
Pin mapping and electrical qualification belong to the electrical guide.

Page 2 requires a **27 µF input electrolytic for hard plugging or input slew
above 10 V/µs**. The selected **Panasonic EEU-FS1H270** is 27 µF / 50 V;
its [FS-series datasheet](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1255.pdf)
lists a 5 mm diameter × 11 mm body, with +0.5 mm diameter and +1.5 mm length
tolerance. The model reserves 5.5 × 5.5 × 12.5 mm, and keeps the vent clear.
Its 2 mm lead pitch must be formed gently for the 2.54 mm pad grid without
loading the seal.

The project-cut **24 × 24 × 1.6 mm isolated-pad perfboard** is an engineering
mounting choice, not a commercial board footprint. Two ledges support its
copper-free edges at z=12 mm; the tray floor top is z=8.4 mm. Trimmed solder
and insulated wiring may project at most 2 mm below the board, leaving a
1.6 mm clearance to the floor. A cleared rear band accepts a soft restraint,
and a separate loop relieves cable load. No screws or drilling through the
RECOM body are permitted. The PWR1 tray and base have a new screw pattern;
the main enclosure size, other trays, RF1 holes and cable paths are retained.
Nominal fit does not establish printed fit, temperature or electrical operation.

### CC1101

The existing 433.92 MHz module has no confirmed board manufacturer or mechanical
drawing. [TI's CC1101 page](https://www.ti.com/product/CC1101) describes the IC,
not the user's module, antenna or header arrangement. The 55 x 30 x 18 mm
reservation is an adjustable-tray design limit, **not a measured module size**.
The actual board, GDO2 access, connector polarity and antenna extension must be
checked. Keep its dedicated 433.92 MHz antenna separate from the three 2.4 GHz
antennas. A final SMA or RP-SMA cutout cannot be selected from the chip name.

### LD2450

[Hi-Link's product page](https://www.hlktech.com/cn/Goods-352.html) specifies
44 x 15 mm, a 5 V supply, 3.3 V UART signals and wall mounting around 1.5-2 m.
The product page's relative downloads failed, but the manufacturer's download
host provides the [3D STEP archive](https://h.hlktech.com/download/HLK-LD2450-24G/1/HLK-LD2450--3D%E5%9B%BE.zip) and
[radome guide](https://h.hlktech.com/download/HLK-LD2450-24G/1/%E6%AF%AB%E7%B1%B3%E6%B3%A2%E4%BC%A0%E6%84%9F%E5%99%A8%E5%A4%A9%E7%BA%BF%E7%BD%A9%E8%AE%BE%E8%AE%A1%E6%8C%87%E5%8D%97_%E6%B5%B7%E5%87%8C%E7%A7%91.pdf). The guide calls for a smooth, uniform, nonconductive
window parallel to the antenna. Its design pages discuss 6.2 mm air half-wave
multiples, preferring 12.4 or 18.6 mm when space allows; a later generic mounting
page instead says 3-5 mm. Treat these as design guidance requiring validation,
not one universal fit dimension. Window thickness depends on dielectric
properties; the thin-window alternative is at most an eighth wavelength in
the material, not in air. The cassette must hold safe board edges and leave
the active antenna face free of metal, ribs and wiring. The chosen printed
material, window thickness and air gap remain RF test items. Ceiling mounting
is not automatically equivalent to the manufacturer's wall orientation.

### Adafruit BME680 STEMMA QT / product 3660

The [product page](https://www.adafruit.com/product/3660) distinguishes the
post-2020 STEMMA QT board from the differently shaped original. The official
[Eagle board](https://github.com/adafruit/Adafruit-BME680-PCB/blob/master/Adafruit%20BME680.brd)
defines a 25.4 x 17.78 mm outline. Its lower-left-origin hole centers are
(2.54,2.54), (22.86,2.54), (2.54,15.24), (22.86,15.24); the lower pair are
2.54 mm drills and the upper plated pair are 2.5 mm drills. These dimensions
were read from the current manufacturer's CAD, not from a scaled photo.
The manifest records the pattern even if the cassette uses edge retention.
An externally ventilated pod avoids trapping the sensor with the warm splitter
and radios. Leave the sensor vent and QT connectors unobstructed; avoid glue or
foam on the sensor. The
[manufacturer downloads page](https://learn.adafruit.com/adafruit-bme680-humidity-temperature-barometic-pressure-voc-gas/downloads)
also links its CAD and 3D model.

## Antennas, harnesses and small retained parts

The selected three **TE/Linx ANT-2.4-LCW-SMA** antennas are external to the shell:
[manufacturer source](https://www.te.com/en/product-L9000082-01.html). Their
nominal 83.1 mm length and 10 mm maximum width are in the existing
[RF BOM](../../hardware/external-antenna/rf-bom.json); allow additional swivel
sweep. The three **Taoglas CAB.618.E** cables are nominally 150 mm, 50 ohm,
1.13 mm coax, I-PEX MHF I/U.FL right-angle plug to standard SMA female bulkhead.
The [manufacturer catalogue](https://www.taoglas.com/datasheets/Taoglas_Cable_Assembly_Catalog.pdf)
(page 11) gives the grouped drawing and includes this 150 mm SKU. Its illustrated
200 mm sibling is labelled ±6 mm; that **does not establish the exact tolerance
of CAB.618.E**. RF1 conservatively budgets **144 mm**, retaining 25 mm of service
slack. The [cable specification](https://cdn.taoglas.com/specifications/30021F0020000A_Taoglas.pdf)
gives a **6.8 mm minimum bend radius** for that cable family. Its exact internal
wire part number is not established for CAB.618.E, so this is the project
engineering basis; obey any stricter requirement supplied with the cable.
The generator uses circular bends with
that radius and collision-checks their sampled paths, not only sharp-corner
guides. Straight lead-in remaining before the first bend must be at least **21 mm**:
17 mm reference heatshrink plus up to 4 mm flange/body length, calculated from
the grouped drawing. A 27 mm guide lead-in leaves that clearance after the
first bend.

RF1 replaces the former Amphenol-specific D holes with **round 6.8 mm holes**:
6.6 mm project clearance plus 0.2 mm trial print allowance. This is a project
cutout, **not a Taoglas panel recommendation**. The 3 mm-thick coupon now matches
the 3 mm wall and offers 6.6/6.8/7.0 mm trials. The 1/4–36 threaded barrel must
seat without force; fit the supplied washer and nut and hold the shoulder
against rotation when fitting the antenna. The drawing's 11.4±0.3 mm projection,
1.75±0.2 mm nut and 1.1±0.3 mm washer leave a nominal 5.55 mm after the 3 mm wall
(4.75 mm using the most adverse stated dimensions). This arithmetic **does not
prove full antenna thread engagement**: test the complete stack on the coupon.
The linked STEP download was challenged and was not used for geometry claims.
[rf-evidence.json](rf-evidence.json) records source hashes, derived allowances and
remaining checks. The current PCB and radio firmware are MC2-D.

The inline fuse holder and female 5.5 x 2.1 mm DC adapter have no selected
manufacturer part numbers. Their listed 35 x 18 x 18 mm and 40 x 16 x 18 mm
envelopes are engineering allowances. Both need positive retention and insulated
terminals in the utility bay; neither may be left loose on a PCB. Select a fuse
against the measured inrush/load and wire ratings. The remaining required items
are the seven carrier harnesses, ZAC93 2x5 mating header, BME QT cable, cable
retainers and enclosure hardware. Screw counts/lengths belong to the generated
assembly BOM. The battery bank, PoE switch and Home Assistant server remain
outside this case.

## Physical acceptance still required

Before full printing, measure the delivered ZAC93 socket/board envelope and the
existing CC1101, identify the actual PoE splitter, check every cable with its
connectors fitted, and print the small fit parts. After assembly, check that
retention touches safe surfaces, cables cannot abrade metal or reach live pads,
connectors remain serviceable, and antennas/radar apertures remain clear. Run
temperature, simultaneous-load and radio-coverage checks with the cover fitted.
Digital collision tests cover the declared envelopes, not unmeasured hardware.
