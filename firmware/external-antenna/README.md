# MC2-D classic ESP32 external-antenna firmware

MC2-D retains the MC2-B host, **ESP32-DevKitC-VIE**, with the **ESP32-WROVER-IE** module (8 MB flash, 8 MB quad PSRAM and a factory external antenna connector). This classic ESP32 host differs electrically from the earlier MC2-A ESP32-S3: **it is not a drop-in module swap or an OTA upgrade for an S3**. The current carrier accepts two 19-pin rows; MC2-A accepted two 22-pin rows. The S3 design remains in Git history; the original MC1 profile remains in `../module-carrier/`.

MC2-D replaces TinyC6[D] with **Seeed Studio XIAO ESP32C6, pre-soldered-header SKU 102010636**. The ROM UART GPIOs stay the same, but its 4 MB flash and GPIO-controlled external antenna require the MC2-D C6 firmware below. The smaller XIAO footprint requires the MC2-D carrier. Its factory headers do not expose EN/BOOT: two fine insulated wires from bottom test pads to carrier J10 preserve automatic reset and Ethernet recovery. The **Seeed XIAO MG24** Zigbee NCP is unchanged. All three 2.4 GHz radios retain separate antennas. CC1101 RF actions/topics, LD2450 controls, BME680, three active BLE connections, Z-Wave transport, four-wire Zigbee TCP6638 and local Thread Border Router REST8081 remain enabled. No additional Linux border router is introduced.

The [host build evidence](build-evidence.json) records the compiled image, both OTA slots, DRAM/IRAM usage and actual ESP32 image header. **Hardware remains untested.** Static linker headroom does not establish runtime heap capacity or concurrent protocol reliability. Before migration, measure minimum internal heap, largest free block, free PSRAM and loop time with all three BLE connections, Thread traffic, Zigbee, Z-Wave and RF activity running together. The [C6 evidence](c6-build-evidence.json) and [host tests](test-results.json) remain separately identified.

The ESP32-WROVER-IE has a fixed external RF path. XIAO ESP32C6 selects its external U.FL path with **GPIO3 LOW (switch power enabled) and GPIO14 HIGH (external path)**. These are C6-local pins, not host pins. The C6 application sets the GPIOs, waits 100 ms and verifies their input levels before starting the radio on every boot. On a GPIO error or mismatch it leaves Thread stopped and emits an error over native USB Serial/JTAG; it does not silently start with an unconfirmed antenna selection. GPIO readback does not verify the RF switch or attached antenna. Follow the [MC2-D XIAO MG24 programming guide](../../docs/mc2-zigbee.md) to build and program its **`--antenna external`** image; PB04 and PB05 must be high before the radio stack starts. That guide uses the shared recipe with the current MC2-D connections and output selection. Attach all antennas before operating the radios. Follow the [RF acceptance procedure](../../docs/rf-commissioning.md).

## Pin and memory contract

[pin-plan.json](pin-plan.json) is copied from the MC2-D CAD contract and checked for parity by host tests.

- Host **GPIO26/TX → XIAO C6 D7/GPIO17/RX (header 8)**; **GPIO36/RX ← XIAO C6 D6/GPIO16/TX (header 7)**.
- Host **GPIO27 → J10.1 → C6 EN bottom test pad TP8**; **GPIO15 → J10.2 → C6 BOOT/GPIO9 bottom test pad TP2**, both open-drain. XIAO has native USB and no USB-UART bridge fighting its ROM RX17. Identify the labelled pads against the [MC2-D wiring guide](../../hardware/external-antenna/index.html); attach these two wires before soldering the factory headers into the carrier. They are required for automated recovery, even when buying pre-soldered headers.
- **C6 GPIO8 is already pulled high by the XIAO's onboard 5.1 kΩ resistor to its local 3.3 V.** No external R3 or temporary pull-up is required. ROM download needs GPIO8 high while GPIO9 is low. Never tie the C6 regulator output to another 3.3 V rail.
- LD2450 uses host **TX23/RX18** on UART0. UART1 belongs to MG24; UART2 belongs to C6. The host's physical GPIO1/3 USB-UART connection stays unused by peripherals, preserving ROM flashing.
- Host serial logging is disabled (`UART0`, baud 0), and the ESP-IDF console is explicitly disabled. Logs remain available over the encrypted ESPHome API. The classic ESP32 has no native USB Serial/JTAG peripheral.
- SPI2 uses **SCK12, MOSI2, MISO19**, shared by W5500 and CC1101 at the configured bus speeds. GPIO12 and GPIO2 require the carrier's **10 kΩ pull-downs**. GPIO12 must be low at reset for the WROVER-IE's 3.3 V flash/PSRAM supply. GPIO5 is W5500 CS; GPIO15 is C6 BOOT. Do not change reset-time pulls casually.
- GPIO34/35/36/39 are input-only and have no internal pull resistors. GPIO6–11 serve flash; GPIO16/17 serve PSRAM. None of those memory pins may be repurposed.
- The host runs at **160 MHz**, with **quad PSRAM at 40 MHz** to avoid the old chip's 80 MHz SPI-host contention. The image requires **ESP32 ECO V3 or later**, matching WROVER-IE. Despite 8 MB installed PSRAM, the classic ESP32 exposes at most **4 MB directly mapped PSRAM**; this profile does not use bank-switching to increase the ordinary heap. See [Espressif external RAM documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32/api-guides/external-ram.html).

The new ESPHome node name is **`mc2-classic-hub`**. Back up Thread credentials, Zigbee/Z-Wave network data and deployment secrets before moving radios. Perform the initial full factory flash through the DevKitC's USB-UART connection, with the matching MC2-D partition table. Never send this ESP32 image to an S3. An app-only OTA cannot replace a factory partition table. Later OTA is permitted only for the same confirmed MC2-D host and layout. Build tools never flash hardware or change Home Assistant.

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
   python3 firmware/external-antenna/prepare.py "$HOME/ha-radio-hub-private/mc2d"
   ```

2. Edit `~/ha-radio-hub-private/mc2d/firmware/external-antenna/secrets.yaml` to set the deployment's encrypted ESPHome API key, OTA password and real MQTT broker/username/password. Edit the copied `hub.yaml` substitutions to set the intended `rf_received_topic`, `rf_raw_topic`, `rf_transmit_result_topic` and `rf_source`. Add the private `rm433_button_1_code` through `rm433_button_8_code` overrides if learned-button events are needed. Use the existing Home Assistant topic/code contract when retaining those automations. Keep the board, memory, GPIO and node-name settings unchanged.

3. Before soldering the VIE into the carrier, attach its external antenna and connect its **Micro-B USB** port to the computer with a data cable. Power the loose board from USB only; disconnect PoE and other external power. Select the serial port belonging to this VIE, not the XIAO C6 or another ESP board.

4. Compile the edited private configuration again and perform its first full USB-UART installation. Replace the example serial-port placeholder with the port actually assigned to the VIE:

   ```sh
   private_config="$HOME/ha-radio-hub-private/mc2d/firmware/external-antenna/hub.yaml"
   /path/to/pinned/esphome run "$private_config" --device /dev/cu.REPLACE_WITH_VIE_PORT
   ```

   `run` builds the private configuration and uploads the matching bootloader, partition table and application over USB-UART. If automatic bootloader entry fails, hold **BOOT**, press and release **EN**, then release **BOOT** after the connection begins. Runtime serial logs are disabled to preserve UART0 for LD2450; use encrypted API logs after Ethernet is connected.

5. Disconnect USB before connecting the assembled carrier's PoE-derived supply. Complete power, peripheral and concurrent-load commissioning before switching Home Assistant to `mc2-classic-hub`. The initial USB operation and later Home Assistant migration are separate from the offline validation performed in this repository.

## Reproduce the C6 RCP

Only **XIAO ESP32C6 / SKU 102010636 (factory headers)** is supported by the current hardware recipe. The earlier TinyC6[D] and TinyC6-U-01 images are incompatible. Renaming an old image cannot bypass the updater: it checks the ESP32-C6 chip ID, **4 MB** flash header, application descriptor (`mc2d-xiaoc6-ext-v1`), and matching MC2-D board/antenna metadata. The OpenThread platform string is `MC2-D 102010636 external antenna`. The user LED and battery charger are unused; do not connect a battery in this PoE-powered design.

The GPIO assignments and power-up sequence follow the [manufacturer's hardware overview](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#hardware-overview) and [January 2026 schematic](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH_260114.pdf). No I²C expander or extra antenna-control wires are needed. The old FXL6408 driver is removed. The RF path still needs physical commissioning with the intended antenna attached.

Use the **same ESP-IDF 5.5.5 SDK** as the classic ESP32 host, with its C6 tools installed. Only native USB Serial/JTAG carries error messages; runtime logs never share the radio UART. The prepared SDK example runs Spinel UART at **460800 8N1, no flow control**. Its application starts at **0x10000**, and the verified factory app partition is **1 MiB**.

```sh
python3 firmware/external-antenna/prepare_c6.py /tmp/mc2-c6-build \
  --idf /path/to/esp-idf-5.5.5
cd /tmp/mc2-c6-build
idf.py set-target esp32c6
idf.py build
# Run from the repository root:
python3 firmware/external-antenna/verify_c6.py /tmp/mc2-c6-build > /tmp/mc2-c6-build/build-report.json
```

Perform initial C6 factory programming through its native USB **before soldering**, using the bootloader, partition table and app from this build (`idf.py flash` in its prepared directory). Its onboard GPIO8 pull-up is present while the board is loose. Fit the EN/BOOT service leads before carrier assembly; leave them insulated and disconnected while doing the standalone USB flash. Hold BOOT while resetting if ROM download mode is needed. The command is an explicit physical programming operation and is not part of validation. After assembly use the [checked Ethernet update procedure](updates/README.md). A C6 application cannot be flashed to H2 or vice versa.

## Preserved recovery behavior

The host probes the RCP before starting Thread, quarantines incompatible/unresponsive firmware, retains the other protocols, and offers an explicit retry. A fatal post-startup Thread fault can cause one full host restart before quarantine. The Thread dataset stays in host NVS; the C6 RCP is not its owner. Host OTA safe mode and the DevKitC USB-UART bootloader remain available; the classic ESP32 has no native USB console. These software mechanisms and offline checks do not replace power, concurrent-load, restore and whole-house RF qualification.
