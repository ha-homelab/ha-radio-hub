# Downloadable engineering build package

The **v0.3.0-beta.2** package targets the current **MC2-C + FH1-MC2-C-PWR1**
prototype with the RECOM PWR1 power assembly: a classic ESP32 host, TinyC6[D] Thread radio, external-antenna MG24
Zigbee radio and three independent 2.4 GHz antenna paths. Download the ZIP and
its checksum from [GitHub Releases](https://github.com/ha-homelab/ha-radio-hub/releases).
This is a source, CAD and assembly package; no installation or physical
acceptance is claimed.

Start with [the ordered build guide](start-here.md), [MC2-C hardware](external-antennas.md),
[the full-hub assembly instructions](full-hub-assembly.md) and
[the matching firmware guide](../firmware/external-antenna/README.md).
The archive includes the committed sources, tests, documentation and historical
reference designs. The [design registry](../hardware/designs.json) identifies
MC2 as the one active design; do not mix earlier pin maps, images or enclosures
with MC2-C.

## Verify and use the package

`RELEASE-MANIFEST.json` records the exact source commit and every included file's
size and SHA-256. The adjacent checksum verifies the complete archive:

```sh
# Run in the directory containing both downloaded files.
shasum -a 256 -c ha-radio-hub-v0.3.0-beta.2-build-pack.zip.sha256
unzip ha-radio-hub-v0.3.0-beta.2-build-pack.zip
cd ha-radio-hub-v0.3.0-beta.2
python3 tools/check.py
python3 tools/preview.py
```

For the current assembly, use these files from the same extracted archive:

- `hardware/external-antenna/fabrication/MC2-C-prototype-gerbers.zip` and its
  manifest: the native PCB fabrication export, with [ordering instructions](pcb-order.md).
- `mechanical/full-hub/FH1-MC2-C-PWR1-print-package.zip`: the enclosure parts,
  quantities and fit coupon. Follow the [print instructions](../mechanical/full-hub/README.md).
- `hardware/external-antenna/harness.csv`: the current pin-to-pin harness;
  use it with the [full assembly inventory](../mechanical/full-hub/components.json).
- `firmware/external-antenna/`: the exact-target build and programming recipes,
  including the TinyC6[D] external-antenna selection and classic-ESP32 host.

Previously committed fabrication and print assets keep their original evidence
and hashes. Packaging does not imply a new native CAD export or new hardware
measurements. The largest current enclosure print is 215 × 215 mm; print and
check the fit coupon before committing to the enclosure. Actual module fit,
power, temperatures, RF coexistence and coverage remain subject to the
[physical validation gates](../hardware/external-antenna/validation.md).

There are no ready-to-flash household firmware images, network credentials,
private RF codes or HA registry exports in the outer build package. Build the
matching target from the firmware guide and keep installation configuration
private. The source licenses and third-party notices are included.

## Earlier packages

`v0.3.0-beta.1` retains the previous Pololu converter and FH1-MC2-C-RF1
enclosure. Its files and hashes remain historical. Use beta.2 consistently for
the RECOM converter, capacitor, wiring and mount; no native carrier copper or
firmware change is required.

`v0.1.0` and `v0.2.0` describe the original Pi-based assembly. The latter added the
migrated RF Ethernet contracts, but predates the later D0 print/assembly material
and the current MC2-C/FH1 design. Those archives are not current MC2 manufacturing
or deployment packages. MC1, LP-D0 and other historical sources remain available
for reference and regression tests; their geometry and firmware are not MC2-C
substitutes.

## Rebuild from a reviewed commit

```sh
python3 tools/package_release.py --ref HEAD --version v0.3.0-beta.2 --output .build/releases
```

The packager reads Git objects at the selected commit, not the working directory.
Uncommitted edits and ignored installation files cannot enter the archive.
It rejects tracked private paths, firmware binaries, symlinks, submodules and
recognized credential patterns. A release must be built only after the selected
source tree's required CI, security analysis and review have completed successfully.
The build process preserves committed file contents and uses the commit timestamp;
ZIP bytes are repeatable within the same Python/zlib environment.

Tag the tested commit, upload the ZIP and checksum, and mark the release as a
**prerelease** until physical acceptance is recorded. Successful software tests
and digital geometry checks are not hardware certification.
