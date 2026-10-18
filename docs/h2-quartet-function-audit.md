# Single-carrier and H2 Quartet function audit

**Review date: 2026-10-17. Baseline: `fe2b5879663f98789868961fc7e64eb0df61b8dd`.**

A single carrier is a reasonable replacement for maintaining two alternative PCB implementations. That mechanical consolidation does not require replacing the S3, Ember coordinator or SC16 with H2 processors. Conversely, four identical H2 boards simplify the stock of spare processors but introduce new firmware and presently change several supported interfaces. **An all-H2 carrier is not yet a demonstrated replacement with unchanged functions and unchanged complexity.**

The mounting requirement is independent of this software decision: factory-installed male pins must enter plated carrier holes and be soldered underneath. There are no female sockets and no hand-soldered castellated module edges. A factory-assembled module can contain its own fine-pitch parts; those parts must not become the builder's assembly work. Direct soldering also means replacing a board requires desoldering.

## Evidence levels

Neither C0+M0 nor I0 has demonstrated complete operation on physical hardware. Their stronger evidence is a complete compiled software target, compiled radio firmware and offline contract tests. This audit does not promote that baseline to a tested product.

- **Existing complete target:** [S3 firmware](../firmware/low-power/README.md) includes Ethernet, encrypted ESPHome API, OTA, BLE proxy, RF, radar, BME680, Z-Wave proxy, Zigbee serial forwarding and local Thread BR. S3 application 1,716,944 bytes; static RAM report 161,127/341,760 bytes. H2 RCP and [MG24 Ember firmware](../firmware/low-power/mg24/README.md) also compiled separately.
- **H2 component target:** [the existing Quartet probe](../firmware/h2-quartet/README.md) compiles W5500 and an active BLE proxy with three connection slots. Application 1,061,120 bytes; static RAM report 106,302/258,000 bytes. It omits all the other services, encryption and the OTA service. These numbers are not free runtime heap or a full-hub memory budget.
- **Current baseline tests:** 77 existing repository tests passed with ASan/UBSan enabled. These exercise RF contracts, receiver/transmitter lifecycle, SC16 register behavior, Zigbee session/backpressure behavior, offline migration and packaging. They do not test the proposed H2 SPI transport, H2 radio timing or real networks.
- **Bounded new BR probe:** an independent minimal H2 ESP-IDF 5.5.5 application enabled native OpenThread FTD, platform netif and Border Router. Configuration succeeded. The build failed before compilation because the target-specific H2 BR archive is absent. [Reproducible probe and result](../firmware/h2-quartet/function-audit/README.md).

## Function-by-function comparison

| Contract | C0+M0 / I0 baseline | All-H2 Quartet evidence and required work |
| --- | --- | --- |
| One external Ethernet link, no internal switch | One W5500; full S3 build | One W5500 retained; H2 Ethernet/BLE component build passed. Carrier signal integrity and complete traffic remain untested. |
| Active BLE proxy | ESPHome, three active connection slots | The same count compiles on H2. Concurrent Thread/RF/peripheral loads, encryption and OTA remain to be integrated. |
| Local Thread Border Router | Compiled S3 host + H2 RCP; offline REST-client tests | Not compiled as a complete H2 BR. Stock IDF lacks the H2 BR library. A custom port is real additional work. Moving OTBR to HA would change this contract. |
| Independent Thread, Zigbee and BLE radios | S3 BLE, H2 Thread, MG24 Zigbee | Three independent H2 radios preserve this architectural property. Antenna coupling and simultaneous reception are not established by component count. |
| Stock ZHA / Ember interface | MG24 Ember 8.2.3 / EZSP 18; current ZHA dependency compatibility reviewed | H2 ZBOSS is a different host protocol. The selected custom ZHA integration currently reports incompatibility with HA 2026.7+. It is not a drop-in replacement. |
| Zigbee backup and migration | Existing Ember/ZHA host path retained; physical recovery still untested | Selected ZBOSS firmware exposes a placeholder network key to ZHA. Ordinary ZHA backups are not restorable through that path. Its separate NVRAM snapshot/fork procedure is a changed operational contract. |
| Zigbee UART backpressure | 115200 8N1 with RTS/CTS; eight session tests | Candidate Zero-M map uses two wires without RTS/CTS. Protocol acknowledgements/buffers do not make this the same hardware-flow-control contract. Overflow handling and recovery need their own proof. |
| RF Airbridge behavior | CC1101, RCSwitch/Dooya TX, RM433 events, exact MQTT/native API semantics, lifecycle tests | CC1101 remains necessary. H2 has suitable peripheral classes, but the complete RF package has not been built and exercised on the proposed H2 map and shared SPI bus. |
| Radar data and controls | LD2450 UART256000, three targets, counts, presence/motion/stillness, timeout, multi-target and radar-Bluetooth controls, firmware version | Peripheral H2 needs both data forwarding and command/response forwarding. Forwarding only presence or coordinates loses existing functions. |
| Environmental data | BME680 temperature, pressure, humidity, raw gas resistance | Peripheral H2 must preserve readings, configuration and availability. Raw gas resistance must not be relabelled as CO2 or calibrated IAQ. |
| Z-Wave proxy | ZAC93 through tested SC16 channel A, 115200 8N1; normal ESPHome Z-Wave proxy | ZAC93 remains necessary. New H2 SPI/UART transport must preserve the byte stream, ownership, flow control, loss reporting and reset behavior. No Quartet transport firmware exists yet. |
| Firmware/service recovery | S3 can drive H2 EN/BOOT; separate radio service interfaces | Zero-M's normal header does not expose EN. Local buttons/USB remain, but remote EN control is lost in the current map. The old control connection itself also did not prove automatic recovery from every RCP failure. |
| Power-saving Ethernet policy | Driver enforces/verifies 10M half-duplex; failure stops Ethernet | Minimal H2 probe uses ordinary W5500 settings. Port the policy and verify negotiation before claiming equal power behavior. |
| Image update and authentication | S3 encrypted API and OTA configured; radios serviced separately | Minimal H2 probe has neither API encryption nor OTA service. Four controllers require an explicit version and recovery policy. Generating an `ota.bin` file does not enable OTA. |

Source contracts are in [the complete YAML](../firmware/low-power/hub.yaml), [core configuration](../firmware/low-power/proof.yaml), [radar package](../firmware/packages/ld2450.yaml), [BME680 package](../firmware/packages/bme680.yaml), [RF package](../firmware/packages/rf-airbridge.yaml) and [test descriptions](../tests/README.md).

## What is actually preserved, what is pending, and what changes

**Preserved by retaining the architecture:** one physical LAN connection, separate radio front ends and the existing CC1101/ZAC93/LD2450/BME680 modules. This is a design statement, not a hardware acceptance certificate. The only new H2 service combination with a successful build is W5500 plus BLE proxy.

**Pending:** full-hub compilation, local H2 BR, complete radar/control and Z-Wave forwarding, RF behavior on H2, shared-SPI timing, authenticated update/recovery, thermal behavior, power and concurrent radio performance. None can be marked equivalent merely because the new processor has the relevant peripheral.

**Known changes in the current candidate:** Ember to ZBOSS; stock ZHA to a currently incompatible custom integration or an intentional Zigbee2MQTT migration; different backup/recovery procedure; loss of the original RTS/CTS and remote H2 EN-control connections; a new interprocessor protocol replacing the SC16 driver. These are real differences today, even if further development can address them.

The ZBOSS facts come from the [firmware maintainer's ZHA integration](https://github.com/tostmann/zha-zboss-esp) and [Zigbee2MQTT's adapter documentation](https://www.zigbee2mqtt.io/guide/adapters/zboss.html). The former explicitly describes the placeholder key and separate NVRAM recovery; the latter labels ZBOSS experimental and lists missing backup/restore, install-code and Inter-PAN features. These limitations should not be generalized to the H2 silicon itself.

## Lowest-change single-carrier recommendation

If unchanged host interfaces and minimum new software are required, consolidate the mechanical design around **a finished S3 board with suitable PSRAM, a finished H2 RCP board, a finished Ember-compatible Zigbee assembly, a finished SC16IS752 assembly, W5500 and assembled power modules**. Solder their factory male headers directly through one carrier. Keep CC1101, ZAC93, radar and the external BME680 pod.

This is an architectural recommendation, not a qualified shopping list. The exact finished S3, Ember and SC16 modules must satisfy these constraints before their footprints are released:

1. The S3 exposes the GPIO budget, native USB and suitable PSRAM. The present image targets N16R8. Factory USB-UART/LED circuits must not fight the selected UART or control pins. A board with fewer usable pins can invalidate the no-extra-circuit goal.
2. The Ember assembly runs firmware whose NCP protocol, baud rate, RTS/CTS, reset/boot and host support match the preserved contract. An arbitrary MG24 module does not inherit the compiled MGM240PA22VNA3 image's pin mapping or RF configuration. A ready assembly can remove hand soldering without requiring a new Zigbee host protocol.
3. The SC16 assembly exposes channel A, IRQ and SPI mode selection, and supplies valid reset/bias behavior. Current YAML accepts **1.8432 or 3.6864 MHz** oscillators. A common **14.7456 MHz** board needs a small schema extension and a divisor-8 regression test; the existing register core already computes integer divisors. It is not currently a zero-edit drop-in. This bounded adaptation is considerably smaller than designing the Quartet SPI protocol.
4. GPIO remapping still requires configuration and contract validation: the current OTBR component hardcodes native UART ownership and checks LD2450 pins39/40. Preserve the three native UART allocations rather than adding an accidental fourth user.

No new Linux host, internal Ethernet switch, BLE RPC protocol or Zigbee2MQTT migration is needed for this route. It can reduce the builder's loose-part assembly while retaining the current software architecture. Physical validation remains necessary for any new carrier.

If identical H2 boards remain the higher priority, retain the Quartet as the selected **development** architecture, with the known interface changes explicit. A single carrier does not make its firmware mature, and a new rendered board image must not imply successful operation.

## Local H2 BR development boundary

The public [IDF build rule](https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/CMakeLists.txt) links a target-specific BR archive; [the pinned archive tree](https://github.com/espressif/esp-thread-lib/tree/33209823e559560f54dcd41cbf3dbdd27f46d569) has no H2 entry. The new probe reproduced this exact failure. Do not substitute a C6 binary under the H2 name and call that a supported port.

The missing work is not the 802.15.4 radio driver alone. Border routing requires IPv6 route/neighbor handling, multicast, MeshCoP discovery, and SRP/service discovery forwarding. Depending on the intended feature set, upstream DNS and NAT64 also need implementation.

[Zephyr's open BR implementation](https://github.com/zephyrproject-rtos/zephyr/blob/main/subsys/net/l2/openthread/openthread_border_router.c), its [sample](https://github.com/zephyrproject-rtos/zephyr/tree/main/samples/net/openthread/border_router), [H2 target](https://docs.zephyrproject.org/latest/boards/espressif/esp32h2_devkitm/doc/index.html), and [W5500 binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/ethernet/wiznet,w5500.html) form a plausible development starting point. Its tested ESP BR configuration targets S3 and uses PSRAM; no H2 full-BR build was established in this audit. Porting to Zephyr also does not automatically preserve ESPHome's BLE/API services.

For the protocol-reuse Quartet layout, BLE and the Thread host stack both consume the main H2's memory even though Thread RF runs on another H2. For the distributed layout, native Thread stays on the gateway while the other H2 holds the complete BLE stack; a framed stream/socket transport must carry the BLE proxy API. Raw HCI instead puts the BLE host back on the gateway and does not provide the same memory separation.

## Completion gates for an equivalence claim

Require the complete build and measured runtime memory first, then independent reset/reconnect tests, unchanged public API/entity behavior, a recovered Zigbee network on an erased spare, Thread pairing/discovery/routing/reboot persistence, RF receive/transmit/receive under concurrent traffic, all radar controls, and error-free Z-Wave serial behavior. Keep per-function results separate from carrier DRC/fit checks and board renderings. A photograph or successful PCB manufacture cannot close a firmware gate.
