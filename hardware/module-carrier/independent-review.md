# MC1 compact carrier independent review

Reviewed 18 October 2026 UTC. Scope: the **65 × 75 mm carrier**, native pin assignments and geometry, retained protocol interfaces, and the new host-assisted update paths. This is an engineering prototype. No assembled hardware, radio performance or physical programming operation was tested. This reviewer authored the earlier XIAO firmware adaptation; this review is not independent of that adaptation's implementation.

The carrier area is **32.3% smaller** than the preceding 80 × 90 mm version. Four ready-made modules, seven fitted harness headers, three axial diodes and two resistors remain on top: **16 fitted items, 18 electronic footprint positions, 133 pads**. J8/J9 are unpopulated service pads. Factory male module pins solder directly into carrier plated holes. There are no female module sockets or underside flying wires. **H2 R7 must nevertheless be removed before assembly**, which is a separate small surface-mount modification to a purchased module. Initial programming takes place before permanent soldering. USB sockets remain fitted, but there is no postassembly USB plug-in clearance guarantee.

## Electrical audit

The independent [native parser](audit_carrier.py) does not import the CAD generator or design ledger. It checks manufacturer hole coordinates, **133 pad assignments**, **31 connected groups / 101 connected endpoints**, separation of regulator outputs, top-side assembly, pad containment, courtyard separation, fitted versus DNP state, conservative socket projections, narrow harness housings and nylon support envelopes. Its **13 mutation checks** include swapped UARTs/flow control, split shared SPI, connected Nano VBUS, paralleled supplies, an omitted service footprint, wrong header geometry, an accidentally fitted service header and a collision with a physical USB shell. Final evidence is recorded separately in [independent-audit.json](independent-audit.json).

- Nano GPIO43 TX → H2 GPIO23 RX at J3.3; Nano GPIO44 RX ← H2 GPIO24 TX at J3.2. GPIO47 controls H2 EN; GPIO48 controls H2 BOOT/GPIO9. The same pair now serves the RCP application and the fixed ROM serial loader.
- Nano TX17 → XIAO PC07 RX; RX18 ← PC06 TX; RTS7 → PC04 CTS; CTS21 ← PC05 RTS. Ember/EZSP remains **115200 8N1 with RTS/CTS** on TCP6638.
- Shared SPI GPIO13/11/12 reaches WIZ850io and CC1101, with separate chip selects. The three native UARTs serve H2, MG24 and LD2450. DFR0627/WK2132 provides the separate Z-Wave UART.
- J8 exposes XIAO PC00/ground; J9 exposes Nano GPIO0/ground. Neither is fitted with a header in this layout. These pads do not create an automatic host-controlled reset path for MG24 or a guaranteed usable USB recovery corridor.

All **86 module pads** retain 1.80 mm copper and 1.10 mm drills, a nominal 0.35 mm annular ring. Actual pin fit, solder bridges and continuity still need inspection.

## H2 modification and programming

The [Espressif H2 DevKit guide and schematics](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html) establish the conflict: the onboard powered CP2102N drives ROM RX23 through R7, even if its USB cable is absent. The reviewed **v1.3 schematic has R7 = 470 Ω**. Remove that resistor and verify isolation before connecting Nano TX43. R9 connects H2 TX to the bridge's receive input and is not a second transmitter. Check the actual board revision and component identity; do not remove a similarly placed part by appearance alone.

Native H2 USB Serial/JTAG on GPIO26/27 remains available for the initial preassembly flash. The DTR/RTS auto-reset stage uses open-collector transistors; connecting that USB-UART port during host programming can still assert reset/boot and is excluded from the service procedure. EN uses the board pull-up; GPIO9 relies on its intrinsic reset-time pull-up. Verify BOOT voltage and timing with Nano's GPIO48 LED-gate load present. A removed resistor does not itself prove the complete strap/reset circuit works.

The new temporary TCP6639 updater requires an encrypted ESPHome API action, a fresh 128-bit token, a **durable maintenance latch after restart**, Ethernet online and no launched OpenThread stack. It accepts one authenticated client, bounds authentication and transfer time, installs its own 115200 UART driver, enters ROM through BOOT/EN, and closes/reset-cleans the session without clearing maintenance. The host explicitly resumes Thread only after esptool succeeds. Review corrections made socket nonblocking setup fail closed and verify the actual H2 partition-table binary before accepting the fixed **0x10000 / 1 MiB factory application** target.

The token handshake and image stream on TCP6639 are **not encrypted**; the API used to arm it is encrypted. Use the trusted management network and do not expose the port externally. The update tool defaults to an offline plan, checks artifact hashes, programs only the application and pins its tools. Fourteen updater tests, including real loopback binary forwarding, fragmented authentication response and rejected authentication, were independently rerun successfully with the C++ policy under address/undefined-behavior sanitizers. These are host/source tests, not a successful hardware flash.

## MG24 updates and remaining recovery limits

The existing XIAO image installs a UART XMODEM Gecko bootloader and EmberZNet8.2.3/EZSP18 application. `universal-silabs-flasher` **1.1.0**, Bellows **1.1.0** and zigpy **2.3.0** can use `socket://HOST:6638`, probe `bootloader:115200,ezsp:115200`, request normal EZSP software bootloader entry and send the application GBL. No USB reset profile is appropriate to that raw TCP path. The [reviewed flasher source](https://github.com/NabuCasa/universal-silabs-flasher/tree/d0d751cbbbb4e652f5ebf1129a1c66390ddfa3d6) uses the installed application to enter its bootloader. ZHA or Zigbee2MQTT must release the serial connection first. The host wrapper checks the board-specific build report and application hash; the generic flasher alone does not establish MC1 board identity.

This supports ordinary updates, not every recovery scenario. A valid-looking but hung MG24 application may neither answer EZSP nor enter the bootloader, and the present 14-pin carrier connection has no host-controlled MG24 reset. A failed S3 that cannot run Ethernet/OTA also has no independent network recovery controller. J8/J9 remain emergency physical pads; access or removal of the assembly can still be required. The compact arrangement deliberately trades the former USB service corridors for area. The application protocols are retained; universal remote recovery is not promised.

## Power boundaries

Three separate Schottky branches feed the controller inputs from the isolated 5 V bus. Nano uses **VIN JP1.15**; **VBUS JP1.12 and 3V3 JP1.2 remain unconnected**. H2/XIAO regulator outputs are also separate from the peripheral 3.3 V buck. WIZ850io and external peripherals use that separate rail. These are verified net assignments, not measured backfeed results.

Nano's onboard USB diode and carrier branch diode implement the intended supply OR. Its advertised external VIN range is **6–21 V**; operation from regulated 5 V minus the branch drop is inferred from the onboard converter and USB circuit, below that published external range. Loaded start-up, radio bursts, rail droop and temperature require testing. See the [Waveshare schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf).

Preassembly programming must use each board's correct supply path. XIAO's SAMD11 probe requires USB VBUS; its header VIN does not power the intended probe regulator. A blanket VBUS blocker disables that probe. Supply diodes do not isolate signal pins. If physical rework/service is later necessary, use the module-specific [service analysis](studies/square-layout/service-review.md), not an assumed one-port-powered interconnected assembly.

## Placement and physical fit

Final anchors are H2 **(2,1.5), 0°**; Nano **(62.5,39), 180°**; XIAO **(18,57.5), 270°**; WIZ850io **(61,67.9), 180°**. Three 2.7 mm holes at **(35,6), (24,51.8), (34,72)** assume nylon M2.5 hardware of at most 5 mm body/head diameter. The independent geometric audit includes those support envelopes.

USB insertion envelopes are intentionally absent. The actual socket metal is still reserved: conservative protrusions of **2 mm for Nano, 1 mm for H2 and 3 mm for XIAO** beyond their PCB edges. No projected collision was found. Tight allowances are approximately **0.49 mm from the Nano shell to R2's courtyard**, **0.479 mm from the XIAO shell to D1's courtyard**, and **1.12 mm from H2's shell to the fitted J6 mating housing**. These are source-based engineering reservations, not tolerances measured on delivered parts. Dry-fit the actual boards and narrow connectors before soldering. Harness wires must leave vertically before bending; arbitrary large locking housings and sideways boots are not covered.

WIZ850io opens down/positive Y at **y77**, spanning **x42.79–58.89**: **2 mm beyond the carrier**. Its PCB occupies **x39.34–62.34, y49.3–74.3**. The reserved Ethernet plug/latch corridor is **x35–65, y74.3–113**. This is an engineering envelope, not a universal cable specification. The [manufacturer drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png) supports the module and jack dimensions. The enclosure must support insertion force. Before cables and clearances, the populated nominal span is already about **65.04 × 82.48 mm**, due to antenna/jack overhangs; 65 × 75 describes the carrier PCB only.

## RF and ceiling mounting

H2's antenna is beyond the top edge, nominally **x6.83–20.03, y−5.475–−0.075**. The minimum nominal 0.075 mm edge separation is small enough that board/assembly tolerances matter. [Espressif recommends](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board) antenna placement beyond the baseboard, enclosure clearance and final range testing. Its enclosure guidance recommends at least 15 mm clearance in all directions. The carrier alone does not establish compliant enclosure or harness clearance.

XIAO's ceramic body projects approximately to **x−0.0339–1.9661, y66.1996–71.3996**. It is partly above the carrier. The source is the [Seeed native board](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip). Ceramic antenna selection is PB04 low / PB05 high. The final full XIAO **x0–5, y64.5–73.5** strip excludes pours and vias; tracks are excluded except the narrow **x2.5–3.8, y72.48–73.5** PC07/RX escape. Required header pads remain allowed. Independent native inspection finds exactly one required 0.25 mm F.Cu ZB_RX segment touching this strip through the narrow escape pocket, and no vias.

The [Kinghelm KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf) describes body tolerances and one matched evaluation-board clearance pattern; it does not specify a universal carrier clearance beneath a finished XIAO. Seeed already has nearby header and ground geometry on its own board. Neither clearing only the ceramic outline nor copying the evaluation board proves the stacked assembly RF-qualified. Nano likewise uses an edge exclusion derived from manufacturer imagery, not a measured complete-carrier antenna qualification.

For ceiling mounting, assume the modules face the room. Radiation is not one-way: carrier copper, harnesses, metal lath and foil can couple to the antenna near field and alter its match/pattern. A larger ceiling standoff does not remove metal a few millimetres below an antenna on the carrier. Keep wiring and enclosure metal away from antenna ends and qualify the actual ceiling installation. No equal-range, coexistence or dB improvement is claimed.

## Retained behavior and final evidence

Local Thread Border Router/REST/dataset behavior, active BLE, Ember for ZHA/Zigbee2MQTT, Z-Wave, CC1101, LD2450 and BME680 retain their protocol boundaries. Thread preflight and persistent quarantine contain many RCP faults; a terminal failure after startup causes one **complete host restart**, briefly interrupting every service. An unrelated host panic while Thread is armed may also quarantine Thread. RTC emergency retention is not a guarantee across total power loss if NVS storage fails. Shared SPI still depends on the pinned startup order and disallows runtime CC1101 reset/configure; concurrent load timing remains unmeasured.

The promoted native board passes the independent audit and all **13 CAD artifact hashes** match. Native reports show **zero ERC/DRC violations, zero unrouted items and zero schematic-parity issues**, with **20 CAD tests** recorded. All source hashes in the author's clean-reproduction record were also independently checked. The final PCB SHA-256 is:

    cd28bc7a3875a8776e82679640d4388aaa7d5d4e21d166d6cca9cae9079c1fb1

The assembly drawing was visually inspected against the selected module orientation, central header arrangement, DNP service pads and outward RJ45. The H2 isolation drawing accurately describes the electrical R7 intervention and explicitly is not a physical part locator. Both final native PCB images were inspected with their full perimeter visible; the image hashes and recorded source-board hash match the current files. They depict the unpopulated carrier, not physical assembled hardware.

The final [firmware record](../../firmware/module-carrier/build-evidence.json) contains the complete S3 build and remapped H2 RX23/TX24 build. All **18 source hashes** in that record and **14 source hashes** in the [test record](../../firmware/module-carrier/test-results.json) were independently compared without mismatch. The firmware author records **55 host tests plus two REST contract tests** passing. This review independently reran all 14 updater tests after the final API MAC-validation change; `--mac` refers to the ESPHome device/base MAC, not the W5500 interface MAC.

The S3 OTA image is **1,731,456 bytes**, with **163,795 bytes static RAM** and **6,395,008 bytes free in each OTA slot**. Its SHA-256 is:

    8ce7ab689de3373ade9a73f256d00267962a75cdf862e3df671e501d07b231c9

The H2 application is **208,928 bytes**, SHA-256:

    db23216a075bc250bc229e90cf798cd17cadd35f9ad632dc92eda2e2979e50b9

These are build/linker measurements, not peak operating memory or successful programming results. Remaining acceptance work is physical: exact module/socket fit, R7 identification and isolation, power/strap measurements, actual remote flashes and interrupted-update recovery, concurrent protocol stress, thermal behavior, antenna/enclosure interaction, pairing and backup restoration. **Source, native CAD and host-test review found no remaining blocker to the documented prototype; they do not establish production or RF qualification.**
