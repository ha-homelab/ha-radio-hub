# MC2 external-antenna firmware

MC2 is a separate electrical revision. It uses **ESP32-S3-DevKitC-1U-N8R8** for Ethernet/BLE and the host application, **Unexpected Maker TinyC6-U-01** for the Thread RCP, and **Seeed XIAO MG24** with its U.FL path enabled for Zigbee. All three 2.4 GHz radios have separate antennas. Neither the ceramic Nano-M nor the H2 image is an interchangeable substitution. The original MC1 profile and its evidence remain in `../module-carrier/`.

**Full offline builds passed; hardware remains untested.** The [S3 build evidence](build-evidence.json) records a 1,731,456-byte OTA image, two 3,932,160-byte OTA slots (2,200,704 bytes spare in each), and 163,795 bytes of static RAM. These are linker/image measurements, not runtime memory peaks. The [C6 evidence](c6-build-evidence.json) records a 235,456-byte RCP application and the required GPIO8 strap contract. [Host tests](test-results.json) passed 23 MC2 checks, 62 shared MC1 regressions and 13 MG24 recipe checks. Both MG24 antenna modes were built; the new onboard application/GBL is byte-identical to the original onboard application/GBL.

The S3 and C6 factory external-antenna modules have fixed RF paths and need no GPIO antenna selection. MG24 does: build the [shared XIAO recipe](../module-carrier/zigbee/README.md) with **`--antenna external`**. The generated `mc1-xiao-mg24-external-*` basename identifies that shared board recipe; it is also the required MC2 Zigbee image. PB04 and PB05 are both high before its radio stack starts. Attach all intended antennas before operating the radios. Firmware compilation does not establish coverage, isolation or antenna suitability; follow the [RF acceptance procedure](../../docs/rf-commissioning.md).

## Pin and memory contract

[pin-plan.json](pin-plan.json) is copied from the MC2 CAD contract and checked for parity by the host tests. The changes from MC1 are:

- S3 **GPIO15/TX → TinyC6 GPIO17/RX (header 12)**, **GPIO16/RX ← TinyC6 GPIO16/TX (header 13)**. The repeated number 16 belongs to different MCUs.
- S3 **GPIO47 → TinyC6 EN/RST (header 15)** and **GPIO39 → TinyC6 GPIO9/BOOT (header 11)**, both open-drain. TinyC6 has native USB, so no USB-UART bridge resistor removal is needed.
- **C6 GPIO8 (header 10) must have the carrier's 10 kΩ pull-up to C6-local 3.3 V (header 4).** GPIO8 floats at reset and must be high while GPIO9 is low for ROM download. This is required for both local and Ethernet recovery; firmware cannot correct a missing reset-time strap. Do not tie the C6 regulator output to another board's 3.3 V rail. See the [ESP32-C6 datasheet, Boot Configurations](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf).
- LD2450 uses S3 **TX8/RX40**. GPIO38/48 are reserved for the S3 DevKit's revision-dependent RGB LED; GPIO43/44 for its USB-UART bridge; GPIO35/36/37 for octal PSRAM.
- S3 has **8 MB flash and 8 MB octal PSRAM**. TinyC6 has **8 MB flash**. The other SPI, Zigbee UART and I²C assignments remain in the contract, including all 21 application GPIO.

The ESPHome node name remains `module-carrier-hub`; retain only one node with that identity in a deployment. CC1101 RF actions/topics, LD2450 controls, BME680, three active BLE slots, Z-Wave transport, four-wire Zigbee TCP6638, local Thread Border Router and REST8081 are retained. The WK2132 driver and Thread guard implementation are shared with MC1. MC2 health entities/actions explicitly say C6. The S3 native USB console remains available for recovery.

MC1's 16 MB factory partition table must **not** be used on the 8 MB DevKit. Save the Thread dataset and deployment credentials before changing boards. Initial MC2 installation uses the generated full factory image and matching partition table; an app-only OTA cannot change a partition table. Subsequent OTA assumes that verified MC2 layout. No live network migration or device programming is performed by the build tools.

## Reproduce the S3 build

Use ESPHome **2026.9.1**, ESP-IDF **5.5.5**, and an empty output directory. Preparation copies sources, creates disposable credentials and retrieves only the pinned REST component.

```sh
python3 firmware/external-antenna/validate.py /tmp/mc2-s3-build \
  --esphome /path/to/pinned/esphome --compile
RF_CPP_SANITIZERS=1 python3 -m unittest discover \
  -s firmware/external-antenna/tests -v
RF_CPP_SANITIZERS=1 python3 -m unittest discover \
  -s firmware/module-carrier/tests -v
```

The generated build report checks the real GPIO configuration, shared SPI ordering, all BLE slots, both OTA slots and image margins, and the open-drain recovery implementation. It records image and source hashes. Runtime heap peaks, electrical behavior and RF range require assembled hardware.

## Reproduce the C6 RCP

Use the **same ESP-IDF 5.5.5 SDK** as the S3 host, with its C6 tools installed. The prepared SDK example runs Spinel UART at **460800 8N1, no flow control**. Its application starts at **0x10000**, and the verified factory app partition is **1 MiB**.

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

The host probes the RCP before starting Thread, quarantines incompatible/unresponsive firmware, retains the other protocols, and offers an explicit retry. A fatal post-startup Thread fault can cause one full host restart before quarantine. The Thread dataset stays in S3 NVS; the C6 RCP is not its owner. S3 OTA safe mode and native USB recovery remain available. These software mechanisms and offline checks do not replace power, concurrent-load, restore and whole-house RF qualification.
