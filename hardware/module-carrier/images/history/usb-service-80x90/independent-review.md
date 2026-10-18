# MC1 Nano independent integration review

Reviewed 17 October 2026, with final evidence dated 18 October UTC. Scope: the **80 × 90 mm Nano carrier**, native KiCad files, selected firmware interfaces, recovery behavior and current drawings. The former 100 × 90 mm review is retained in history. No assembled hardware was tested. This reviewer authored the earlier XIAO firmware adaptation; this is therefore not an independent audit of that adaptation's implementation.

The arrangement retains the seven application groups while reducing carrier area by **20%** relative to 100 × 90 mm. It uses four finished modules, nine harness/service headers, three axial diodes and two resistors. All mounted parts remain on top; factory male module pins are soldered underneath. There are no female module sockets, carrier surface-mount assembly steps or underside jumper wires. PCB area does not establish delivered cost, enclosure size or lower power consumption.

## Independent electrical checks

The read-only [audit script](../../../audit_carrier.py) parses the native PCB without importing the generator or design ledger. Manufacturer header geometry and the selected firmware contract define its expected endpoints. The [recorded result](../../../independent-audit.json) passes **133 pad assignments**, **31 separate connected groups / 101 connected endpoints**, module hole positions, top-side placement, pad containment, native courtyard separation and evidence hashes. Eleven intentional corruptions are detected, including crossed UART/flow-control signals, a split shared SPI bus, connected Nano VBUS, paralleled regulators, a shorted supply diode, a missing recovery header and incorrect hole geometry.

- Nano GPIO43 TX → H2 GPIO4 RX; GPIO44 RX ← H2 GPIO5 TX. GPIO47 reaches H2 EN, and GPIO48 reaches H2 GPIO9/BOOT. Nano ROM output is followed by a physical H2 reset before the Spinel probe. H2's application UART is separate from its onboard USB-UART bridge.
- Nano GPIO17 TX → XIAO PC07 RX, and GPIO18 RX ← PC06 TX. GPIO7 RTS → PC04 CTS; GPIO21 CTS ← PC05 RTS. This is the selected **115200 8N1 RTS/CTS** Ember/EZSP transport. The former S3 GPIO16 RTS assignment must not be reused.
- Shared SPI GPIO13/11/12 reaches WIZ850io and the CC1101 harness, with separate chip selects. Three native UARTs serve Thread, Zigbee and LD2450. WK2132 remains the external Z-Wave UART bridge.
- XIAO PC00 reaches local J8; Nano GPIO0 reaches new local J9 through **JP1.13**. Both pair the signal with ground and are normally open. Native USB and reset access remain available. Nano preserves a manual native-USB recovery route; it does not contain the former S3 board's separate USB-UART bridge.

All **86 module header pads** use 1.80 mm copper / 1.10 mm drills, a nominal 0.35 mm annular ring. This is 14 fewer module solder joints than the previous host. Actual pin tolerances, solder wetting, bridges and continuity still need inspection.

## Power and service boundaries

The three controller inputs have separate Schottky branches from the isolated 5 V bus. Nano receives its branch at **VIN JP1.15**; **VBUS JP1.12 and 3V3 JP1.2 remain unconnected** to carrier rails. H2 and XIAO regulator outputs likewise remain separate from the peripheral 3.3 V supply. WIZ850io and the external peripherals use the separate 3.3 V buck. These are verified nets, not measured isolation results.

Nano's onboard USB diode and carrier input diode provide the intended supply OR. Its vendor specifies external VIN at **6–21 V**. Operation from regulated 5 V minus the branch drop is inferred from the onboard converter and USB circuit, below that published external range. Loaded cold-start, brownout, radio-burst and USB-insertion tests are required. See the [Waveshare schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf).

USB service is module-specific. Keep the interconnected carrier normally powered and check backfeed, rail voltages and enumeration. Supply diodes do not isolate signal pins. XIAO's SAMD11 programming probe requires **USB VBUS**; header VIN does not power its intended probe supply. A blanket VBUS blocker prevents that service path. The [official-netlist service review](../../../studies/square-layout/service-review.md) records the evidence.

Before programming H2, activate **Pause Thread for H2 Service**, wait for the restart, and confirm **Thread State = maintenance** and **Thread Guard Durable = on** after reconnection. Automatic RCP reset callbacks are absent in that state. Elective service pause refuses restart if its write, commit or readback fails; RTC-only emergency retention is not accepted as a maintenance interlock. Resume with explicit retry after programming.

## Placement, plugs and assembly

Final module origins/rotations are Nano **(39,2), 270°**; H2 **(78.5,28), 270°**; XIAO **(18,70), 270°**; WIZ850io **(76,82.9), 180°**. KiCad may serialize 270° as −90°. Harnesses occupy two horizontal bands between modules. Three 2.7 mm mounting holes at **(4,22.1), (50,21.4), (77,60.9)** assume nylon M2.5 hardware with a maximum 5 mm body/head diameter.

Independent comparison of native courtyards with declared mating housings, USB envelopes and supports found no projected overlap. Tight allowances are:

- XIAO courtyard to D1: **0.229 mm**; adjacent diode courtyards: **0.28 mm**.
- WIZ courtyard to the third support: **0.40 mm**.
- Adjacent header housing bands: **0.50 mm**.
- H2 USB envelope to J3/J5: **0.55 mm**.
- First support to Nano courtyard: **0.59 mm**; to H2 USB envelope: **0.60 mm**.

These assume **5.5 mm-wide narrow mating housings**, **30 mm axial USB allowance**, and wires departing upward before bending above the modules. Arbitrary shells, low right-angle plugs, large screw heads and wires crossing antennas are not covered. Both H2 USB sockets remain fitted. XIAO's USB envelope ends at x50.921; WIZ PCB starts at x54.34, a **3.419 mm** gap. Dry-fit actual plugs, underside module parts and supports before permanent soldering.

WIZ850io opens **down / positive Y** at **y92**, spanning **x57.79–73.89**: 2 mm beyond the carrier. Its PCB occupies **x54.34–77.34, y64.3–89.3**. Reserved plug/latch corridor: **x50–80, y89.3–128**. This is an engineering allowance, not a universal boot specification. The enclosure/supports must withstand insertion loads. Orientation matches the [WIZnet dimension drawing](https://docs.wiznet.io/img/products/wiz850io/wiz850io_dimension.png).

## Antennas and ceiling mounting

Final review moved H2 4.5 mm right without enlarging the carrier. Its nominal antenna projection is **x80.075–85.475, y32.83–46.03**, outside the 80 mm carrier edge. Outermost carrier pad copper ends at x79.4. This improves on the intermediate layout with FR4 beneath part of the antenna. Minimum nominal overhang is only 0.075 mm; manufacturing and positioning tolerances still matter. WIZ PCB is separated from the antenna projection by 18.27 mm vertically.

[Espressif recommends](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board) placing the antenna outside the baseboard, providing enclosure clearance and testing final range. Its enclosure guidance recommends at least 15 mm clearance in all directions. This drawing does not prove complete enclosure/harness compliance; nearby header wiring must bend away from the antenna. An edge position alone is not an RF measurement.

XIAO's ceramic body projects approximately to **x−0.0339–1.9661, y78.6996–83.8996**. Its entire antenna is not outside the carrier. Source: [Seeed native board](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip). Firmware selects ceramic with PB04 low / PB05 high.

The final board preserves the entire **x0–5, y77–86** XIAO strip against copper pours and vias. Tracks are excluded except for a **1.3 × 1.02 mm** escape pocket at **x2.5–3.8, y84.98–86**. Independent inspection finds only the required **ZB_RX** path there: two connected 0.25 mm B.Cu segments and no vias. The blanket reduction to y84.1 was rejected. Required header pads remain allowed; this is not an absolutely copper-free region.

The [Kinghelm KH5220-A36 datasheet](https://www.kinghelm.com.cn/upload/file/20230213/KH5220-A36.pdf), pages 4–5, specifies body tolerances and clearance for a particular matched evaluation board. It does not specify a carrier clearance beneath complete XIAO. Seeed's board already has its own nearby headers and ground geometry. Neither a ceramic-outline allowance nor the evaluation-board drawing proves this carrier RF-qualified. The final pocket minimizes added carrier metal while retaining routing; comparative assembled Zigbee tests remain necessary.

For ceiling mounting, assume modules face into the room. That does not make the antennas one-way beams or remove near-field coupling to the carrier, wires or metal lath. Keep metal, foil insulation and harnesses away; assess the actual ceiling/enclosure. Increasing ceiling standoff does not remove copper a few millimetres from an antenna on the carrier itself. No equal-range, coexistence or specific dB improvement is claimed.

## Firmware containment and compatibility

Source review checked bounded read-only Spinel preflight, API/capability checks, physical reset registration, persistent guard state, terminal callbacks and service mode. Missing/incompatible H2 can be quarantined before SDK startup. A terminal fault after startup records its cause and permits **one complete S3 restart**, after which Thread remains disabled until explicit retry. Every host service is interrupted by that restart; this is not seamless process isolation.

The durable armed marker also covers SDK panic/watchdog paths bypassing callbacks. An unrelated host panic while Thread is armed can conservatively quarantine Thread. A normal new boot clears an older armed marker before waiting for Ethernet, preventing the old session from arming the new waiting phase. Dataset storage is separate. Ordinary lack of a dataset or Ethernet is not classified as a terminal RCP fault.

NVS writes are committed and read back. Checksummed RTC retention is a secondary guard for emergency faults across warm resets; it is not promised after complete power loss when NVS cannot write. The 20-second stack-start deadline assumes a schedulable main task. These limits are recorded in the [recovery instructions](../../../../../firmware/module-carrier/thread-recovery.md).

Shared SPI retains its pinned startup-order restriction: CC1101's initial manual reset occurs before Ethernet starts. Ordinary transactions use the bus lock; runtime CC1101 reset/reconfiguration is rejected. MISO behavior, interrupt latency and simultaneous heavy traffic need hardware testing. WK2132 forwarding handles bounded FIFO transfers, wire-idle flushing and ambiguous-write faults; source tests do not establish actual I2C timing.

Ember/EZSP preserves the ZHA/Zigbee2MQTT path, and the local border router retains Home Assistant's REST/dataset contract. Compilation does not establish pairing, migration, backup restoration, concurrent BLE sessions or long-term reliability.

## Final evidence

The independent audit verified all **12 artifact hashes** in the CAD verification manifest. Native reports show **zero ERC violations, zero DRC violations, zero unconnected items and zero schematic-parity issues**; **18 CAD tests** are recorded. The hardware author reproduced the clean route/checks from committed generator, SES and manual-route sources in [reproduction evidence](../../../cad/checks/reproduction.json). Saved project rules retain Default 0.25 mm / Power 0.8 mm tracks, 0.2 mm clearance, 0.8/0.4 mm vias and six intended power-net assignments.

Final reviewed PCB SHA-256:

    057a7b642679e39965cc45b57765e67d7230496f94db0e204b7836f4750fdb4a

The [firmware evidence](../../../../../firmware/module-carrier/build-evidence.json) records successful S3/H2 builds using ESPHome 2026.9.1 / ESP-IDF 5.5.5. Twelve current firmware source/hash entries were independently compared with no mismatch. The firmware author reports **41 host tests** (27 guard/probe plus 14 transport) and two REST-client tests. S3 OTA is 1,728,512 bytes, SHA-256:

    7a43a92ad66e4c930cd83ab347a300264965e8668661a6345038464eeb9f7a87

The final assembly drawing was visually inspected: orientation, factory header numbering, service regions and outward RJ45 match native geometry. Both final native renders were also inspected after reducing zoom to retain the full board perimeter; their provenance/image hashes match the reviewed board and files. These front/back images represent the carrier PCB, not populated hardware or a manufactured sample. Use dimensioned CAD and the connector ledger for construction; generated concept photographs remain history.

Remaining acceptance work is physical: module/plug fit, loaded Nano power, USB/backfeed behavior, recovery fault injection, shared-bus stress, thermal behavior, enclosure/ceiling effects, simultaneous radio performance and network backup/migration. **MC1 remains an engineering prototype, not a production-qualified design.**
