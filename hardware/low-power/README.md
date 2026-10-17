# Low-power LP-P0: prototype hardware contract

This is a separate design with **one S3 host and one Ethernet interface**, three dedicated radio controllers H2/MG24/ZAC93, and CC1101. Assembly, firmware for the individual radio modules and hardware testing are required. No board has been fabricated or tested, and there is no verified “3 W” result.
The [ready-module carrier](carrier/) and [integrated board](integrated/) are
separate engineering revisions; use their own verification reports and connector maps.

The current calculation gives scenarios of **2.03 / 2.82 / 4.92 W incremental AC power**. These are not measurements or a confidence interval. **3 W AC is a testable target**, not a guaranteed specification. Detailed assumptions, current reserves and calculation boundaries are in [power-budget.json](power-budget.json); the earlier architectures are compared separately in [energy-comparison.json](energy-comparison.json).

## Files and validation

- [BOM](bom.json): exact main models, quantities, `bench`/`carrier`/`both` stages and primary sources. Do not combine alternatives for different stages into a single order.
- [Pinmap](pinmap.json) and [wiring CSV](wiring.csv): 26 unique S3 GPIOs, three native UARTs and two SPI buses. The CSV defines signals; a GPIO number is not a header contact number.
- [Visual connection atlas](visual/README.md): offline interactive pin-to-pin guide, part identification sketches and printable connection sheets, with physical-pad evidence and unverified header positions distinguished.
- [Manufacturing and sales](../../docs/manufacturing.md): first articles, batch sizes, fabrication services and all three delivery formats.
- The [combined firmware](../../firmware/low-power/hub.yaml) uses the same GPIOs. Build status and software limitations are in [firmware/low-power](../../firmware/low-power/).
- [Enclosure mockup](../../mechanical/low-power/): 160×100 mm carrier reservation, 190×145×45 mm shell. The EvalPoE/DevKit development boards are not claimed to fit this enclosure.

Run from the repository root: `python3 hardware/low-power/validate.py`. This checks contracts and arithmetic, not electrical operation.

## Two assembly stages

**Bench:** external active IEEE 802.3af/at PSE → Ethernet cable → **Silvertel EvalPoE fitted with Ag97005-FL**. EvalPoE `DATA OUT` → short RJ45 patch cable → **WIZ850io**. EvalPoE isolated 5 V output → fused distribution → LD2450 and **Pololu D24V22F3**. The shared 3.3 V buck output powers S3, H2, MGM240P, ZAC93, CC1101, SC16 and BME680. There is no internal switch; one external cable supplies power.

EvalPoE compatibility with Ag97000-FL is explicitly stated on the [manufacturer's page](https://silvertel.com/ag97000/), although the PDF manual lists older models. Specify **Ag97005-FL** when ordering rather than assuming the module is included with an empty EvalPoE. Check bridge-bypass and output-filter settings against the revision of the [EvalPoE manual](https://silvertel.com/images/Eval-Board-User-Guides/POE-Eval-Board-User-Manual.pdf): the FL uses its built-in bridges, bypasses the external bridge, uses class 0 and keeps the nominal untrimmed output. Measure 5 V and polarity before connecting logic.

**Ready-module carrier (LP-C0):** distributes isolated 5 V and regulated 3.3 V,
provides a local SC16/clock/reset circuit and keyed harnesses to the controller,
radios and sensors. Its [MG24 daughterboard](carrier/mg24-adapter/) mounts the
exact MGM240PA22VNA3 and provides UART, BOOT and SWD service access.
The external EvalPoE, buck, WIZ850io and radio boards still
need separate mounting. A bare carrier does not include those modules.

**Integrated board (LP-I0):** places the bare S3/H2/MGM240P modules, W5500,
PoE magjack, Ag97005-FL, buck and support circuits on a separate PCB. ZAC93,
CC1101, radar and the external BME680 remain cable-connected. It needs its own
larger enclosure and physical bring-up; the earlier concept case is not a fit claim.

**WIZ850io does not expose PoE center taps on its SPI headers. Do not connect
Ag97005-FL inputs to those headers.** LP-C0 retains the external isolated front
end; LP-I0 uses its own specified PoE-capable magjack. A successful CAD check
is not validation of PoE isolation, Ethernet performance or radio coexistence.
Until the boards pass bring-up, EvalPoE on the bench remains the assembly path.

## Power and calculation

The selected [Ag97005-FL](https://silvertel.com/images/datasheets/Ag97000-Datasheet-low-cost-isolated-12W-Power-over-Ethernet-PoE-module-solution.pdf) is the 5 V/9 W version, 1.8 A nominal. The generic “12 W” describes the family, not this SKU. Class 0 is retained for startup/peaks; an average of 3 W AC alone does not justify selecting class 1. Use the recommended 100 µF + 100 nF + 10 µF output capacitors, accounting for parts already installed on EvalPoE. The main output-capacitance range is 47–470 µF; check additional capacitance and buck startup with an oscilloscope.

The peak **design reserve**, adding simultaneous loads, is 1.025 A at 3.3 V and 0.25 A directly at 5 V. At 85% buck efficiency and 0.15 W distribution loss, this is **5.38 W at the PD output**. It is not a guaranteed maximum for the actual modules. [D24V22F3](https://www.pololu.com/product/2857) is advertised as 2.6 A typical under specified conditions; this assembly needs a separate **1.5 A test with 5 V input** and thermal verification. Do not apply a 24 V input rating at 5 V without a curve/test. A 1.5 A slow-blow fuse on the secondary 5 V branch is an initial candidate; select the final I²t after startup testing and checking wire gauge.

Average-consumption model: `P5 = P3.3 / ηbuck + Pradar + Pwiring`, then `PAC = P5 / ηPD / ηcable / ηPSE`. The ηPD input/output boundaries are the PoE module pins; built-in bridges are already included. Low-voltage wiring is counted once. The 81.5% value is the selected FL's **peak typical** datasheet efficiency, not a guaranteed efficiency at 1.9 W. The model uses 68/76/81.5%; the two lower values are assumptions pending measurement. Add the fixed consumption of a new dedicated PSE separately; the already-running shared HA server and baseline network-infrastructure consumption are excluded.

The minimum load for maintaining PoE MPS is 70 mA at 5 V. Continuous LD2450 operation normally supplies this load, but startup and fault states must be checked; no parallel resistor for waste heat is added in advance. Required network/BLE/radar functions must remain active: disabling them does not qualify as reaching 3 W. The W5500 firmware forces 10 Mbps half-duplex; the budget deliberately retains the conservative 100 Mbps estimate without subtracting expected savings. Link stability and actual power have not yet been measured.

## S3, UARTs and the actual DevKit

The target module is **ESP32-S3-WROOM-1-N16R8**. GPIO26–37 are excluded because of flash/PSRAM, 19/20 are reserved for native USB, and 0/3/45/46 are excluded as strapping pins. GPIO38 is free. UART0 belongs to LD2450, UART1 to the MG24 TCP bridge with RTS/CTS, and UART2 to H2 OTBR. These UART numbers do not determine physical GPIOs: the GPIO matrix is used. There is no fourth native UART, so ZAC93 connects through SC16IS752.

Existing DevKits require **physical** changes before connection:

1. The S3 development board's USB–UART TX must not drive GPIO44, which receives H2 TX. Check/isolate the USB–UART connections to 43/44 and the effect of auto-reset against the actual board schematic. Selecting native USB in YAML does not disconnect these traces.
2. Similarly, on the H2 DevKit, check and isolate USB–UART TX from GPIO23, which will receive S3 data. Do not join two push-pull outputs.
3. GPIO48 must be free of the RGB LED; the official DevKitC-1 v1.1 has its LED on 38, while the earlier version uses 48. An “N16R8” label does not identify the board revision.
4. External 3.3 V and USB/5 V must not power different regulators in parallel. Disconnect the shared supply and peripherals for initial flashing; on a running bench setup, use a verified USB data-only/isolated-VBUS path. Check for back-powering and loading of an unpowered controller through UART.

The [official DevKit guide](https://docs.espressif.com/projects/esp-idf/en/v5.1.2/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html) and [S3 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) define these constraints. An unverified clone cannot be treated as a drop-in board for this pinout.

## H2 and MG24

**ESP32-H2-MINI-1-H4S**, 4 MB, is a dedicated Thread RCP, not another IP host. S3 TX43 → H2 GPIO23 RX, H2 GPIO24 TX → S3 RX44. S3 GPIO47 controls EN and GPIO48 controls BOOT/GPIO9; both outputs are open-drain, with HIGH meaning the line is released through an external pull-up. EN: 10 kΩ to 3.3 V + 1 µF to GND; BOOT: 10 kΩ to 3.3 V. Also pull H2 GPIO8 up to 3.3 V through 10 kΩ: download boot requires GPIO8=1, GPIO9=0. Hold GPIO25 low with 10 kΩ to GND; do not change eFuses. Keep EN/BOOT/GND service test points accessible. [H2 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-h2-mini-1_mini-1u_datasheet_en.pdf).

**MGM240PA22VNA3** is the selected +10 dBm MG24 variant with a built-in antenna. It requires a custom Ember NCP image with UART 115200, 8N1 and hardware RTS/CTS matching this contract: S3 TX17 → PA05/pad12 RX; PA06/pad13 TX → S3 RX18; S3 RTS16 → PB01/pad5 CTS; PB00/pad6 RTS → S3 CTS21. An [NCP and UART-XMODEM bootloader have been built](../../firmware/low-power/mg24/) for this assignment using Simplicity SDK 2025.6.3 / Zigbee 8.2.3 / EZSP 18. Generation, compilation, CRC and image checks passed; module flashing, UART/CTS, pairing and radio-network operation have not yet been tested. Factory and SLZB images are not claimed to be interchangeable.

To enter the built bootloader, expose **PA00/pad7 BOOT** with 10 kΩ to 3.3 V and a separate service jumper to GND; hold it LOW during reset. This uses no S3 GPIO. For SWD, expose PA01/pad8 SWCLK, PA02/pad9 SWDIO, RESETn/pad31, GND and 3.3 V VTref. RESETn has an internal pull-up to DVDD: only pull it to GND and release it; **do not add an external pull-up to 3.3 V**. Connect power to VDD/pad15 and all GND pins according to the [MGM240P datasheet](https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf). Verify the service-connector pinout against the selected programmer; USB-UART does not replace SWD for initial programming of a blank module.

## SC16IS752 and ZAC93

The selected part is **SC16IS752IPW,128, TSSOP28**. SPI is shared with CC1101, with separate CS pins GPIO41 and 15. IRQ pin15 → S3 GPIO42, with **1 kΩ to 3.3 V**, according to [NXP rev9.1](https://www.nxp.com/docs/en/data-sheet/SC16IS752_SC16IS762.pdf). I2C/SPI pin9 and unused SDA pin14 → GND. Supply pin8=3.3 V, pin22=GND. The current driver uses SPI mode 0 at 4 MHz; the SC16IS752 limit is 4 MHz, not the SC16IS762's 15 MHz.

Channel A: TXA/pin3 → ZAC93 header pin8 RX; ZAC93 pin10 TX → RXA/pin4. ZAC93 pin1=3.3 V, pin6/9=GND; do not connect other contacts without checking the revision. Hardware flow control is disabled; CTSA/pin2 and CTSB/pin16 → GND; RXB/pin24 is pulled up to 3.3 V through 10 kΩ; RTSA/RTSB/TXB outputs remain unconnected. The eight unused GPIOs have separate 100 kΩ resistors to GND to prevent floating inputs without shorting a future output.

Use an **ABLS-3.6864MHZ-B2-T** crystal between XTAL1/pin6 and XTAL2/pin7; prescaler 1 and divisor 2 give 115200 baud. Initial 22/33 pF C0G load capacitors come from the NXP example and require frequency/startup checks with the actual 18 pF crystal and stray capacitance. Initially keep the SPI harness no longer than 5 cm and check edges/noise with an oscilloscope; adjust driver speed and repeat testing if needed. **The firmware setting `crystal_frequency: 3686400` is mandatory.** A typical off-the-shelf 14.7456 MHz breakout is not interchangeable without configuration/driver changes.

RESET/pin5 receives the open-drain output of **TPS3808G33DBVR**, with 10 kΩ to 3.3 V; VDD/SENSE=3.3 V, CT unconnected (20 ms), and MR may use its internal pull-up or a button to GND. Install 100 nF at VDD and 1 nF at SENSE. [TI datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf). SC16 power starts alongside the S3; software reset does not replace slow-ramp/brownout testing.

A 64-byte FIFO fills in about 5.56 ms of continuous data at 115200 8N1. The handler must service IRQ before the remaining FIFO headroom runs out; a 2048-byte software queue cannot compensate for late hardware-FIFO reads. Stress-test alongside RF TX, BLE, Ethernet and Thread. Loss/overrun must not silently turn into valid Z-Wave messages.

## RF, sensors, antennas and enclosure

CC1101: shared SPI7/8/6, CS15, GDO0→GPIO4 open-drain with 4.7 kΩ to 3.3 V, GDO2→GPIO5. This is a two-signal RF design; boards without accessible GDO2 need a separate solution. Preserve the existing RF contract/encodings when connecting to the new host. Check the clone's physical contacts against its markings, not an arbitrary photo.

LD2450 receives 5 V directly from the PD, with UART TX→S3 GPIO40 and RX←GPIO39 and common secondary GND. BME680 VIN receives 3.3 V, SDA1/SCL2, 100 kHz, address 0x77. Use the stock Adafruit pull-ups; keep the external pod away from heat and initially limit I²C to 10–20 cm. Adding sensors requires capacitance/edge margin; a free address does not imply GPIO/power headroom. BME680 gas resistance is not a direct CO₂ measurement.

Retain the stock antennas: S3 PCB, H2 PCB, built-in MGM240P, regional ZAC93 and the existing 433 MHz CC1101 antenna. Do not substitute 2.4/5.8 GHz antennas for 433 MHz. Place antennas along the carrier edges, away from metal, buck/PoE circuitry and cable bundles; apply each module's datasheet keep-out rather than a single general rule. Simultaneous BLE/Thread/Zigbee operation at 2.4 GHz requires loss/latency checks and channel selection. Individual radio certifications do not certify the combined enclosure.

The radar looks through a 1.2 mm nonmetallic wall; radome geometry and the absence of conductive fillers matter. ZAC93 limits ambient temperature around it to 0…40 °C; the S3 N16R8 has a 65 °C limit, which does not justify heating ZAC93 above 40 °C. Measure air temperature near the modules separately from buck surface temperature. The low-power drawings retain **unmeasured** envelopes for the existing ZAC93/CC1101, wires and connectors.

## Before releasing a hardware revision

1. Check actual modules/connectors, DevKit UART isolation, GDO2, GPIO48 and the 3.3 V supply. Do not connect unisolated interfaces with two active drivers.
2. Assemble on the bench with EvalPoE; check rails, MPS, cold start, load transients and thermal performance. Record AC and DC separately.
3. Flash H2 and MG24, check UART/CTS and SC16 without RF load, then exercise all functions together, including long runs and recovery from power/Ethernet loss.
4. Review the selected PCB revision and its verification report before first-article fabrication. Resolve electrical, isolation, return-path, RF keep-out and mechanical findings, then run DFM and bench validation. The earlier enclosure mockup is not proof of fit for either complete assembly.
