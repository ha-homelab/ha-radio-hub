# H2 Quartet compilation probe

This directory preserves a **successful minimal component build**, not the Quartet gateway firmware. See [the architecture assessment](../../docs/h2-simplification.md).

`h2-ble-ethernet.yaml` is the exact compiled input: ESP32-H2, W5500 and ESPHome active Bluetooth proxy with three connection slots. Its pins are placeholders, not the Quartet wiring map. It contains no household credentials and was not flashed.

The build used ESPHome **2026.9.1**, ESP-IDF **5.5.5**, and a 4 MB H2 target. The compiler's board identifier is the standard H2 DevKit target; it does not qualify the physical Zero-M wiring.

```sh
esphome version
esphome config firmware/h2-quartet/h2-ble-ethernet.yaml
esphome compile firmware/h2-quartet/h2-ble-ethernet.yaml
```

Use the pinned ESPHome version in an isolated environment. No upload/run command is needed. Compilation downloads may use the usual ESPHome toolchain cache.

`build-evidence.json` records the exact input hash and resulting image hashes. Binaries and full machine-specific logs are not published. The app file is named `firmware.ota.bin` by the build system even though **no OTA service is configured** in this probe.

- Static RAM report: **106,302 / 258,000 bytes** (41.2%). This is not runtime free heap.
- Application binary: **1,061,120 bytes**.
- Excluded: Thread host/BR, Zigbee bridge, RF, radar, BME680, Z-Wave, encryption and OTA service.
- No board flashing, radio tests or power measurements occurred.

Do not deploy this unencrypted probe as the finished household hub. Its purpose is to establish a reproducible baseline before the local-BR and transport work.
