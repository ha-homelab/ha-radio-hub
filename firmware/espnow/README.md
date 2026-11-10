# ESP-NOW sensor extension for MC2-D

This opt-in firmware adds three example sensor satellites to the **existing full
MC2-D hub**. It uses the ESP32-DevKitC-VIE's existing 2.4 GHz antenna and changes no
carrier pins, wiring, parts, or enclosure. The C6 remains the Thread RCP and the
MG24 remains the Zigbee radio. Ethernet remains the hub's IP connection.

**Acceptance status:** configuration/build validation is separate from hardware
acceptance. Simultaneous BLE, Thread, Zigbee, RF, Z-Wave, and ESP-NOW operation
still needs the bench procedure in [the ESP-NOW guide](../../docs/espnow.md).

The [compilation evidence](build-evidence.json) records the pinned toolchain,
recipe hashes and generated images. The complete host application is
**2,010,624 bytes**, within both 3,932,160-byte OTA slots. Its linker reports
**5,256 bytes of static DRAM headroom** and **36,005 bytes of IRAM headroom**.
Static DRAM headroom is not the available runtime heap; it is a small margin
for adding more static data. Measure minimum internal heap, largest free block
and free PSRAM under simultaneous load before deploying this extension.

## Files

- `hub.yaml`: complete MC2-D profile with the extension enabled.
- `hub-radio.yaml`: ESP-NOW radio, fixed channel, explicit Wi-Fi/BLE coexistence
  SDK settings, enrolled station MACs, and radio diagnostics.
- `hub-sensors.yaml`: named remote sensors, provider keys, and freshness diagnostics.
- `satellite-base.yaml`: shared ESP32-C3-DevKitM-1 settings; USB power and serial
  service, ESP-NOW without a Wi-Fi association, API, or OTA server.
- `sensor-bme280.yaml`: temperature, humidity, and pressure on GPIO4/5 I²C.
- `sensor-ds18b20.yaml`: one powered temperature probe on GPIO4.
- `sensor-contact.yaml`: persistent dry-contact state on GPIO4.
- `secrets.example.yaml`: **nonfunctional placeholders**, not deployable credentials.
- `prepare.py`: isolated copy of the pinned hub dependencies and disposable
  validation credentials. Does not connect to or flash any device.

The satellite pin examples are for **separate ESP32-C3-DevKitM-1 boards**. Do not
attach these sensors to those pin numbers on the MC2-D carrier: the hub pins are
already assigned. Existing ESP32/S2/S3/C6 boards can be adapted after checking their
board definition and actual free pins. ESP32-H2 has no Wi-Fi radio for ESP-NOW.

## Build and enroll

Use the repository's pinned [requirements](../requirements.txt), currently
ESPHome 2026.10.2 / ESP-IDF 5.5.5. Prepare outside the checkout:

```sh
python3 firmware/espnow/prepare.py ~/.codex/artifacts/ha-radio-hub-espnow/build
esphome config ~/.codex/artifacts/ha-radio-hub-espnow/build/firmware/espnow/hub.yaml
esphome compile ~/.codex/artifacts/ha-radio-hub-espnow/build/firmware/espnow/hub.yaml
esphome compile ~/.codex/artifacts/ha-radio-hub-espnow/build/firmware/espnow/sensor-bme280.yaml
```

The output directory must not already exist. `--upstream /path/to/esp-thread-br`
can reuse a local clone containing the exact dependency commit. See
`python3 firmware/espnow/validate.py --help` for automated checks.

To compile and verify **all four profiles** with disposable credentials in a
new directory:

```sh
python3 firmware/espnow/validate.py /tmp/mc2-espnow-check \
  --esphome /path/to/pinned/esphome --compile
RF_CPP_SANITIZERS=1 /path/to/pinned/python -m unittest discover \
  -s tests -p 'test_espnow.py'
```

The validator checks the complete hub's original pin and memory contracts,
both OTA partitions, the final Wi-Fi/coexistence SDK settings, and each sensor
build. Its JSON receipts explicitly leave hardware acceptance unverified.
The same compilation and tests run in the required `ESP-NOW complete hub and
sensor examples` CI job. Validation images contain disposable credentials and
must not be installed as deployment images.

Before installing, replace the **prepared** `firmware/espnow/secrets.yaml` with
real hub API/OTA/MQTT values, the four actual **Wi-Fi station MAC addresses**, and
three different random provider keys. Generate each provider key with
`python3 -c 'import secrets; print(secrets.token_hex(32))'`. The hub and its matching
satellite must have identical provider keys. Do not publish this file or compiled
firmware containing the keys.

Also restore the installation's RF topic/source substitutions and learned-button
code overrides in the prepared `firmware/external-antenna/hub.yaml`, as described
in [private host programming](../external-antenna/README.md#initial-host-programming-with-private-configuration).
Preparation deliberately uses `build-only/rf/*` topics and disabled learned
codes. Supplying a real MQTT broker alone does not restore existing RF
automations. Keep the base node name, pins, memory settings and partition layout.

The ESP-NOW `Own address` startup log gives each satellite's station MAC. The hub
exposes `ESP-NOW Station MAC` through its existing encrypted HA API. A Bluetooth,
Ethernet, or Wi-Fi AP address is not interchangeable with the station address.
For initial serial identification, keep the documented placeholder peers; no
unknown peer is automatically enrolled. Attach the correct antenna before
powering any external-antenna board.

All four profiles default to **channel 6**. To change it, set `espnow_channel` in
both hub and every satellite and rebuild. The ESP-NOW radios do not join the home
Wi-Fi AP and do not follow its automatic channel changes. Select a channel after
checking the installed Wi-Fi, Zigbee, and Thread plan; do not assume 6 is optimum.

Build and flash one actual satellite configuration per board via its serial USB
port. The hub continues to use the existing MC2-D installation/update procedure.
No physical device was flashed by preparing or compiling these profiles.

## Sensor behavior and limits

Sensor states and heartbeat uptime are resent every 30 seconds; state changes
also trigger an outgoing update. The hub sends a challenge on startup, when
resynchronization is needed, and periodically. Leave both sides powered during
enrollment and allow at least one full heartbeat interval for the online state.

`ESP-NOW ... Online` starts false and becomes true only after the hub decodes a
finite uptime value with the provider's key and current challenge. It becomes
false at 90 seconds without another accepted heartbeat. `Last Seen Age` measures
that same heartbeat, not raw radio activity or validity of a physical measurement.
Numeric measurements time out to unavailable after 90 seconds without an update;
the native transport also invalidates remote states after its 120-second
challenge timeout, observed on the next 15-second poll.

**Gate contact-based automations on `ESP-NOW Contact Online`.** A stale contact
must not be interpreted as a newly open/closed door. The native binary sensor
becomes unknown after the challenge timeout; it is not forced to a fabricated
safe state. Reed contacts are persistent state, not guaranteed event delivery:
a brief button press may be lost. This profile is not a fire, security, emergency,
or motor safety controller.

These examples deliberately stay awake. Deep sleep requires a separate tested
wake/receive/challenge/retry strategy. Sending once and immediately sleeping is
not reliable after a hub restart, and producer rolling-code state is written to
flash on each boot. A dev-board USB bridge, regulator, or LED may dominate battery
consumption. See the guide for battery-node design and other sensor uses.

Preserve satellite NVS during ordinary firmware updates. If a deliberate full
erase resets its rolling-code counter, a running hub can reject the lower counter.
Verify the satellite's key and station MAC, then restart the hub to begin a new
challenge/session; do not disable the replay checks to recover communication.

## Protocol and security boundary

This uses ESPHome's **native `packet_transport` protocol over ESP-NOW**, including
per-provider XXTEA payload encryption, producer rolling codes, and receiver
ping/pong challenges. It is not arbitrary ESP-NOW packet auto-discovery, Matter,
Thread, Zigbee, Wi-Fi provisioning, or a transparent ESPHome API/OTA tunnel.

The native `espnow` peer list limits accepted senders operationally; MAC addresses
can be spoofed. Packet transport identifies a provider by its node name and key,
not a cryptographically bound MAC. Its payload encryption is not native ESP-NOW
PMK/LMK link encryption and not an authenticated-encryption construction. Keep it
to low-consequence telemetry; the extension intentionally defines no remote
relay, curtain, or motor commands.

The explicit SDK options in `hub-radio.yaml` are required for this pinned build:
ESPHome's Ethernet-only final configuration would otherwise disable the Wi-Fi
driver and coexistence. No `wifi:` block is added, so the existing Ethernet-only
OTBR guard remains in force. The classic ESP32 shares one 2.4 GHz radio between
BLE and ESP-NOW; using both is supported in STA mode but is not a promise of full
radio capacity or house-wide coverage under every load.

Primary implementation references:

- [ESPHome ESP-NOW](https://esphome.io/components/espnow/)
- [ESPHome packet transport](https://esphome.io/components/packet_transport/)
- [Pinned ESP-NOW implementation](https://github.com/esphome/esphome/blob/2026.10.2/esphome/components/espnow/espnow_component.cpp)
- [Pinned packet transport implementation](https://github.com/esphome/esphome/blob/2026.10.2/esphome/components/packet_transport/packet_transport.cpp)
- [ESP-IDF 5.5.5 radio coexistence](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32/api-guides/coexist.html)
