# MC1 XIAO MG24 Ember NCP

This is the MC1 carrier's dedicated Zigbee coordinator firmware for the **Seeed Studio XIAO MG24 Pre-Soldered, SKU 102010690**, using **EFR32MG24B220F1536IM48**. It replaces the M0 bare-module assembly while retaining the existing Ember host protocol. It is not the M0 MGM240P image and is not the community XIAO image that communicates through the onboard USB serial bridge.

**Build and offline validation passed. Hardware commissioning is still required.** Actual compiled images were produced locally; the repository publishes their checksums in [build-evidence.json](build-evidence.json), plus source and build recipes. Generated images remain ignored. No radio, USB programmer, Home Assistant installation or production Zigbee network was accessed during this build.

## Electrical and software contract

- XIAO **D6 / PC06 / TX** goes to S3 **GPIO18 / RX**.
- XIAO **D7 / PC07 / RX** comes from S3 **GPIO17 / TX**.
- XIAO **D4 / PC04 / CTS** comes from S3 **GPIO16 / RTS**.
- XIAO **D5 / PC05 / RTS** goes to S3 **GPIO21 / CTS**.
- **115200 baud, eight data bits, no parity, one stop bit, hardware RTS/CTS**. All signals are 3.3 V logic. USART0 is routed to these pins in both application and bootloader.
- XIAO **D0 / PC00** is the active-low bootloader entry input. MC1 J8 exposes D0 and ground for a temporary service jumper. Leave J8 open for normal operation.
- Power enters the XIAO **5V** pin through the carrier's Schottky diode; **GND** is common. The XIAO **3V3** pin is a regulator output and is not tied to the S3 regulator output. Follow the [Seeed power guidance](https://wiki.seeedstudio.com/xiao_mg24_getting_started/#hardware-overview).
- The factory male headers solder directly into the carrier. No female sockets, castellated-edge soldering, bottom-pad wires or external SWD probe are needed.

MC1 S3 exposes the byte stream on **TCP port 6638**. S3 must implement UART hardware flow control locally; a host TCP option cannot toggle these physical pins. Use one coordinator owner at a time: **ZHA/Bellows** or **Zigbee2MQTT `adapter: ember`**. The application is dedicated Zigbee, not multiprotocol firmware.

For Zigbee2MQTT, select the MC1 address using `serial.port: tcp://<mc1-address>:6638`, `serial.adapter: ember` and `serial.baudrate: 115200`. For ZHA select the Silicon Labs EZSP/Ember radio and `socket://<mc1-address>:6638`. Zigbee2MQTT lists [EmberZNet 8.2.x support and the XIAO board](https://www.zigbee2mqtt.io/guide/adapters/emberznet.html); [Bellows implements EZSP18](https://github.com/zigpy/bellows/tree/dev/bellows/ezsp/v18). This preserves their normal backup/restore interfaces. It does not itself prove migration of a specific live network: validate a backup and recovery on a test network before replacing its coordinator.

## Board adaptation

The application uses **Simplicity SDK 2025.6.3, EmberZNet 8.2.3, EZSP18**. The upstream NCP stack, security, address tables and ASH framing remain the SDK example. The adaptation changes the board interface:

1. Route UART and flow-control signals to the four factory header pins above.
2. Configure the fitted **39 MHz HFXO** with **CTUNE 95** and **32.768 kHz LFXO** with **CTUNE 44**; select HFXO and LFXO as their clock sources. Manufacturing calibration remains enabled, as in the official board configuration. Use the MCU's DC/DC converter, bypass disabled, peak-current override **9**. These values follow [Silicon Labs' XIAO Zigbee configuration](https://github.com/SiliconLabsSoftware/arduino/tree/868660a857077dbdf757c7e9ded96e20fa84e50c/variants/xiao_mg24/zigbee/config), not the older generic CTUNE 140 recipe. Clock frequency, tuning and RF performance still need board measurements.
3. Immediately after GPIO driver initialization, before the radio stack starts, [mc1_board_init.h](mc1_board_init.h) drives **PB04 low** to select **RF1/onboard ceramic antenna**, then **PB05 high** to power its FM8625H RF switch. **PB04 high selects the U.FL antenna**; this firmware deliberately selects the ceramic antenna. See [Seeed's schematic, MCU/RF sheet](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MGM240S_KICAD_Prj.pdf).
4. Keep onboard SPI flash deselected with **PA06 high**, and the active-low user LED off with **PA07 high**. Disable PTI. The NCP uses internal flash for its network state; the extra external flash is not required.

The bootloader never starts the radio. It uses the SDK's boot clock path and the same UART/header assignment, with PC00 entry. The application reestablishes the antenna selection after every restart. The four carrier UART nets do not connect to onboard SAMD11's **PA08/PA09** serial nets. The XIAO USB CDC port is therefore **not a second Zigbee serial interface** in this build; USB remains the onboard CMSIS-DAP programming/debugging connection.

[board-sources.json](board-sources.json) records immutable source links and hashes used to check these settings. [config.json](config.json) is the authoritative machine-readable configuration.

## Reproduce the build

Use SLC **6.0.15**, Java **21**, Silicon Labs Python adapter pack **3.10.1** (its manifest says **3.10.5**), Arm GNU **12.2.Rel1 / GCC 12.2.1**, and Simplicity Commander **1.25.0 build1995**. SLC requires the native JEP adapter pack, not merely Python on PATH. The already existing [Linux dependency bootstrap](../../low-power/mg24/bootstrap_linux.py) and [version/checksum lock](../../low-power/mg24/dependencies-linux.json) can provision these same tools; this new recipe does not modify M0.

Set the following shell variables to their installed locations, then run from the repository root. Output must be a new directory; no command below flashes hardware.

```sh
python3 firmware/module-carrier/zigbee/generate.py \
  --sdk "$SISDK_DIR" --slc "$SLC_BIN" --gcc "$ARM_GCC_DIR" \
  --python-pack "$SILABS_PYTHON_PACK" --java-home "$JAVA21_DIR" \
  --output "$MC1_BUILD_DIR"

python3 firmware/module-carrier/zigbee/build.py \
  --project "$MC1_BUILD_DIR" --gcc "$ARM_GCC_DIR" \
  --commander "$COMMANDER_BIN"

python3 -m unittest discover -s firmware/module-carrier/zigbee -p test_recipe.py -v
```

The build checks the generated macros and board-initialization hook before compiling. It verifies S-record checksums, Cortex-M vectors, separate bootloader/application ranges, the exact merged image, and GBL/Intel HEX conversion roundtrips. Its report records recipe and image SHA-256 hashes. SDK version/protocol headers are checked; an unpacked SDK's complete Git identity is not attested by this check. Nine SDK-independent tests cover malformed images, unsafe substitution, omitted/duplicate macros, native Python runtime validation and the required RF initialization hook.

## Initial programming and recovery

The initial image includes a **24 KiB reserved bootloader region** and the NCP application starting at **0x08006000**. The build produces `artifacts/mc1-xiao-mg24-initial.hex` for initial SWD programming and `artifacts/mc1-xiao-mg24-ncp.gbl` for subsequent application updates through the Gecko UART bootloader. Their SHA-256 hashes are in the build report. Do not substitute the M0 images or the community PA08/PA09 software-flow-control image.

1. Attach a USB data cable to the **XIAO** USB-C port. Its onboard SAMD11 supplies CMSIS-DAP. Prefer initial programming before soldering. For service after assembly, keep the complete carrier normally powered and use the carrier's documented USB VBUS-blocking procedure; do not power only the XIAO while its connected S3 is unpowered.
2. Use the **Silicon Labs Arduino package's OpenOCD 0.12.0-arduino1-static**, including its `target/efm32s2_g23.cfg`. Generic OpenOCD distributions may lack this target. The [official upload recipe](https://github.com/SiliconLabsSoftware/arduino/blob/868660a857077dbdf757c7e9ded96e20fa84e50c/platform.txt) uses that target for this board.
3. After checking the image hash and selecting the intended board, the following is an explicit **programming operation**, not a build command. These commands are documented, **not executed or hardware-verified here**:

```sh
"$OPENOCD_BIN" -s "$OPENOCD_SCRIPTS" \
  -f interface/cmsis-dap.cfg -f target/efm32s2_g23.cfg \
  -c 'init; reset_config srst_nogate; reset halt' \
  -c "program {$MC1_INITIAL_HEX} verify" \
  -c 'reset run; exit'
```

4. Leave **J8 open**, restart, and connect the single HA/Zigbee2MQTT owner to S3 TCP6638. Verify reported stack/EZSP versions and the four-wire handshake under traffic.
5. To enter UART bootloader recovery locally, temporarily bridge **J8 D0 to GND**, press/release the XIAO reset button, then remove the jumper. It uses the same header UART and hardware handshake. The SDK's software bootloader entry command remains available through the NCP. A broken application can instead be recovered through the onboard CMSIS-DAP link; no application firmware is needed for that debug probe.

## Hardware acceptance still open

Before using the assembled carrier on the live home network, measure 5 V/3.3 V supply behavior with both carrier and USB connected; verify boot/recovery and CTS backpressure; check oscillator startup, antenna selection and RF range; then join a test device, exercise sustained traffic and perform a backup/restore test. Compare packet loss and range with the previous coordinator. An equivalent Ember interface preserves the software path, but a successful offline build does not certify soldering, antenna clearance, power integrity or a measured network migration.
