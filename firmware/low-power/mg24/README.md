# MGM240P Zigbee NCP — reproducible build for LP-P0

**The build and offline checks passed on 2026-10-17 on macOS arm64. The firmware has not yet been tested on a physical MGM240P.** The outputs include the Ember NCP application, a UART-XMODEM bootloader with CRC, a GBL3 application update, and a merged S37 for the initial SWD flash. This completes the software image build; startup, UART/CTS, pairing, power recovery, and radio interoperability still require hardware testing.

The exact order code is **MGM240PA22VNA3**, with SLC target **MGM240PA22VNA**. Do not substitute an arbitrary EFR32MG24 target: the module component includes its power/PA settings and built-in **39 MHz** HFXO. In the generated configuration, `SL_CLOCK_MANAGER_LFXO_EN=0` and the LF source is the internal LFRCO; an external 32.768 kHz crystal is not required.

## Pinned source and tools

- [Simplicity SDK v2025.6.3](https://github.com/SiliconLabs/simplicity_sdk/releases/tag/v2025.6.3), commit `b41bec3ff2485199c1a5a9995b3e649e118c1b8d`: Zigbee **8.2.3**, EZSP **18 / 0x12**. [Official release contents](https://docs.silabs.com/sisdk-release-notes/2025.6.3/sisdk-release-notes-overview/).
- SLC **6.0.15**, Java **21**, the separate Silicon Labs **Python adapter pack 3.10.1** with native JEP and Jinja (its internal manifest reports Python 3.10.5), Arm GNU Toolchain **12.2.Rel1** / GCC **12.2.1**, and Simplicity Commander **1.25.0 build 1995**. The completed build did not use IAR, a paid license, or Silicon Labs authentication.
- Application: SDK `protocol/zigbee/app/projects/ncp/zigbee_ncp_uart_hw/zigbee_ncp_uart_hw.slcp`; bootloader: `platform/bootloader/sample-apps/bootloader-uart-xmodem/bootloader-uart-xmodem.slcp`.
- [config.json](config.json) contains the target, upstream paths, and all modified macros; [dependencies-linux.json](dependencies-linux.json) contains direct official URLs, sizes, and SHA256 hashes for the Linux x86_64 archives. These five archives were actually downloaded and verified, totaling **993 384 273 bytes**. Execution of the tools must be confirmed separately on a Linux runner.

The bootstrap verifies the SHA256 of the downloaded SDK archive. With a manually supplied `--sdk`, the generator checks the actual `sdk_version` and `EZSP_PROTOCOL_VERSION`, but does not verify the Git commit of the entire unpacked tree: the report records `source_commit_verified=false` and lists the expected commit separately. The SDK and generated vendor sources are not included in the repository; they are downloaded separately under their own licenses. This directory stores configuration, scripts, and the [completed build report](build-evidence.json). The report hashes describe that macOS build and do not promise identical bytes on every host.

## Electrical interface contract

Both images use USART0, **115200, 8N1, hardware RTS/CTS**:

- PA05 / module pad 12 — NCP RX ← S3 GPIO17 TX.
- PA06 / pad 13 — NCP TX → S3 GPIO18 RX.
- PB01 / pad 5 — NCP CTS ← S3 GPIO16 RTS.
- PB00 / pad 6 — NCP RTS → S3 GPIO21 CTS.
- **PA00 / pad 7 — BOOT**, using only a service jumper/button to GND, normally pulled up through **10 kΩ to 3.3 V**. Holding it LOW during reset selects the UART-XMODEM bootloader. This signal does not consume an S3 GPIO.
- PA01 / pad 8 — SWCLK; PA02 / pad 9 — SWDIO; RESETn / pad 31 — reset; also connect GND and VTref. RESETn already has an internal pull-up to DVDD: the external service contact only grounds it; **do not add a pull-up to 3.3 V**.

The [MGM240P manufacturer datasheet](https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf) defines power, the remaining GND connections, and the RF keepout. Do not connect 5 V UART signals. USB-UART does not replace SWD for the initial flash of a blank module.

## Linux CI / local build

Requirements: Linux x86_64, Python 3 for this project's scripts, Java 21, `make`, `unzip`, `tar` with xz/bzip2 support, and the Commander runtime libraries. The bootstrap downloads only the pinned archives, checks their size/SHA256 before extraction, and requires a new directory. It neither flashes hardware nor installs anything system-wide. On a headless runner, you can set `QT_QPA_PLATFORM=offscreen`.

From the repository root:

```sh
python3 firmware/low-power/mg24/bootstrap_linux.py --output /tmp/mg24-tools
python3 firmware/low-power/mg24/generate.py \
  --sdk /tmp/mg24-tools/sdk \
  --slc /tmp/mg24-tools/tools/slc_cli/slc \
  --python-pack /tmp/mg24-tools/tools/python \
  --gcc /tmp/mg24-tools/tools/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi \
  --output /tmp/mg24-build
python3 firmware/low-power/mg24/build.py \
  --project /tmp/mg24-build \
  --gcc /tmp/mg24-tools/tools/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi \
  --commander /tmp/mg24-tools/tools/commander/commander
python3 -m unittest discover -s firmware/low-power/mg24 -p 'test_*.py'
```

`JAVA_HOME` must point to Java 21; pass `--java-home` to `generate.py` if needed. On macOS, install the same versions through the [public SLT CLI](https://docs.silabs.com/simplicity-installer-slt/latest/slt-getting-started-slt-cli/first-time-installation-setup), or use official archives for that platform; then supply absolute paths to SLC/GCC/Commander and point `--python-pack` to the installed vendor Python directory containing `apack.json` and `jep/`. This uses the same generator, not a different project.

SLC uses the native JEP adapter pack, not an arbitrary Python/Jinja installation from PATH. The original Linux CI lacked this separate package, causing every template generator to fail with `python script did not properly register a template generator`. The bootstrap now downloads the package with SHA256 verification; the required `--python-pack` checks the manifest and native JEP, and the generator passes `--tool-path` and `--ignore-slt`. This removes the implicit dependency on a global SLT installation.

SLC `--configuration` changes active macros but does not expand commented-out pin-tool placeholders. After generation, `generate.py` therefore explicitly sets each macro in the generated headers and requires exactly one match. Changes are marked; the SDK is not edited. `build.py` rechecks the active GPIO/USART/flow-control/clock macros before compilation. Regenerate with the same script into a new directory; otherwise, the pin tool can restore empty assignments.

`build.py` runs the standard `make release` for both projects. Commander performs the official bootloader post-build step (CRC), creates GBL3, merges the addressed S37 files, and unpacks the GBL again for verification. Checks cover S-record checksums, flash ranges, absence of overlaps, stack/reset vectors, exact byte preservation in the merged image, and the GBL round trip. The output includes `artifacts/build-report.json` with SHA256 hashes. Separate tests cover corrupted records, mismatches, and missing/duplicate macros.

## Outputs and programming procedure

[Completed build](build-evidence.json): NCP **224 852 bytes** of addressed data; bootloader with CRC **11 272 bytes**. The application starts at `0x08006000`; the bootloader starts at `0x08000000` and fits entirely within the reserved 24 KiB. `size` includes heap/stack reservations in BSS, so its total must not be presented as actual runtime RAM usage.

- `artifacts/ha-radio-hub-mg24-initial.s37` — bootloader with CRC + application, for the initial flash through a compatible SWD probe.
- `artifacts/ha-radio-hub-mg24-ncp.gbl` — application only, for subsequent UART-XMODEM updates; it does not replace a missing bootloader.
- `bootloader/artifact/bootloader-uart-xmodem-crc.s37` — standalone bootloader. Use the CRC version, not the intermediate `build/release/*.s37`.

On the bench, first check 3.3 V, common GND, SWD, and the exact model. The operator can then write the addressed initial S37 through Commander and check the result with the standard `verify` command; do not change debug-lock, OTP/eFuse, or security configuration. The scripts in this directory **never perform flash/erase operations**. After removing the BOOT jumper, reset the module, check the ASH reset/version response, and only then connect ZHA. For a service XMODEM update, close the Zigbee client, hold PA00 LOW during reset, and use the documented bootloader menu; upload support through our TCP bridge has not been implemented or tested separately.

The following commands were checked against `Commander1.25.0 --help`, but **have not been run on the device**. `PROBE_SERIAL` is the serial number of the chosen J-Link/Silicon Labs probe, not a USB-UART adapter. First perform only the identification read:

```sh
COMMANDER=/tmp/mg24-tools/tools/commander/commander
PROBE_SERIAL=REPLACE_WITH_ACTUAL_PROBE_SERIAL
"$COMMANDER" device info --serialno "$PROBE_SERIAL" --tif SWD
```

The generated header sets `PART_NUMBER="MGM240PA22VNA"`, flash `0x180000` (1536 KiB), and SRAM `0x40000` (256 KiB). Autodetection may report the underlying silicon rather than the module order code; compare the report with the markings/family and memory, and do not force an unknown `--device`. Only after this check, for a new test module:

```sh
"$COMMANDER" flash /tmp/mg24-build/artifacts/ha-radio-hub-mg24-initial.s37 --serialno "$PROBE_SERIAL" --tif SWD
"$COMMANDER" verify /tmp/mg24-build/artifacts/ha-radio-hub-mg24-initial.s37 --serialno "$PROBE_SERIAL" --tif SWD
```

The S37 already contains addresses. `--address`, `--masserase`, `--force`, and disabling verification are unnecessary here.

Do not erase the NVM of a running coordinator without a backup: this procedure is currently intended for a new test module. The GBL/bootloader are not signed with a secure-boot key; key provisioning and irreversible lock bits are outside this prototype's scope.

## Host compatibility — source review, not pairing

- **ZHA**: EZSP 18 was added in [bellows 0.49.0](https://github.com/zigpy/bellows/releases/tag/0.49.0). The checked [Home Assistant 2026.10.2](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/components/zha/manifest.json) version uses ZHA 2.3.1, which [pins bellows 1.1.0](https://github.com/zigpy/zha/blob/2.3.1/pyproject.toml). It contains an EZSP 18 handler.
- **Zigbee2MQTT**: [2.14.2](https://github.com/Koenkk/zigbee2mqtt/blob/2.14.2/package.json) uses zigbee-herdsman 10.10.0; the [official `ember` documentation](https://www.zigbee2mqtt.io/guide/adapters/emberznet.html) includes EmberZNet 8.2.x. Select **`adapter: ember`**, not the legacy `ezsp`.
- Only one active TCP bridge client on port 6638. Do not connect ZHA and Z2M simultaneously. The S3 UART implements baud rate/CTS/RTS; TCP does not carry USB-UART control signals.

Build references: [SLC usage](https://docs.silabs.com/simplicity-studio-5-users-guide/latest/ss-5-users-guide-tools-slc-cli/03-usage), [Commander offline convert](https://docs.silabs.com/simplicity-commander/latest/simplicity-commander-commands/convert-and-modify-file-commands), and the upstream `readme.md` files for both examples in the pinned SDK.
