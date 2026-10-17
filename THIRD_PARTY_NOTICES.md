# Third-party source and licenses

The repository's [MIT license](LICENSE) applies to original HA Radio Hub code,
documentation and CAD. It does not replace the licenses of the dependencies below.

## RF Airbridge

The Ethernet port derives its receive decoder, transmit validation, ESPHome
package and compatibility tests from
[ha-homelab/rf-airbridge at c96777d](https://github.com/ha-homelab/rf-airbridge/tree/c96777d0df65a7420e4883d79187f31eb1b98c9b).
Copyright (c) 2026 RF Airbridge contributors. The complete upstream
[license and notices](third_party/rf-airbridge.LICENSE) are preserved.

The original RF integration code is MIT licensed. The source is adapted under
`firmware/include/`, `firmware/packages/rf-airbridge.yaml` and `tests/`.
The original ESP8266 receiver patch is not used by this port.

## ESPHome

The local `firmware/components/remote_receiver/` component is based on ESPHome
2026.9.1. Its [provenance](firmware/components/remote_receiver/PROVENANCE.md)
records the upstream revision, modifications and file scope. Its
[license](firmware/components/remote_receiver/LICENSE) covers those files:
C++ runtime code is GPLv3, Python code is MIT.

Other ESPHome components and runtime dependencies are installed by the pinned
build process and keep their upstream licenses. A combined firmware image is
not licensed solely under the repository's MIT license. Device images also
contain private configuration and are not published as release assets.

## Other components

OpenThread, OTBR, ESP-IDF, ser2net, Linux container packages and Python build
dependencies retain their upstream licenses. Build definitions identify their
versions. Manufacturer names and trademarks are used only to identify parts.
