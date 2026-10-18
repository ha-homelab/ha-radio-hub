# Prototype acceptance record

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

Record actual values, part revisions and firmware commits in a **private** copy.
Every item below starts **not physically tested**. Do not publish network datasets,
keys, installation QR codes, RF captures, home maps or device identities.

## Before applying power

- Confirm PoE+ PSE, isolated splitter output voltage/polarity, connector current
  rating, fuse placement and insulated terminations. No passive-PoE substitute.
- Check the 5 V rail is not shorted and no ZAC93/CC1101/BME680 supply or GPIO is at 5 V.
- Verify the actual ESP32-S3-ETH-M pin map; remove camera and microSD peripherals.
- Check case clearances, solder-joint insulation, fastener length and strain relief.
- Feed each board from one supply path at a time; disconnect shared power before
  using USB for flashing unless a verified data-only/service arrangement is fitted.

## Power and thermal acceptance

- Measure splitter output and voltage at the Pi and sensor board during startup,
  radio transmission, Ethernet traffic and BLE scanning. Record dips and resets.
- Measure total sustained/peak DC current. The proposed **20 W / 4 A at 5 V**
  ceiling is a design acceptance target, not a component maximum or a measured fact.
- Verify PoE switch budget, no Pi undervoltage/throttling events, and adequate
  margin for the exact supply and cable length. If these fail, change power design.
- Run closed-case mixed traffic for at least 24 hours; log ambient/internal
  temperature, board temperatures, resets and packet/API availability. Extend to
  seven days before replacing a working gateway.

## Individual interfaces

- ZHA **or** Zigbee2MQTT: pair a spare device, exercise commands and recover after
  Pi/relevant service restarts. Confirm a second TCP client is rejected.
- Thread: verify local RCP initialization, OTBR REST access, IPv6 route and mDNS
  on the actual HA network. Commission a spare Matter-over-Thread device and
  exercise it after restarting HA and then after restarting only the hub.
- Z-Wave: verify region, ZAC93 firmware/API version and Z-Wave JS minimum required
  by the current ESPHome transport. Test a spare device and controller backup.
- BLE: observe a known supported BLE sensor and test an active connection; record
  coverage with all other radios transmitting. Do not infer classic audio support.
- RF: keep the private source/topics/codes and original configuration backup.
  Confirm open-drain GPIO4 with the external 4.7 kΩ pull-up; measure release and
  RX recovery after TX. Test RC-Switch, RM433 hold suppression, Dooya TX, busy,
  TX cooldown while RX is active, broker reconnect without replay, and no TX
  self-echo. Verify send_failed on injected RMT failure/cooperative timeout,
  fail-closed behavior, and explicit recovery by restart. The 30 s timer requires
  a running event loop; measure actual driver-hang/watchdog behavior separately.
  There is no guaranteed 30 s recovery bound or implicit success on a fault.
- RF cutover: map the new MAC/device/unique IDs explicitly; preserve intended
  entity IDs and update device triggers. Exercise rollback with the old board
  powered off while the new board owns its production MQTT identity.
- Radar: walk through known distances/zones, compare open antenna vs closed
  plastic window, check ghosts and transitions; stationary occupancy is separate.
- BME680: verify 0x77/0x76 address, stable readings after warmup, independent ambient
  comparison and no bias from the hub exhaust. Gas resistance is not a CO₂ test.

## Mixed operation and recovery

- Transmit RF while Zigbee/Thread/BLE operate and record dropped events. Adjust
  placement/channels based on measurements, not only nominal band separation.
- Power-cycle the entire box ten times and confirm services/ESPHome reconnect.
- Disconnect uplink and restore it; ensure independent radio networks recover.
- Confirm no management/radio ports are reachable from an untrusted network.
- Test restore procedures using backups before household migration; preserve the
  old gateways until the new installation passes these checks.
