# Compact S3 full-firmware build proof

The selected study target is **Waveshare ESP32-S3-Nano-M: 16 MB flash, 8 MB octal PSRAM, 21 application GPIO, shared W5500/CC1101 SPI2**. The comparison target is **LOLIN S3 Mini v1.0.0: 4 MB flash, 2 MB quad PSRAM, 24 application GPIO, separate SPI2/SPI3**. Neither configuration has been flashed or tested on a physical carrier.

These scripts prepare the entire existing MC1 application in a new temporary directory. They retain local Thread border routing and its REST API, three active BLE proxy connections, four-wire Ember transport, Z-Wave through the checked WK2132 driver, radar controls, BME680, native RF receive/transmit, the existing MQTT schemas, encrypted ESPHome API, OTA and native USB logging. The active carrier firmware is not edited.

## Verified builds — 2026-10-17

Both complete builds and their generated-code/SDK checks passed with ESPHome 2026.9.1, ESP-IDF 5.5.5 and GCC 14.2.0. No firmware was uploaded and no installed SDK source was patched.

**Nano:** OTA image **1,717,232 bytes**, two application slots of **8,126,464 bytes each**, leaving **6,409,232 bytes per slot**. Static linked RAM is **161,579 bytes**; this is not peak runtime memory. Full artifact hashes, resolved partition offsets and source checks are in [build-evidence-nano.json](build-evidence-nano.json).

**Mini:** OTA image **1,714,976 bytes**, two application slots of **1,835,008 bytes each**, leaving **120,032 bytes per slot**. Static linked RAM is **159,259 bytes**. The smaller image does not prove that 2 MB PSRAM is enough under maximum simultaneous load. Evidence is in [build-evidence-mini.json](build-evidence-mini.json).

All **14 Nano mutation checks** passed. These results establish a concrete full-firmware build for the compact host, while electrical, radio and simultaneous-load acceptance remain unperformed.

## Reproduce

Use Python supported by ESPHome 2026.9.1 and an ordinary C/C++ build environment. From the repository root:

```sh
python3 -m venv /tmp/mc1-compact-build-venv
/tmp/mc1-compact-build-venv/bin/pip install esphome==2026.9.1
/tmp/mc1-compact-build-venv/bin/python hardware/module-carrier/studies/compact-s3/firmware/prepare.py /tmp/mc1-nano-proof --board nano
/tmp/mc1-compact-build-venv/bin/esphome -s build_jobs 4 compile /tmp/mc1-nano-proof/firmware/module-carrier/hub.yaml
/tmp/mc1-compact-build-venv/bin/python hardware/module-carrier/studies/compact-s3/firmware/verify.py /tmp/mc1-nano-proof/firmware/module-carrier/hub.yaml --board nano --output /tmp/mc1-nano-proof/build-evidence.json
/tmp/mc1-compact-build-venv/bin/python hardware/module-carrier/studies/compact-s3/firmware/test_verify.py /tmp/mc1-nano-proof/firmware/module-carrier/.esphome/build/compact-s3-nano-hub
```

The output directory must not already exist. The optional `-s build_jobs 4` override changes only build parallelism; omit it for the default two workers. Preparation fetches the pinned `esp-thread-br` commit `29a2345e3f0c61bba9307f3daea5ed0c94388ed3`; optionally pass `--upstream /path/to/existing/esp-thread-br` containing that commit. ESPHome installs its pinned ESP-IDF 5.5.5 toolchain in its normal cache. No manual cache patch is needed. The generic `esp32-s3-devkitc-1` build descriptor is used for the Nano's S3 SoC; explicit flash, PSRAM and GPIO settings define the actual board contract.

For the Mini comparison, use a new output directory, `--board mini` in both preparation and verification, and the generated build name `compact-s3-mini-hub`. Omit the final `test_verify.py` command: its mutation suite is specifically for the Nano shared-SPI contract. `verify.py --board mini` checks the Mini's generated configuration and artifacts. Do not put the Nano pin map on the Mini or the Mini's GPIO33–37 assignments on an octal-PSRAM module.

Preparation generates disposable build-only credentials. Consequently binary hashes identify this recorded build; new builds are not expected to be byte-identical. No production secret is read and no upload command is run. Firmware images stay in the temporary output directory and are not committed.

## Verification scope

`verify.py` checks the **generated C++**, not just the requested YAML: each assigned GPIO, bus parent, clock/baud rate, BLE slot count, serial controller ownership and open-drain RF output. It verifies the required SDK IPv6/Thread/PSRAM options, compares the copied runtime C/C++ files to the active implementation, and checks that the final OTA image fits both generated app partitions. It also records the artifact sizes and SHA-256 hashes.

For Nano, the verifier checks the pinned startup-order and arbitration source assumptions and rejects any generated call to runtime CC1101 `reset()`/`configure()` or a setup-priority override. The original CC1101 reset sequence is not patched: it runs at DATA priority 600 before Ethernet priority 250; SPI setup is priority 1000. Ordinary operations use the IDF bus lock. A future runtime reset feature requires a new implementation and validation, not merely disabling this guard.

The [mutation checks](test-results.json) cover incorrect pins/bus assignment, loss of open-drain RF output, loss of IPv6 forwarding, wrong PSRAM mode, extra native UART ownership, unsafe runtime reset/reconfiguration, and missing or undersized OTA partitions.

Compilation cannot prove available runtime heap, radio performance, electrical levels, link throughput or reset behavior. Hardware acceptance remains: power/USB service validation; cold/warm S3 and H2 resets; concurrent Ethernet and RF receive/transmit; IPv6/multicast/Thread commissioning; three BLE connections; Zigbee flow control; Z-Wave and radar simultaneous load; minimum internal/external heap and stack margins; and an OTA update/recovery cycle. Mini additionally needs qualification of its reduced 2 MB PSRAM capacity and small OTA growth margin.

The [selected pin plan](../pin-plan.json), [Mini alternative](../pin-plan-mini.json) and [firmware review](../firmware-review.md) describe the physical and architectural boundaries.
