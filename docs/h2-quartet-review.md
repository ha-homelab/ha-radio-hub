# Independent consolidation review

Reviewed 2026-10-17. This is a design review, not a statement that Q1 has been
fabricated, flashed or tested. The proposed canonical construction is one
finished-module carrier. The choice of all-H2 versus mixed controllers is a
separate decision from how that carrier is assembled.

## Finding

One carrier can replace the competing C0 + M0, I0 and D0 construction routes.
Factory-populated modules can remove the builder's fine-pitch IC, RF module and
support-component soldering. Factory-fitted male headers enter carrier holes
and are soldered from the underside. There are **zero female module sockets and
no castellated-side solder joints** in this construction rule. More height is
acceptable. Module replacement consequently needs desoldering.

An all-H2 carrier does **not yet establish equivalent functionality or lower
total complexity**. It reduces hardware variety while adding a Thread BR port,
a peripheral transport, and different Zigbee host/recovery behavior. These must
not disappear behind a common Q1 label. Existing designs are themselves
unvalidated hardware: their compiled software and specified interfaces are a
baseline, not evidence of a working household installation.

## Functional parity gates

- **Local Thread BR:** the existing S3 path has a supported Espressif BR library;
  the published ESP-IDF library tree has no H2 BR binary. An H2 build needs a
  genuinely working port, including IPv6 routing, multicast and service
  discovery. A remote RCP connected to a server changes this requirement.
  [IDF linking](https://github.com/espressif/esp-idf/blob/v5.5.5/components/openthread/CMakeLists.txt),
  [library tree](https://github.com/espressif/esp-thread-lib).
- **Zigbee integration:** C0/I0 specify an Ember NCP with UART RTS/CTS and ZHA or
  Zigbee2MQTT. H2 ZBOSS is a different protocol. Stock Z2M calls it experimental
  and lacks its normal adapter backup, install-code and Inter-PAN facilities.
  Its custom ZHA integration currently warns against HA 2026.7+ because of a
  dependency conflict. The author's Z2M NVRAM fork is not equivalent to standard
  cross-adapter migration. Do not claim lossless migration until a spare-device
  restore has actually passed.
  [Z2M support](https://www.zigbee2mqtt.io/guide/adapters/zboss.html),
  [ZHA warning](https://github.com/tostmann/zha-zboss-esp).
- **BLE:** the H2 Ethernet/BLE component compile is useful evidence. It omits the
  complete workload, encryption and OTA. Active connections, discovery,
  reconnection and HA's proxy API must survive concurrent Thread, Zigbee and RF
  traffic. Advertisement-only forwarding is not parity with an active proxy.
- **Z-Wave:** preserve the vendor ZAC93 firmware and region, the exact serial
  byte stream and the server-facing interface. A custom SPI transport must
  detect lost bytes and stale sessions; replacing SC16 is not just exchanging
  connector labels.
- **433 MHz:** retain the RF Airbridge MQTT schema, native send/learn actions,
  RM433 events, both CC1101 GDO signals, timing and receive recovery after send.
- **Sensors:** retain LD2450 reports and configurable zones/settings, and BME680
  acquisition plus its external ventilated pod. A new MCU location must not
  silently heat the environmental sensor or obstruct the radar.
- **Power:** preserve isolated active PoE and separate 5 V/3.3 V loads, branch
  protection and inrush margin. Do not carry forward the unmeasured 3 W target
  as a measured property of four development boards. Their onboard regulators
  simplify assembly but do not prove equal energy consumption.
- **Recovery and service:** the proposed H2-Zero-M headers do not expose EN.
  Local RESET/BOOT buttons and USB are not equivalent to the earlier
  host-controlled RCP reset/update lines. Explicitly decide how to recover a
  wedged radio and isolate each supply during service. Built-in reset/BOD also
  does not automatically reproduce an external TPS3808 threshold and timing.
- **USB:** H2-Zero's USB VBUS and 5 V input are connected. The carrier must not
  backfeed the computer or parallel its supply with PoE. A service power rule
  must cover signal-line backpower too, not only the positive supply wire.

## A mixed-module route that preserves the host protocols

If strict protocol compatibility is the priority, keep a finished S3 host with
sufficient PSRAM, one finished H2 Thread RCP, an Ember Zigbee board, and the
necessary serial/peripheral support on the **same single carrier concept**.
This is a fallback to evaluate, not a silently selected replacement for the
all-H2 objective.

The strongest small header-based Zigbee candidate found is **Seeed XIAO MG24
Pre-Soldered, SKU 102010690**, using EFR32MG24B220F1536IM48. Seeed lists the
pre-soldered product and publishes its schematic and native KiCad files. Its
21 x 17.8 mm board includes the radio, power circuitry and an onboard
CMSIS-DAP/SWD programmer. It is not the same part as the bare MGM240PA22VNA3.
[Product](https://www.seeedstudio.com/Seeed-Studio-XIAO-MG24-Pre-Soldered-p-6381.html),
[design files](https://wiki.seeedstudio.com/xiao_mg24_getting_started/).

There is an existing community Ember NCP build, but its manifest uses **internal
PA08/PA09 through the onboard SAMD11 USB bridge, 115200 with software flow
control**. It does not appear on the factory D6/D7 header pins. A carrier UART
implementation would need a new NCP/bootloader assignment: D6 = PC06 and
D7 = PC07 are exposed; two additional header GPIO could carry RTS/CTS after
peripheral-routing verification. The onboard programmer remains available via
USB. Antenna selection, clock configuration, reset/boot access and all service
paths must be validated on that exact board. This is less physical assembly
work, but not a drop-in use of the existing M0 binary.
[Actual NCP manifest](https://github.com/darkxst/silabs-firmware-builder/blob/SiSDK/manifests/seeedstudio/xiao_mg24_zigbee_ncp.yaml),
[manufacturer schematic](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MGM240S_KICAD_Prj.pdf).

An assembled **SMLIGHT SLZB-07Mg24** is an alternative if a short USB host cable
is accepted. Its vendor supplies Zigbee coordinator firmware and ZHA/Z2M
support. It adds a USB-host/serial transport to the S3 and does not expose the
old four-wire contract without separately verified connections. Do not remove
its case to solder undocumented UART pads. **SONOFF ZBDongle-E is not a
four-wire substitute**: the community firmware documentation explicitly states
that it lacks hardware flow control.
[SMLIGHT](https://smlight.tech/products/slzb-07mg24),
[firmware hardware notes](https://github.com/darkxst/silabs-firmware-builder).

No examined commodity module has yet demonstrated all of: exact old MGM240P
binary compatibility, factory male UART headers, unchanged RTS/CTS/reset/boot,
and no additional software work. Do not label the mixed carrier completed
until its exact chosen board and firmware are frozen.

## Visual and release migration

The complete local visual inventory is in
[visual-inventory.json](../hardware/h2-quartet/visual-inventory.json). Its actions
are **proposals**, not assertions that the assets have already been replaced.

1. Make Q1 the sole active board entry point only after the hardware choice is
   explicit. Keep C0/M0/I0/D0 and the Pi reference reachable under historical
   labels; their dimensions, BOMs and Gerbers are not Q1 deliverables.
2. Generate Q1 assembly, top/bottom copper, solder-side, USB-service and enclosure
   images from its actual layout. An AI illustration can explain appearance but
   must not replace dimensioned CAD or be called a photograph of a built unit.
3. Update README, gallery, pin atlas and parts-catalog generators together. Old
   generated HTML otherwise continues promoting the retired boards, even if
   their Markdown entry points are changed.
4. Archive the old pin maps, native PCB renders, fabrication PDFs/ZIPs and
   enclosure fit claims together with their provenance. Keep generic component
   illustrations only where the exact new part still matches the caption.
5. Regenerate the parts inventory, release index and provenance checksums from
   the final sources. A Q1 release must not bundle an old enclosure STL or old
   assembly PDF under an unqualified current filename.

Acceptance requires matching one canonical BOM, pin map, carrier, firmware
roles, power/service procedure and all generated visuals. Counting fewer boards
or generating a new attractive overview alone does not meet the request.
