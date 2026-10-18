# SLZB Thread firmware review

Audit date: 2026-10-17. Read-only source and documentation review; no SLZB hardware tests, flashing, or changes to the active hub firmware. Our reference is the complete ESP32-S3 Nano profile, not a radio-only bridge.

## Decision

SMLIGHT provides a credible implementation benchmark for our **S3 + Ethernet + dedicated Thread radio + separate Zigbee radio** architecture. It does not establish that one H2 can replace this complete system. An xU/MRxU/Ultima product can remove much of the work required for a conventional Zigbee/Thread gateway, but its stock BLE function does not preserve our active BLE connections, and the published alternate ESPHome image does not implement a local OTBR. Preserve these distinctions before comparing prices or board dimensions.

## Where Thread actually runs

The official manual distinguishes two different products of the word “Thread”:

- **Remote OTBR:** the SLZB radio runs RCP firmware and exports its serial stream over USB or TCP. Home Assistant or another computer runs OTBR. The manual gives TCP port 6638 as an example; multi-radio products have separate endpoints.
- **Local OTBR:** the border router runs inside **SLZB-06xU, SLZB-MRxU or Ultima**. HA connects to its REST API at `http://device-ip:8080`; the HA OTBR app is unnecessary. LAN IPv6 is required and enabled on the device. Matter Server remains a separate HA-side service.

Older non-U models supporting remote Thread must not be described as equivalent local border routers. The manual still labels the local integration beta. [Official Thread setup](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/thread-setup-network-and-usb-connection).

The 3.2.6.dev0 announcement introduced local OTBR and excluded simultaneous standalone **Zigbee Hub mode** and Ethernet/Wi-Fi router/bridge modes. That restriction must not be generalized into “a separate Zigbee coordinator cannot run”: MR devices have two radio SoCs precisely for independent roles. [Release announcement](https://smlight.tech/articles/slzb-os-v3-2-6-dev0), [series overview](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/slzb-series-overview).

## BLE and source availability change the comparison

The current specialized BLE manual requires SLZB-OS 3.3.3.dev7 or newer and HA 2026.8 or newer. It explicitly supports advertisement forwarding, not active BLE connections. Active *scanning* only requests scan responses; it does not provide active GATT device connections. This is a functional reduction relative to our ESPHome active proxy. [Official BLE manual](https://smlight.tech/support/manuals/books/slzb-os/page/bluetooth-low-energy).

SMLIGHT's alternate ESPHome firmware does enable `bluetooth_proxy: active: true`. However, its published source combines BLE with UART `stream_server` endpoints, not a local OpenThread stack. Installing this image replaces SLZB-OS; it is not an extra feature switched on inside the same OS. Its documentation also disables the web server to conserve memory. [ESPHome installation guide](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/esphome-firmware-for-ultima-and-xu-series).

Source snapshots inspected:

- **Official alternate ESPHome:** `smlight-tech/slzb-esphome` at **3397f6ffe7b0a58cf1546c8293bfa644235a9769**. [Active BLE configuration](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/packages/bluetooth/bluetooth.yaml), [UART streaming](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/packages/stream_servers/ss_uart1.yaml), [core configuration](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/packages/core/core.yaml). No local OTBR implementation was found in this snapshot. The external streaming component reference is not pinned to an immutable revision.
- **Legacy core:** `smlight-dev/slzb-06-firmware` at **907468cb45bd8ae16a265abb4ccc17f7a1339a9c**. Its [main program](https://github.com/smlight-dev/slzb-06-firmware/blob/907468cb45bd8ae16a265abb4ccc17f7a1339a9c/src/main.cpp) uses Arduino Ethernet/serial forwarding and generic serial discovery. This older implementation is not the current S3 local OTBR source.
- **Official HA-side client:** `smlight-tech/pysmlight` at **85142c6b80123819d31a388b210532fff09458eb**. [BLE UDP protocol](https://github.com/smlight-tech/pysmlight/blob/85142c6b80123819d31a388b210532fff09458eb/pysmlight/ble_proxy.py) handles advertisements and acknowledgements, not GATT commands. [Mode constants](https://github.com/smlight-tech/pysmlight/blob/85142c6b80123819d31a388b210532fff09458eb/pysmlight/const.py) distinguish `thread` from `otbr`.

I did not locate the current full SLZB-OS local OTBR implementation in the audited official public repositories. This is a bounded source-availability finding, not a claim that no source exists elsewhere.

## Reuse and licensing

The [MR5U marketing page](https://smlight.tech/products/slzb-mr5u) advertises a lighter MIT-licensed open-source core, separately from SLZB-OS. The two actual firmware repositories inspected above instead contain **GPLv3** licenses: [alternate ESPHome license](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/LICENSE), [legacy core license](https://github.com/smlight-dev/slzb-06-firmware/blob/907468cb45bd8ae16a265abb4ccc17f7a1339a9c/LICENSE). We have not resolved the marketing statement to a specific MIT source artifact. The [HA client is Apache-2.0](https://github.com/smlight-tech/pysmlight/blob/85142c6b80123819d31a388b210532fff09458eb/LICENSE).

SMLIGHT also publishes a [device-restricted firmware license dated 2024-03-28](https://smlight.tech/legal/licenses/restrictive-smlight-slzb06-v20240328.txt), linked by a radio firmware catalog fixture in the HA client. It restricts modification and use on other hardware. Do not assume it governs every current artifact, or assume a downloaded SLZB binary may be flashed onto our Nano. Check each artifact's terms. No vendor code or binary was copied into this project during this audit; the availability/license discrepancy is not an allegation of a license violation. For implementation, our existing ESP-IDF/OpenThread dependencies offer a clearer source path than treating SLZB-OS as a portable firmware package.

## What transfers to our design

The xU overview specifies an ESP32-S3R2 with 2 MB quad PSRAM and W5500 Ethernet. That shows local OTBR is practical on an S3 with less PSRAM than our 8 MB Nano, under SMLIGHT's workload. It does **not** qualify our combined active BLE, RF transmit/receive, radar, Z-Wave, Zigbee and Thread workload in 2 MB. Retain runtime memory measurements as the criterion. [Hardware overview](https://smlight.tech/support/manuals/books/slzb-06xmrxmrxuultima-series/page/slzb-series-overview).

The official ESPHome [Ultima hardware definition](https://github.com/smlight-tech/slzb-esphome/blob/3397f6ffe7b0a58cf1546c8293bfa644235a9769/hw_defs/ultima/r1_04.yaml) uses an I2C TCA9555 for slow controls. A finished expander module could free MCU pins for LEDs, reset, boot and buttons. It cannot replace timing-sensitive RF, UART flow control or Ethernet SPI signals. This is an alternative mechanical tradeoff, not a reason to add loose parts to the already complete 21-GPIO Nano solution.

The most useful transfer is the **failure matrix** exposed by SMLIGHT's release history: link-loss IPv6/OMR recovery, Border Agent discovery after restart, RCP failures, and bounded memory use. Changelog 3.3.8.dev7 specifically describes IPv6/OMR recovery after link loss/reboot; other entries fix mDNS port/state, logging-related failures and stop/start behavior. Those fixes establish real test cases; they do not establish our current SDK lacks every corresponding mechanism. [Official changelog](https://smlight.tech/support/manuals/books/slzb-os/page/changelog-slzb-os).

## Confirmed source-level risk in our pinned startup path

This finding is **not a reproduced crash**. It follows the exact ESP-IDF **5.5.5**, commit **b774170ff46c393eeb5e495ea37936038d3f4f4f**, OpenThread submodule **b678a4f63b6f9397d1a0fa8f31e5b8e0271a4d00**, used by the successful Nano build. The build has `CONFIG_OPENTHREAD_FTD=y`, `CONFIG_OPENTHREAD_RADIO_SPINEL_UART=y`, assertions enabled, and `CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT=y`.

1. Our [wrapper](../../../../firmware/low-power/components/low_power_otbr/low_power_otbr.cpp) resets H2, then calls `esp_openthread_start()`. It checks returned errors, but registers neither `esp_openthread_set_coprocessor_reset_failure_callback()` nor `esp_openthread_set_compatibility_error_callback()`, nor an RCP hardware-failure handler.
2. IDF [radio initialization](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/openthread/src/port/esp_openthread_radio_spinel.cpp#L75) installs a reset-failure trampoline whose application callback starts NULL and is asserted before use. The same pattern exists for radio compatibility errors. The FTD [configuration](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/openthread/private_include/openthread-core-esp32x-ftd-config.h#L606) enables these callbacks; no default application registration was found in the initialized path or generated hub source.
3. On a silent/missing RCP, [SpinelDriver::ResetCoprocessor](https://github.com/espressif/openthread/blob/b678a4f63b6f9397d1a0fa8f31e5b8e0271a4d00/src/lib/spinel/spinel_driver.cpp#L135) first waits for the software reset response. Its fallback calls [UartSpinelInterface::HardwareReset](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/openthread/src/spinel/esp_radio_spinel_uart_interface.cpp#L359), which returns success even when no hardware-reset handler was registered. A second response timeout enters the asserting trampoline. Each Spinel response wait is bounded by the source's 2-second constant; that does not make the wrapper a recoverable startup state machine.
4. This path can panic/reboot the **whole S3**, interrupting unrelated functions. `esp_openthread_start()` itself [waits indefinitely for its worker semaphore](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/openthread/src/esp_openthread.cpp#L303); its worker also uses `ESP_ERROR_CHECK`. A returned-error check around this API does not catch these fatal paths.

Adding a no-op callback is insufficient: `ResetCoprocessor()` calls `DieNow()` after a returning failure callback; [compatibility handling](https://github.com/espressif/openthread/blob/b678a4f63b6f9397d1a0fa8f31e5b8e0271a4d00/src/lib/spinel/radio_spinel.cpp#L2460) also ends in `DieNow()`. Proper containment needs an explicit supported recovery/termination design, not a blanket assertion disable or a callback that merely logs.

Conversely, do not say RCP recovery is absent: IDF configures **three restoration attempts**, and [RadioSpinel::RecoverFromRcpFailure](https://github.com/espressif/openthread/blob/b678a4f63b6f9397d1a0fa8f31e5b8e0271a4d00/src/lib/spinel/radio_spinel.cpp#L2041) implements recovery. A transient reboot may recover. Missing application-level reset control and fatal terminal failure paths remain the specific risks.

Audit fingerprints: wrapper SHA-256 `92492effbb5ce3621ffcec84bb6a906c5afd71da4c2a53a360a2161fc0625961`; IDF radio port `f8714ee1dd0b81ce1dc836206146becb0b66aebf77957ddd235910f83710a89c`; UART interface `93b7bbdbbf62cb515176bac023f94e87251c7e6cc6f771aeeb7d65767e0ce063`.

## Concrete qualification plan

1. **RCP startup and recovery:** test H2 absent, held in reset, stale incompatible RCP, one warm reset, and repeated resets while BLE/Zigbee/RF/Z-Wave run. Capture boot reason, UART trace and service availability. Target: a bounded Thread-degraded state with diagnostics and controlled retries; no host reboot storm. Validate any containment change against both callback and `DieNow` paths. Pin the tested host/RCP pair rather than assuming all firmware versions interoperate.
2. **Ethernet and IPv6:** unplug/replug, boot with no Ethernet, change the LAN prefix, and restart the upstream router. Check IPv6 neighbor discovery, OMR routes and real Matter commands after return. Our wrapper launches once; SDK event processing may already restore connectivity. Patch only failures actually observed.
3. **Discovery:** verify `_meshcop._udp` identity, port and state before/after RCP restart, Ethernet changes and HA restart. REST reachability alone is not proof that discovery and commissioning work. Confirm the active dataset survives and a fresh device can join.
4. **OTA acceptance:** retain ESPHome [safe mode/rollback](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/safe_mode/safe_mode.cpp), which already exists. Its successful-boot timer is not a Thread health assessment. Test malformed/failed upgrades and interruption during boot; define health without rejecting a legitimately uncommissioned or temporarily disconnected hub. Verify rollback does not erase the Thread dataset.
5. **Resources and load:** record internal free heap, largest internal block, PSRAM free/minimum, task stack watermarks, queue drops and reset cause during simultaneous active BLE, Ethernet traffic, RF transmission, radar, Z-Wave and both mesh radios. Include logging enabled and repeated reconnects. Source compilation establishes API/link compatibility, not these runtime margins.

No new assertion-containment, recovery or OTA policy has been implemented or claimed tested by this report.
