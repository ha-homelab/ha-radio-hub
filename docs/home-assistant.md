# Connecting to Home Assistant

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

The appliance appears in HA through standard integrations. Its logical networks remain independent: Zigbee through ZHA, Thread through OTBR, Matter through Matter Server, Bluetooth and sensors through ESPHome, and Z-Wave through the existing Z-Wave JS driver. A second Home Assistant instance on the Pi is not required.

## Zigbee

1. First check that `ser2net` is ready and Pi:6638 is reachable from the HA host. One radio adapter can serve only one Zigbee stack: do not run ZHA and Zigbee2MQTT simultaneously.
2. Settings → Devices & services → Add integration → **Zigbee Home Automation**. Choose manual radio setup with **EZSP/Ember (Silicon Labs)**, serial device path `socket://PI_IP:6638`, and baud rate 115200. RTS/CTS for the physical USB UART is already enabled in `ser2net` on the Pi. Use the `socket://` format, not `tcp://` or `http://`.
3. For a new network, enable pairing and check an event from one test sensor. When moving an existing ZHA network, use its backup/migration process rather than factory-resetting the coordinator.
4. For Zigbee2MQTT instead of ZHA, use adapter `ember` and port `tcp://PI_IP:6638`; do not run it alongside ZHA. This option has not yet been tested on hardware as part of the new hub.

[ZHA](https://www.home-assistant.io/integrations/zha/) supports network serial adapters, but stability depends on the LAN. The radio sits next to the Pi, not next to the HA server. Before updating the coordinator firmware, stop its sole client and `ser2net`; restore the same Ember UART profile after the update.

## Thread and Matter

In HA, add **OpenThread Border Router** with URL `http://PI_IP:8081`. This is the [OTBR REST endpoint](https://www.home-assistant.io/integrations/otbr/), not the web UI on 8080. In the **Thread** integration, check the network name and preferred network; synchronize Thread credentials to the phone using the [HA Thread instructions](https://www.home-assistant.io/integrations/thread/). For an existing network, use its credentials instead of creating a second network with the same name.

The HA server needs **Matter Server**: OTBR does not replace it. HA OS can install the official Matter Server app; HA Container uses the separate [Matter Server instructions](https://github.com/home-assistant-libs/python-matter-server). Connect the Matter integration to the same server that already serves your existing Matter devices. Do not create a new fabric without a reason.

Add a Matter-over-Thread device from the Companion app on the phone while standing near the new device. You need the QR/setup code, the phone's Bluetooth, working IPv6/multicast connectivity, and the correct Thread dataset. **The ESPHome Bluetooth proxy does not replace the phone's Bluetooth during Matter commissioning**. [HA Matter](https://www.home-assistant.io/integrations/matter/) describes this process and the distinction between Matter and Thread: a Thread logo alone does not guarantee Matter support.

After adding one device, check three things: a physical action changes its state in HA; disconnecting the WAN does not prevent local control; and the device returns without pairing again after restarting OTBR with its volume preserved. To check independence, turn off only one radio node at a time.

## Bluetooth, LD2450, and BME680

Add **ESPHome**, using node `ha-radio-hub-sensors.local` or its DHCP reservation and the local API encryption key. HA will receive LD2450 target coordinates/count, presence, uptime, and BME680 temperature/humidity/pressure/gas resistance. Assign the sensors to a room; HA creates the entity IDs, so do not put invented IDs into automations in advance.

Add **Bluetooth** if it is not already present. The [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/) forwards BLE advertisements and provides three simultaneous active GATT connections. Add BLE devices through their own integrations, such as BTHome; the proxy does not make an arbitrary Bluetooth Classic appliance compatible. The number of broadcast sensors is not the number of active connection slots.

LD2450 check: move from left to right and confirm that coordinates change; move away and check the timeout. Do not use presence as the sole condition for switching off a critical load. BME680 check: compare temperature/humidity with a separate sensor after warm-up and with the enclosure closed; Pi heating cannot be corrected by universally subtracting a few degrees. Gas Resistance is published in ohms, not ppm.

## Z-Wave: moving the existing ZAC93

The ZAC93 board retains its existing network when its UART host is replaced, provided its memory is not erased. First back up the existing Z-Wave JS NVM and keys, stop its driver, power off both ESP32 boards, move the four ZAC93 wires according to the diagram, and start the new S3-ETH. The old ESP32 must no longer be physically connected to this module.

In the **existing Z-Wave JS UI**, change Serial Port to `esphome://ha-radio-hub-sensors.local:6053?key=URL_ENCODED_API_KEY`, keeping the network keys. You can generate a correctly encoded URL with this local Python command:

```sh
python3 -c 'from getpass import getpass; from urllib.parse import quote; print("esphome://ha-radio-hub-sensors.local:6053?key=" + quote(getpass("API key: "), safe=""))'
```

The result contains a secret; do not publish it in an issue or log. The transport format is defined by [Z-Wave JS](https://github.com/zwave-js/zwave-js/blob/master/docs/usage/esphome-connection.md). The HA integration's WebSocket server field remains the address of the **Z-Wave JS server**, usually `ws://ZWAVE_JS_HOST:3000`, not ESP32:6053. One driver subscribes to the proxy. A separate connection from the ESPHome integration for BLE/sensors is normal.

Confirm the previous Home ID, radio region, and device list; trigger a physical event on a known Z-Wave sensor. Do not exclude/re-include all devices merely to change the UART host. If the new combination is unstable, stop the driver, return the module to the old ESP32, and restore its transport URL while keeping the same network keys. For a new, empty ZAC93, follow the [zac93-esp32 project](https://github.com/ha-homelab/zac93-esp32).

## RF

The wired RF node uses `firmware/rf-ethernet.yaml` on the **second S3-ETH-M**. MQTT receives the existing `rf/received`, `rf/received/raw`, and `rf/transmit/result` topics; the native API provides `send_rf_code` and `send_dooya_code`. Source/topics and codes come from the private wrapper. The experimental `esphome.radio_hub_rf_received` event and `send_rc_switch` action are no longer interfaces of this port.

Before connecting, follow the [full RF migration procedure](../hardware/rf-migration.md): backup, offline import, private wrapper build, bench test, old-node shutdown, new integration, entity mapping, and rollback. **The MAC address and HA registry identity change**. You can retain the old names in YAML and assign previous entity IDs to the corresponding new entities after releasing the IDs from the old records; check device triggers and `device_id` references separately.

Check the registered action names in Developer tools → Actions. For the previous name `rf`, expect `esphome.rf_send_rf_code` and `esphome.rf_send_dooya_code`. MQTT receive automations retain the previous string codes with leading zeros. Native RM433 events have types `button_1`…`button_8`; do not enable parallel native/MQTT automations for the same button press.

Test RX and command transmission separately: `send_finished` and `delivery_confirmed: false` do not confirm a physical action at the receiver. After every successful transmission, check `receiver_resumed: true` and that RX returns. `send_failed` means a detected radio/RMT error or cooperative timeout; a latched fault requires a restart and investigation. The 30-second timer works only while the event loop is running, so a blocked driver has no guaranteed recovery deadline. After success, RX also works during the 750 ms cooldown, which blocks only new TX commands. All hardware checks still need to be performed on your bench; the repository does not modify the running HA installation.
