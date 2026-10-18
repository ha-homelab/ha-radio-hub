# MC2 Ethernet updates

This is the MC2 counterpart of the [MC1 checked update procedure](../../module-carrier/updates/README.md). Use the MC2 `update.py` and C6 image, not the MC1 H2 command. The implementation retains the authenticated temporary UART tunnel, durable maintenance interlock, application-only write, identity check and explicit execution gate. Install the pinned packages in `requirements.txt` in an isolated virtual environment.

## C6 application

Save the output of `firmware/external-antenna/verify_c6.py` as `c6-report.json`. The updater requires a matching hash, **esp32c6**, **8 MB flash**, **RX17/TX16**, and the verified application offset **0x10000**. It rejects H2 reports. Commands without `--execute` only validate local files and print a plan; they do not contact the hub.

The assembled carrier must include the **10 kΩ C6 GPIO8 pull-up to the C6's own 3.3 V output** (headers 10 and 4). ROM download needs GPIO8 high and GPIO9 low at reset. A compiled image cannot compensate for this missing resistor; verify the strap voltage during commissioning before relying on network recovery.

```sh
python3 firmware/external-antenna/updates/update.py c6 \
  --host <mc2-address> --image /path/to/build/esp_ot_rcp.bin \
  --report /path/to/c6-report.json
```

For the authorized update, set `MC1_API_KEY` to the deployed encrypted ESPHome API key (the environment variable name is retained for the existing tooling) and add `--mac <expected-base-mac> --execute`. Do not place the key in command arguments. The tool persists C6 maintenance, restarts the hub once, opens a token-authenticated UART session, invokes esptool for **C6 app 0x10000 only**, closes the tunnel and retries Thread. Bootloader, partitions, eFuses and existing host datasets are not written. An interrupted update leaves Thread in maintenance; restore a matching C6 application and retry. S3 USB recovery and local C6 BOOT/RESET are the fallback when host service is unavailable.

## Zigbee application

Use **`mc1-xiao-mg24-external-ncp.gbl`** and its matching `build-report.json` from the shared XIAO recipe. MC2 requires explicit external-antenna metadata with **PB04=1 and PB05=1**. It rejects onboard and old unlabelled reports. Keep the external antenna attached.

```sh
python3 firmware/external-antenna/updates/update.py mg24 \
  --host <mc2-address> --image /path/to/mc1-xiao-mg24-external-ncp.gbl \
  --report /path/to/build-report.json
```

After backing up the Zigbee network and stopping its single ZHA/Zigbee2MQTT owner, add `--coordinator-stopped --execute`. This updates only the application through existing TCP6638; it does not flash the initial HEX or bootloader. Initial USB/CMSIS-DAP and J8 recovery follow the [XIAO guide](../../module-carrier/zigbee/README.md#initial-programming-and-recovery).

S3 app-only OTA uses ESPHome after the correct MC2 factory partition layout has been installed. Back up deployment secrets and Thread credentials separately. No update has been executed on assembled hardware as part of development validation.
