# Square-layout firmware and service review

**Decision: a 100 × 100 mm arrangement can retain the existing firmware and all service interfaces without removing USB-C.** Prefer the proposed stock-module arrangement: S3 on the right, inverted H2 centrally above WIZ850io, and horizontal XIAO MG24 on the left. Position and rotation are mechanical changes; preserve every numbered pad's net. Exact fit, routing, antenna clearances and plug access belong to this study's CAD checks, not this firmware conclusion.

The active 100 × 90 mm carrier remains the reference. This review does not approve replacing it with an unrouted placement study. It makes no hardware-test or wireless-recovery claim.

The static candidate at XIAO **(18,59), 270°** preserves all 17 component identities and all 145 pad assignments (103 connected) from the active carrier. Its transformed USB/header envelopes clear the other footprint courtyards; XIAO USB has only **0.18 mm** to the WIZ courtyard. That temporary USB envelope also enters the H2 RF clearance region: treat it as a maintenance connection and remove the cable afterward. These checks establish consistency with the assumed envelopes, not a measured plug fit or radio performance with the cable connected. See the [independent USB/RF review](usb-rf-review.md).

## What must remain unchanged

- S3–XIAO UART: GPIO17 → D7/PC07, GPIO18 ← D6/PC06; GPIO16 → D4/PC04 CTS, GPIO21 ← D5/PC05 RTS. Both application and bootloader use 115200 8N1 with hardware flow control.
- J8 remains a local D0/PC00-to-ground boot-entry jumper. The XIAO reset button must remain reachable. J8 does not provide reset, SWD or a USB interface.
- S3–H2 UART remains GPIO41 → H2 GPIO4 and GPIO42 ← H2 GPIO5. EN and BOOT control remain GPIO47/48, open-drain. H2 USB and onboard serial-bridge service pins stay unused by application wiring.
- Keep every WIZ850io SPI/power connection, the separate MCU supply branches, external peripheral supply and all sensor/radio headers unchanged. Moving WIZ below H2 does not change its software interface; rerouted copper still needs normal electrical checks.

These contracts are implemented by the [complete firmware](../../../../firmware/module-carrier/README.md), [XIAO NCP and bootloader recipe](../../../../firmware/module-carrier/zigbee/README.md), and [TCP bridge](../../../../firmware/low-power/components/zigbee_tcp/zigbee_tcp.cpp). An exact pin-preserving rotation needs no new binary. A new native board must still be checked against these nets, including explicit unconnected pins.

## Service options

1. **Keep USB-C and make the plug reachable — preferred.** The new square placement offers this route. Initial programming and application-independent debug/recovery remain through the onboard SAMD11 CMSIS-DAP probe. Retain plug-shell and cable-bend space, not only the empty receptacle outline. The normal assembly remains factory male pins soldered directly into carrier holes.
2. **Keep USB-C but permanently obstruct it.** Normal Zigbee operation is unchanged, but assembled-board recovery becomes worse. Flashing before assembly does not replace future access. Access regained by removing an enclosure lid is acceptable service access; access requiring desoldering a directly mounted module is not equivalent. A verified slim or right-angle plug may help, but its measured body and cable routing must fit.
3. **Remove USB-C without replacing its interface.** The runtime UART and power header can still work if rework leaves their circuitry intact. However, the board outline and its 14-pin mounting pattern do not shrink. Only connector height/projection and its plug corridor disappear. This adds fine-pitch rework and loses convenient access to the onboard programmer; it is not a cost or complexity improvement over an equally priced square board that retains the connector.
4. **Remove USB-C and relocate USB or SWD access.** Electrically possible, but it adds a harness, small-pad attachment or a pogo fixture, strain relief and another verified programming interface. It is a separate redesign. Merely adding carrier pads cannot obtain signals absent from the XIAO factory header. This does not satisfy the existing direct-header-only assembly goal as cleanly as keeping USB-C.

The official XIAO design routes USB D+/D− to SAMD11, not to the application's PC04–PC07 UART. MG24 SWD is on TP17/TP18, reset on TP4; TP5/TP6 instead belong to **SAMD11's own** SWD interface. None of these SWD signals is on the standard 14-pin XIAO header. Reusing the wrong test points would program the wrong chip. Source: [Seeed schematic, SAMD11 and power sheets](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MGM240S_KICAD_Prj.pdf) and [official KiCad archive](https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip).

## UART recovery is not a substitute for the USB programmer

The compiled Gecko bootloader occupies a reserved 24 KiB region; the NCP application starts at `0x08006000`. If the bootloader remains healthy, its existing four-wire UART can receive an application update after local J8/reset entry. The S3 TCP bridge is a byte transport, not a complete firmware updater; a specific end-to-end upload tool/sequence over TCP has not been physically qualified here. Stop the normal coordinator owner during an update.

A missing, erased or damaged bootloader cannot be repaired by assuming that same bootloader will run. CMSIS-DAP supplies a separate debug/programming path, subject to the chip's debug/security state. The repository's initial-image procedure follows the [Silicon Labs OpenOCD CMSIS-DAP upload recipe](https://github.com/SiliconLabsSoftware/arduino/blob/868660a857077dbdf757c7e9ded96e20fa84e50c/platform.txt). Neither Zigbee OTA, S3 OTA nor automatic S3-driven H2 reflashing is an established replacement for this physical access.

## XIAO's programming probe needs USB VBUS

This review found an existing service-documentation error, independent of board size. The blanket recommendation to block USB VBUS is unsuitable for this XIAO circuit:

- The factory header's pin14, named VBUS/5V, connects to **VIN** in the official netlist.
- Onboard D1 carries power from USB **VBUS** to **VIN**, blocking the reverse path.
- SAMD11 regulator U10 has both IN and EN on **VBUS**, and supplies `D11_3V3`.

Thus normal carrier power on VIN does not power the SAMD11 probe through its intended supply path. Blocking host VBUS leaves that path unpowered; any parasitic signal backfeed is not a valid supply. This is established by exporting the official KiCad schematic to XML and checking U4.14, USB1, D1 and U10 connectivity, including the diode symbol's direction. It is not a physical enumeration test.

The intended XIAO service topology supplies USB VBUS while the **whole carrier remains normally powered**. Onboard D1 and carrier D3 separate the supply branches; check actual diode orientation, rail voltages, backfeed and enumeration on the purchased board before adopting that procedure. Do not power only XIAO while its signal-connected neighbors are unpowered. Keep initial programming on loose modules as the simplest first step. Qualify S3 and H2 service by their own USB port circuits rather than extrapolating a single adapter rule.

## Cost and complexity

100 × 100 mm is **11.11% more PCB area** than 100 × 90 mm, and **37.5% less** than the original 160 × 100 mm. Both compact sizes fit the advertised size ceiling for [JLCPCB's five-piece, two-layer offer](https://jlcpcb.com/help/article/how-do-i-place-an-order) and [PCBWay's ten-piece, one/two-layer offer](https://m.pcbway.com/activitypcb.aspx), checked 2026-10-17. These are fabrication offers, not delivered project quotes; finish, thickness, quantity, shipping and other options still matter.

The square's potential benefit is more useful room for headers, service plugs and assembly. USB removal has no demonstrated fabrication saving within that same size class, adds rework and reduces serviceability. Keep the connector if the square CAD arrangement clears it; compare the completed routing and measured assembly access before promoting the square layout.
