# Browser USB installation

You can install a privately built **MC2-D ESP32 host** image from a browser.
The laptop connected to USB needs a compatible browser and a data cable; the
firmware build can run on another computer or server. This project does not
currently publish a generic, ready-to-flash full-hub image.

The hub needs its actual MQTT settings, encryption key, OTA password and RF
configuration. The complete build also includes local components, the matching
partition table and a pinned upstream Thread REST component. Copying only
`hub.yaml` into ESPHome Device Builder is insufficient. The validation scripts'
disposable credentials and `build-only/rf/*` topics are not deployment settings.

## Choose the physical board first

- **MC2-D host:** Espressif **ESP32-DevKitC-VIE / ESP32-WROVER-IE**, classic
  ESP32, 8 MB flash, quad PSRAM and ECO V3 or later. Use the complete MC2-D
  private build below. Its initial installation image is `firmware.factory.bin`.
- **Thread RCP:** Seeed **XIAO ESP32C6**, pre-soldered SKU **102010636**, 4 MB
  flash, with the MC2-D external-antenna configuration. This is a separate
  ESP-IDF application, not the ESPHome host. Follow the
  [C6 build and initial programming instructions](../firmware/external-antenna/README.md#reproduce-the-c6-rcp).
  No browser-ready C6 factory bundle is published here yet.
- **Zigbee NCP:** Seeed **XIAO MG24**, pre-soldered SKU **102010690**, uses a
  Silicon Labs MCU. ESPHome Web cannot flash it. Use the
  [MG24 programming and recovery guide](mc2-zigbee.md).

Images for the historical S3, MC1 or low-power designs are not interchangeable
with MC2-D. A browser can detect a chip family, but that does not establish the
board, memory size, antenna routing, carrier wiring or partition compatibility.

## Prepare the complete private host image

Use a reviewed checkout or complete source package on the **build computer**.
Follow [the host build prerequisites](../firmware/external-antenna/README.md#reproduce-the-host-build)
with **ESPHome 2026.10.0 and ESP-IDF 5.5.5**. These requirements apply to the
builder; they do not need to be installed on the USB laptop.

1. From the repository root, prepare a new private directory:

   ```sh
   python3 firmware/external-antenna/prepare.py "$HOME/ha-radio-hub-private/mc2d"
   ```

   Keep the **entire generated directory tree**. The preparer copies the local
   component packages and retrieves the pinned REST source. It also creates
   disposable example credentials that must be replaced before deployment.

2. Complete the private configuration described in
   [initial host programming](../firmware/external-antenna/README.md#initial-host-programming-with-private-configuration).
   Set the real API encryption key, OTA password, MQTT credentials, RF source,
   topics and any required learned-button codes. Preserve the reviewed board,
   pin, memory and partition settings. Keep the configuration outside Git.

3. Compile the private configuration without uploading it:

   ```sh
   /path/to/pinned/esphome compile \
     "$HOME/ha-radio-hub-private/mc2d/firmware/external-antenna/hub.yaml"
   ```

   Replace `/path/to/pinned/esphome` with the prepared ESPHome executable. If
   using Device Builder on the build server, it must have the same pinned
   toolchain and complete prepared file layout; use **Manual download → Factory
   format** after compiling this private configuration.

4. Retrieve the resulting **`firmware.factory.bin`** from this build, using the
   output location printed by the compiler, and transfer it privately to the
   USB laptop. The merged factory image includes the initial bootloader and
   partition layout. An app-only `mc2-classic-hub.bin`, an OTA file, a source ZIP
   or an image from `validate.py` is not a substitute.

The personalized binary contains deployment configuration. Do not attach it,
its build log or `secrets.yaml` to a public issue or release.

## Install from the browser

1. Program the loose DevKitC-VIE before permanent assembly. Attach its intended
   external antenna. Disconnect PoE, other external power and peripherals;
   power the loose board only through its **Micro-B USB data connection**.
2. Open [ESPHome Web](https://web.esphome.io/) in a desktop browser with Web
   Serial support. Current Chrome or Edge is the recommended path. Availability
   depends on the browser and OS exposing `navigator.serial`; mobile and iOS
   are not a supported installation path in this guide.
3. Select **Connect** and choose the DevKitC's USB-UART port. Do not select the
   C6, MG24 or another connected device. Close serial monitors that hold the
   port open.
4. Choose **Install**, select the private `firmware.factory.bin`, and check the
   target again before confirming the write. A factory installation can replace
   existing data; preserve the existing configuration and network backups
   before reusing an installed board. Do not select a generic "prepare" image
   instead of your compiled MC2-D image.
5. If automatic boot entry fails, hold **BOOT**, press and release **EN**, then
   release **BOOT** when the connection begins. Keep power and USB stable while
   writing. After completion, disconnect USB before connecting the assembled
   carrier's normal power supply.

This host uses Ethernet; the browser does not provision its Wi-Fi. Runtime
serial logging is disabled because the application uses the UART for LD2450.
After assembly, use the encrypted ESPHome API over Ethernet to inspect logs.
Verify MQTT, each radio and peripheral, and concurrent operation through the
[commissioning procedure](rf-commissioning.md). A successful USB write is not
hardware acceptance or Home Assistant migration.

## Troubleshooting and later updates

- **Connect is unavailable:** use HTTPS ESPHome Web in a browser exposing Web
  Serial. Try a current desktop Chrome or Edge installation.
- **No serial port:** use a known data cable, connect directly rather than
  through an unreliable hub, and install the USB-UART bridge manufacturer's
  driver if the OS does not detect it. On Linux, check access to the serial
  device according to the distribution's group/udev guidance; avoid making the
  device world-writable.
- **Port busy or permission rejected:** close other serial clients and grant
  access to this exact port in the browser. Reconnect after an OS driver change.
- **Wrong-chip or boot failure:** stop and verify the board, flash/PSRAM size,
  complete factory image and selected port. Do not bypass a chip mismatch or
  flash the host image into the C6. Existing unknown layouts require reviewed
  recovery, not repeated erase attempts.
- **Flash succeeds but the hub is absent:** connect its intended Ethernet
  network after assembly, check DHCP and the private MQTT/API settings, then use
  encrypted network logs. USB installation does not supply missing credentials.

For later updates on a confirmed matching host, retain the
[existing verified-target update procedure](../firmware/external-antenna/updates/README.md).
The C6 and MG24 keep their own image identities, backup requirements and recovery
paths. Hardware testing of the complete MC2-D assembly remains outstanding.
