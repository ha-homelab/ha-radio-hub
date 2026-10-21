# MC2-D Zigbee: program the XIAO MG24 external antenna image

This is the current programming route for **U3, Seeed XIAO MG24 Pre-Soldered
SKU 102010690**, on the MC2-D carrier. Use **`--antenna external`** throughout:
the application drives **PB04=1 and PB05=1** before starting Zigbee, selecting
the U.FL connector. Attach the specified 2.4 GHz antenna before running it.

The recipe is shared with MC1 and its files retain `mc1` in their names. This
does not make MC1 host wiring or its default onboard-antenna example suitable
for MC2-D. Build and offline validation have passed; actual radio operation
and physical commissioning still need verification.

## 1. Prepare the tools

Use these pinned tools and set their paths in your shell:

- `SISDK_DIR`: **Simplicity SDK 2025.6.3** directory.
- `SLC_BIN`: **SLC 6.0.15** executable.
- `ARM_GCC_DIR`: **Arm GNU 12.2.Rel1 / GCC 12.2.1** toolchain root containing `bin/`.
- `SILABS_PYTHON_PACK`: Silicon Labs **Python 3.10.1 adapter pack** directory
  containing `apack.json` and its native JEP library. Its manifest reports
  3.10.5; an ordinary Python installation is not a replacement for this pack.
- `JAVA21_DIR`: **Java 21** installation.
- `COMMANDER_BIN`: **Simplicity Commander 1.25.0 build1995** executable.

The [Linux dependency bootstrap](../firmware/low-power/mg24/bootstrap_linux.py)
and [version/checksum lock](../firmware/low-power/mg24/dependencies-linux.json)
cover these build dependencies. For initial programming, also locate the
**OpenOCD 0.12.0-arduino1-static** executable and scripts from the Silicon Labs
Arduino package: set `OPENOCD_BIN` and `OPENOCD_SCRIPTS`. The scripts must include
`target/efm32s2_g23.cfg`; generic OpenOCD installations may lack this target.

Choose a new, **absolute** output path outside the repository and set
`MC2_BUILD_DIR` to it. It must not already exist. Keep it separate from any
MC1/onboard build. Run the following commands from the repository root.

## 2. Generate and build the external image

These commands create files only; they do not program a board:

```sh
python3 firmware/module-carrier/zigbee/generate.py \
  --sdk "$SISDK_DIR" --slc "$SLC_BIN" --gcc "$ARM_GCC_DIR" \
  --python-pack "$SILABS_PYTHON_PACK" --java-home "$JAVA21_DIR" \
  --antenna external --output "$MC2_BUILD_DIR"

python3 firmware/module-carrier/zigbee/build.py \
  --project "$MC2_BUILD_DIR" --gcc "$ARM_GCC_DIR" \
  --commander "$COMMANDER_BIN"
```

The build emits the following under `$MC2_BUILD_DIR/artifacts/`:

- **`mc1-xiao-mg24-external-initial.hex`**: initial CMSIS-DAP programming image,
  containing the bootloader and application. The application starts at
  `0x08006000`, after the reserved 24 KiB bootloader region.
- **`mc1-xiao-mg24-external-ncp.gbl`**: application-only image for later network
  updates through the Gecko UART bootloader.
- **`build-report.json`**: board, target, antenna configuration, image hashes
  and offline validation results. Confirm `status` is
  `build-and-offline-validation-pass`, `board_sku` is `102010690`, and `antenna`
  records `mode: external`, `rf_path: RF2/U.FL`, `select_level: 1` and
  `enable_level: 1`. Retain this report with its images.

Do not rename an onboard image to make it appear external. The RF selection is
compiled into the application; the MC2 updater checks the matching metadata.
The exact command schema and filenames come from the shared
[generator](../firmware/module-carrier/zigbee/generate.py),
[builder](../firmware/module-carrier/zigbee/build.py) and
[antenna contract](../firmware/module-carrier/zigbee/antenna.py).

## 3. Program the loose XIAO through its USB-C port

Perform initial programming **before soldering the XIAO into the carrier**.
Connect only the intended loose XIAO to USB, with its antenna attached. Its
onboard SAMD11 provides the CMSIS-DAP probe; no separate SWD probe is required.
Use a USB data cable. Leave other CMSIS-DAP programmers disconnected so target
selection is unambiguous.

After identifying the board and checking the image against its build report,
the following command **writes the initial image to the connected XIAO**:

```sh
MC2_INITIAL_HEX="$MC2_BUILD_DIR/artifacts/mc1-xiao-mg24-external-initial.hex"
"$OPENOCD_BIN" -s "$OPENOCD_SCRIPTS" \
  -f interface/cmsis-dap.cfg -f target/efm32s2_g23.cfg \
  -c 'init; reset_config srst_nogate; reset halt' \
  -c "program {$MC2_INITIAL_HEX} verify" \
  -c 'reset run; exit'
```

**Checkpoint:** OpenOCD finishes programming and verification without errors.
Disconnect USB before mounting the board or applying the assembled hub's PoE
supply. A successful verification checks written bytes, not Zigbee range.

Do not copy this loose-board power procedure onto a soldered carrier. In-circuit
USB service requires checking the complete assembly's power isolation and
backfeed behaviour; use the normal MC2 network update route when available.

## 4. Connect and test on MC2-D

Use the [current MC2-D connector ledger](../hardware/external-antenna/cad/connectors.json)
and [pin guide](external-antennas.md#pin-connections-and-initial-programming).
The host is the classic ESP32, not the S3 described in historical MC1 material:

- Host GPIO32/TX → XIAO D7/PC07/RX.
- XIAO D6/PC06/TX → host GPIO39/RX.
- Host GPIO33/RTS → XIAO D4/PC04/CTS.
- XIAO D5/PC05/RTS → host GPIO14/CTS.

The application and bootloader use **115200 baud, 8N1, hardware RTS/CTS** over
these header pins. The XIAO's USB port is the programming/debug probe, not a
second Zigbee serial adapter. Keep **J8 open** for normal operation.

After [wiring and power checks](start-here.md#4-wire-and-test-the-power-before-connecting-home-assistant),
give the radio one owner: **ZHA** with `socket://HUB_IP:6638` and Silicon Labs
EZSP/Ember, or **Zigbee2MQTT** with `tcp://HUB_IP:6638` and `adapter: ember`.
Use 115200 baud in either case. Replace `HUB_IP` with the hub's actual address.
The host firmware handles the physical RTS/CTS signals.

**Checkpoint:** the host identifies the NCP, then a spare test device joins,
reports and responds. Check the reported SDK/EZSP version against the recipe's
**EmberZNet 8.2.3 / EZSP18** target and run the
[RF acceptance procedure](rf-commissioning.md). An existing household network
needs its backup/migration process before replacing its coordinator.

## Updates and recovery

For later application updates, back up Zigbee state, stop the sole coordinator
owner and follow the **[MC2 network update guide](../firmware/external-antenna/updates/README.md#zigbee-application)**
with the external NCP GBL and matching report. Use the MC2 updater, which checks
the required external antenna mode. The initial HEX is not a network-update image.

If local UART bootloader recovery is needed, MC2 **J8.1** is XIAO D0/PC00 and
**J8.2** is ground. Temporarily short those service pads while resetting the
XIAO, then remove the short. Normal operation requires J8 open. A missing or
damaged bootloader instead needs CMSIS-DAP recovery and an appropriate service
power arrangement; do not power only one connected module through USB.

The [shared MG24 engineering reference](../firmware/module-carrier/zigbee/README.md)
contains advanced clock, image-layout and build-validation detail. Its **MC1/S3
host pin assignments and onboard-image example are historical**; the commands
and connections on this page are the MC2-D route.
