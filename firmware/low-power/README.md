# Single-Ethernet low-power firmware

This is an **experimental unified software target**, not an electrically validated product or a measured power claim. `hub.yaml` builds one ESP32-S3 N16R8 image containing ESPHome Bluetooth proxy, RF Airbridge, LD2450, BME680, Z-Wave proxy through SC16IS752, a transparent Zigbee NCP TCP bridge, and an H2-backed Thread border router. H2 and MG24 still require their own radio firmware. There is no internal Ethernet switch, Linux host, second W5500, or Wi-Fi transport.

`proof.yaml` is the shared core package. Use **`hub.yaml`** for the complete target. The existing `../hub.yaml` and `../rf-ethernet.yaml` remain independent supported prototypes.

## Verified locally on 2026-10-17

The complete `hub.yaml` linked successfully with ESPHome 2026.9.1 / ESP-IDF 5.5.5. Application/OTA binary: **1,716,944 bytes**; factory image: **1,782,480 bytes**. The IDF size report records **161,127 / 341,760 bytes of static RAM (47.1%)** and 21.1% of the application slot. Static RAM usage does not include all runtime allocations, BLE connections or task stacks; it is not a measured free-heap result.

The separate H2 RCP also built with IDF 5.5.5: **208,928 bytes**, with 80% of its 1 MiB application partition unused. Nineteen mandatory host SDK options were checked after compilation, including IPv6 routing, VFS/select, Thread Commissioner/Joiner, BLE and octal PSRAM. `validate.py` repeats those checks and records binary SHA-256 values in the prepared `build-result.json`.

Eight native Zigbee bridge tests passed with ASan/UBSan, including partial transfers, exclusive connection ownership, stale TX FIFO removal, both CTS stall cases, timer wraparound and driver-reset failure. The two actual-C / Home Assistant REST-client regression tests passed. Hardware was not flashed or exercised; neither the power target nor multi-radio runtime stability has been demonstrated.

## Reproduce the host build

Python 3.12 or newer, Git, and the ESPHome prerequisites are required. From the repository root:

```sh
python3 -m venv .venv-low-power
.venv-low-power/bin/pip install -r firmware/requirements.txt
python3 firmware/low-power/validate.py \
  --esphome .venv-low-power/bin/esphome --compile \
  --output /tmp/radio-hub-build
```

Choose a new output directory outside the source `firmware/` tree. Omitting `--output` builds in a temporary directory and removes it afterward. For an offline source cache, add `--upstream /path/to/esp-thread-br-clone`; it must contain commit `29a2345e3f0c61bba9307f3daea5ed0c94388ed3`. Toolchain/dependency downloads still require their own caches.

The preparer exports the exact upstream commit, carries its Apache-2.0 license, and applies checked patches to the REST component. It generates **disposable** API, OTA and MQTT credentials; the broker is a documentation address. The result verifies compilation, not household configuration. Do not flash these build credentials as a finished installation.

Pinned host versions are ESPHome **2026.9.1**, ESP-IDF **5.5.5**, and the ESP Thread BR commit above. ESP Thread BR's reference example was based on IDF 5.5.4; this integration uses IDF's 5.5.5 OpenThread stack and compiles the pinned REST implementation against it. Configuration fails on unsupported host versions.

Build products are under:

```
/tmp/radio-hub-build/firmware/low-power/.esphome/build/low-power-hub-proof/
```

ESPHome puts its application and merged factory binaries in this build directory. Keep the corresponding generated YAML, secrets, dependency lock, ELF and build log privately with any deployed image. A successful build does not establish RF coexistence, RAM headroom under traffic, or a particular wattage.

## Prepare and build the H2 RCP

Use ESP32-H2 with 4 MB flash (the hardware target is ESP32-H2-MINI-1-H4S). Obtain the exact SDK in a separate directory:

```sh
git clone --branch v5.5.5 --depth 1 --recursive --shallow-submodules \
  https://github.com/espressif/esp-idf.git /tmp/radio-hub-idf
test "$(git -C /tmp/radio-hub-idf rev-parse HEAD)" = b774170ff46c393eeb5e495ea37936038d3f4f4f
/tmp/radio-hub-idf/install.sh esp32h2
. /tmp/radio-hub-idf/export.sh
python3 firmware/low-power/prepare_h2.py /tmp/radio-hub-h2 --idf "$IDF_PATH"
idf.py -C /tmp/radio-hub-h2 -DIDF_TARGET=esp32h2 build
```

The preparer verifies IDF 5.5.5 and, for a Git checkout, its exact commit. It copies the stock RCP C source unchanged, disables unused example console/coexistence dependencies, and sets UART0 to **460800 8N1**, H2 **RX23/TX24**, no RTS/CTS. Products and the exact flash offsets are in `/tmp/radio-hub-h2/build/flasher_args.json`. The H2 must run this RCP before the host starts. An absent or incompatible RCP can trigger the upstream OpenThread driver's panic/restart; unrelated ESPHome services are not guaranteed to survive that fault.

## Wiring and runtime contract

Use the reviewed [hardware pin map](../../hardware/low-power/README.md). The S3 UART allocation is intentional: native ESPHome radar UART0 on TX39/RX40, raw Zigbee UART1 on TX17/RX18/RTS16/CTS21, Thread UART2 on TX43/RX44. Z-Wave uses SC16IS752 channel A on SPI3, CS41/IRQ42, with a **3.6864 MHz** crystal and divisor 2 at 115200 8N1. Add no other native `uart:` entry: it could claim a port used by another stack.

The W5500 uses SCK13/MOSI11/MISO12/CS14/IRQ10/RESET9 on its own hardware SPI bus. The other SPI bus is SCK7/MOSI8/MISO6, shared by CC1101 CS15 and SC16 CS41. CC1101 GDO0 connects to open-drain TX4 with a 4.7 kΩ pull-up; GDO2 connects to RX5. BME680 uses I²C SDA1/SCL2 at 100 kHz.

**DevKit adaptation is a physical prerequisite.** Isolate the S3 board's USB–UART transmitter from GPIO44 before connecting H2 TX; native USB19/20 remains available for flashing. Isolate an H2 DevKit USB–UART transmitter from H2 RX23 before connecting S3 TX. GPIO48 must not remain connected to a board revision's addressable LED because it drives H2 BOOT9. H2 EN/BOOT are controlled as open-drain outputs with the specified external 10 kΩ pull-ups. H2 GPIO8 also needs its required boot pull-up. Check the hardware document for all other bias, reset and decoupling requirements; software cannot resolve output contention.

The [MG24 build kit](mg24/README.md) provides a separately built Ember NCP and
UART-XMODEM bootloader for MGM240PA22VNA3, using 115200 8N1 and hardware flow
control. Its PA06/TX, PA05/RX, PB00/RTS and PB01/CTS mapping is checked in the
generated configuration; it is not an assumption about factory firmware.
Initial flashing uses SWD; PA00 is the bootloader service input. Compilation and
offline image checks passed; physical startup, flow control and pairing remain
hardware acceptance gates.

The host runs at 160 MHz with octal PSRAM at 80 MHz. BLE active scanning explicitly uses a 30 ms window every 320 ms and permits three active proxy connections. No deep sleep is used. BME680 heater measurements, active BLE connections and traffic change consumption.

The W5500 SPI clock is 10 MHz. Separately, `low_power_ethernet` stops the driver, selects PHY **10 Mbit/s half duplex**, verifies the register and restarts it. This avoids a duplex mismatch with an auto-negotiating partner's parallel detection. Do not force the switch to full duplex. Confirm actual link negotiation, throughput and loss on the intended PoE switch. If PHY configuration fails, the component leaves Ethernet stopped; it does not silently fall back to a higher-power mode.

## Home Assistant and local network

- Add ESPHome using the installation's API encryption key. BLE, radar, BME680 and Z-Wave proxy use the normal ESPHome interfaces. Z-Wave JS still runs in Home Assistant or on its existing server; it is not embedded in the S3.
- Add ZHA using Ember and `socket://HOST:6638`. The bridge accepts one client, preserves bytes, and applies hardware RTS/CTS. Five seconds without UART TX progress disconnects the client and resets both UART FIFOs before accepting a new session. Never connect ZHA and Zigbee2MQTT concurrently.
- Add the OpenThread Border Router integration with `http://HOST:8081`. The server uses the already-created Ethernet netif, OpenThread's own task, shared NVS, and the existing ESPHome event loop. It does not create another Ethernet driver, Wi-Fi interface, or `app_main`.
- Thread initially has no generated demonstration network. Import/create the intended dataset through the REST client, then enable Thread. A stored active dataset is restored at boot. Keep HA and the device on an IPv6/multicast-capable trusted LAN; mDNS, Thread routing and Matter discovery require hardware acceptance testing.
- REST and Zigbee TCP have no authentication or transport encryption. Restrict them to the trusted automation network. REST can expose/change Thread credentials. Do not publish these ports to the Internet.

RF uses the existing native API commands, busy rejection/cooldown, RM433 decoder and MQTT payload implementation. This public target has **synthetic topics and no household button codes**. The legacy importer currently creates a separate Ethernet RF profile; it does not automatically migrate private configuration into this combined hub. Review and privately merge the needed substitutions and legacy sensors, retain secrets, then validate and compile the combined configuration again before any cutover.

## REST regression check

The test compiles the actual exported REST C handlers and JSON dataset parser, then drives a loopback HTTP adapter with `python-otbr-api` 3.0.0. It reproduces upstream's incorrect HTTP-200 response for an unknown URL, and verifies that the HTTP-404 patch lets the client send the correct field casing and preserve network name, channel and timestamp. This is an offline contract test, not an on-device HTTP or Thread routing test.

```sh
python3 -m venv .venv-otbr-test
.venv-otbr-test/bin/pip install -r firmware/low-power/requirements-test.txt
.venv-otbr-test/bin/python firmware/low-power/test_rest_contract.py \
  --prepared /tmp/radio-hub-build --idf /tmp/radio-hub-idf
```

A native C compiler (`clang`) is required. The exported unmodified REST source is preserved under `upstream-original/`; the patched source is under `firmware/low-power/generated/esp_ot_br_server/`. Only the REST C files are compiled; upstream's browser provisioning UI/filesystem and Wi-Fi provisioning are omitted.

## Flashing and acceptance

Flashing is a separate, deliberate step after electrical checks and private configuration. For H2, use `idf.py -C /tmp/radio-hub-h2 -p SERIAL_PORT flash`; its generated flasher arguments define offsets. For S3, edit the copied configuration/secrets and use `esphome run /tmp/radio-hub-build/firmware/low-power/hub.yaml --device SERIAL_PORT`. Both commands write hardware and must target the correct board. No tool in this repository executes them automatically.

Before moving existing networks, verify H2 Spinel/version handshake, stable NCP flow control, Z-Wave request/response on the external UART, REST dataset persistence across reboot, IPv6 routing/Matter pairing, BLE notifications, RF receive/transmit without self-echo, radar/BME readings, link recovery, and concurrent traffic. Measure power at the same AC/PoE boundary over representative operation; software compilation does not prove the target energy budget.

Primary references: [ESP Thread BR source](https://github.com/espressif/esp-thread-br/tree/29a2345e3f0c61bba9307f3daea5ed0c94388ed3), [ESP-IDF 5.5.5 source](https://github.com/espressif/esp-idf/tree/b774170ff46c393eeb5e495ea37936038d3f4f4f), [W5500 datasheet](https://docs.wiznet.io/img/products/w5500/W5500_ds_v110e.pdf), [ESPHome Ethernet](https://esphome.io/components/ethernet/), [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/).
