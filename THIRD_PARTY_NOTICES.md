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

The single-host prototype fetches the REST component from
[Espressif esp-thread-br at 29a2345](https://github.com/espressif/esp-thread-br/tree/29a2345e3f0c61bba9307f3daea5ed0c94388ed3).
Its prepared copy retains upstream notices and is patched during the build for
the HTTP 404 dialect probe, a separate REST port and ESPHome-owned network setup.
ESP-IDF 5.5.5 supplies the OpenThread host and H2 RCP. These dependencies are not
relicensed by the repository's MIT license; generated firmware must retain their
license obligations and the ESPHome obligations above.

The [MG24 build kit](firmware/low-power/mg24/README.md) downloads Silicon Labs
Simplicity SDK 2025.6.3, SLC and Commander plus the Arm GNU toolchain. Their
vendor licenses continue to apply to the downloaded tools, generated sources,
libraries and firmware. Vendor SDK sources and generated radio images are not
distributed as this repository's original MIT code.

OpenThread, OTBR, ESP-IDF, ser2net, Linux container packages and Python build
dependencies retain their upstream licenses. Build definitions identify their
versions. Manufacturer names and trademarks are used only to identify parts.
