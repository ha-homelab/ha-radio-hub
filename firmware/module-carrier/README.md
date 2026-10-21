# MC1 complete firmware target

> **Historical MC1 revision.** The current [MC2 external-antenna build](../../docs/external-antennas.md) uses different modules, pins, flash layout and housing. Keep this material with MC1 boards only.


MC1 keeps the existing S3 application and Thread/Ember protocol boundaries. It changes the physical modules, remaps the H2 UART, and replaces the discrete SC16IS752 circuit with a DFRobot DFR0627 module. It does not require a new multi-MCU application protocol or a port of the Thread Border Router to H2.

Use `hub.yaml` with a **Waveshare ESP32-S3-Nano-M** (factory male headers), **ESP32-H2-DevKitM-1-N4S**, and the specified four-wire XIAO MG24 firmware. The generic `esp32-s3-devkitc-1` build descriptor selects the S3 toolchain; it is not the physical board. This profile explicitly selects **16 MB flash and 8 MB octal PSRAM**, preserves the node name `module-carrier-hub`, and uses all 21 available non-strap application GPIO.

The [build record](build-evidence.json) records the full image, partition margins and generated GPIO checks. The [host test record](test-results.json) distinguishes simulated fault coverage from physical testing. The separately compiled [XIAO MG24 firmware](zigbee/README.md) and matching H2 RCP retain their existing protocol interfaces; the H2 image is rebuilt for its ROM UART pins. No hardware has been flashed or qualified by this change.

The complete guarded Nano image compiled with ESPHome 2026.9.1 / ESP-IDF 5.5.5: **1,731,872-byte OTA image**, **163,771 bytes static RAM**, and two **8,126,464-byte OTA slots**, each with **6,394,592 bytes** remaining. These are image/linker measurements, not peak runtime memory. All **70 MC1 host tests** and **103 shared RF/root tests** passed. Prior H2 and MG24 build evidence is retained unchanged.

The generated 16 MB factory partition layout differs from the historical 8 MB layout, including the NVS location. Export/back up the existing Thread dataset and deployment configuration before a first factory installation or partition migration. App-only OTA ordinarily keeps the installed partition table; it does not perform this migration. Verify the actual installed layout. Runtime dataset preservation described below assumes an unchanged, correctly installed partition table.

The shared [RF startup guard](../components/rf_tx_startup/README.md) releases CC1101 GDO0 before ESP-IDF first routes the RMT output. It checks the pinned upstream source and SDK version, and build verification confirms the actual linked transmitter call reaches the narrow wrapper. Runtime transitions also verify GDO0 Hi-Z and IDLE/TX/RX status before transmitting or resuming capture; failed checks latch a fault and skip the waveform. No GPIO or carrier layout changes are required for this correction.

## Functions retained

- Single W5500 Ethernet interface, IPv6 forwarding, local Thread Border Router with H2 RCP and REST port 8081.
- Active BLE proxy with three connections, encrypted native API, OTA, MQTT.
- CC1101 receive/transmit and the existing RF topic/payload/action contracts.
- Four-wire, flow-controlled Ember serial transport on TCP 6638 for Zigbee.
- ZAC93 through ESPHome's Z-Wave proxy, now using a checked DFR0627 UART1 adapter.
- Native LD2450 UART and all existing radar controls; BME680 on the shared I2C bus.

## Exact wiring and service

The [machine-readable pin contract](pin-plan.json) describes the Nano-M factory headers. Logical assignments are:

- One shared SPI2 bus: SCK13, MOSI11, MISO12. W5500 uses CS14, IRQ10, RESET9. CC1101 uses CS6, GDO0/TX4 and GDO2/RX5.
- MG24 UART1: TX17, RX18, RTS7, CTS21. The four-wire Ember 115200 8N1 contract is unchanged.
- H2 UART2: S3 TX43 goes to H2 GPIO23/RX; H2 GPIO24/TX goes to S3 RX44. S3 GPIO47 controls H2 EN and GPIO48 controls H2 BOOT/GPIO9.
- LD2450 UART0: TX8/RX38. I2C: SDA1/SCL2 at 400 kHz, shared by BME680 and DFR0627.

The Nano has native USB on 19/20 and no USB-UART bridge on 43/44. ROM boot messages on TX43 can reach H2; the firmware resets H2 before its read-only preflight and OpenThread startup. GPIO48 drives a slow open-drain BOOT control, compatible with the Nano's LED MOSFET gate load. The carrier must retain accessible GPIO0-to-GND recovery because the Nano has no dedicated BOOT button.

H2 control outputs are open-drain. BOOT stays released high, and each hardware reset holds EN low for 10 ms then waits 100 ms. MC1 uses the H2 DevKit EN pull-up and GPIO9's intrinsic reset-time pull-up. Verify actual levels and the strap hold interval on the assembled carrier. The [assembled-device update guide](updates/README.md) provides S3 OTA, authenticated temporary H2 ROM-UART transport plus host esptool, and MG24 application GBL updating through TCP6638. The H2 path requires isolating the DevKit v1.3 USB-UART transmitter by removing R7 before assembly. It arms only after a durable Thread maintenance restart; normal operation has no TCP6639 listener. The host tool defaults to an offline plan and performs no flash unless `--execute` is supplied. Do not run simultaneous programmers. Paused/quarantined Thread performs no automatic reset or retry; an explicitly authenticated update session controls reset separately. Initial programming happens before soldering. USB and local recovery remain emergency options with the limitations in the update guide.

Power DFR0627 from 3.3 V; set **IA1=1 and IA0=0**. Its UART1 register address is **0x50** and FIFO address is **0x51**. Reserve the complete **0x50–0x57** address block for this module. TX1 goes to ZAC93 RX and RX1 comes from ZAC93 TX. UART2 is disabled. BME680 remains at 0x77 (or 0x76 if configured). Earlier instructions using IA1=1/IA0=1 and 0x70/0x71 were incorrect with BME680 on the same bus: the DFR0627 also acknowledges other channel/FIFO addresses in 0x70–0x77. Disabling UART2 does not remove that overlap. Change the physical switch before using the corrected firmware.

## Shared SPI contract

ESPHome 2026.9.1 supports W5500 `spi_id`. Its SPI-device transactions arbitrate the same IDF bus as CC1101. The pinned CC1101 startup reset sequence directly toggles CS; therefore the generated-code check requires its default DATA setup priority (600), before Ethernet (250), with the bus initialized at 1000. No runtime CC1101 `reset()`/`configure()` or setup-priority override is permitted by this profile. RF modulation uses the existing RMT/GDO lines, not continuous SPI packet transfer. Firmware compilation and these source checks do not replace simultaneous Ethernet/RF load testing.

## Thread failure containment

The [detailed recovery contract](thread-recovery.md) describes the exact implementation and remaining limits. In ordinary operation all three active BLE slots, Zigbee, Z-Wave, radar, RF, MQTT and Thread remain enabled.

Before the real OpenThread stack starts, a bounded read-only UART probe verifies HDLC integrity, Spinel 4.3, RCP/raw-radio capabilities, API compatibility and required radio features. No answer, an incompatible RCP or unavailable guard storage quarantines Thread without entering the SDK stack. The other functions continue. The probe does not read or modify network credentials.

For an unrecoverable failure after startup, registered callbacks persist the fault and perform **one complete hub restart**, then leave Thread quarantined. All protocols briefly disconnect during that restart. SDK terminal paths that bypass those callbacks are detected conservatively after a panic/watchdog reset using a persisted armed marker. An unrelated crash while Thread was armed can therefore also quarantine Thread. This is bounded fault containment, not a claim of seamless recovery or perfect fault attribution.

Home Assistant receives `Thread State`, `Thread Last Fault`, `Thread Quarantined`, fault/retry/reset counts, role, reset reason and internal/PSRAM memory measurements. Use the momentary **Retry Quarantined Thread** switch or native API action `retry_quarantined_thread` after fixing the cause. This durably clears only the guard and restarts the hub once. We deliberately avoid adding the ESPHome `button` component because it conflicts with the existing Dooya API argument named `button`; that public RF schema is preserved.

Normal power-on, temporary Ethernet loss and absence of a commissioned Thread dataset do not by themselves trigger quarantine. The guard uses NVS namespace `hub_thread`; OpenThread's dataset remains untouched. Persistent quarantine survives normal resets, firmware updates and power cycles. If NVS writing fails during a fault, checksummed RTC memory protects a warm restart only; persistence across total power loss is not guaranteed while storage is failing. Existing ESPHome OTA safe mode/rollback is retained, with no claim that its successful-boot timer tests Thread connectivity.

## Why this is not the stock WeiKai component

ESPHome 2026.9.1's WeiKai implementation truncates a `write_array` above its I2C transfer size, writes without checking available TX FIFO capacity, and does not propagate failed FIFO reads or serial errors as a disconnected UART. A Z-Wave serial frame can exceed that transfer size. The local component is deliberately limited to the purchased DFR0627's UART1 at 115200 8N1 with its 14.7456 MHz crystal.

The driver uses 2 KiB FreeRTOS TX/RX queues and a dedicated worker with 256-byte staging queues. It admits each application write in full or declares a fault, and divides hardware FIFO transfers into checked 64-byte chunks. It accounts for 256-byte FIFO count wrap, checks TX free space, detects serial errors before/after RX, and never replays an ambiguous failed write. A transport error discards the staging queues, stops delivery from the external queues and makes `is_connected()` false, which the existing Z-Wave proxy observes. Recovery requires restarting the hub. Periodic register checks also detect a module reset or configuration loss.

After initialization, only the dedicated priority-2 FreeRTOS worker accesses the WK2132 registers and FIFOs. A TX enqueue wakes it immediately; otherwise it polls at a nominal 2 ms interval with a 4096-byte task stack. This preserves isolation from the ESPHome application loop. Synchronous I2C transactions are serialized with BME680 by the pinned ESP-IDF driver's bus semaphore: `i2c_master_execute_defined_operations()` calls `s_i2c_synchronous_transaction()`, which acquires `bus_lock_mux`. The ESPHome wrapper uses stack-local operation arrays and the adapter never changes the shared device address. Only the WK worker changes the WK register page, so a BME transaction can safely run between WK transactions. No additional application mutex or second I2C bus is needed. See the [pinned IDF implementation](https://github.com/espressif/esp-idf/blob/v5.5.5/components/esp_driver_i2c/i2c_master.c).

A full 256-byte receive FIFO represents 22.22 ms at 115200 8N1. The 2 ms poll is a target, not a proven worst-case latency. An unavailable I2C bus or prolonged higher-priority work can still cause a detected UART overrun. Unlike the previous SC16's interrupt-assisted worker, this worker uses timed RX polling with a four-times-larger hardware FIFO. The device must pass concurrent Thread/BLE/radar/RF/Zigbee/Z-Wave load testing before reliability parity is claimed. The adapter avoids silent corruption; it cannot manufacture real-time scheduling guarantees.

The [DFRobot module documentation](https://wiki.dfrobot.com/dfr0627), [official register implementation](https://github.com/DFRobot/DFRobot_IICSerial/blob/master/src/DFRobot_IICSerial.cpp), and [register/FSR definitions](https://github.com/DFRobot/DFRobot_IICSerial/blob/master/src/DFRobot_IICSerial.h) establish the address selection, crystal, baud divisor, FIFO size and error bits. This component does not embed the vendor Arduino library.

## Reproduce without flashing

Install the pinned ESPHome 2026.9.1 environment first. The preparation script makes a disposable copy, retrieves only the pinned REST server dependency, and generates temporary credentials. It never overwrites deployment secrets or uploads firmware.

```sh
python3 firmware/module-carrier/validate.py /tmp/mc1-build \
  --esphome /path/to/pinned/esphome --compile
RF_CPP_SANITIZERS=1 python3 -m unittest discover \
  -s firmware/module-carrier/tests -v
```

An existing clone containing esp-thread-br commit `29a2345e3f0c61bba9307f3daea5ed0c94388ed3` can be supplied with `--upstream /path/to/esp-thread-br`.

Prepare the H2 RCP with the same ESP-IDF 5.5.5 as the S3 integration:

```sh
python3 firmware/module-carrier/prepare_h2.py /tmp/mc1-h2 \
  --idf /path/to/esp-idf-5.5.5
cd /tmp/mc1-h2
idf.py set-target esp32h2
idf.py build
```

Run `python3 firmware/module-carrier/verify_h2.py /tmp/mc1-h2` from the repository to verify the finished H2 pin/configuration contract and print its artifact hashes. Linux CI can obtain `idf_path` from the completed S3 build's `build/project_description.json`, install that SDK's `esp32h2` tools in an isolated `IDF_TOOLS_PATH`, and reuse the exact same SDK with this recipe. No manually patched SDK cache is required.

The RCP retains Spinel UART 460800 8N1, no hardware flow control, and 4 MB flash. The rebuilt image uses ROM-compatible RX23/TX24 and requires the corresponding new carrier wiring. The H2 is a Thread RCP, not an additional BLE proxy.

The active firmware and CAD pin manifests both describe RX23/TX24. Preparation and build verification reject a stale RX4/TX5 manifest; the host regression suite also checks manifest parity and the physical H2/S3 crossover. The smaller single-retainer carrier changes placement and enclosure support, not these GPIO assignments or the compiled application.

## Qualification gates

The native tests exercise the production transport core and injected device failures; they do not emulate radio timing or prove the physical WK2132 silicon. Verify the actual module clock, I2C address/pull-ups, 115200 baud, logic levels, carrier power, and full-duplex UART with a logic analyzer. Exercise Z-Wave inclusion/exclusion, secure commands, large serial frames, modem reconnect, and error reporting under concurrent radio traffic. Confirm Thread routing/discovery/REST, Zigbee CTS backpressure, all three BLE sessions, RF raw transmit/receive and radar controls on the populated carrier. Measure runtime heap, stack margins, service interval distribution and temperature. Use the retained deployment RF/MQTT settings and provision real secrets separately.
