# Visual connection atlas

<!-- MC2-CURRENT-DESIGN -->
> **Current build: [MC2 — three external antennas](../../../docs/external-antennas.md).** This page retains an earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC2 build.

Open [the interactive atlas](generated/index.html) in a browser. It runs entirely
offline and provides component selection, pin/signal search, every net endpoint,
support-component values, and printable connection sheets. GitHub displays HTML
as source; download the repository/build package (keeping the whole `generated/`
folder together), then open `generated/index.html`, or serve the directory locally:

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory hardware/low-power/visual/generated
```

Then open `http://127.0.0.1:8766/`. The atlas is for the **single-host low-power
LP-P0 contract**, not the original two-S3/Pi modular assembly.

## Reading a connection

Each row names the selected component's signal and physical pad, followed by the
connected component and its physical pad. For example, WIZ850io `J1.3 MOSI`
connects to S3 `GPIO11`, which is **module pad 19** on the selected WROOM module.
That does not mean pin 19 of a DevKit header. Actual development-board header
positions are deliberately unassigned until their revisions are inspected.

Arrows show fixed signal direction; unarrowed open-drain lines require the net's
notes. Supply and ground rows represent shared nets: selecting their names lists
every endpoint, including individual ground pads. An X means that the pin is
left unconnected or requires the separate PoE front end; it is not a wire.

The parts gallery combines original **identification sketches** with separate
**contact-location references** for the verified S3, H2, MG24, WIZ850io and Pololu
modules. The sketches are not photographs or physical pin maps. Contact drawings
state their viewing convention and source; open them at full size for pad numbers.
Use the linked manufacturer drawings for dimensions and assembly decisions. Unknown CC1101 and LD2450 connector positions are not
inferred from generic pictures. The ZAC93 header assignment remains conditional
on confirming the actual board revision.

## PCB connectors

The **Board connectors** tab selects C0 (carrier), M0 (MG24 daughterboard),
I0 (integrated board), or D0 (DIY single-sided board) and its connector manifest. Each row identifies the board connector pin, net, destination signal,
voltage and assembly notes. The adjacent drawing uses actual KiCad pad centres
in PCB top/component view. It is not the cable mating-face view, which is mirrored.
Pin 1 is highlighted; shared physical pads are grouped without inventing separate
positions. Expand the PCB drawing to locate each connector. Use moulded circuit
numbers and a continuity test instead
of inferring polarity from wire colour.

D0 preserves C0 signal roles but requires the numbered insulated wire links in
its [assembly instructions](../diy/README.md), in addition to its bottom copper.
Its **J10 is JST XH 2.50 mm**, mating with XHP-4, rather than C0's JST SH/QT socket.
Use the continuity-verified XH-to-factory-QT cable; a QT plug does not fit D0 J10.
Both C0 and D0 use the separate populated M0 radio adapter.

The connector manifest also names the mating housing and crimp contacts. Unknown
reused-module contact positions remain unknown; a numbered carrier socket does
not establish the destination module's unverified pin numbering.

When one carrier contact lists several remote endpoints, all of them belong to
the same net. For example, C0 J4.9 serves WIZ850io J1.2 and J2.1. Use an insulated,
strain-relieved fan-out splice or a suitable distribution point; do not assume
that two wires may share a crimp contact. WIZ850io J2.4 remains unconnected.

## Printable sheets

- [S3 host](generated/s3-connections.svg)
- [WIZ850io Ethernet](generated/w5500-connections.svg)
- [H2 Thread radio](generated/h2-connections.svg)
- [MG24 Zigbee radio](generated/mg24-connections.svg)
- [SC16 UART bridge](generated/sc16-connections.svg)
- [ZAC93 Z-Wave module](generated/zac93-connections.svg)
- [CC1101 RF module](generated/cc1101-connections.svg)
- [LD2450 radar](generated/ld2450-connections.svg)
- [BME680 environmental sensor](generated/bme680-connections.svg)
- [Reset supervisor](generated/supervisor-connections.svg)
- [Isolated PoE module](generated/pd-connections.svg)
- [3.3 V buck converter](generated/buck-connections.svg)
- [Service signals](generated/service-connections.svg)

The drawings use logical port placement. A row's vertical location is **not** a
connector-face position. The general logic interfaces use 3.3 V; MG24 RESETn uses internal DVDD
and must only be sunk or released, never pulled up externally to 3.3 V.
The LD2450 power input is 5 V. PoE primary-side power must never reach these signal pins.

## Sources and repeatable generation

[connections.json](connections.json) records source URLs, datasheet revisions,
physical-pin evidence and remaining unknowns. Its validator checks the firmware
contract, ground coverage, pull-ups, RF open-drain behavior, UART handshaking and
the boundary between isolated low voltage and the PoE front end.

```sh
python3 hardware/low-power/visual/validate.py
python3 -m unittest discover -s hardware/low-power/visual -p 'test_*.py'
python3 hardware/low-power/visual/build.py
python3 hardware/low-power/visual/build.py --check
```

Generated files are committed so readers need no drawing toolchain. The manifest
binds them to the electrical data, board connector manifests, physical drawings
and viewer template hashes. These checks validate documentation consistency;
they do not establish electrical operation or authorize production.
