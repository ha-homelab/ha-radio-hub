# Attribution and source notes

The portable footprints in `Carrier.pretty/` other than `Wurth_61204021621` and `Littelfuse_449` come from the official KiCad footprint libraries distributed with **KiCad 10.0.6** (bundled files; release-tag identity not assumed). Upstream project: <https://gitlab.com/kicad/libraries/kicad-footprints>. Individual supplied files are bound by the output SHA256 manifest. Optional external 3D-model references were removed so the PCB has no missing workstation dependency. The original geometry is preserved. In the JST-SH footprint, the two isolated solder hold-down pads originally both named MP are renamed MP1/MP2 to represent two separate NC terminals; they are not cable contacts. All other original footprint metadata is retained.

The library license is [Creative Commons Attribution-ShareAlike 4.0 with the KiCad libraries exception](KICAD-LIBRARY-LICENSE.md). Refer to that file for the exception governing designs which use these libraries. These library files retain their upstream license; the repository license does not replace it.

The two custom footprints are generated from the manufacturer dimensional drawings linked in `design.py`: Würth 61204021621 and Littelfuse 449. Their body and pad dimensions are design data, not a copied manufacturer artwork. `Carrier.kicad_sym` contains original simple boxed physical-pin symbols, generated here; it does not copy stock KiCad schematic symbols.

Routing was generated locally with [FreeRouting 1.9.0](https://github.com/freerouting/freerouting/releases/tag/v1.9.0), followed by native KiCad checking and explicit power/ground zone finishing. The router binary is not redistributed. Routing success is not used as a substitute for ERC, DRC or schematic parity.
