# MC2-B classic ESP32 external-antenna firmware

MC2-B uses **ESP32-DevKitC-VIE**, with the **ESP32-WROVER-IE** module (8 MB flash, 8 MB quad PSRAM and a factory external antenna connector). It replaces the previous MC2-A ESP32-S3 host. This is an electrical and firmware revision, **not a drop-in module swap or an OTA upgrade for an S3**. The current carrier accepts two 19-pin rows; MC2-A accepted two 22-pin rows. The S3 design remains in Git history; the original MC1 profile remains in `../module-carrier/`.

The **Unexpected Maker TinyC6-U-01** Thread RCP and **Seeed XIAO MG24** Zigbee NCP are unchanged. All three 2.4 GHz radios retain separate antennas. CC1101 RF actions/topics, LD2450 controls, BME680, three active BLE connections, Z-Wave transport, four-wire Zigbee TCP6638 and local Thread Border Router REST8081 remain enabled. No additional Linux border router is introduced.

The [host build evidence](build-evidence.json) records the compiled image, both OTA slots, DRAM/IRAM usage and actual ESP32 image header. **Hardware remains untested.** Static linker headroom does not establish runtime heap capacity or concurrent protocol reliability. Before migration, measure minimum internal heap, largest free block, free PSRAM and loop time with all three BLE connections, Thread traffic, Zigbee, Z-Wave and RF activity running together. The [C6 evidence](c6-build-evidence.json) and [host tests](test-results.json) remain separately identified.

The ESP32-WROVER-IE and C6 have fixed external RF paths. MG24 requires the [shared XIAO recipe](../module-carrier/zigbee/README.md) built with **`--antenna external`**; PB04 and PB05 must be high before the radio stack starts. Attach all antennas before operating the radios. Follow the [RF acceptance procedure](../../docs/rf-commissioning.md).

## Pin and memory contract

[pin-plan.json](pin-plan.json) is copied from the MC2-B CAD contract and checked for parity by host tests.

- Host **GPIO26/TX → TinyC6 GPIO17/RX (header 12)**; **GPIO36/RX ← TinyC6 GPIO16/TX (header 13)**.
- Host **GPIO27 → C6 EN/RST (header 15)**; **GPIO15 → C6 GPIO9/BOOT (header 11)**, both open-drain. TinyC6 has native USB and no USB-UART bridge output fighting its ROM RX17.
- **C6 GPIO8 (header 10) requires the carrier's 10 kΩ pull-up to C6-local 3.3 V (header 4).** ROM download needs GPIO8 high while GPIO9 is low. Never tie the C6 regulator output to another 3.3 V rail.
- LD2450 uses host **TX23/RX18** on UART0. UART1 belongs to MG24; UART2 belongs to C6. The host's physical GPIO1/3 USB-UART connection stays unused by peripherals, preserving ROM flashing.
- Host serial logging is disabled (`UART0`, baud 0), and the ESP-IDF console is explicitly disabled. Logs remain available over the encrypted ESPHome API. The classic ESP32 has no native USB Serial/JTAG peripheral.
- SPI2 uses **SCK12, MOSI2, MISO19**, shared by W5500 and CC1101 at the configured bus speeds. GPIO12 and GPIO2 require the carrier's **10 kΩ pull-downs**. GPIO12 must be low at reset for the WROVER-IE's 3.3 V flash/PSRAM supply. GPIO5 is W5500 CS; GPIO15 is C6 BOOT. Do not change reset-time pulls casually.
- GPIO34/35/36/39 are input-only and have no internal pull resistors. GPIO6–11 serve flash; GPIO16/17 serve PSRAM. None of those memory pins may be repurposed.
- The host runs at **160 MHz**, with **quad PSRAM at 40 MHz** to avoid the old chip's 80 MHz SPI-host contention. The image requires **ESP32 ECO V3 or later**, matching WROVER-IE. Despite 8 MB installed PSRAM, the classic ESP32 exposes at most **4 MB directly mapped PSRAM**; this profile does not use bank-switching to increase the ordinary heap. See [Espressif external RAM documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32/api-guides/external-ram.html).

The new ESPHome node name is **`mc2-classic-hub`**. Back up Thread credentials, Zigbee/Z-Wave network data and deployment secrets before moving radios. Perform the initial full factory flash through the DevKitC's USB-UART connection, with the matching MC2-B partition table. Never send this ESP32 image to an S3. An app-only OTA cannot replace a factory partition table. Later OTA is permitted only for the same confirmed MC2-B host and layout. Build tools never flash hardware or change Home Assistant.

## Reproduce the host build

Use ESPHome **2026.9.1**, ESP-IDF **5.5.5**, and an empty output directory. Preparation copies sources, creates disposable credentials and retrieves only the pinned REST component.

```sh
python3 firmware/external-antenna/validate.py /tmp/mc2-classic-build \
  --esphome /path/to/pinned/esphome --compile
RF_CPP_SANITIZERS=1 python3 -m unittest discover \
  -s firmware/external-antenna/tests -v
RF_CPP_SANITIZERS=1 python3 -m unittest discover \
  -s firmware/module-carrier/tests -v
```

The generated report checks actual GPIO calls, the compiled ESP32 chip ID/minimum revision, disabled console, UART ownership source assumptions, SPI ordering, all BLE slots, both OTA slots and open-drain recovery. It records image/source hashes and DRAM/IRAM linker headroom. `mc2-classic-hub.bin` is an application image; `firmware.factory.bin` includes the initial installation layout. **The validation build contains disposable credentials and build-only RF topics: do not deploy its images.** Make a private deployment build as described below. Runtime heap peaks, electrical behavior and RF range require assembled hardware.

## Initial host programming with private configuration

Both `prepare.py` and `validate.py` generate random, disposable API/MQTT/OTA credentials for offline checks. The copied profile also uses the documentation-only MQTT broker `192.0.2.1`, `build-only/rf/*` topics and disabled learned-button codes. A successfully compiled proof image is not a configured Home Assistant deployment.

1. Prepare a new private directory outside the repository. Keep it private and do not commit its `secrets.yaml` or resulting binaries:

   ```sh
   python3 firmware/external-antenna/prepare.py "$HOME/ha-radio-hub-private/mc2b"
   ```

2. Edit `~/ha-radio-hub-private/mc2b/firmware/external-antenna/secrets.yaml` to set the deployment's encrypted ESPHome API key, OTA password and real MQTT broker/username/password. Edit the copied `hub.yaml` substitutions to set the intended `rf_received_topic`, `rf_raw_topic`, `rf_transmit_result_topic` and `rf_source`. Add the private `rm433_button_1_code` through `rm433_button_8_code` overrides if learned-button events are needed. Use the existing Home Assistant topic/code contract when retaining those automations. Keep the board, memory, GPIO and node-name settings unchanged.

3. Before soldering the VIE into the carrier, attach its external antenna and connect its **Micro-B USB** port to the computer with a data cable. Power the loose board from USB only; disconnect PoE and other external power. Select the serial port belonging to this VIE, not the TinyC6 or another ESP board.

4. Compile the edited private configuration again and perform its first full USB-UART installation. Replace the example serial-port placeholder with the port actually assigned to the VIE:

   ```sh
   private_config="$HOME/ha-radio-hub-private/mc2b/firmware/external-antenna/hub.yaml"
   /path/to/pinned/esphome run "$private_config" --device /dev/cu.REPLACE_WITH_VIE_PORT
   ```

   `run` builds the private configuration and uploads the matching bootloader, partition table and application over USB-UART. If automatic bootloader entry fails, hold **BOOT**, press and release **EN**, then release **BOOT** after the connection begins. Runtime serial logs are disabled to preserve UART0 for LD2450; use encrypted API logs after Ethernet is connected.

5. Disconnect USB before connecting the assembled carrier's PoE-derived supply. Complete power, peripheral and concurrent-load commissioning before switching Home Assistant to `mc2-classic-hub`. The initial USB operation and later Home Assistant migration are separate from the offline validation performed in this repository.

## Reproduce the C6 RCP

Use the **same ESP-IDF 5.5.5 SDK** as the classic ESP32 host, with its C6 tools installed. The prepared SDK example runs Spinel UART at **460800 8N1, no flow control**. Its application starts at **0x10000**, and the verified factory app partition is **1 MiB**.

```sh
python3 firmware/external-antenna/prepare_c6.py /tmp/mc2-c6-build \
  --idf /path/to/esp-idf-5.5.5
cd /tmp/mc2-c6-build
idf.py set-target esp32c6
idf.py build
# Run from the repository root:
python3 firmware/external-antenna/verify_c6.py /tmp/mc2-c6-build
```

Perform initial C6 factory programming through its native USB **before soldering**, using the bootloader, partition table and app from this build (`idf.py flash` in its prepared directory). While the board is loose, temporarily fit the same 10 kΩ pull-up from GPIO8/header 10 to its local 3.3 V/header 4, since carrier R3 is not connected yet. Hold BOOT while resetting if ROM download mode is needed. The command is an explicit physical programming operation and is not part of validation. After assembly use the [checked Ethernet update procedure](updates/README.md). A C6 application cannot be flashed to H2 or vice versa.

## Preserved recovery behavior

The host probes the RCP before starting Thread, quarantines incompatible/unresponsive firmware, retains the other protocols, and offers an explicit retry. A fatal post-startup Thread fault can cause one full host restart before quarantine. The Thread dataset stays in host NVS; the C6 RCP is not its owner. Host OTA safe mode and the DevKitC USB-UART bootloader remain available; the classic ESP32 has no native USB console. These software mechanisms and offline checks do not replace power, concurrent-load, restore and whole-house RF qualification.
