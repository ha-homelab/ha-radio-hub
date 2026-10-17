# Validation status

Initial design reviewed on **2026-10-16**. This record separates software evidence
from hardware acceptance; it is not a declaration that the appliance works in a home.

## Local evidence

- Main ESPHome 2026.9.1 configuration: schema validation and full ESP-IDF 5.5.5
  compilation passed. It includes W5500 Ethernet, active BLE proxy, ZAC93 UART,
  LD2450 UART and BME680 I²C. Static RAM 104,319 / 341,760 bytes; application
  942,199 bytes. Runtime heap and simultaneous load remain unmeasured.
- Experimental Ethernet RF configuration: schema validation passed; final compile
  evidence is recorded in the firmware guide and GitHub workflow when available.
- Linux config renderer: positive rendering and invalid-input tests passed.
  Docker Compose parsed the rendered configuration. No local Docker daemon or
  USB hardware was available for service runtime validation.
- CAD: eight exported STL files were re-imported and checked for watertightness,
  consistent winding, positive volume and one connected body. See the generated
  [mesh report](../mechanical/generated/mesh-report.json). These are geometry checks.
- Original source and documentation: the repository provides an offline checker
  for local links, Python/shell/JSON syntax, required assets, pin-map collisions
  and common credential patterns. This is not an exhaustive security audit.

## Reproducible CI

[Prototype validation](https://github.com/ha-homelab/ha-radio-hub/actions/workflows/check.yml)
runs offline checks, renderer tests, both ESPHome builds, CAD regeneration and a
Linux ser2net image build. [Thread RCP build](https://github.com/ha-homelab/ha-radio-hub/actions/workflows/thread-rcp.yml)
builds the pinned PCA10059 USB firmware with an Arm toolchain. Read the actual
workflow result; the existence of a workflow is not evidence it passed.

## Still requires hardware

No boards were flashed or commissioned. Component/cable fit, FDM tolerances,
insert strength, PoE startup/peak margin, temperatures, radio coexistence,
range, correct RF waveforms, commissioning, restart recovery and sensor accuracy
have not been measured. The full [acceptance checklist](acceptance.md) is the
next step on a physical prototype. Existing household services were not changed.
