# Parts catalog and visual assembly reference

[View the complete parts gallery on GitHub](parts-gallery.md) or [download/open the filterable HTML catalog](../hardware/parts/index.html). It includes every row of the original modular BOM, LP-P0 reference, C0 and M0 assembly/harness BOMs, I0 assembly BOM, and D0 DIY assembly/harness BOMs. Search by model, value or reference; filter by build and component family. Each card preserves exact quantities, reference designators, package and original row notes. [Download the machine-readable inventory](../hardware/parts/inventory.json).

The catalog is a build reference, not a claim that the prototypes have passed hardware qualification. The [manufacturing options](../hardware/low-power/manufacturing-options.json), [pin-to-pin atlas](../hardware/low-power/visual/generated/index.html) and each board's release gates remain authoritative for assembly.

## Choose the build before making a shopping list

- **Original Pi modular hub:** use the original modular filter. Its `compatibility_wifi_only` and `wired_rf_only` rows are alternatives, and `injector_only` applies only when using an injector. The second Ethernet ESP32 replaces the old RF host; it is not an additional radio. [Original BOM](../hardware/bom.csv).
- **C0 + M0:** use C0 fitted parts and C0 harness/external rows, plus the M0 fitted parts and M0 harness. C0 needs the populated M0 adapter, external S3/H2/WIZ850io, sensors, RF/Z-Wave radios and power modules. The two ends of the C0–M0 cable are counted separately in their respective harness BOMs. The “remote modules” and “MG24 adapter” C0 rows are assembly references, not extra duplicate sets. [C0](../hardware/low-power/carrier/README.md) · [M0](../hardware/low-power/carrier/mg24-adapter/README.md).
- **D0 DIY + M0:** use D0 fitted parts and D0 adapters/harness/jumper-wire rows, plus the M0 assembly and harness. The main board uses through-hole parts and insulated wire links, but SC16 and TPS3808 still require fine-pitch soldering onto separate factory-made Adafruit 1208/1230 adapter PCBs. Those adapter kits do not include the ICs or male headers. M0 remains a factory-made SMT assembly. D0 J10 uses JST XH and a verified splice to the factory QT cable; it is not a direct QT socket. Use the final [D0 jumper schedule and instructions](../hardware/low-power/diy/README.md) for wire quantity and routing.
- **I0 integrated:** use I0 fitted parts plus the external-module and harness accessory cards. S3, H2, MGM240P, W5500, PoE PD, buck and local support circuitry are on I0. Do not also buy the C0/M0 fitted parts or WIZ850io for this build. ZAC93, CC1101, LD2450 and BME680 remain external. [I0](../hardware/low-power/integrated/README.md).
- **LP-P0 reference:** this is the electrical/bench reference, not an additive purchase list. It helps identify external modules and bench alternatives. DevKit boards are alternatives to bare modules, not parts to fit to an I0 footprint. Review their USB-UART and LED isolation requirements before connecting the low-power harness.

For each complete low-power hub, allow one regional ZAC93, one existing verified CC1101 module, one HLK-LD2450, one Adafruit 3660 BME680 board and the matching harnesses. Confirm parts included in kits: Adafruit QT cables are separate, a supplied radio antenna is not another purchase, and a precrimped QT cable replaces the loose housing/contact assembly. The [Silvertel EvalPoE page](https://silvertel.com/ag97000/) distinguishes an empty evaluation board from orders that include a PD module; I0 fits the bare **Ag97005-FL** directly.

## What the pictures mean

**Manufacturer photo** means a remotely hosted product/family image observed on the linked manufacturer's page. A family image may show another marking or revision; the caption says so. **Manufacturer render** is labeled separately. **Dimensioned diagram** is a source-derived project drawing of the actual contact geometry. **Original illustration** is a generic family sketch, not a product photo, dimensional inspection or substitute for a footprint.

Main modules have source-linked identification images where available. Bare S3, H2 and MGM240P use the [verified contact diagrams](../hardware/low-power/visual/physical/README.md), which distinguish module pads from development-board pins. The exact physical layout of the user's existing CC1101 module is not known, so the catalog deliberately does not show an arbitrary clone as that installed module.

The [C0](../hardware/gallery/carrier-c0.png), [M0](../hardware/gallery/mg24-m0.png), [I0](../hardware/gallery/integrated-i0.png) and [D0](../hardware/gallery/diy-d0.png) images are **native KiCad bare-PCB renders**, not photographs of manufactured or populated boards. D0 is shown from the copper/bottom side; its render omits the separately assembled insulated wire links. See their [render provenance](../hardware/gallery/README.md).

External images remain the copyright of Adafruit, Espressif, Hi-Link, Pololu, Silvertel, SMLIGHT, WIZnet and Zooz as credited beside the image. They are embedded by URL, not downloaded into this repository. No redistribution license for those images is asserted, and the repository's MIT license does not apply to them. Image source URLs and the review date are recorded in [catalog.json](../hardware/parts/catalog.json). A blocked/offline remote image falls back to a visibly labeled original family illustration. Local illustrations in `hardware/parts/illustrations/` are original project artwork under MIT; source-derived physical contact diagrams retain their own provenance notices.

## Buying links and substitutions

All current **AliExpress links are search links with unverified results**. They are provided for convenience, not as approved listings. No exact seller listing was verified for this catalog. Search results can mix incompatible variants, and the selected option within one listing matters. No live price, stock, delivery, seller authenticity or certification claim is made. Manufacturer/datasheet links appear under “Exact BOM notes & official sources” and image-source links.

Match the complete model and package. In particular:

- ESP32-S3 **N16R8**, H2 **H4S**, and MGM240**PA22VNA3** identify specific targets; a different memory/antenna variant is not automatically compatible.
- Select **Ag97005-FL (5 V)**, **D24V22F3 (3.3 V)**, **WIZ850io** for the modular build, and the specified **W5500 + Bel 0813-1X1T-57-F** for I0. A generic PoE splitter or RJ45 socket does not meet those footprints and isolation contracts.
- Use the correct radio region for ZAC93, **433.92 MHz** matching for CC1101 and its antenna, and verify SMA versus RP-SMA from the real hardware. The bare S3/H2/MGM240P targets have integrated antennas; do not attach an external antenna to an unconnected RF pad.
- JST **XH 2.50 mm**, JST **SH 1.00 mm**, IDC **2.54 mm contacts / 1.27 mm ribbon**, and similar-looking unbranded plugs are different. Match terminal type, wire gauge and actual keyed pin order. The 40-pin C0 connector is **not Raspberry Pi GPIO compatible**.
- Preserve capacitor voltage, dielectric, DC-bias capability and package, particularly I0's **100 V primary-side** capacitors and **2 kV** isolation/shield capacitor. Preserve crystal frequency/load, TVS part, fuse type and resistor tolerance. A matching printed value alone is insufficient.

## Rebuild and verify coverage

Run from the repository root with Python 3.12 or newer:

```sh
python3 hardware/parts/build.py
python3 hardware/parts/build.py --check
python3 -m unittest discover -s hardware/parts -p 'test_*.py'
```

Generation and tests work offline. `--check` is read-only and rejects stale HTML/JSON/illustrations. The validator compares every canonical source row, quantity, value, footprint and note exactly, rejects missing or repeated rows, and requires explicit image provenance and unverified AliExpress labels. Tests also discover assembly/harness BOMs so a newly added board cannot silently disappear from the catalog. Online image availability is not a CI requirement because manufacturer servers can block requests or change URLs.

To view locally with working relative links:

```sh
python3 -m http.server 8765
```

Open `http://localhost:8765/hardware/parts/index.html`. The HTML also works as a local file; remote photos need internet access.
