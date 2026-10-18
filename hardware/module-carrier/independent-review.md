# MC1 two-sided carrier independent review

Reviewed 18 October 2026 UTC. Scope: the **51 × 75 mm two-sided carrier**, native pin mirroring and geometry, solder access, retained protocol interfaces and host-assisted updates. This is an engineering prototype. No assembled hardware, radio performance or physical programming operation was tested. This reviewer authored the earlier XIAO firmware adaptation; this review is not independent of that adaptation's implementation.

The carrier area is **21.5% smaller** than the preceding 65 × 75 mm version. **Three controllers face the room on the front**: Nano, H2 and XIAO. **Thirteen fitted items face the ceiling on the rear**: WIZ850io, seven male harness headers, three axial diodes and two resistors. The total remains **16 fitted items, 18 electronic footprint positions, 133 pads**. J8/J9 are unpopulated service pads. Factory male module pins solder directly into carrier plated holes. There are no female module sockets or underside flying wires. **H2 R7 must still be removed before assembly**, a separate small surface-mount modification to a purchased module. Program the modules before permanent soldering. USB sockets remain fitted, without guaranteed postassembly plug-in clearance.

Moving parts to the rear does not make their solder tails disappear. Native DRC correctly flags **43 rear through-hole pads inside the projected front-module courtyards**. These are retained and individually classified, not hidden or asserted physically safe. The final conductor clearance remains a measured acceptance gate.

## Electrical audit

The independent [native parser](audit_carrier.py) does not import the CAD generator or design ledger. It checks manufacturer hole coordinates, **133 pad assignments**, **31 connected groups / 101 connected endpoints**, separation of regulator outputs, the required front/rear assembly sides, all-layer plated holes, pad containment, same-side courtyard separation, fitted versus DNP state, conservative socket projections, narrow harness housings and nylon support envelopes. Its **18 geometry/net mutation checks** include swapped UARTs/flow control, split shared SPI, connected Nano VBUS, paralleled supplies, an omitted service footprint, wrong header geometry, an accidentally fitted service header a collision with a physical USB shell, incorrect native backside mirroring, lost PTH copper, a cyclic solder sequence and a rear body under an antenna. Nine additional final-evidence mutations verify that the DRC classifier rejects unrelated or extra errors, missing lists/pairs, the wrong enclosing module and stale body/pad positions. Final evidence is recorded separately in [independent-audit.json](independent-audit.json).

Native KiCad flips were tested on a separate temporary footprint: B.Cu serialization negates canonical **local Y**, while the footprint angle handles the flip axis. The audit checks that actual mirrored hole geometry against manufacturer coordinates; it does not merely permit a changed layer label. Logical pin/net membership remains unchanged.

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

## Placement, access and vertical clearance

Front anchors are H2 **(2,1.5), 0°**; Nano **(49.5,39), 180°**; XIAO **(18,57.5), 270°**. Rear WIZ850io has the native mirrored anchor **(28.84,67.9), 0°**. Rear harness columns occupy the H2 interior projection; rear passives occupy the Nano interior projection. WIZ stays clear of front-module solder rows.

The independent solder-order graph uses native bodies/courtyards and a **2 mm access halo** around solder points. It has no cycle: install and solder the rear headers/passives before the front H2/Nano cover those joints. WIZ and XIAO do not create a mutual obstruction. This is a necessary access test, not proof of every soldering-iron angle. The recommended practical sequence is rear components first, inspect/trim/clean their front-side joints, then install the front controllers and solder their pins from the rear. The earlier assembly must remain inspectable before the next step hides it.

The initial lower support overlapped the retained XIAO USB shell by 0.12 mm; that conflict was caught independently and the support was moved. The reviewed target supports are **(29.5,8), (29.5,44), (24.2,57.5)**, with 2.7 mm holes and nylon M2.5 hardware of at most 5 mm body/head diameter. Support checks apply on both sides. Do not substitute wider metal screw heads without another fit/RF check.

The vertical clearance rule is explicit:

    module-to-carrier gap − underside-component height − opposing tail/solder height ≥ 1 mm

Every term refers to the worst overlapping location on the actual purchased parts, including solder fillets. A **3 mm gap with 1 mm underside parts and 1 mm trimmed tails** is only a conditional example. Factory header height, tail length and underside components have not been measured. A nominal 2.54 mm plastic header does not establish a safe gap. Do not trim a required solder joint flush merely to force an assumed clearance. If the measured inequality fails, revise the arrangement before assembly. Do not float unsupported modules on partially engaged pins; any different supported spacing requires another mechanical and pin-engagement check.

Ceiling standoffs also must clear the rear WIZ body, mated headers and wire bends. No universal ceiling offset is established by the PCB outline. The raised assembly still requires measured clearance; an insulating spacer or solder mask is not a substitute for a known conductor gap.

USB insertion envelopes remain intentionally absent. Physical socket reservations remain **2 mm for Nano, 1 mm for H2 and 3 mm for XIAO** beyond their PCB edges. These source-based engineering allowances must be checked against actual sockets and narrow harness housings. Harness wires must depart toward the ceiling before bending, and stay away from antenna ends.

Rear WIZ850io opens down/positive Y at **y77**, spanning **x30.95–47.05**: **2 mm beyond the carrier**. Its PCB occupies **x27.5–50.5, y49.3–74.3**. The [manufacturer drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png) supports the module and jack dimensions. The enclosure must allow its plug/latch and withstand insertion force. Before cables or enclosure clearance, the populated nominal span is about **51.04 × 82.48 mm** due to antenna/jack overhangs; 51 × 75 describes the carrier PCB only.

## RF and ceiling mounting

H2's antenna is beyond the top edge, nominally **x6.83–20.03, y−5.475–−0.075**. The minimum nominal 0.075 mm edge separation is small enough that board/assembly tolerances matter. [Espressif recommends](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board) antenna placement beyond the baseboard, enclosure clearance and final range testing. Its enclosure guidance recommends at least 15 mm clearance in all directions. The carrier alone does not establish compliant enclosure or harness clearance.

XIAO's ceramic body projects approximately to **x−0.0339–1.9661, y66.1996–71.3996**. It is partly above the carrier. The source is the [Seeed native board](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip). Ceramic antenna selection is PB04 low / PB05 high. The final full XIAO **x0–5, y64.5–73.5** strip excludes pours and vias; tracks are excluded except the narrow **x2.5–3.8, y72.48–73.5** PC07/RX escape. Required header pads remain allowed. Independent native inspection finds only the required 0.25 mm F.Cu ZB_RX escape near this strip, with no other routed net or via in the reservation.

The [Kinghelm KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf) describes body tolerances and one matched evaluation-board clearance pattern; it does not specify a universal carrier clearance beneath a finished XIAO. Seeed already has nearby header and ground geometry on its own board. Neither clearing only the ceramic outline nor copying the evaluation board proves the stacked assembly RF-qualified. Nano likewise uses an edge exclusion derived from manufacturer imagery, not a measured complete-carrier antenna qualification.

For ceiling mounting, assume the modules face the room. Radiation is not one-way: carrier copper, harnesses, metal lath and foil can couple to the antenna near field and alter its match/pattern. A larger ceiling standoff does not remove metal a few millimetres below an antenna on the carrier. Keep wiring and enclosure metal away from antenna ends and qualify the actual ceiling installation. No equal-range, coexistence or dB improvement is claimed.

## Retained behavior and final evidence

Local Thread Border Router/REST/dataset behavior, active BLE, Ember for ZHA/Zigbee2MQTT, Z-Wave, CC1101, LD2450 and BME680 retain their protocol boundaries. Thread preflight and persistent quarantine contain many RCP faults; a terminal failure after startup causes one **complete host restart**, briefly interrupting every service. An unrelated host panic while Thread is armed may also quarantine Thread. RTC emergency retention is not a guarantee across total power loss if NVS storage fails. Shared SPI still depends on the pinned startup order and disallows runtime CC1101 reset/configure; concurrent load timing remains unmeasured.

The final native [audit](independent-audit.json) passes **133 pad checks, 31 net groups and 27 negative/mutation tests**. All **17 CAD manifest hashes** match. The hardware suite records **22 tests**. Raw KiCad DRC retains **43 errors**, each exactly matched by native UUID and current geometry to the planned 33 header-pad/U2 or 10 passive-pad/U1 projection. There are **zero unclassified findings, zero unrouted items, zero schematic-parity issues and zero ERC errors**. No native error was suppressed. Missing report lists, unrelated errors, stale positions and changed pairings fail closed.

The author's clean reconstruction reports the same conditional result; all its recorded source hashes were checked. The final PCB SHA-256 is:

    87e2dbdd2d7be9daeb703dff1356812abf905cf625409c61e812d707ffb88e39

The independent parser SHA-256 is recorded in the audit JSON. Front/rear assembly diagrams and final native PCB images were visually inspected. They retain the whole board perimeter, show the rear view mirrored correctly, and agree on the controller/harness/WIZ sides. Both image hashes and their source-board provenance match the final files. These are drawings of the carrier, not photographs of fabricated hardware.

Every logical pin/net map matches the saved 65 × 75 mm single-sided predecessor's source mapping; no firmware or protocol behavior is changed by this layout. The existing firmware evidence remains applicable at source level: all 18 build-source and 14 test-source hashes match, with 55 host tests and 2 REST contract tests recorded. This mechanical revision does not create new hardware-runtime proof.

**Vertical clearance remains unqualified and fabrication release is false.** Before irreversible assembly, measure the actual module gaps, underside parts, trimmed joints, ceiling standoffs and cable bends. Accept every overlapping location only if the stated clearance inequality passes with sound solder joints. Then qualify power/strap behavior, actual remote updates/recovery, simultaneous protocol load, temperature and RF performance on the complete assembly.
