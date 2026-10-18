# Frozen compact MC1 Nano routing

`mc1.ses` is the saved FreeRouting 1.9.0 session for the 65 × 75 mm network-maintained carrier, H2 application/ROM UART23/24. WIZ850io is at (61,67.9), 180°, with the RJ45 opening outward at the bottom. This session is incompatible with earlier placements.

`../manual-route.json` completes THREAD_TX and ZB_RX using explicit 0.25 mm centreline paths. The paths were simplified with obstacle checks and then accepted by native KiCad DRC. ZB_RX uses only the permitted trace pocket beside the XIAO antenna; no via or ground pour is allowed there.

Run `../finalize.py` then `../apply_manual_route.py`. `../reproduce_check.py` regenerates in a clean temporary copy and verifies DRC, ERC, netlist parity and regression tests. Every native-write stage restores the original Default/Power classes with `../project_rules.py`; no DRC check is disabled. A new autorouter run is not an identical reproduction.
