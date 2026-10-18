# RF Airbridge → Ethernet: configuration migration and HA cutover

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](../docs/module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

The wired branch uses a **dedicated Waveshare ESP32-S3-ETH-M + CC1101** and `firmware/rf-ethernet.yaml`. The original ESP8266 board remains ready for rollback. This guide covers preparation **without access to the live network**; flashing commands and HA changes are performed separately after bench testing. Current compilation and test status is recorded in [validation.md](../docs/validation.md).

The original contract comes from [RF Airbridge, revision c96777d](https://github.com/ha-homelab/rf-airbridge/tree/c96777d0df65a7420e4883d79187f31eb1b98c9b). This port moves the application RX/MQTT/API contract to another board. It does not transfer the ESP8266's unique hardware identity: the Ethernet board has a **different MAC**, so retaining the name and API key alone does not preserve the HA device ID or entity-registry unique ID.

## What is migrated

The installation's `esphome.name`, `friendly_name`, `rf_source`, `rf_received_topic`, `rf_raw_topic`, `rf_transmit_result_topic`, eight `rm433_button_*_code` values, MQTT settings and private `binary_sensor` definitions are preserved. Default event topics are `rf/received`, `rf/received/raw` and `rf/transmit/result`. Do not replace existing custom values with example values.

Application contract:

- RX publishes `schema: 1`, `source`, `origin: radio`, `format`, `frequency_mhz`, `boot_id`, `sequence`, `event_id` and `uptime_ms`. RC-Switch retains `protocol`, `bits` and **string** `code` and `value`; leading zeros in `code` are preserved. `boot_id`, `sequence`, `event_id` and `uptime_ms` naturally change after replacement/restart and do not identify the remote control.
- RM433 remains a separate `format: rm433` with `encoding: rc_switch_1`, 24 bits and `pulse_length_us`; repeated identical codes are suppressed until 350 ms of silence. The native `RM433 Button` event retains types `button_1`…`button_8`. Do not transmit RM433 through standard 350 µs RC-Switch protocol 1: its timing is different.
- MQTT events use QoS 0 and `retain: false`; there is no delivery buffer for an offline period. Raw learning is off after startup; unknown raw frames are published with length/rate limits. Reception never triggers an RF transmission by itself.
- The native API retains `send_rf_code(code, protocol, repeats)` and `send_dooya_code(remote_id, channel, button, check, repeats)`. For a node named `rf`, these register as `esphome.rf_send_rf_code` and `esphome.rf_send_dooya_code`; verify the actual names in HA.
- Both actions share one `mode: single` worker: a new command receives `busy` when the transmitter is occupied instead of entering a queue; a 750 ms transmit cooldown follows RMT completion. RX resumes immediately on successful completion while new TX requests are still blocked; the entire cooldown is not an RX-suppression window. Results `invalid_request`, `busy` and `send_finished` are published on the original result topic. The new `send_failed` result reports a detected radio/RMT error or expiry of the cooperative 30-second completion wait; after a fault latches, restart the node and investigate the cause. For successful software transmission, specifically check `status: send_finished` and `receiver_resumed: true`. `delivery_confirmed: false` remains in every case: verify the physical receiver's action separately.

**Timeout limitation:** the script counts 30 seconds only while the event loop continues to run. The stock RMT transmitter can block in `rmt_tx_wait_all_done(-1)`; this is not a guaranteed 30-second bound on a hang or a promise of automatic recovery. If the loop is blocked, `send_failed` may not be published either. Board behavior, the watchdog and recovery from a real driver hang require separate bench testing.

Changing transport does not require changing these payload fields in MQTT automations. However, private templates, callback lambdas, sensor filters and HA device references must be checked against the actual configuration. C++/YAML test parity does not prove the analog timing or range of the new CC1101 wiring.

## Wiring changes

The old NodeMCU used one shared GDO0/GPIO4 line for TX/RX. The new RF board uses separate SPI3: SCLK7, MOSI8, MISO6, CS15; **GPIO4 TX → GDO0, GDO2 → GPIO5 RX**, with only 3.3 V power and common ground. GPIO4 is **open-drain** and requires an external **4.7 kΩ pull-up to 3.3 V**. The line is released after TX: CC1101 also drives GDO0 in receive mode, so a normal push-pull output can cause driver contention. Before powering on, verify that GDO2 is available on the actual module and review the [complete wiring](wiring.md).

The new ESP32 receiver uses `filter: 150us`: the old 250 µs setting removes short RM433 pulses of about 240 µs during RMT software filtering. The importer preserves a lower explicit threshold, but replaces an old threshold above 170 µs with 150 µs and records this in `report.json`. Recheck noise immunity and normal motion sensors on the bench.

The port uses a minimal local RMT receiver patch for ESPHome 2026.9.1 that stops/resumes capture around TX. This is a separate ESP32 implementation; the old project's ESP8266 interrupt patch is not treated as RMT-compatible. Bench verification of RX→TX→RX, GPIO4 release and absence of self-echo remains mandatory.

## 1. Private backup

Before making changes, save the following in private storage:

1. The active device YAML, its include/package files, `secrets.yaml`, ESPHome version and a known working ESP8266 binary.
2. An HA backup and sources for RF automations/scripts/dashboards. Separately record the old **entity ID → sensor purpose/code** mapping, device IDs, API action names, MQTT source/topics/client ID and discovery settings.
3. Several reference observations from RF devices you own: received-event fields, RM433 hold behavior, the effect of known RC-Switch/Dooya commands and RX resumption after TX. Do not publish actual codes or payloads.

Do not reflash the old board. A second CC1101 is convenient for an independent bench setup; if moving a single module, disconnect power from both boards before rewiring it.

## 2. Offline configuration preparation

`tools/migrate_rf.py` supports a standard **RF Airbridge device wrapper**: `packages.rf_airbridge`, standard API/OTA/MQTT settings, an inline `binary_sensor` list, ordinary `web_server` settings and a limited set of CC1101/receiver parameters. It works with YAML nodes, preserves `!secret`, `!lambda`, code strings and entity filters, does not execute YAML, does not connect to HA/MQTT and does not read files referenced by `!include`.

Supported `esphome.comment`, `project.name/version`, `min_version` and `compile_process_limit` fields are preserved. `project.on_update` requires manual migration, as do other lifecycle hooks; it is not silently discarded. The purpose of metadata is described in [ESPHome Core](https://esphome.io/components/esphome/). The local RF receiver patch still requires exactly ESPHome 2026.9.1, so an incompatible source `min_version` will be detected when validating the final wrapper.

From the repository root, in an environment with `firmware/requirements.txt` installed:

```sh
umask 077
python tools/migrate_rf.py \
  --source /path/to/private/device.yaml \
  --secrets /path/to/private/secrets.yaml \
  --output private/rf-cutover
```

This creates `private/rf-cutover/device.yaml`, `secrets.yaml` and `report.json`. The directory has mode 0700 and files have mode 0600; an existing directory is not overwritten. Console output reports only the sensor count. Inside the repository, migration output is allowed only under Git-ignored `private/`; still check `git status` before committing. Ordinary old `esp8266`, `wifi`, `spi` and `logger` settings are replaced by the new board profile and listed in the report; hooks such as `wifi.on_connect` require manual migration and stop the import.

MQTT secrets are exported as `mqtt_broker`, `mqtt_username` and `mqtt_password`. `api_encryption_key` and `ota_password` are added only if the corresponding setting exists in the source: an empty `api:` block and ESPHome OTA without a password retain the absence of those settings. The importer requires an explicit source API block, does not guess keys, and does not remove existing encryption or passwords. Other secrets actually used are also copied; unused Wi-Fi credentials are unnecessary on the new board. Exported `secrets.yaml` values must be literals: nested `!include`, `!lambda` and references to other secrets are not migrated automatically. If a source `!secret` reference uses one of the exported names for a different value, the import stops before writing output. Rename that source secret and its references; identical values do not cause a conflict.

From `cc1101`, the importer retains `frequency` only for the 433.92 MHz profile and retains `max_dvga_gain`; the old `cs_pin` is replaced. From `remote_receiver`, it retains `dump`, `tolerance`, `idle` and a supported `filter`, while replacing the old `pin`. Supported `web_server` fields are `port`, `auth`, `version`, `local`, `include_internal` and `enable_private_network_access`; custom callbacks and extra fields require manual adaptation. Replacement of old pins and adjustment of an excessive receiver filter are recorded in the report.

The automatic path assumes the included `rf-airbridge.yaml` matches the stated RF Airbridge source. The importer checks the `!include` form and filename, but does not read or prove the identity of its contents: compare your package with the pinned upstream revision. Use manual migration for a modified package.

The tool intentionally stops on unsupported firmware blocks and radio-profile parameters, custom API actions, RX callbacks, nested includes, conflicting component IDs and duplicate YAML keys. This means manual migration is required; it is not permission to delete old logic. For an old monolithic YAML, create a private wrapper manually and transfer all required entity definitions, filters and custom callbacks. ESP8266-specific code needs separate adaptation.

Manual-wrapper structure, without installation-specific values:

```yaml
substitutions:
  rf_airbridge_path: ../../firmware
  rf_node_name: rf
  rf_friendly_name: RF
  rf_source: rf
  rf_received_topic: rf/received
  rf_raw_topic: rf/received/raw
  rf_transmit_result_topic: rf/transmit/result
packages:
  rf_ethernet: !include ../../firmware/packages/rf-ethernet-base.yaml
api:
  encryption:
    key: !secret api_encryption_key
ota:
  - platform: esphome
    password: !secret ota_password
mqtt:
  broker: !secret mqtt_broker
  username: !secret mqtt_username
  password: !secret mqtt_password
# Add private rm433_button_*_code substitutions and binary_sensor definitions here.
# Keep private secrets.yaml beside this file with the keys actually used.
```

These paths assume `private/rf-cutover/device.yaml`. The example shows configured API encryption and an OTA password; if the original installation had neither, the importer preserves their absence. The wrapper includes a credential-free base: `!secret` must resolve beside the private wrapper, not beside the public top-level file. Do not replace this include with `firmware/rf-ethernet.yaml`. `rf_node_name: rf` is only an example: preserve the actual old name. Unset RM433 slots are disabled by default; the public project does not contain your 15, or any other number of, installation-specific sensors.

Also check the receiver-filter normalization notice for 150 µs; this is needed for RM433 on ESP32. Review the diff locally: identity, source/topics, discovery/availability/client ID, all codes, bit lengths, delay filters, names and internal sensor `id` values. Then compile **this exact wrapper**, not just the public template:

```sh
esphome config private/rf-cutover/device.yaml > private/rf-cutover/config-check.log 2>&1
esphome compile private/rf-cutover/device.yaml > private/rf-cutover/build.log 2>&1
```

Expanded configuration and logs may contain secrets; keep them private. Do not flash the device before compilation succeeds and warnings have been reviewed. This step does not change the working home installation.

## 3. Bench testing before cutover

Do not start the new node on the production broker with the old name/client ID/topics while the old node is still active. This can disconnect MQTT sessions, duplicate commands and overwrite discovery records.

For parallel comparison, create a separate private bench copy with a different node name and either a separate MQTT broker or entirely separate `rf_*_topic`, `mqtt.topic_prefix` and `mqtt.client_id` values; disable MQTT discovery on the bench node. Do not connect its events to production actuator automations. Before final cutover, restore the original contract and compile the final wrapper again.

Flash the second S3-ETH over USB with PoE disconnected. For the prepared bench copy, use the following command, replacing `SERIAL_PORT` with the board's actual port:

```sh
esphome upload private/rf-bench/device.yaml --device SERIAL_PORT
```

Check Ethernet/API/MQTT with the test configuration. Ensure that the stock RF antenna is connected. Receive real commands from your own remotes, compare payloads with the reference and observe RM433 hold/repeat behavior. Transmit only a known command to a receiver you intend to control, then check RX again. TX must not produce a self-echo that triggers control actions; accumulated captures are flushed during the transition. After completion, separately check resumed RX and the absence of unwanted repeats during the 750 ms TX cooldown. Test `busy`, invalid arguments, `send_failed` through bench fault injection, restart after a fault, broker disconnection and recovery without replaying old button presses. Invalid input arguments must not disrupt RX; a hardware/RMT fault blocks transmission and may leave capture disabled until restart.

The native `RM433 Button` event can fire while MQTT is unavailable; this is part of the original architecture, not a reason to enable two automations for one press. Do not add a transmit queue over the existing single-worker behavior without separately updating the scenarios.

## 4. Home Assistant cutover

First finish any active RF scenarios and temporarily disable affected automations, especially those transmitting commands. Save a list so they can be re-enabled.

1. Power off the old ESP8266. Keep its integration and records for rollback, but disable the old integration during cutover. Old and new nodes with the same name/client ID must not run simultaneously.
2. After the old node is off, flash the final wrapper over USB: `esphome upload private/rf-cutover/device.yaml --device SERIAL_PORT`. Then disconnect USB, restore normal power and connect the final S3-ETH with the production private configuration. Record the new Ethernet MAC and DHCP reservation. The old Wi-Fi DHCP reservation does not automatically become an Ethernet reservation.
3. Add the new physical node to the ESPHome integration using its actual address and, if encryption is configured, the API encryption key. Check its MAC/board: a matching name does not prove that the old registry record was transferred. Do not manually edit `.storage` or spoof the MAC/unique ID.
4. Match new entities to the old private list by purpose, code/channel and type, not discovery order. Temporarily rename each old inactive entity to an unused ID with an `_legacy` suffix, then assign the previous entity ID to the corresponding **new** entity through Settings → Devices & services → Entities. Log both sides for rollback. [HA allows entity IDs to be changed in entity settings](https://www.home-assistant.io/docs/configuration/customizing-devices); verify this operation for the specific integration.
5. Separately update `device_id` references/device triggers to the new board. They use internal device identity, so preserving the entity-ID string is insufficient. Check areas/labels, conditions, service targets, templates and dashboards. [HA device triggers](https://www.home-assistant.io/triggers/device/) describes the use of internal IDs.
6. Verify actual action names in Developer tools → Actions. With the same node name, the previous `*_send_rf_code`/`*_send_dooya_code` names are expected, but confirm that each action exists and targets the correct node. Do not replace them with the old experimental `send_rc_switch`.
7. MQTT automations must listen to the original topics and fields. Preserve the original entity-management method: native API or MQTT discovery. Do not create duplicates of one physical sensor through both paths. Discovery-ID generation, `topic_prefix` and MQTT client ID behavior are described in [ESPHome MQTT](https://esphome.io/components/mqtt/); the same name does not guarantee the previous discovery unique ID.
8. Receive one real event of each type; inspect the automation trace while TX scenarios are disabled. Then enable scenarios one at a time and confirm the receiver's physical action. Watch for errors/repeats after restarting HA and the node.

Automatic merging of history/statistics after a registry-identity change is not promised. Keeping an entity ID helps preserve old references, but the complete set of references must be checked separately; HA does not automatically update all YAML automations on rename. See [automation troubleshooting](https://www.home-assistant.io/docs/automation/troubleshooting/).

## 5. Rollback

Reasons to roll back include loss of reception after TX, self-echo causing repeated commands, unstable Ethernet/power, changed event semantics or incomplete HA migration. First disable affected automations and wait for actions to finish.

1. Power off the new S3-ETH and disable its integration. This releases the old name and MQTT client ID.
2. If entity IDs changed, rename the new records to temporary unused IDs, then restore the original IDs to the old `_legacy` records using the log. Restore `device_id` references and changed actions/automations from backup. Do not delete the new records until rollback is verified.
3. If moving the only CC1101, disconnect power from both boards and restore the old NodeMCU wiring. Do not copy the new open-drain/GDO2 wiring to the old board without checking its original schematic.
4. Power on the old ESP8266 with its previous firmware, enable the old ESPHome integration and verify MQTT/API and real RF reception.
5. Re-enable automations one at a time. Check that only one node owns each MQTT client ID and that TX actions are not duplicated. Continue fixes for the new board using a separate bench contract.

Neither the generator nor the repository tests change the live home network, broker or registry. Saved private files support a verifiable cutover; they do not establish that hardware migration has already been completed.
