# MC1 square geometry study — separate candidate

This directory tests a **100 × 100 mm, two-layer** alternative. It does not replace the active `hardware/module-carrier/cad/` design. S3 moves to the right, inverted H2 occupies the middle, horizontal XIAO MG24 sits at the left edge, and WIZ850io follows directly below H2 with its RJ45 mouth facing down, 2 mm beyond the carrier.

All 17 fitted parts, 145 physical pins and 103 connected pins retain their electrical identities. Factory male module pins still solder directly into carrier holes; there are no sockets, no extra SMT parts and no connector removal. All five loose axial components remain on top. The area is 10,000 mm², 11.1% greater than the active 100 × 90 mm board.

The exact placement, service reservations and tradeoffs are in `geometry-study.json` and `geometry-study.md`. `assembly-top.svg/png` is a scaled explanatory view; `mc1.kicad_pcb` and `mc1.kicad_sch` are the editable native candidate. `design.json`, `connectors.json`, and `BOM.csv` carry the actual pad and part ledger. Manufacturer mechanical evidence is linked in `design.py` and `design.json`.

## Main qualification

The layout retains all three 30 mm USB service envelopes. XIAO's 14 mm-wide envelope passes through a tight gap: 0.645 mm to the H2 antenna body, 0.680 mm to the WIZ PCB, and 0.180 mm to the WIZ courtyard. Those are engineering reservations, not measured USB cable specifications. The selected plug and vertical cable exit must be checked physically. The service cable temporarily enters H2's RF clearance area; remove it during normal operation and RF testing.

H2's antenna is now internal, facing the gap above WIZ. WIZ PCB clearance is 15.325 mm; lateral clearance to the S3 PCB is 15.56 mm. The enlarged copper keepout and lack of adjacent parts do not prove RF performance. This is the main tradeoff against the active board's edge-facing H2 antenna. XIAO's antenna faces the left carrier edge and is only partly beyond it. The enclosure must preserve radio clearance and all connector access.

Keep every stock USB connector. Removing USB-C does not remove the module substrate. It also complicates independent firmware recovery, especially XIAO's SAMD11/CMSIS-DAP path. S3 v1.1 uses Micro-USB, not USB-C. For the corrected per-board USB power procedure, see the active CAD README and `../service-review.md`: **a VBUS blocker alone does not power XIAO's SAMD11 probe from its VIN header**. Do not apply an unqualified, common USB-power recipe to all three boards.

## Reproduction

Use KiCad 10's Python and CLI, plus installed KiCad libraries:

```sh
"$KICAD_PY" generate.py --libraries "$KICAD_LIBRARIES"
"$KICAD_CLI" sch export netlist --format kicadxml -o .build/mc1.xml mc1.kicad_sch
cp routing/mc1.ses .build/mc1.ses
"$KICAD_PY" finalize.py
"$KICAD_PY" apply_manual_route.py
"$KICAD_CLI" pcb drc --format json --output checks/drc.json --schematic-parity mc1.kicad_pcb
"$KICAD_CLI" sch erc --format json --output checks/erc.json mc1.kicad_sch
python3 test_design.py
```

`project_rules.py` preserves the actual project settings after native saves: 0.25 mm default signals, 0.80 mm power/ground, 0.20 mm clearance, 0.80/0.40 mm vias, and 0.50 mm copper-edge clearance. No DRC severity or exclusion is relaxed. `reproduce_check.py --python "$KICAD_PY" --cli "$KICAD_CLI" --libraries "$KICAD_LIBRARIES"` rebuilds and verifies a clean temporary copy. The saved router session and manual centerlines belong only to this placement.

This is a reviewable engineering candidate. Native checks do not establish physical assembly, thermal performance, RF coexistence or firmware interoperability. No fabrication files are released or ordered.
