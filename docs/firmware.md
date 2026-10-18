# Firmware and software

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

The main build uses a Raspberry Pi 4 running Linux, two independent USB radios, and a Waveshare **ESP32-S3-ETH-M** with 16 MB flash. The S3 runs Ethernet, a Bluetooth proxy, LD2450, BME680, and a UART proxy for the existing Zooz ZAC93. A separate second S3-ETH-M with CC1101 handles the wired RF Airbridge; the previous ESP8266 is retained for rollback. All boards share the PoE power system. Private configuration and HA registry migration are handled separately using the migration guide.

## What has actually been verified

- Main `hub-s3-eth.yaml`: schema validation and a full build passed with ESPHome **2026.9.1**, ESP-IDF **5.5.5**. Static RAM: 104 319 / 341 760 bytes (30.5%); program: 942 199 bytes. This is not a measurement of free memory while BLE is running.
- RF Ethernet: schema validation and a full build of a **synthetic fixture migrated using the actual importer**, with 15 legacy binary sensors, custom source/topics, and an RM433 slot, passed with ESPHome **2026.9.1** / ESP-IDF **5.5.5**. Static RAM: 72 991 / 341 760 bytes (21.4%); program: 699 707 bytes. The empty public template was also built. RF/migration regression tests with ASan/UBSan check the software contracts; current results and test coverage are listed in the [validation log](validation.md).
- The current **private configuration of the running RF Airbridge** was also migrated offline and successfully compiled with ESPHome **2026.9.1**: 15 legacy RF sensors, RAM 73 247 bytes (21.4%), program 697 435 bytes (8.6%). All 10 configuration preservation checks passed. The installation's source files, secrets, and binaries remain in the Git-ignored `private/` directory. The new board is not ready yet; waveform/RX→TX→RX behavior and the physical HA cutover have not been tested.
- `software/render_config.py`: input constraint and configuration tests passed; Docker Compose parsed the configuration successfully.
- No physical board has been flashed. Electrical connections, simultaneous radio operation, thermal behavior, and long-term stability require bench testing.
- A Docker daemon is unavailable on the development machine: container startup, Linux driver loading, and RCP communication have not been tested locally. The Thread RCP ARM build was not run locally; the pinned PCA10059 firmware built successfully in [Linux GitHub CI](https://github.com/ha-homelab/ha-radio-hub/actions/runs/38992347499). That test does not verify radio communication.

## 1. Main ESP32-S3

Use the S3-ETH-M specifically, without a camera or microSD card: GPIO4/5 and GPIO1/2/17/18 are used by those peripheral connectors in other board configurations. The pin map follows [Waveshare](https://www.waveshare.com/wiki/ESP32-S3-ETH) and [ESPHome Ethernet](https://esphome.io/components/ethernet/).

- W5500 is already on the board: SCLK13, MOSI11, MISO12, CS14, IRQ10, RESET9.
- ZAC93: S3 GPIO17 TX → ZAC93 pin 8 RX; S3 GPIO18 RX ← ZAC93 pin 10 TX; 3V3 → pin 1; GND → pin 6. Baud rate: 115200, 8N1. Do not supply 5 V to the ZAC93.
- LD2450: S3 GPIO4 TX → radar RX; S3 GPIO5 RX ← radar TX; 5 V radar supply and common ground. UART: 256000, 8N1, 3.3 V logic levels.
- BME680: SDA GPIO1, SCL GPIO2, 3V3, and GND. The default Adafruit STEMMA QT address is **0x77**; change `bme680_address` for a board with a different address.

Create the Python environment from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r firmware/requirements.txt
python firmware/validate.py --compile
```

The last command uses disposable keys in a temporary directory and deletes the test binary. For your own firmware, create local secrets:

```sh
cp firmware/secrets.example.yaml firmware/secrets.yaml
openssl rand -base64 32
openssl rand -hex 24
```

Place the first result in `api_encryption_key` and the second in `ota_password` in `firmware/secrets.yaml`. Do not add that file to Git. The API key is required by the ESPHome integration and Z-Wave JS. Build your firmware:

```sh
esphome config firmware/hub-s3-eth.yaml
esphome compile firmware/hub-s3-eth.yaml
```

Before the first flash, disconnect PoE power and peripherals. Connect a USB data cable to the computer; if needed, hold BOOT while pressing RESET. Select the actual serial port in `esphome upload firmware/hub-s3-eth.yaml --device PORT`. After flashing, disconnect USB, wire the peripherals according to the diagram, and apply the normal power supply. Do not connect independent 5 V sources together without isolation.

For subsequent updates: `esphome upload firmware/hub-s3-eth.yaml --device ha-radio-hub-sensors.local`; if mDNS is unavailable, use the reserved DHCP address. Logs: `esphome logs firmware/hub-s3-eth.yaml --device ha-radio-hub-sensors.local`. The configuration has no Wi-Fi fallback: Ethernet is required for the API and OTA.

[ESPHome's LD2450 integration](https://esphome.io/components/sensor/ld2450/) provides coordinates for three targets and presence sensors. Start by testing one person in front of the uncovered board. After setup, disable the radar's own Bluetooth using its diagnostic switch if it is not needed. This does not disable the ESP32 Bluetooth proxy. Do not treat the LD2450 as a guaranteed detector of a completely stationary person in all conditions.

[BME680](https://esphome.io/components/sensor/bme680/) publishes temperature, pressure, humidity, and **gas resistance** every 60 seconds. This configuration does not calculate CO₂ or VOC ppm, or promise calibrated IAQ. Place the sensor in the ventilated side compartment, away from the Pi and converters. You can disable the `firmware/packages/bme680.yaml` package until the sensor is installed. Use 3.3 V and a short cable of up to 20 cm for the I²C expansion, and check the combined pull-up resistance: adding boards with pull-ups in parallel reduces the resistance. Do not connect devices with pull-ups to 5 V.

## 2. Thread RCP: Nordic PCA10059

This is a separate USB radio, not a BLE proxy or Zigbee coordinator. OTBR runs on the Linux Pi; the RCP supplies its IEEE 802.15.4 radio. The build uses the official [OpenThread nRF52840](https://github.com/openthread/ot-nrf528xx/blob/1ff0a4905e436eb79605582f36b689063b1282ef/src/nrf52840/README.md) path with a USB bootloader. That upstream recommends nRF Connect SDK for new commercial products; the selected legacy platform serves here as a reproducible DIY prototype.

Install an Arm GNU toolchain with `arm-none-eabi-gcc`, CMake, Ninja, Git, and the upstream dependencies. Then run:

```sh
bash firmware/build-thread-rcp.sh
```

The script pins the Git SHA and submodules, builds a USB RCP with `-DOT_BOOTLOADER=USB`, and creates `.build/thread-rcp/ot-rcp-pca10059.hex`. Tools and system dependencies are not pinned byte for byte; this pins the source and does not claim bit-for-bit reproducibility.

Flash the HEX using **nRF Connect for Desktop → Programmer**, selecting the PCA10059 specifically. Press the dongle's RESET button to enter its stock USB bootloader. Write the application and preserve the bootloader; do not use erase-all. See [Nordic Programmer](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-programmer/programming_nrf52840_dongle.html/programming-nrf52840-dongle). After reboot, a USB CDC ACM serial port should appear on the Pi. Find its stable name with `ls -l /dev/serial/by-id/`; the USB name can change after a firmware replacement. Record the name used by the working RCP firmware.

If the image cannot be installed or the RCP does not respond, do not accidentally modify the Zigbee radio. Another documented USB Thread RCP can be substituted on the bench, but its baud rate, flow control, and OpenThread RCP API compatibility must be checked. The provided Compose configuration uses a URL with 1000000 baud and no hardware flow control for Nordic USB CDC.

## 3. Zigbee MG24

Use the SMLIGHT **SLZB-07Mg24** with its stock **Zigbee coordinator / Ember NCP** firmware. Record its version before making changes. Do not install Thread/multiprotocol firmware on the same unit. A new, working Zigbee adapter does not have to be reflashed; use SMLIGHT's official tool for the exact model if updating it.

Pi-side `ser2net` enables **115200, 8N1, and RTS/CTS**, as specified for SLZB-07/MGx in the [SMLIGHT settings](https://smlight.tech/support/manuals/books/slzb-07pxmgx/page/zigbee2mqtt-setup). This controls the USB UART between the Pi and the adapter; a flow-control toggle in the remote TCP client does not replace this setting. If the manufacturer changes the UART profile in new firmware, update the renderer and ZHA consistently. A different adapter family requires a separate settings check.

## 4. Linux services on the Pi

Install 64-bit Raspberry Pi OS Lite/Debian, Docker Engine, and the Compose plugin using the [official Docker guide](https://docs.docker.com/engine/install/debian/). The Pi is a separate appliance; Home Assistant continues running on the existing server. Connect both USB radios and the internal Ethernet cable. Reserve DHCP addresses for the Pi and ESP32. For the first bench test, place HA, the Pi, ESP32, and phone on the same LAN with working IPv6 and multicast.

Copy the repository to the Pi. The following command uses TEST-NET example addresses only: replace them and the USB symlinks.

```sh
python3 software/render_config.py \
  --hub-ip 192.0.2.10 --ha-ip 192.0.2.20 --interface eth0 \
  --thread-device /dev/serial/by-id/usb-Thread_REPLACE \
  --zigbee-device /dev/serial/by-id/usb-SMLIGHT_REPLACE
docker compose --env-file software/runtime/hub.env -f software/compose.yaml config --quiet
```

The renderer only creates local files. It rejects identical Thread/Zigbee devices, wildcard IPs, unstable paths such as `/dev/ttyUSB0`, and invalid characters. `--ha-ip` must be the HA connection source address **as seen by the Pi**, which matters with containers/NAT. If HA has multiple addresses, add only the required sources to the allow-list after verifying the network path.

Generate the runtime files on the Pi itself: `hub.env` contains `SER2NET_CONFIG` with the absolute path to the generated `ser2net.yaml`. Rerun the renderer after moving the directory from another computer or updating an old `hub.env`. For a custom `--output`, use that directory's `hub.env` in every `docker compose --env-file` command; a missing bind-mount file is not created automatically. The renderer writes files atomically with mode 0600 and rejects symlinks in place of output files.

Now apply the settings on the **Pi**, not the workstation:

```sh
sudo install -m 644 software/runtime/60-ha-radio-hub.conf /etc/sysctl.d/60-ha-radio-hub.conf
sudo sysctl --system
docker compose --env-file software/runtime/hub.env -f software/compose.yaml up -d --build
docker compose --env-file software/runtime/hub.env -f software/compose.yaml logs --tail 100
```

Sysctl enables IP forwarding and reception of IPv6 RA/RIO, following [OpenThread setup-host](https://github.com/openthread/ot-br-posix/blob/f064121702b7c2a9f7bf853ca39167c26ee11ec9/etc/docker/border-router/setup-host). OTBR uses host networking, NET_ADMIN, and TUN for routing; its stock entrypoint also modifies forwarding/NAT rules. This is a configuration for a dedicated Pi, not an unconditional installation script for an existing router.

`software/versions.json` stores the source/image pins. The OTBR REST API listens only on the Pi's LAN IPv4 address at port 8081; the local web UI listens on 127.0.0.1:8080. `ser2net` listens on Pi:6638 and permits one client from the HA address. **The OTBR REST API has no built-in authentication**: use firewall/ACL rules to permit TCP8081 only from HA and the chosen administrator, and TCP6638 from HA. Permit ESPHome API6053 and OTA3232 from HA/the administrator's computer. Do not expose these ports to the internet. Do not block IPv6 ICMP, multicast, mDNS, or Thread routing between permitted devices; simple IPv4 port forwarding does not replace this connectivity.

Verification: the OTBR log should contain a successful Spinel handshake and RCP version; `docker compose ... exec otbr ot-ctl state` should return the Thread state. Before a network is created/joined, disabled/detached is acceptable. Check access to `http://PI_IP:8081/node` from the HA host. A successful `curl` alone does not prove that Matter commissioning works.

**For a new network only**, if the home does not already have a preferred Thread network:

```sh
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset init new
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset networkname HaRadioHub
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset channel 25
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset commit active
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl ifconfig up
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl thread start
```

Channel 25 is an initial setting; check it against your Wi-Fi/Zigbee channels. Do not run `dataset init new` over the home's existing preferred network: first back up its credentials and import the existing dataset. Dataset files contain network keys. Back up the Docker volume `otbr-data` and Z-Wave/Zigbee network backups to private storage; `docker compose down -v` deletes OTBR state.

## 5. RF Airbridge over Ethernet

`firmware/rf-ethernet.yaml` uses a separate **second S3-ETH-M** with CC1101, MQTT, and the native API. It preserves `rf/received`, `rf/received/raw`, `rf/transmit/result`, RM433 button events, `send_rf_code`, and `send_dooya_code`, with a single worker, `busy` rejection, and a 750 ms cooldown. Private source/topics/codes and legacy sensor definitions are imported into a local wrapper; the public template does not contain them.

RF SPI3: SCLK7, MOSI8, MISO6, CS15; GPIO4 TX → GDO0 **open-drain with an external 4.7 kΩ pull-up to 3.3 V**, GDO2 → GPIO5 RX. W5500 remains on GPIO9–14. This is a separate RF board: the wiring does not apply to the main S3 with LD2450. The local RMT receiver patch matches ESPHome 2026.9.1 and manages capture around TX; it does not use the existing ESP8266 patch.

```sh
python firmware/validate.py --config rf-ethernet.yaml
python firmware/validate.py --config rf-ethernet.yaml --migration-fixture --compile
```

The first command validates the public template; the second runs the actual importer on a synthetic configuration with 15 sensors and fully compiles the result. Disposable secrets are used, and nothing is flashed. Before replacing an installed node, follow the [offline migration, bench test, cutover, and rollback procedure](../hardware/rf-migration.md). Preserving `esphome.name` and the API key does not guarantee the previous HA device ID/unique ID: the Ethernet board has a different MAC address. Private entity mapping and device-trigger checks are required. After cutover, keep the old ESP8266 powered off as a spare.
