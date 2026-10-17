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

## KiCad and Espressif footprint libraries

The prototype PCBs and physical contact references include footprint data from
the KiCad library contributors, distributed with **KiCad 10.0.6**, and from the
[Espressif KiCad library contributors at dd76561812ab300351234ba6e0ec1295641796f0](https://github.com/espressif/kicad-libraries/tree/dd76561812ab300351234ba6e0ec1295641796f0).
These library sources are licensed under **Creative Commons Attribution-ShareAlike
4.0 with the KiCad electronic-design exception**. They are not relicensed as MIT.
The exception waives CC BY-SA article 3 for electronic designs and generated
files using library data to the extent those outputs would be Adapted Material;
the original board designs can retain the project's MIT license. Retain the
upstream notices when redistributing the library files themselves.

The copied source and local license scope are:

- [LP-C0 Carrier.pretty](hardware/low-power/carrier/Carrier.pretty/): selected
  KiCad footprints, with external 3D-model references removed for portability.
  The two isolated JST-SH hold-down pad identities are changed from `MP` to
  `MP1`/`MP2`, as described in the [local notice](hardware/low-power/carrier/NOTICE.md).
  The original project footprints `Wurth_61204021621` and `Littelfuse_449` are
  generated from manufacturer dimensions. The upstream notice is preserved in
  [KICAD-LIBRARY-LICENSE.md](hardware/low-power/carrier/KICAD-LIBRARY-LICENSE.md).
  The [LP-M0 adapter library](hardware/low-power/carrier/mg24-adapter/Carrier.pretty/)
  also uses selected KiCad connector/passive footprints under that notice;
  its `MGM240P` footprint is project-generated from manufacturer dimensions.
  Its [adapter notice](hardware/low-power/carrier/mg24-adapter/NOTICE.md)
  records the corresponding provenance and modifications.
- [LP-I0 Hub.pretty](hardware/low-power/integrated/footprints/Hub.pretty/):
  selected KiCad footprints with external 3D-model references removed, plus
  the pinned Espressif `ESP32-H2-MINI-1` footprint. Project-generated
  `MGM240P`, `D24V22F3`, `Ag97000_FL`, `Bel_0813_1X1T_57_F` and `Littelfuse_449`
  use transcribed manufacturer dimensions. Notices are preserved in
  [LICENSE-kicad-footprints.md](hardware/low-power/integrated/vendor/LICENSE-kicad-footprints.md)
  and [LICENSE-espressif.md](hardware/low-power/integrated/vendor/LICENSE-espressif.md).
- [Physical contact source references](hardware/low-power/visual/physical/source/):
  unchanged KiCad `ESP32-S3-WROOM-1` and pinned Espressif
  `ESP32-H2-MINI-1` source footprints, with
  [the library notice](hardware/low-power/visual/physical/source/LIBRARY-LICENSE.md).
  [The contact-reference README](hardware/low-power/visual/physical/README.md)
  and source-hash manifest identify the generated SVGs and their provenance.
- [LP-D0 DIY library](hardware/low-power/diy/DIY.pretty/) uses adapted KiCad
  JST-XH footprint bodies with larger through-hole lands. Its
  [local notice](hardware/low-power/diy/NOTICE.md) and
  [KiCad library license](hardware/low-power/diy/KICAD-LIBRARY-LICENSE.md) apply.
  The adapter mating footprints transcribe dimensions and pin connectivity
  from identified Adafruit drawings; the vendor adapter boards are not bundled.

See the [KiCad library license and exception](https://www.kicad.org/libraries/license/)
and the [pinned Espressif license](https://github.com/espressif/kicad-libraries/blob/dd76561812ab300351234ba6e0ec1295641796f0/LICENSE.md).
Manufacturer dimension references do not grant rights to redistribute vendor
logos, photographs or PDF artwork. Those materials are linked as sources,
not bundled as project-owned artwork.

## Parts-gallery images

The [parts gallery](docs/parts-gallery.md) embeds selected manufacturer-hosted
photographs and renders by URL. Adafruit, Espressif, Hi-Link, Pololu, Silvertel,
SMLIGHT, WIZnet and Zooz retain their rights to those images; this repository
does not grant a redistribution license for them. Each image has a source and
credit in [the catalog metadata](hardware/parts/catalog.json). No local copies
of those photographs are included in the build package.

The local family illustrations under `hardware/parts/illustrations/` are original
MIT-licensed project artwork. The [PCB gallery](hardware/gallery/) is rendered
from the project's native board geometry; the footprint-library notices above
continue to apply. Source-derived contact drawings keep their separate provenance.

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
