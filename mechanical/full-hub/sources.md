# Full-hub mechanical source ledger

Reviewed 2026-10-19. The user confirmed the delivered Z-Wave board is a **Zooz
ZAC93**. No board, connector or enclosure has been physically measured in this
work. [components.json](components.json) separates published nominal dimensions
from the larger engineering envelopes used for layout. Envelopes include the
allocated installed pins/socket height, while cable insertion and bend space is
listed separately. They are not manufacturer tolerances or a fit certificate.

## Selected parts and mounting evidence

### Carrier and its four fitted modules

The current carrier is MC2-B, with ESP32-DevKitC-VIE / ESP32-WROVER-IE,
Unexpected Maker TinyC6-U-01, Seeed XIAO MG24 and WIZnet WIZ850io. Its authoritative
outline, four mounting holes and fitted-part plan geometry are in the project
[CAD manifest](../../hardware/external-antenna/cad/design.json). The bare PCB is
100 x 100 mm with four 2.7 mm holes at (4,4), (96,4), (4,96), (96,96).
WIZ850io's jack reaches y=102 mm and needs a plug/latch corridor to y=138 mm in
carrier-local coordinates. The populated height is an allocation, not a measured
stack. Individual modules are retained by their soldered headers; the case
supports the carrier and the Ethernet jack. Do not add screws through module
PCBs. The wiring authority remains the
[connector ledger](../../hardware/external-antenna/cad/connectors.json).

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

The [Pololu D24V22F3 page](https://www.pololu.com/product/2857) specifies
17.8 x 17.8 x 8 mm. Its
[drawing](https://www.pololu.com/file/0J1031/d24v22fx-step-down-voltage-regulator-dimension-diagram.pdf)
defines two diagonal 2.18 mm mounting holes, nominally 2.3 mm from the adjacent
edges, a 1.02 mm PCB and underside components reaching 1.1 mm below it.
Use insulated M2 supports or an open tray; do not press the underside onto a
solid adhesive pad. The manifest converts the hole coordinates to a lower-left
origin. The larger 12 mm installed-height allocation includes wiring allowance.
The supply's thermal capability at the actual 5 V input and enclosed load still
requires measurement.

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
sweep. The three **Amphenol 095-902-545-150** cables are 150 mm with 1.13 mm cable:
[product](https://www.amphenolrf.com/en-us/part/095-902-545-150/8897/) and
[drawing](https://www.amphenolrf.com/en-us/assets/file/4068032676/). The SMA
bulkhead drawing uses a 6.6 mm round / 6.1 mm flat panel cutout. Printed clearance
and nut engagement require the fit coupon and the actual parts.

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
