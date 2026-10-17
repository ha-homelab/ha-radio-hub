# Attribution and source notes

`Carrier.pretty/MGM240P.kicad_mod` is project-authored from the Silicon Labs MGM240P Revision 1.0 dimensional and recommended-land-pattern drawings (especially Figure 8.3). The same verified geometry is shared with the integrated PCB. It is not copied from a KiCad library or a manufacturer CAD archive. The source URL and engineering limitations are in README.md.

Other `Carrier.pretty/` files are bundled KiCad footprints distributed with KiCad 10.0.6, with external optional 3D-model references removed. A corresponding upstream library tag is not assumed. Source project: https://gitlab.com/kicad/libraries/kicad-footprints . These files retain the [KiCad library license and exception](../KICAD-LIBRARY-LICENSE.md); the repository license does not replace their license. `outputs/sha256.json` identifies the supplied files.

`Carrier.kicad_sym` contains original generated schematic symbols. FreeRouting 1.9.0 was used for local routing, followed by native KiCad ERC/DRC and parity checks. The router is not redistributed. No Silicon Labs binary firmware or proprietary CAD/tool archive is included in this adapter directory.
