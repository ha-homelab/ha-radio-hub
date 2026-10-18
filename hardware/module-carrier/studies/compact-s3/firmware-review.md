# Compact S3 firmware review

**Preferred implementation: Waveshare ESP32-S3-Nano-M, with Ethernet still connected directly to S3 and W5500/CC1101 sharing one hardware SPI bus.** It preserves the current 8 MB PSRAM capacity, increases flash to 16 MB and is sold with factory male pins ([manufacturer product options](https://www.waveshare.com/product/esp32-s3-nano.htm)). The [selected pin plan](pin-plan.json) uses 21 distinct application GPIO. Thread and Zigbee retain their existing controllers and protocols. The bounded firmware change is a GPIO/SPI configuration remap, with explicit shared-bus startup restrictions; no new network transport or runtime C++ implementation is introduced.

This is a firmware and source audit. Physical module fit, supply behavior, available pre-soldered male headers, radio performance and peak runtime memory must be qualified separately. Build status and reproducible commands are recorded in [firmware/README.md](firmware/README.md).

**Build result:** both full configurations compiled successfully. Nano's OTA image is 1,717,232 bytes with 6,409,232 bytes free in each OTA slot; Mini's image is 1,714,976 bytes with 120,032 bytes free per slot. Nano preserves 8 MB PSRAM. The generated pin/bus configuration and SDK features passed verification, and 14 mutation checks passed. Neither build has been flashed or measured on hardware.

## Actual resource requirements

The [active full profile](../../../../firmware/module-carrier/hub.yaml) uses **24 distinct application GPIO**:

- W5500: three SPI bus signals, CS, interrupt and reset — six.
- CC1101: three separate SPI bus signals, CS and two raw-RF GDO signals — six.
- H2: UART TX/RX plus separate EN/BOOT controls — four.
- XIAO MG24: UART TX/RX/RTS/CTS — four.
- LD2450: UART TX/RX — two.
- WK2132 and BME680 share one I²C bus — two.

S3 native USB uses GPIO19/20 in addition to these application signals. The current allocation consumes UART0 for radar, UART1 for the four-wire Zigbee bridge, UART2 for Thread, SPI2 for Ethernet and SPI3 for CC1101. BLE itself needs no external GPIO. Native USB logging avoids consuming a fourth UART. RF pulses use RMT through GDO0/GDO2; they are not streamed over SPI.

The Nano's [official schematic](https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf) exposes 24 application-capable GPIO on plated headers. Excluding GPIO0/3/46 strapping pins leaves exactly 21. Native USB19/20 remains dedicated. The shared bus uses SCK13/MOSI11/MISO12, with independent W5500 CS14 and CC1101 CS6. H2 uses TX43/RX44 and open-drain EN47/BOOT48; radar uses TX8/RX38; Zigbee uses TX17/RX18/RTS7/CTS21. I²C1/2, Ethernet IRQ10/reset9 and RF GDO4/5 remain independent.

GPIO43 emits ROM UART output during an S3 restart. The existing Thread launch sequence asserts H2 reset for 10 ms, releases it, waits 100 ms, then starts Spinel. This removes the preceding boot chatter from the running RCP session without changing eFuses. Test cold and warm resets, partial power cycles and native USB recovery on hardware. GPIO48 drives only the onboard LED MOSFET gate through a high-value pull-down; using it for slow open-drain H2 BOOT avoids a fast clock load. The Nano has no dedicated BOOT button: retain accessible GPIO0-to-ground service contacts. It is not acceptable to make recovery depend on working network firmware.

## Mini comparison: two buses, smaller memory

The [alternative Mini plan](pin-plan-mini.json) retains two separate SPI buses. The S3 Mini's official schematic exposes 27 GPIO through its plated header rows. Leaving strap GPIO3 unused and reserving GPIO43/44 for ROM UART service leaves exactly 24. BOOT0, LED47 and USB19/20 are outside this application allocation. **GPIO33–37 are usable on this FH4R2 quad-PSRAM board; do not carry this assignment onto an octal-PSRAM S3 variant.** Manufacturer sources: [board specifications](https://www.wemos.cc/en/latest/s3/s3_mini.html), [v1.0.0 schematic](https://www.wemos.cc/en/latest/_static/files/sch_s3_mini_v1.0.0.pdf).

The six remaps are H2 TX/RX → GPIO33/34, H2 EN/BOOT → GPIO37/38, and radar TX/RX → GPIO35/36. H2-side GPIO4/5, XIAO-side PC04–PC07, baud rates and protocols remain unchanged. H2 reset/boot remain open-drain. Change the old carrier's radar-specific validation guard from GPIO39/40 to GPIO35/36 while preserving UART ownership. The [isolated preparation script](firmware/prepare.py) performs these bounded changes without modifying active firmware or runtime C++.

## Selected Nano shared-SPI implementation and limits

Pinned ESPHome **2026.9.1** accepts `ethernet.spi_id`. Its [Ethernet schema and generator](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/ethernet/__init__.py) validate a hardware bus and pass its parent object to Ethernet. The [ESP32 Ethernet implementation](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/ethernet/ethernet_component_esp32.cpp) then reuses that initialized host. The [SPI backend](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/spi/spi_esp_idf.cpp) acquires/releases the IDF bus around normal device transactions. This can reduce 24 GPIO to **21**, retaining all interrupts, resets and serial handshake signals.

There is a specific lifecycle qualification: [CC1101 configure()](https://github.com/esphome/esphome/blob/2026.9.1/esphome/components/cc1101/cc1101.cpp) manually toggles CS and delays before its first guarded SPI command. In this exact application, CC1101's default DATA priority 600 initializes before Ethernet priority 250; SPI initializes at 1000. The RF package never calls `reset()` or `configure()` at runtime, and its ordinary commands use guarded transactions. Exposing a later CC1101 reset would require locking that complete sequence or deliberately stopping Ethernet. Keep both chip selects inactive at reset and verify the actual modules release MISO when deselected.

The Nano uses this supported shared-SPI path because it has exactly 21 suitable header GPIO. The isolated verifier rejects runtime CC1101 reset/configure calls, changed setup priorities and incorrect generated bus assignments. Mini retains two buses and avoids that contention, but reduces available memory and has no confirmed factory-pin option. Neither configuration has yet demonstrated concurrent Ethernet/RF behavior on physical hardware. W5500 IRQ polling can save another GPIO but changes service latency; dropping independent reset/control signals is not counted as equivalent function preservation.

## Flash and PSRAM: capacity is not measured demand

The existing N8R8 has 8 MB flash and 8 MB PSRAM; those fitted capacities are not measured minimum requirements. The complete current image is approximately 1.72 MB. A 4 MB target must preserve two adequately sized OTA application partitions, NVS and OTA metadata, and verify the finished image against both app slots rather than merely checking total flash.

The active IDF configuration uses PSRAM for OpenThread allocation and its message pool. It requests 1024 message buffers; the default buffer size on this 32-bit target is 128 bytes, plus a pointer array — approximately 132 KiB for those allocations. This is one known allocation, not total peak use. Internal RAM must still hold other stacks, queues, DMA-capable memory and runtime objects. A successful 2 MB-PSRAM build does not measure heap fragmentation, stack margins or the peak while BLE, Thread, Zigbee, RF, radar and Z-Wave operate together. Relevant [IDF Kconfig](https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/Kconfig), [pool allocator](https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/src/port/esp_openthread_messagepool.c) and [OpenThread buffer definition](https://github.com/openthread/openthread/blob/main/src/core/config/misc.h).

The selected Nano preserves 8 MB PSRAM, so it does not rely on shrinking the memory budget. The S3 Mini remains a reasonable **2 MB PSRAM qualification candidate**, with quad mode explicitly selected and missing PSRAM treated as an error. Acceptance requires measured internal/external minimum free heap, largest allocatable block, task stack margins, sustained concurrent traffic and an OTA cycle. No camera, display or framebuffer workload is present in this profile.

## Why moving Ethernet to H2 or MG24 is a larger change

Moving W5500 does not remove Ethernet work; it introduces a processor-to-processor network transport. Preserving the current local Thread border router requires S3 to receive a real network interface carrying IPv6, multicast, neighbor discovery and link state. Forwarding only TCP/MQTT messages or using W5500's IPv4 hardware sockets is not equivalent to the current raw Ethernet/lwIP interface.

**H2 as Ethernet bridge:** reusing its existing UART would save the six S3 Ethernet pins in principle, but requires a framed/multiplexed channel alongside Spinel, flow control, restart recovery and a virtual network driver. The current 460800-baud 8N1 channel has a maximum wire payload of 46080 bytes/s before framing and Thread traffic. This is a substantial throughput reduction from the current direct link. A separate SPI transport costs about four/five S3 signals itself; sharing Spinel and Ethernet on it saves fewer pins and still needs new firmware. There is also a boot dependency: S3 currently waits for Ethernet before initializing and resetting H2. An H2-provided Ethernet link requires that lifecycle to be refactored, and a radio reset would also remove the network path.

**H2 running native Thread plus Ethernet:** this may remove the RCP boundary, but it is a different distribution of the border-router, BLE/API and networking functions. Stock availability, RAM/stack margins and compatibility must be demonstrated; it is not physically impossible merely because the current build does not implement it. The earlier [H2 function audit](../../../../docs/h2-quartet-function-audit.md) records why those ports were not selected for MC1.

**MG24 as Ethernet bridge:** the current XIAO runs a dedicated Ember NCP. Adding Ethernet and multiplexing its four-wire 115200-baud serial path would change that boundary and require a new S3 network adapter while preserving normal EZSP/ASH behavior. That channel carries at most 11520 bytes/s before protocol overhead and Zigbee traffic. Additional GPIO availability alone does not provide this firmware or equivalent throughput. Keeping Zigbee's existing NCP role also isolates network failures from its serial recovery path.

The unused WK2132 UART2 could offload radar and save two S3 GPIO, but its current driver intentionally implements UART1 only. Dual-channel service at radar 256000 plus Z-Wave 115200 needs driver work and an I²C throughput/latency audit. It is another optional redesign, not a free resource already available to the current firmware.

These are implementable research directions when a much smaller pin-limited host justifies them. The Nano fits the complete application with 21 GPIO and stock shared-SPI support, while the Mini fits with 24 GPIO and two buses. Neither requires moving Ethernet onto an auxiliary radio MCU; doing so has no demonstrated physical advantage proportional to the additional network, performance and recovery complexity.
