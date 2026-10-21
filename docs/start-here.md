# Start here: build the MC2-D / FH1 hub

Use this route for the **MC2-D carrier and FH1 full-hub enclosure**. It takes
you from loose parts to a tested Home Assistant node. The hardware is an
engineering prototype: software and CAD checks have passed, but the physical
assembly, thermal behaviour and house coverage still need measurement.

For a readable local guide, run `python3 tools/preview.py` from the repository
root and open the printed URL. It serves documentation; it does not flash boards
or connect to Home Assistant. Stop it with **Ctrl+C** when finished.

## 1. Identify the parts before ordering or soldering

Start with the [shopping list](mc2-shopping.md), [carrier BOM](../hardware/external-antenna/cad/BOM.csv)
and [full-case inventory](../mechanical/full-hub/components.json). Those cover
different parts of the same build; the carrier BOM alone is not a complete hub.

Check the labels on the four carrier modules:

- **U1: ESP32-DevKitC-VIE / WROVER-IE**, classic ESP32 with two 19-pin rows,
  external antenna, 8 MB flash and 8 MB physical PSRAM. Already ordered by the owner.
- **U2: Seeed XIAO ESP32C6 (Pre-Soldered), 102010636**, the 4 MB board with
  factory 2×7 male headers. Use MC2-D RCP firmware with GPIO3/14 external
  antenna control. Its underside EN/BOOT pads need two recovery leads to J10.
- **U3: Seeed XIAO MG24**, pre-soldered SKU 102010690, for external-antenna Zigbee.
- **U4: WIZ850io**, the data-only SPI Ethernet module.

The off-carrier parts include the isolated 5 V PoE splitter, **RECOM R-78K3.3-1.0
3.3 V buck with its 27 µF input capacitor and perfboard mount**,
DFR0627 UART bridge, regional **Zooz ZAC93**, CC1101 and its 433.92 MHz antenna,
LD2450 and BME680. The ZAC93 is already received for this project; do not buy a
second one by default. Each of the three 2.4 GHz radios needs its own specified
antenna and pigtail. Check actual dimensions, connectors and quantities against
the [assembly inventory](../mechanical/full-hub/components.json).

**Ready to continue:** the received parts match the active revision, and every
module, cable and antenna has an identified place in the inventory. Keep MC1,
MC2-A/S3 and Pi-era instructions in the [history section](design-history.md).

## 2. Program the three controllers while they are loose

Follow the [MC2-D firmware guide](../firmware/external-antenna/README.md) for
tool versions, commands and board selection. Attach the appropriate antenna
before a radio runs. Use USB power only for each loose board.

1. Prepare a **private deployment directory** and replace its generated API,
   OTA and MQTT credentials, broker and RF topics with your intended values.
   The validation build has disposable credentials and `build-only/rf/*`
   topics; it is not a deployable household configuration.
2. Give **U1/VIE a full initial USB-UART flash**, including its MC2-D partition
   table. The node name is `mc2-classic-hub`. An S3 or MC1 image, and an app-only
   OTA over an old partition layout, are not valid initial installations.
3. Build and flash the **XIAO ESP32C6 RCP** with the matching pinned ESP-IDF.
   Use the factory BOOT/RESET buttons for loose-board USB download. The board
   already includes the GPIO8 pull-up. Verify the MC2-D XIAO identity and
   external-antenna selection; TinyC6 binaries are incompatible.
4. Follow the [MC2-D XIAO MG24 programming guide](mc2-zigbee.md), which selects
   **`--antenna external`**, and program its external initial HEX through the
   XIAO's onboard CMSIS-DAP probe. Output filenames retain `mc1` because the
   build recipe is shared; the guide gives the current MC2-D host connections.
5. Leave the **ZAC93 on its Zooz firmware**. It is not an ESPHome target.

**Ready to continue:** programming and verification succeed for all three
selected boards; keep the exact private configuration, image hashes and build
reports. Loose-module programming does not yet verify Ethernet or the radios
working together. Unplug USB before assembling the PoE-powered hub.

## 3. Print small parts, dry-fit, then assemble the carrier

Use the [FH1 print instructions](../mechanical/full-hub/README.md) and
[exploded layout](../mechanical/full-hub/index.html). Print the **fit coupon and
ZAC93 tray first**, then check the real board and its underside mating socket.
The largest part is 215 × 215 mm; the identified TRONXY XY-3 has a nominal
310 × 310 mm bed. Check the slicer's usable area and brim before printing.

Dry-fit every received component, mated plug, solder tail and cable route.
Follow the [MC2-D assembly order](external-antennas.md#pin-connections-and-initial-programming):
all modules face the same side, low axial parts and carrier headers go first.
The C6/MG24 modules use factory headers. Fit and inspect C6 underside EN/BOOT
leads above the carrier, accessible through the service window with the carrier removed from the case; module tails are soldered from the back. The historical MC1 rear-first assembly is a
different carrier. Install each off-board module's restraint, the radar holder
and the ventilated BME680 pod; do not rely on cable friction to hold boards.

**Ready to continue:** no board or plug is forced into position, miniature coax
plugs have slack, the ZAC93 antenna area is clear, the radar faces its window,
and the lid closes without compressing a wire. A rendered fit is not this test.

## 4. Wire and test the power before connecting Home Assistant

Keep the [full wiring image](../hardware/external-antenna/full-hub-wiring.svg)
beside the [pin-by-pin assembly instructions](full-hub-assembly.md). Read
actual pad numbers and module labels; drawings and cable colours do not define
the connector's mating-side orientation.

- The power path is **existing battery-fed PoE switch → isolated 5 V splitter →
  fuse/J1 → buck/J2 and controller rails**. The splitter's data-only RJ45 plugs
  into WIZ850io. Raw PoE does not connect to the carrier.
- The RECOM replaces the earlier Pololu at the same J2 interface. Use the new
  PWR1 power tray and [power wiring](full-hub-assembly.md#power-and-ethernet),
  including both ground returns and correct capacitor polarity. Its input must
  remain at least 4.5 V under load; take 5 V before the controller isolation diodes.
- With power disconnected, continuity-check J1–J7 and J10 (TP8/EN and TP2/BOOT)
  and look for shorts between
  5 V, 3.3 V and ground. Preserve the specified boot pull-ups/pull-downs and
  keep controller-local 3.3 V outputs separate from the peripheral buck rail.
- Meter the disconnected splitter and buck first. Then connect the electronics
  and check the rails again under load, including at ZAC93. Disconnect power
  before changing any wiring.
- **ZAC93 uses a remapped cable:** J4.1→pin 1, J4.2→pin 6, J4.3→pin 9,
  J4.4→pin 8/RX, J4.5→pin 10/TX. It is not a straight-through 2×5 cable.
  Its DFR0627 bridge is on J3; set **IA1=1, IA0=1** and use UART1 at 115200 8N1.

**Ready to continue:** measured rails and polarity agree with the component
requirements, no component overheats, Ethernet links, and the router gives the
hub an address. Record that address; use it if `.local` names do not resolve.

## 5. Bring up one service at a time

Use **Settings → Devices & services → Add integration** in Home Assistant.
Keep the lid open for the first checks. Replace `HUB_IP` below with the measured
hub address; the placeholder is not a real hostname.

1. **ESPHome:** add `mc2-classic-hub` (or `HUB_IP`) with the private encrypted
   API key. It uses **TCP 6053**. Confirm `Hub Uptime` advances and inspect the
   [health entities](../firmware/external-antenna/health.yaml). Read running logs
   through the encrypted API; the USB-UART application console is disabled.
   Verify a real LD2450 movement event and fresh BME680 readings (default update
   interval 60 s). Check a compatible Bluetooth sensor through its HA integration;
   add an active-connection test if your devices use GATT.
2. **Zigbee:** give the coordinator exactly one owner. For ZHA choose the
   Silicon Labs EZSP/Ember radio with **`socket://HUB_IP:6638`** and 115200 baud.
   For Zigbee2MQTT instead use **`tcp://HUB_IP:6638`**, `adapter: ember` and
   115200 baud. The firmware supplies physical RTS/CTS. Confirm the NCP is
   identified and a spare test device reports and responds.
3. **Thread:** add **OpenThread Border Router** at **`http://HUB_IP:8081`**.
   OTBR runs on this hub; it does not require another Linux border router.
   `ready_uncommissioned_or_disabled` can be normal before a network is set up;
   after joining/creating the intended network, verify Thread state and an
   actual device. Use the [HA Thread procedure](https://www.home-assistant.io/integrations/thread/)
   to check the chosen dataset and phone credentials. A matching network name
   alone does not mean matching credentials.
4. **Matter-over-Thread:** use the HA Matter integration/server and Companion
   app with the device's setup code. The hub supplies Thread transport, not a
   Matter controller. The phone's Bluetooth, IPv6 and multicast connectivity
   still matter; this hub's BLE proxy does not replace phone commissioning.
   Follow [HA's Matter setup](https://www.home-assistant.io/integrations/matter/)
   and the [Thread device guide](thread-devices.md), then test a real command.
5. **Z-Wave:** configure Z-Wave JS / Z-Wave JS UI with the native ESPHome
   transport from the [ZAC93 instructions](full-hub-assembly.md#first-power-and-home-assistant).
   It uses **6053 plus the URL-encoded API key**. The HA Z-Wave integration
   connects to that Z-Wave JS server's **WebSocket**, not directly to the hub.
   Confirm ZAC93 is identified in the correct region and test a device. Use one
   Z-Wave driver only; port 6638 is Zigbee.
6. **433 MHz RF:** confirm the private MQTT broker and topic contract, then
   receive a known remote event. Test transmission against an intended test
   receiver and verify reception resumes. Compiling successfully does not
   establish that learned codes or the household's MQTT topics were retained.

**Ready to continue:** each intended service has passed a physical event or
command test. A connected TCP socket or visible HA integration alone is not
end-to-end evidence. See [HA's external OTBR configuration](https://www.home-assistant.io/integrations/otbr/)
for the REST endpoint and [Bluetooth integrations](https://www.home-assistant.io/integrations/bluetooth/)
for supported remote adapters.

## 6. Close the case, qualify, then migrate

Repeat the same tests with the case closed and at its final position. Follow
the [RF commissioning procedure](rf-commissioning.md), including simultaneous
traffic, intended active BLE connections, measured heap/temperature/supply
behaviour, recovery after PoE loss and the 72-hour soak. Record results in the
[coverage sheet](../hardware/external-antenna/coverage-results.csv).

Before switching an existing home, save HA configuration, private firmware
secrets, Thread credentials and Zigbee/Z-Wave backups. Keep the old coordinator
configuration available. Move one service at a time, stop its previous driver,
and verify the same test events before moving the next service. Do not erase
radio state or re-include devices simply to change a host connection.

**Rollback:** stop the new service's driver before restoring the previous
connection and its appropriate backup. Do not run two owners of one Zigbee or
Z-Wave radio. A moved ZAC93 keeps its network state unless reset; return that
same radio to its old host if needed. A later firmware rollback requires a
known-good image for this exact hardware and partition layout; use the
[checked network update and recovery guide](../firmware/external-antenna/updates/README.md).

## Troubleshooting: symptom → first checks

- **No DHCP address / HA cannot reach the hub:** check PoE switch power, measured
  5 V/3.3 V, the splitter's data output into U4 and Ethernet link. Try its DHCP
  address instead of `.local`. An address proves neither ESPHome credentials
  nor Thread's IPv6 path; test those separately.
- **USB connects but no running logs appear:** expected after boot. UART0 serves
  the radar and console output is disabled. Use encrypted ESPHome API logs;
  USB-UART is retained for initial flashing and recovery.
- **Host fails to boot or reports missing PSRAM:** check the exact VIE/WROVER-IE
  board and factory image, then inspect the GPIO12/GPIO2 boot pull-downs and
  supply integrity. Do not change eFuses to disguise a wrong module or strap.
- **Thread says `quarantined` or `maintenance`:** read `Thread Last Fault` and
  `C6 UART Update State`. Check C6 image, power, UART wiring and boot straps.
  Complete an interrupted update if necessary, then use **Retry Quarantined
  Thread** after correcting the cause. Do not erase the host's Thread dataset.
- **Zigbee times out:** close any second ZHA/Zigbee2MQTT client. Check TCP 6638,
  all four UART/RTS/CTS wires, the external-antenna MG24 image and open J8 during
  normal operation. Poor range also warrants checking the U.FL path and antenna.
- **ZAC93 is missing or stops responding:** check the J4 remap, 3.3 V at ZAC93,
  bridge address jumpers, UART1 and the API key used by Z-Wave JS. A
  `wk2132_uart` log saying **`UART stream invalid`** requires a device restart
  after its cause is corrected; reconnection alone does not reset the bridge
  driver. A host restart is not a ZAC93 power cycle. If the radio needs a power
  cycle, stop its driver and cycle PoE with USB disconnected; do not factory reset.
- **BME680 absent / temperature reads high:** check J7, the default 0x77 address
  (or the private `bme680_address` override for 0x76), 3.3 V pull-ups and the
  shared bus harness. Keep the sensor opening clear in its external pod and
  compare after thermal equilibrium. Gas resistance is not calibrated CO₂.
- **LD2450 has no updates:** check J6 power and TX→RX crossing at **256000 baud**.
  Compare with the lid open to separate a serial fault from window/placement
  effects; keep metal and wires away from the radar face.
- **RF events reach the wrong topic or never reach HA:** inspect the private
  broker credentials, topic substitutions and learned-code overrides first.
  `build-only/rf/*` means the proof configuration was not prepared for deployment.
- **Works on the bench, fails with the lid or combined traffic:** compare the
  recorded open/closed-case results; inspect cable compression, antenna spacing,
  power/temperature and `Hub Minimum Free Heap`/`Hub Largest Heap Block`. Follow
  the [RF acceptance workflow](rf-commissioning.md) rather than assuming gain or
  enclosure clearance guarantees coverage.
