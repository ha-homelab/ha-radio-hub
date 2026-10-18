# SMLIGHT SLZB Thread comparison

This review compares the current SMLIGHT SLZB family with the complete MC1 compact-S3 proposal. The user confirmed that “ZLB” meant SMLIGHT SLZB. It is a source-based engineering assessment, not a test of a purchased SMLIGHT device or a new carrier implementation.

Open the [visual comparison](index.html) or [architecture diagram](comparison.svg). The supporting reviews cover [hardware](hardware-review.md), [firmware and failure recovery](firmware-review.md), and [Home Assistant compatibility](compatibility-review.md).

## Decision

Keep S3-Nano-M as the full-function candidate. SLZB-MRxU confirms that an ESP32-S3 host, W5500 and two separate radio MCUs are a practical commercial architecture. The U-series local-OTBR mode is relevant; the older remote-radio mode puts the Thread stack on a different computer and has a different failure boundary.

The native SLZB-OS BLE proxy forwards advertisements but does not supply the three active BLE connections in our ESPHome profile. The official alternative ESPHome profiles support active BLE but the reviewed profiles export radio UART streams instead of providing the same local-OTBR service. These are separate firmware configurations, not interchangeable feature checkboxes.

Their 2 MB PSRAM host is useful evidence against treating 8 MB as a universal Thread requirement. It does not establish our full application's peak memory use. Nano still offers ordinary factory pins, sufficient GPIO and 8 MB PSRAM with ample OTA headroom.

## Improvements to prioritize

1. Define and test fatal RCP failure handling. The pinned stack can assert or terminate and reboot the entire S3; normal returned-error handling does not cover every failure. Do not mistake an empty callback for fault isolation.
2. Exercise Ethernet disconnect/reconnect, address changes, IPv6/OMR routes, discovery and Thread dataset persistence. Some of this belongs to ESP-IDF already; test the complete behavior before duplicating it.
3. Measure heap, stacks and transport latency during simultaneous Thread, active BLE, Zigbee, Z-Wave, RF, radar and OTA load. Keep the existing REST contract tests.
4. Verify an OTA health/rollback and service-recovery procedure. Existing SDK rollback infrastructure is not proof of the desired application health policy.

SMLIGHT Ultima's I2C expander is worth understanding, but moving just H2 reset/BOOT to another module saves two native GPIO while adding hardware and a startup dependency. Nano already fits the 21-pin plan. Ultima can replace several assembled functions, but complete parity with our active BLE, LD2450 and existing RF/environment interfaces is unproven.

## Evidence and scope

The latest release entry is not automatically the stable channel. The local-OTBR documentation still describes a beta path; distinguish current release notes from older generic mode pages. The project has not established a license-compatible port of the current SLZB-OS implementation. Public old core code, official ESPHome configurations and downloadable SLZB-OS binaries have different evidence and licensing boundaries; see the firmware review.

No active firmware, PCB, radio image or household network was changed. The source-identified RCP failure risk has not been reproduced on hardware or fixed in this review.

Regenerate and check the visual artifacts from the repository root:

```sh
python3 hardware/module-carrier/studies/slzb-thread/render.py
python3 hardware/module-carrier/studies/slzb-thread/render.py --check
```

[decision.json](decision.json) contains the conclusions and comparison data. Screenshots are browser captures of the generated diagram, not fabricated product photographs.
