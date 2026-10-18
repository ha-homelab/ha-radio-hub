# One current design, retained engineering history

On 18 October 2026 **MC2-A** became the current design: a 100 × 100 mm carrier
with factory external-antenna S3/C6 modules and external-mode XIAO MG24 firmware.
It retains local services while separating all three 2.4 GHz antenna feeds.
MC1 remains historical and continues to have regression checks. Its last
47.5 × 75 mm layout, Nano 16 MB flash target and H2 pin map are not MC2.

On 17 October 2026 the project chose **MC1: one carrier for finished modules**.
The decision prioritizes existing functions and Home Assistant compatibility over
using identical ESP32-H2 processors everywhere. Factory male module pins are
soldered directly into plated carrier holes; female module sockets are excluded.

The [design registry](../hardware/designs.json) identifies the only active custom
PCB design. The [current assembly guide](external-antennas.md) and
[current visual guide](../hardware/external-antenna/index.html) are the starting points.

## Why the alternatives are retained

The first MC1 layout used a 160 × 100 mm outline, followed by a 100 × 90 mm
full-size S3 carrier, then an 80 × 90 mm Nano carrier with USB cable corridors.
The subsequent **65 × 75 mm Nano carrier** removed those corridors, retained
physical USB shells and implemented preassembly programming plus network updates.
It introduced H2 RX23/TX24 and the documented R7 removal so the standard ROM
loader is reachable, while retaining shared SPI and independent radio controllers.

The historical **51 × 75 mm two-sided carrier** placed S3/H2/MG24 toward the room
and WIZ850io, male harness headers and five axial parts toward the ceiling.
Its electrical pin assignments and firmware are unchanged from the 65 × 75 mm
revision. Staged solder access and measured opposing-tail clearance are now
explicit assembly requirements. Previous snapshots are historical; use the
current front and back drawings together.

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

An intermediate mounting revision added a 6 × 27 mm ear for a fourth support beside
RJ45 (57 × 75 mm overall). Two lower supports straddled its opening. Axial
parts may use arbitrary angles where the final routed result improves; all
functions and firmware pin assignments remain unchanged. See the
[mounting and routing review](../hardware/module-carrier/studies/mounting-routing/review.md).

The following four-hole revision returned to a **51 × 75 mm rectangle**: WIZ moves 6 mm
toward the center, XIAO rotates, and a support fits between U2 and U3. It keeps
four mounting points without the ear. The required assembly order is now
explicitly **the complete back first, then the front**. Rear-first solder access
and unchanged electrical connectivity are checked separately from physical
height and insertion-force qualification. The former ear layout is preserved
under the mounting study.

## Single-anchor split-rail revision

The final MC1 `nano-single-anchor-rails` revision is **47.5 × 75 mm**. It removes
H1, H2 and H4, retains H3 between U2 and U3, and uses split enclosure rails for
edge support. The PCB is 6.86% smaller than the previous four-hole 51 × 75 mm
rectangle. S3 and H2 move closer together; narrow clear edge lands remain for
the enclosure lips. All back components are still soldered before the front.
No sockets, new electronics, pin-map or firmware changes are introduced.

The [preceding four-hole native board](../mechanical/module-carrier/rail-mount/baseline/README.md)
is immutable comparison evidence. The [mounting study](../mechanical/module-carrier/rail-mount/README.md)
defines the split support interface and fit coupons. The
[carrier enclosure prototype](../mechanical/module-carrier/enclosure-prototype/README.md)
extends that interface into printable housing parts. It does not house the
external power, UART bridge, sensors and other radio modules. Actual module and
cable fit, printed tolerances, RF behavior and load capacity remain unqualified.
