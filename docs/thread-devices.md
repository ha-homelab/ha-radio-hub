# Matter-over-Thread devices for the first bench test

This selection is based on official pages checked on **2026-10-16**. These are candidates, not devices tested with HA Radio Hub. Buy the exact revision with **Matter + Thread**, because the same brands also sell Zigbee, Matter-over-Wi-Fi, and older HomeKit-over-Thread versions. A Matter logo alone does not imply Thread.

## Recommended starter set

Start with **one Eve Energy Matter for your region**, **one Aqara Door and Window Sensor P2**, and **one motion sensor of your choice**. First test commissioning and reconnection after a restart. Then add a second continuously powered Thread plug at the far end of the home before buying more battery-powered sensors.

### Eve Energy — smart plug and Thread router

[Official Eve Energy page](https://www.evehome.com/en-us/eve-energy). Choose the Matter revision; in the US/Canada, choose the Type B 120 V version. The manufacturer explicitly describes it as a Thread router/FTD: the plug helps relay other nodes' messages. It is suitable for testing on/off control and, with a supported firmware/HA combination, energy measurements. Check the available energy entities after pairing; do not assume they are identical on older HomeKit and newer Matter firmware.

The plug must remain continuously powered. For the first test, use a small ordinary lamp and follow the load ratings and restrictions of the chosen regional version.

### Aqara Door and Window Sensor P2 — contact sensor

[Official P2 page](https://aqara.com/us/product/door-and-window-sensor-p2/). The manufacturer confirms Matter-over-Thread. Test open/closed state, event consistency, and recovery after sleep. This is a battery-powered endpoint: it does not extend radio coverage for neighboring devices. Do not confuse it with Aqara T1 or the original Zigbee contact sensor. Advertised Aqara-specific features do not automatically become HA entities; the initial goal is a standard contact sensor.

### Aqara Motion and Light Sensor P2 — motion and illuminance

[Official Motion and Light P2 page](https://us.aqara.com/products/motion-and-light-sensor-p2). Matter-over-Thread, PIR, and a light sensor. The page showed a price of $33.99 when checked; availability and price may change. Choose **P2**, not P1. Check motion and illuminance separately in HA. PIR detects motion and does not replace the LD2450's 24 GHz tracking. Sensitivity/timeout settings available only in Aqara Home are not promised through standard Matter entities.

### Eve Motion — alternative PIR

[Official Eve Motion page](https://www.evehome.com/en-us/eve-motion). Choose the Matter version. It provides a useful second manufacturer for testing a mixed-brand network, motion, and illuminance. This is a battery-powered endpoint. For the first bench test, **one** of Eve Motion or Aqara Motion P2 is enough; buying both at once is unnecessary.

### Eve Weather — external temperature and humidity

[Official Eve Weather page](https://www.evehome.com/en-us/eve-weather). Choose the Matter version; older revisions may require a separate update procedure. Temperature and humidity are useful for an independent comparison with the BME680. Proprietary weather charts, forecasts, and history are not assumed to be part of the Matter integration. This is a battery-powered endpoint, not a Thread repeater.

### Nanoleaf Essentials Matter-over-Thread A19/E26 — lighting

[Official bulb catalog](https://nanoleaf.me/en-us/collections/nanoleaf-smart-bulbs) and [Essentials variant guide](https://support.nanoleaf.me/hc/en-us/articles/37415330897556-Resource-Product-User-Guide-Indoor-Essentials-Includes-Seasonal). The catalog includes both **Matter over Thread** and **Matter over Wi-Fi**. Check for Thread on the exact SKU; older HomeKit/Thread bulbs are a separate variant. When checked, the single Thread A19 was marked sold out, while the Thread A19 three-pack was available to order. Check availability separately for each pack; this is an alternative bench-test candidate.

A bulb must remain powered if it is expected to participate in the mesh. Test on/off, brightness, and color modes using the HA entities actually available. For the first network router, a plug is preferable to a bulb behind a conventional wall switch.

## How they connect to this appliance

Thread provides IP connectivity through the local OTBR. A Matter server connected to HA controls the Matter devices; the appliance itself does not replace a Matter controller. Initial commissioning uses HA Companion on a phone, the device's QR code, and the phone's Bluetooth. **The ESPHome Bluetooth proxy does not replace Bluetooth commissioning on the phone.** See [HA Matter](https://www.home-assistant.io/integrations/matter/) and [HA Thread](https://www.home-assistant.io/integrations/thread/) for details and the current procedure.

1. Start OTBR and check the Thread network, then add OTBR to HA.
2. If the home already has a Thread network from Apple/Google/another border router, first decide whether to use its dataset; do not accidentally create several unrelated networks with the same name. Devices in one Matter fabric can use different transports, and identical Thread names do not imply identical credentials.
3. Make the required Thread network preferred in HA and synchronize its credentials to the phone using the instructions for your OS.
4. Put the phone, HA, and border router on a mutually reachable LAN with IPv6 and multicast/mDNS. For the first bench test, use one segment without guest isolation. Internet access does not fix blocked local IPv6.
5. Add devices one at a time, starting near the appliance. Check events/control, battery-device sleep, and recovery after restarting OTBR.
6. Move the devices to their final locations and repeat. An additional continuously powered Thread plug is more useful for extending coverage than a collection of battery-powered endpoints.

Standard Matter functions can work without the manufacturer's cloud. Initial setup, firmware updates, and a particular product's advanced features may have their own requirements; check the exact model. When updating an older HomeKit device to Matter, save the new pairing information separately and understand that the migration may change how it connects.
