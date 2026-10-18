# Thread startup, quarantine and recovery

This implementation adds bounded failure containment around ESP-IDF 5.5.5; it does not patch SDK sources or disable assertions. It preserves the H2 RCP, radio protocol, REST port 8081 and stored dataset. The exact reference SDK is ESP-IDF `b774170ff46c393eeb5e495ea37936038d3f4f4f`, with OpenThread `b678a4f63b6f9397d1a0fa8f31e5b8e0271a4d00`.

## Startup sequence

1. Read and validate the guard record from NVS namespace `hub_thread`. Its version, armed state, quarantine, reason, fault count and explicit retry count are separate from OpenThread storage. Corrupt/unavailable guard storage prevents Thread startup.
2. If an earlier armed session ended in a panic/watchdog, latch `host_crash_while_thread_armed`. This intentionally favors keeping the rest of the hub available over automatically retrying a potentially fatal stack. Normal power-on and intentional shutdown do not imply a Thread fault.
3. Wait for Ethernet. Waiting does not arm the guard, reset H2 or count as a failure.
4. Temporarily own UART2 at 460800 8N1. Release H2 BOOT, reset H2 with a 10 ms open-drain EN pulse and wait 100 ms. Query only read-only Spinel properties: protocol, capabilities, optional RCP API/minimum host API and radio capabilities. Each request has a 1-second deadline and one resend after 500 ms. At most five properties are queried. HDLC CRC, escapes, frame bounds and property/TID matching are checked. Delete this temporary UART driver before OpenThread takes ownership.
5. A failed preflight durably quarantines Thread without a host reboot. The other application services continue. A successful probe does not prove RF operation or future compatibility of every property; the SDK still performs its own full checks.
6. Commit and read back the armed record before invoking SDK startup. Register the physical RCP reset handler and non-returning terminal callbacks before entering the stack. Start the SDK; the ESPHome main loop supervises this phase with a 20-second deadline. The bound assumes the main task remains schedulable; it is not a hard real-time guarantee under arbitrary scheduler or hardware failure.
7. Initialize the border router, restore an existing dataset or await commissioning, then expose REST. A missing dataset is a valid state. No demonstration network or invented credentials are created.

The required radio capability mask matches the pinned port: bits 0–7, plus bit 8 when `CONFIG_OPENTHREAD_RX_ON_WHEN_IDLE` is enabled. The preflight accepts the same Spinel 4.3 and API bounds (host API 11, minimum RCP API 4) as this SDK. Changing SDK versions requires revalidating these constants.

## Runtime fault behavior

ESP-IDF's existing transient RCP restoration is retained, including its maximum restoration count of three. The registered hardware handler now actually pulses H2 EN when the UART layer requests hardware recovery. It does not flash H2 or change the dataset.

If the SDK invokes a terminal reset-failure or incompatibility callback, the callback records quarantine, commits and verifies it, then calls `esp_restart()`. It never returns into `DieNow()`. The restart happens from a normal task context; the code does not delete the OT worker, unwind its C++ stack, release locks it does not own, or attempt partial teardown with live REST callers. Both startup timeout and a returned error after entering the stack use the same terminal route.

Some generic SDK `DieNow`/assert paths bypass application callbacks. In this pinned IDF, `exit()` reaches [`_exit()`, which calls `abort()`](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/newlib/src/syscalls.c#L121); the [panic handler records a reset-reason hint](https://github.com/espressif/esp-idf/blob/b774170ff46c393eeb5e495ea37936038d3f4f4f/components/esp_system/panic.c#L450). Panic reset is therefore covered on the next boot by the armed marker. This is **conservative host-crash detection**, not proof that Thread caused every such reset. The next boot latches quarantine before considering Ethernet or starting Thread.

A terminal event can interrupt all hub functions once. The following boot brings back the remaining application services while Thread stays disabled. The implementation does not promise uninterrupted Zigbee, BLE, RF or Z-Wave during that restart. A recurring unrelated crash in another component is outside this Thread containment boundary.

## Durability and explicit retry

The quarantine record is written and read back. No automatic retry clears it. A normal shutdown clears only the armed marker, never quarantine. An explicit retry increments its counter, clears quarantine and the armed marker, verifies persistence, then asks ESPHome for a normal hub reboot. If clearing cannot be verified, no retry reboot is initiated.

When a fault write fails, a checksummed `RTC_NOINIT` record is a secondary guard across warm resets. The boot path attempts to persist it again. RTC is not treated as durable after power-on/brownout, and the design cannot promise power-loss persistence if NVS itself cannot accept writes. It remains fail-closed when guard storage cannot be opened/read. This storage-failure qualification must remain visible in operator documentation.

No automatic restart is triggered merely by loss of Ethernet, Thread role `disabled`/`detached`, or an uncommissioned network. Those conditions appear in diagnostics. Link/IPv6 restoration continues to depend on SDK behavior and still requires hardware testing.

## Diagnostics and operation

`Thread State` distinguishes Ethernet waiting, RCP checking, stack startup, ready but uncommissioned/disabled, detached, routing, backbone disconnected and quarantined. `Thread Last Fault` records the latched reason. Fault and retry counts persist; RCP hardware-reset count is per boot. Numeric device role follows OpenThread: 0 disabled, 1 detached, 2 child, 3 router, 4 leader. This is not a connectivity test.

Use **Retry Quarantined Thread** only after correcting the fault. It is a momentary switch, with an equivalent encrypted native API action `retry_quarantined_thread`. It reboots the hub and briefly disconnects the other services. No REST endpoint is required to see diagnostics or request retry, since REST is absent while Thread is quarantined.

Before programming H2, activate **Pause Thread for H2 Service** (native action `pause_thread_for_h2_service`). This stores the separate `maintenance_pause` reason without incrementing the fault count, then restarts the hub once. Wait for `Thread State = maintenance` and **Thread Guard Durable = on** after reconnection before arming the [host UART updater](updates/README.md), or before any emergency physical programming. This confirms a paused application with no Thread reset callbacks installed. The updater separately requires an explicit short-lived token and refuses to arm if the Thread stack launched in the current boot. For physical programming, follow the carrier's electrical USB/power procedure. Resume with the same explicit retry control after programming. A failed guard write is visible through **Thread Guard Durable = off**; do not treat RTC-only retention as a persistent service interlock.

The debug sensors report internal free/minimum heap, largest internal block, free PSRAM, longest main-loop interval, uptime and reset reason. They enable measurement; no runtime capacity or long-term stability numbers have been measured on hardware by this change. Existing OTA rollback remains enabled, but its elapsed boot-success timer is not an OTBR health gate.

## What the tests establish

The host suite executes the production guard policy, verified-record write/commit/read helper, packed-integer parser, HDLC CRC/escaping/bounds and preflight capability logic. It exercises missing/stale RCP, loss of response partway through preflight, corrupted frames and records, repeated power cycles, explicit retry, generic SDK crash detection, normal shutdown and storage operation failures. The existing WK2132 transport tests remain enabled.

These tests do not emulate ESP-IDF's task scheduler, flash driver, boot ROM reset classification, electrical UART behavior or a live Thread mesh. The full ESPHome build verifies integration and the generated GPIO/UART/SPI/BLE contract. Hardware acceptance must still cover H2 absent/stale/rebooting; interrupted NVS/OTA writes; warm/cold resets; Ethernet unplug/replug and prefix changes; `_meshcop._udp` discovery; commissioning and saved dataset restoration; and simultaneous BLE/RF/Zigbee/Z-Wave/radar traffic. Record whether each failure causes zero or one host restart, never an automatic retry loop.
