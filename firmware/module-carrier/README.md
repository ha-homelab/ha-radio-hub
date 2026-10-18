# MC1 complete firmware target

MC1 keeps the existing S3 application and Thread/Ember protocol boundaries. It changes the physical modules, remaps the H2 UART, and replaces the discrete SC16IS752 circuit with a DFRobot DFR0627 module. It does not require a new multi-MCU application protocol or a port of the Thread Border Router to H2.

Use `hub.yaml` with an **Espressif ESP32-S3-DevKitC-1 v1.1 N8R8**, **ESP32-H2-DevKitM-1**, and the specified four-wire Ember MG24 firmware. The S3 target explicitly selects 8 MB flash and octal PSRAM. Compile evidence is not a hardware release.

The complete worker-based S3 image compiled successfully with ESPHome 2026.9.1 / ESP-IDF 5.5.5: 1,717,296-byte OTA binary, 161,579 bytes of static RAM, and two 3,932,160-byte application slots in the 8 MB flash layout. The remapped H2 RCP binary is 208,928 bytes. These sizes exclude unmeasured runtime allocation requirements. The [build record](build-evidence.json) contains hashes and verified configuration; [14 sanitized transport tests](test-results.json) cover FIFO backpressure, large frames, count-wrap races, I2C failures, serial errors and queue overflow. The separately compiled [XIAO MG24 firmware](zigbee/README.md) supplies the four-wire Ember NCP and recovery bootloader.

## Functions retained

- Single W5500 Ethernet interface, IPv6 forwarding, local Thread Border Router with H2 RCP and REST port 8081.
- Active BLE proxy with three connections, encrypted native API, OTA, MQTT.
- CC1101 receive/transmit and the existing RF topic/payload/action contracts.
- Four-wire, flow-controlled Ember serial transport on TCP 6638 for Zigbee.
- ZAC93 through ESPHome's Z-Wave proxy, now using a checked DFR0627 UART1 adapter.
- Native LD2450 UART and all existing radar controls; BME680 on the shared I2C bus.

## Exact changed wiring

S3 Thread UART2 TX41 goes to H2 GPIO4/RX. H2 GPIO5/TX goes to S3 RX42. S3 GPIO47 controls H2 EN, and GPIO48 controls H2 BOOT/GPIO9. This frees each development board's onboard USB-to-UART connection. Use the new RCP preparation recipe below: the previous RX23/TX24 RCP binary has the wrong pinout for MC1.

The shared OTBR driver already configures both H2 control outputs as **open-drain**, not push-pull; this was checked in the source copied into the compiled MC1 image. BOOT stays released high, and startup pulls EN low for 10 ms before releasing it. The onboard H2 auto-reset transistors can therefore pull these nets low without opposing a driven-high S3 output. MC1 uses the DevKit's EN pull-up and H2 GPIO9's intrinsic reset-time pull-up; the legacy source comment specifying external 10 kΩ pull-ups describes the earlier carrier. The [H2 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-h2_datasheet_en.pdf) specifies the GPIO9 weak pull-up and permits external high-impedance loads on default straps. Verify its high level across reset and the 3 ms strap hold interval on the assembled carrier.

The host component does **not** flash H2 firmware. During H2 USB service, keep the S3 in a stable state: avoid restarting it or making its first Ethernet connection because OTBR startup issues the reset pulse. Do not run simultaneous programmers. Open-drain resolves electrical contention; it does not arbitrate independent programming/reset operations.

S3 I2C SDA1/SCL2 runs at 400 kHz. Power the DFR0627 from 3.3 V; set IA1=1 and IA0=1. The fixed UART1 register address is 0x70 and its FIFO address is 0x71. DFR0627 TX1 goes to ZAC93 RX; RX1 comes from ZAC93 TX. UART2 is disabled. BME680 remains at 0x77. All other S3 signal pins retain the previous application assignment. The PCB netlist is authoritative for connector positions; these are GPIO numbers.

The board must leave S3 GPIO43/44 (onboard USB-UART), GPIO38 (v1.1 RGB LED), and native USB 19/20 outside the application wiring. H2 uses normal header GPIO4/5, leaving UART 23/24 and USB 26/27 for service. The [official H2 board guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html) lists GPIO4/5 at J1 pins 9/10, EN at J1 pin 2, and BOOT9 at J3 pin 11.

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

The RCP retains Spinel UART 460800 8N1, no hardware flow control, and 4 MB flash. Only the UART pin assignment changes. The H2 is a Thread RCP, not an additional BLE proxy.

## Qualification gates

The native tests exercise the production transport core and injected device failures; they do not emulate radio timing or prove the physical WK2132 silicon. Verify the actual module clock, I2C address/pull-ups, 115200 baud, logic levels, carrier power, and full-duplex UART with a logic analyzer. Exercise Z-Wave inclusion/exclusion, secure commands, large serial frames, modem reconnect, and error reporting under concurrent radio traffic. Confirm Thread routing/discovery/REST, Zigbee CTS backpressure, all three BLE sessions, RF raw transmit/receive and radar controls on the populated carrier. Measure runtime heap, stack margins, service interval distribution and temperature. Use the retained deployment RF/MQTT settings and provision real secrets separately.
