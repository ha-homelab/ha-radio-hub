# RF commissioning for the external-antenna hub

The engineering target is reliable service throughout a roughly **1000 ft²
(93 m²) home**. This is a deployment requirement, not a measured range rating.
External antennas let us move radiators away from the hub electronics and choose
their orientation; they do not prove whole-home coverage.

## Before measuring

1. For the active MC2-D revision, use its matching **classic ESP32/WROVER-IE
   host**, XIAO ESP32C6 RCP and external-antenna MG24 images. MC2-A/S3 and MC1 images
   are not interchangeable. Connect all three 2.4 GHz antennas before enabling their transmitters.
   Check the Zigbee image's **external** antenna label: plugging a cable into the
   XIAO does not change its software-controlled antenna selection.
2. Keep the existing 433.92 MHz antenna on the CC1101 path and the regional
   ZAC93 antenna on its own board. Neither belongs on a 2.4 GHz connector. The
   LD2450 has its own 24 GHz printed array; do not attach a whip to the radar.
3. Start a separate test network. Record actual Wi-Fi, Zigbee and Thread channels
   without changing the production networks. Ethernet removes this hub's Wi-Fi
   traffic, but nearby Wi-Fi and its independent 2.4 GHz radios still matter.
4. Record the firmware versions, antenna models, pigtail lengths, mounting height,
   orientation, test devices and normal reporting intervals. Do not infer link
   quality from advertised antenna gain alone.

## Compare three physical states

Test the same devices and positions on an open bench, with the enclosure closed,
and at the intended central ceiling position. Include the most distant room,
closed doors, the far side of masonry or metal, and the intended locations of
locks and battery sensors. Keep antenna orientation and transmit-power settings
consistent when comparing enclosure effects.

Test each protocol first with the other radios quiet, then with normal combined
Thread, Zigbee, BLE, RF and Ethernet traffic. Also exercise active BLE connections,
RF transmit/receive, network updates, and restoration after PoE power loss. Do not
mistake an open-bench success for a completed installed-enclosure test.

Use [the blank results sheet](../hardware/external-antenna/coverage-results.csv).
Empty measurement fields mean **not measured**, never zero failures.

## Record observable outcomes

- Zigbee/Thread actuators: successful commands out of attempts, response latency,
  retries or route changes where available, and time to recover after a restart.
- Sensors: time since last report, gaps relative to the device's expected cadence,
  missed physical events and unexpected unavailable transitions.
- BLE: received advertisements, missed expected reporting intervals, successful
  GATT operations, disconnects and reconnect time. Passive reception and active
  GATT need separate tests with the actual intended devices.
- Thread diagnostics, if exposed by the selected build: neighbor and router
  tables, link quality and MAC counters. RSSI is supporting evidence; a strong
  RSSI value does not prove low packet loss or low interference.

Agree command timeouts and sensor reporting expectations for each device before
starting. As a project smoke test, run at least 100 actuator operations at each
critical position and a 72-hour normal-use soak. Investigate every missed command,
missed deliberate sensor event, unexplained outage or manual recovery. These are
project acceptance procedures, not industry range-certification thresholds.

## If a position fails

First compare open/closed enclosure and single/combined-radio results. Reposition
radiators, remove nearby metal or cable bundles, and check pigtail seating before
raising transmit power. Keep external cable runs short; extra coax has loss.

Zigbee and Thread need their **own** suitable powered router devices to extend
their respective mesh networks. Battery end devices generally do not route.
Those mesh networks do not extend ordinary BLE reception: add an Ethernet/PoE
Bluetooth proxy near a weak BLE zone and repeat both passive and active tests.
More than one proxy is supported by Home Assistant.

A failed test is a reason to change the deployment or hardware, not to relabel an
unmeasured 93 m² coverage claim as passed. Record the result and repeat the same
positions after each material change.

## Sources

- [ESPHome: reception improvements](https://esphome.io/components/bluetooth_proxy/#improving-reception-performance).
- [Bluetooth SIG: factors affecting range](https://www.bluetooth.com/learn-about-bluetooth/key-attributes/range/).
- [Home Assistant: multiple Bluetooth adapters](https://www.home-assistant.io/integrations/bluetooth/#multiple-adapters).
- [ZHA: powered router devices](https://www.home-assistant.io/integrations/zha/#using-router-devices-to-add-more-devices).
- [OpenThread: node roles](https://openthread.io/guides/thread-primer/node-roles-and-types).
- [OpenThread CLI reference](https://openthread.io/reference/cli/commands).
- [TI: antenna selection guide](https://www.ti.com/lit/an/swra161b/swra161b.pdf).
