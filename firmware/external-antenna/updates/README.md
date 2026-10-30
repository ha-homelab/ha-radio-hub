# MC2-D Ethernet updates

This is the MC2 counterpart of the [MC1 checked update procedure](../../module-carrier/updates/README.md). Use the MC2 `update.py` and C6 image, not the MC1 H2 command. The implementation retains the authenticated temporary UART tunnel, durable maintenance interlock, application-only write, identity check and explicit execution gate. Install the pinned packages in `requirements.txt` in an isolated virtual environment.

## C6 application

The C6 report must name **Seeed Studio XIAO ESP32C6 / 102010636 / MC2-D**, record GPIO3 LOW / GPIO14 HIGH external selection and 4 MB flash, and match the board-specific `mc2d-xiaoc6-ext-v1` IDF descriptor. Earlier TinyC6[D]/TinyC6-U-01 reports and renamed binaries are rejected before connecting. Automated recovery requires **both bottom-pad EN/BOOT service wires to J10**; the pre-soldered side headers do not carry these signals. Onboard GPIO8 pull-up is already fitted. A successful transfer is followed by the C6's reset-time GPIO check; a failed check stops Thread and reports the error through its native USB console.

Confirm the installed radio is the XIAO ESP32C6 on the MC2-D carrier before updating. The unchanged ESPHome host name and MAC identify the host, not which C6 board is physically connected; image checks cannot identify the fitted radio board. Initial replacement of TinyC6 requires a full standalone USB flash of the XIAO, including the matching bootloader and partition table.

Save the output of `firmware/external-antenna/verify_c6.py` as `c6-report.json`. The updater requires a matching hash, **esp32c6**, **4 MB flash**, **RX17/TX16**, and the verified application offset **0x10000**. It rejects H2 reports. Commands without `--execute` only validate local files and print a plan; they do not contact the hub.

The supported **XIAO ESP32C6 already includes R13, a 5.1 kΩ GPIO8 pull-up to its local 3.3 V rail**. No external GPIO8 pull-up is required; MC2-D intentionally omits carrier R3. ROM download needs GPIO8 HIGH and GPIO9 LOW at reset. During commissioning, confirm the fitted module matches the supported XIAO revision, verify the strap voltage and check both EN/BOOT service wires to J10 before relying on network recovery.

```sh
python3 firmware/external-antenna/updates/update.py c6 \
  --host <mc2-address> --image /path/to/build/esp_ot_rcp.bin \
  --report /path/to/c6-report.json
```

For the authorized update, set `MC1_API_KEY` to the deployed encrypted ESPHome API key (the environment variable name is retained for the existing tooling) and add `--mac <expected-base-mac> --execute`. Do not place the key in command arguments. The tool persists C6 maintenance, restarts the hub once, opens a token-authenticated UART session, invokes esptool for **C6 app 0x10000 only**, closes the tunnel and retries Thread. Bootloader, partitions, eFuses and existing host datasets are not written. An interrupted update leaves Thread in maintenance; restore a matching C6 application and retry. DevKitC USB-UART recovery and local C6 BOOT/RESET are the fallback when host service is unavailable.

## Zigbee application

Use **`mc1-xiao-mg24-external-ncp.gbl`** and its matching `build-report.json` from the [MC2-D XIAO programming guide](../../../docs/mc2-zigbee.md). MC2 requires explicit external-antenna metadata with **PB04=1 and PB05=1**. It rejects onboard and old unlabelled reports. Keep the external antenna attached.

```sh
python3 firmware/external-antenna/updates/update.py mg24 \
  --host <mc2-address> --image /path/to/mc1-xiao-mg24-external-ncp.gbl \
  --report /path/to/build-report.json
```

After backing up the Zigbee network and stopping its single ZHA/Zigbee2MQTT owner, add `--coordinator-stopped --execute`. This updates only the application through existing TCP6638; it does not flash the initial HEX or bootloader. Initial USB/CMSIS-DAP and J8 recovery follow the [MC2-D XIAO guide](../../../docs/mc2-zigbee.md#updates-and-recovery).

MC2-D classic ESP32 app-only OTA uses ESPHome after the correct MC2-D factory partition layout has been installed. Back up deployment secrets and Thread credentials separately. No update has been executed on assembled hardware as part of development validation.

MC2-D host identity is `mc2-classic-hub`. Its ESP32-WROVER-IE image is incompatible with the previous MC2-A ESP32-S3 image and carrier. Initial migration requires a full USB-UART factory installation on the new host; do not treat the host-generation change as an OTA update. GPIO1/3 remain connected only to the DevKitC USB-UART bridge. Runtime serial console output is disabled so the remapped UART0 can serve LD2450.
