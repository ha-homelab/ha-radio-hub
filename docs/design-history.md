# One current design, retained engineering history

On 17 October 2026 the project chose **MC1: one carrier for finished modules**.
The decision prioritizes existing functions and Home Assistant compatibility over
using identical ESP32-H2 processors everywhere. Factory male module pins are
soldered directly into plated carrier holes; female module sockets are excluded.

The [design registry](../hardware/designs.json) identifies the only active custom
PCB design. The [current assembly guide](module-carrier.md) and
[current visual guide](../hardware/module-carrier/index.html) are the starting points.

## Why the alternatives are retained

The first MC1 layout used a 160 × 100 mm outline, followed by a 100 × 90 mm
full-size S3 carrier, then an 80 × 90 mm Nano carrier with USB cable corridors.
The current **65 × 75 mm Nano carrier** removes those corridors, keeps physical
USB shells, and uses preassembly programming plus network update paths. It retains
shared SPI, separate radio SoCs, factory male headers and bottom-edge RJ45.
J8/J9 become unpopulated recovery pads. H2 RX23/TX24 plus the documented R7
removal replace the preceding RX4/TX5 wiring so its standard ROM loader is reachable.
Previous snapshots are historical; use the firmware matching the current board.

The previous C0/M0, I0 and D0 sources, measurements, build proofs and renders remain
available to reproduce earlier work. They are historical references, not additional
shopping lists or alternative current MC1 builds. Replacing an old board image with
an MC1 image under the old filename would misrepresent its source and provenance.

- **Original modular assembly:** Raspberry Pi, internal Ethernet switch and two
  Ethernet ESP controllers. Its enclosure and wiring are not MC1 geometry.
- **LP-P0:** the earlier S3 software/electrical baseline, retained for regression
  testing and shared component implementation.
- **C0 + M0:** carrier plus a separately manufactured MG24 adapter.
- **I0:** integrated radio board with its own power, Ethernet and support circuits.
- **D0:** home-etched carrier with wire links and adapter boards.
- **H2 Quartet:** a useful feasibility experiment, rejected as the compatibility
  baseline. It introduced an unimplemented H2 local border router, different Zigbee
  backup/integration behavior and a new interprocessor transport.

## Reading images and claims

MC1 CAD renders are generated from its own PCB sources. Assembly illustrations are
labeled separately from CAD and from photographs. No rendering establishes that a
physical board has been assembled, tested, certified or measured.

The [H2 function audit](h2-quartet-function-audit.md) records why making all
processors identical would not currently be a function-preserving simplification.
The earlier hardware has not been physically qualified either; its compiled
firmware and documented interfaces are the comparison baseline, not field-test
evidence.
