# Updating the assembled MC1 through Ethernet

The assembled carrier can perform normal updates without inserting any module USB cable. The S3 uses its existing ESPHome OTA service. The H2 uses a temporarily enabled host UART bridge to its factory ROM loader. The MG24 uses its existing four-wire Zigbee bridge and Gecko UART bootloader. These paths have compiled/source and offline transport validation; **no physical radio was flashed or recovery-tested in this work**.

## Required initial assembly

Before soldering the modules into the carrier:

1. Install the current complete 16 MB S3 factory image and real deployment credentials. An old 8 MB partition table is not migrated by an application-only OTA update.
2. Install the H2 bootloader, partition table and current RCP application built by `../prepare_h2.py`. Its application and ROM UART both use **H2 RX23/TX24**. The former RX4/TX5 build is incompatible with this carrier revision.
3. On the verified **ESP32-H2-DevKitM-1 schematic v1.3**, remove **R7, 470 ohms**, which connects the onboard CP2102N transmitter to H2 GPIO23. Leave R9 intact. The USB bridge is powered by the board's 3.3 V rail even without a USB cable; unplugging USB does not isolate its TX output. Verify the actual board revision and continuity against the [official schematic](https://dl.espressif.com/dl/schematics/esp32-h2-devkitm-1_v1.3_schematics.pdf) before rework. The current carrier connects S3 TX43 to H2 RX23 and S3 RX44 to H2 TX24; EN47 and BOOT48 retain open-drain control. Native H2 USB remains a preassembly/emergency path; the CP2102N serial-programming TX path is deliberately disconnected.
4. Install the XIAO MG24 **combined initial image**, including its Gecko bootloader, from `../zigbee`. Both NCP and bootloader use PC06/PC07/PC04/PC05 at115200, hardware RTS/CTS. Keep the local PC00 recovery jumper available; no host GPIO controls XIAO nRESET.
5. Verify a complete update and interrupted-update recovery on a test assembly before making its USB connectors inaccessible. Measure power rails and UART levels, then exercise normal radio traffic. A compiled image is not a substitute for that check.

The H2 pin/loader distinction is established by [Espressif's H2 board pin table](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html#header-block) and [IDF5.5.5 UART definitions](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/soc/esp32h2/include/soc/uart_pins.h). Espressif's own [RCP updater](https://github.com/espressif/esp-thread-br/blob/29a2345e3f0c61bba9307f3daea5ed0c94388ed3/components/esp_rcp_update/src/esp_rcp_update.c) likewise uses a ROM serial loader; merely calling it would not have made the former RX4/TX5 wiring flashable.

## Host tools and offline plan

Use Python3.12 or later in a dedicated virtual environment:

```sh
python3 -m venv /tmp/mc1-updater
/tmp/mc1-updater/bin/python -m pip install -r firmware/module-carrier/updates/requirements.txt
```

The wrapper checks the artifact's size/SHA256 against its matching build report, and checks the board/UART/partition contract before any network operation. It rejects initial HEX/S37 images for MG24 and only writes the H2 application at0x10000. A matching report establishes what the supplied build is; it does not read back the entire installed partition table. The correct initial installation remains a prerequisite.

Every invocation defaults to an **offline plan**, even with a real host address. Add `--execute` only when deliberately performing the described update. Do not use build-only placeholder credentials.

## S3 OTA

Use the existing ESPHome OTA workflow with the current deployment YAML and its existing OTA password. This updates the S3 application; it does not flash either radio. Save the Thread dataset and coordinator backup before changing software. Preserve the installed16MB partition layout. Network loss or a corrupt S3 bootloader/partition table cannot be repaired by either subordinate radio: neither has a host-reset/programming connection back to the S3.

## H2 ROM UART update

Generate a new report from the completed H2 build:

```sh
python3 firmware/module-carrier/verify_h2.py /path/to/h2-build > /path/to/h2-report.json
/tmp/mc1-updater/bin/python firmware/module-carrier/updates/update.py h2 \
  --host 192.0.2.10 --image /path/to/h2-build/build/esp_ot_rcp.bin \
  --report /path/to/h2-report.json
```

For deliberate execution, make the existing API encryption key available as `MC1_API_KEY` through your normal local secret mechanism, then repeat the command with `--execute --mac aa:bb:cc:dd:ee:ff`, using the actual ESPHome device/base MAC from API device information (it can differ from the W5500 Ethernet MAC). The wrapper checks the encrypted API peer's name and MAC. It does not discover or select a random device.

The update sequence is:

1. Persist the existing Thread maintenance latch, restart the whole hub once, reconnect, and require `Thread State=maintenance` plus `Thread Guard Durable=on`.
2. Generate a fresh128-bit token and send it over the encrypted ESPHome API using `arm_h2_uart_update`. The endpoint on TCP6639 exists only during the armed interval; normal operation has no listener there.
3. Authenticate the one-time TCP session, take UART2 at115200, and pulse H2 BOOT/EN into ROM download mode. The endpoint is a UART byte transport, not an independent flasher.
4. Run pinned esptool5.3.1 through a loopback-only tunnel. It identifies the H2, writes only the supplied application and verifies the written data. The tool uses `--before no-reset --after no-reset`; GPIO control belongs to the S3. It never writes eFuses, erases the whole chip, or replaces bootloader/partition/NVS data.
5. Close the bridge, release BOOT and reset H2, retaining maintenance. Only after esptool succeeds, explicitly retry Thread through the existing API, restarting the hub once more. Require successful RCP preflight/startup; joining/routing the intended network is a separate functional check.

Arming requires durable maintenance after reboot, no launched OpenThread task, Ethernet and an unused updater. There are at most four authentication attempts, five seconds per handshake, sixty seconds total waiting, ten minutes of transport and thirty seconds without byte progress. Nonblocking socket setup fails closed. Cancellation, disconnect, timeout and normal completion close the listener/UART and leave Thread paused. Other protocols remain active during the serial transfer, but the two deliberate hub restarts interrupt them briefly. An interrupted transfer is retried through the same ROM path with a known-good image; it does not depend on the damaged RCP application. The S3 must still boot, have Ethernet and retain functional guard storage.

`H2 UART Update State` reports `closed`, `waiting_authenticated_client`, or `streaming_rom_uart`. `cancel_h2_uart_update` closes an active window; `retry_quarantined_thread` is refused while the window is active. The host, not this diagnostic, determines whether the image verified successfully.

**Transport boundary:** API arming is encrypted. The short-lived UART TCP connection carries its token and firmware in cleartext. Use the trusted management LAN; do not expose TCP6639 externally. The token prevents an unarmed or unauthenticated client from taking the updater, but is not TLS or a firmware-signing system. H2 secure-boot/flash-encryption/eFuse provisioning is outside this updater's qualified configuration.

## MG24 application GBL update

Stop the single ZHA or Zigbee2MQTT coordinator owner and retain its backup. Use the GBL and report produced together by `../zigbee/build.py`:

```sh
/tmp/mc1-updater/bin/python firmware/module-carrier/updates/update.py mg24 \
  --host 192.0.2.10 --image /path/to/artifacts/mc1-xiao-mg24-ncp.gbl \
  --report /path/to/artifacts/build-report.json
```

After reviewing that offline plan, add `--execute --coordinator-stopped`. The wrapper runs the equivalent of:

```sh
universal-silabs-flasher --device socket://192.0.2.10:6638 \
  --probe-methods bootloader:115200,ezsp:115200 \
  flash --firmware /path/to/artifacts/mc1-xiao-mg24-ncp.gbl
```

Do not add a board `--profile` or `--bootloader-reset`: those imply unrelated hardware wiring. Pinned [universal-silabs-flasher1.1.0](https://github.com/NabuCasa/universal-silabs-flasher/tree/d0d751cbbbb4e652f5ebf1129a1c66390ddfa3d6) recognizes the running EZSP application, requests `launchStandaloneBootloader(mode=0x01)`, reconnects to the115200 Gecko loader and transfers the GBL through XMODEM. The S3 implements physical RTS/CTS locally; TCP has no DTR/RTS-to-GPIO shortcut. Resume the coordinator after success and verify its version, retained network and test-device traffic.

This replaces the NCP application and preserves the existing bootloader. A responsive NCP can enter its loader remotely; an already-running Gecko loader is also probeable. A hung application that never handles the software command cannot be forced into recovery by the existing host wiring. The retained local PC00 jumper plus XIAO reset/power-cycle recovers that case if the bootloader is intact. A damaged bootloader needs SWD/native programmer access. A GBL upload is not a claim of remote recovery from every fault.

## Validation scope

The complete S3 image and remapped H2 RCP are compiled with the pinned toolchain. Offline tests cover token shape/comparison, maintenance/durability/UART ownership interlocks, deadline wraparound, artifact corruption/wrong pins/wrong flash offset, no-network default planning, and binary loopback transfer with fragmented authentication response and rejected authentication. Production WK2132 and Thread guard tests remain included. The PC tool dependencies are pinned separately; no SDK source/cache patch is needed.

Still required on actual hardware: R7 isolation/voltage verification, entering ROM via EN/BOOT, successful and interrupted H2 flash/readback, stale or wrong image refusal, reconnect after both S3 restarts, MG24 software bootloader entry and interrupted GBL recovery, TCP disconnects under radio load, and local recovery with USB connectors physically inaccessible. Do not translate source review or loopback success into completed hardware qualification.
