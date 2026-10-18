# Downloadable build package

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

Use the newest engineering prerelease from
[GitHub Releases](https://github.com/ha-homelab/ha-radio-hub/releases). The original
`v0.1.0` archive predates the complete RF Ethernet port; use `v0.2.0` or later for
the migrated RF contracts and matching wiring instructions.

The illustrated parts catalog and D0 toner-transfer design were added after
`v0.2.0`; that older archive does not contain them. Until a later versioned
package includes these additions, use the current repository's
[parts gallery](parts-gallery.md) and [D0 print/assembly files](diy-pcb.md) as a
matching source set. Do not mix a D0 copper mask with an older or different
revision's drilling or wiring sheet.

The `ha-radio-hub-VERSION-build-pack.zip` archive contains the committed project:
the parts list and wiring, eight printable STL parts, parametric CAD and previews,
firmware sources, Linux deployment files, tests, and assembly/HA instructions.
`RELEASE-MANIFEST.json` records the exact source commit, file sizes and SHA-256
hashes. The adjacent `.sha256` file verifies the archive itself:

```sh
# Run in the directory containing both downloaded files.
shasum -a 256 -c ha-radio-hub-v0.2.0-build-pack.zip.sha256
unzip ha-radio-hub-v0.2.0-build-pack.zip
```

Start with `README.md`, `hardware/bom.csv` and `docs/enclosure.md`. Print
`mechanical/generated/fit_coupon.stl` before the enclosure. The eight STL files
use millimetres; the assembled GLB uses metres. The main base/lid need a print
bed of at least 246 × 206 mm including a 3 mm brim. Actual board and connector
fit, power, heat, radio coexistence and sensor behavior still require the
physical [acceptance checks](acceptance.md).

There are no ready-to-flash household firmware images, network credentials,
private RF codes or HA registry exports in this archive. Compile your own private
configuration with [the flashing guide](firmware.md); use the
[RF migration procedure](../hardware/rf-migration.md) for an existing installation.
The original source licenses and third-party notices are included.

## Rebuild a package from a reviewed commit

```sh
python3 tools/package_release.py --ref HEAD --version v0.2.0 --output .build/releases
```

The packager reads Git objects at the selected commit, not the working directory.
Uncommitted edits and ignored installation files cannot enter the archive.
It rejects tracked private paths, firmware binaries, symlinks, submodules and
recognized credential patterns. A release must be built only after the selected
source tree's required CI, security analysis and review have completed successfully.
The build process preserves committed file contents and uses the commit timestamp;
ZIP bytes are repeatable within the same Python/zlib environment.

To publish, tag the tested commit, upload the ZIP and checksum, and mark the
release as a **prerelease** until physical acceptance is recorded. This prototype
package and its successful software tests are not hardware certification.
