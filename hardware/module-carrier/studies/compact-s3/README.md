# Compact S3 host review

**Historical study snapshot.** The selected Nano design is now implemented in [current MC1](../../index.html#pcb). Findings and build evidence below refer to the pre-implementation revision `177a547c70bba11d5f48dee0bdc8595670a4fafb`. Reproduce the old study from that Git revision; use the active firmware instructions for the new board.

The selected next prototype uses **Waveshare ESP32-S3-Nano-M** in place of the large S3 development board. It keeps the S3 as the Ethernet/application host, the existing H2 as the Thread RCP, and XIAO MG24 as the Ember Zigbee NCP. This is a component-selection and firmware-port study; it does not replace the active routed MC1 carrier.

Open [the visual review](index.html), [same-scale module outlines](outlines.svg), or [the retained architecture](architecture.svg). The three reviews cover [hardware and pin access](hardware-review.md), [firmware and alternative architectures](firmware-review.md), and [independent electrical, RF and service checks](independent-review.md).

## Decision

- Nano-M is 43.18 × 17.78 mm and comes with factory male headers. Its body occupies 51.82% less area than the current 62.74 × 25.4 mm S3 module. This is not a claim about final carrier area or delivered PCB price.
- It preserves 8 MB PSRAM and increases flash to 16 MB. Shared W5500/CC1101 SPI reduces the application pin requirement from 24 to 21; all 21 have ordinary header connections.
- Use GPIO43 as H2 UART TX. The existing host resets H2 before starting Spinel, clearing earlier ROM UART traffic. Assign the LED-gate-connected GPIO48 to the slow open-drain H2 BOOT output. Leave GPIO0/3/46 and native USB19/20 outside the application wiring.
- Keep the carrier branch diode and feed Nano **VIN**, leaving its VBUS and local 3V3 pins off the carrier supply rails. Nano's onboard diode supplies the USB-to-VIN path. The proposed regulated 5 V feed is supported by schematic analysis, but must pass loaded-rail tests: it is below the board's advertised external VIN range.
- Expose the existing GPIO0 and ground for recovery and keep EN/reset accessible. Use native USB; this compact board does not include the original DevKit's additional USB-UART bridge.

The LOLIN S3 Mini comparison supports the original two-SPI allocation but reduces flash/PSRAM to 4 MB/2 MB. Tiny and Zero are excluded because their ordinary header pins do not cover the required application signals; bottom pads are not counted as a solution.

Both full firmware builds passed. The [Nano evidence](firmware/build-evidence-nano.json) records a 1,717,232-byte OTA image and 6,409,232 bytes of remaining space in each app slot. The [Mini evidence](firmware/build-evidence-mini.json) records a 1,714,976-byte image and only 120,032 bytes of remaining space per slot. All 14 Nano verifier mutation tests pass. These results establish build and partition fit, not measured hardware behavior.

## Implementation boundary

The [selected pin plan](pin-plan.json) and [isolated firmware preparation](firmware/README.md) make the software proposal reproducible. No deployment configuration, existing radio firmware, device, or active PCB is changed.

The shared-SPI path depends on the reviewed startup ordering and on not calling the unguarded CC1101 manual reset during runtime. Adding that operation requires a complete bus-locked reset or explicitly stopping Ethernet. Compile and source checks do not establish electrical timing or concurrency reliability.

After software review, the next physical step is a new footprint and placement/routing pass with actual module dimensions, antenna clearances, USB/BOOT service access, harness connector housings and RJ45 insertion support. Only then can a smaller carrier outline be claimed. Bench qualification must cover the complete concurrent application, recovery, OTA, loaded supply rails and RF performance.

## Reproduce the visual artifacts

```sh
python3 hardware/module-carrier/studies/compact-s3/render.py
python3 hardware/module-carrier/studies/compact-s3/render.py --check
```

The visuals derive from [decision.json](decision.json). [board-candidates.json](board-candidates.json) contains manufacturer source references and header facts; [architecture-options.json](architecture-options.json) states the assumptions behind the GPIO comparisons. PNG previews are browser captures of the generated SVGs, not generated photographs or fabricated PCB renders.
