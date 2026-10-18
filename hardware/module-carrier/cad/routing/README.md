# Frozen router session

`mc1.ses` is the FreeRouting 1.9.0 result for the MC1 generated footprint placement. It is preserved to reproduce the checked routing candidate without relying on a new search result. The current left-edge-layout session leaves `/THREAD_EN` and `/ZB_RX` unconnected. `../manual-route.json` and `../apply_manual_route.py` finish those connections. The final native PCB passes KiCad DRC with zero violations, zero unconnected items and zero schematic-parity issues; see `../checks/drc.json`.

Do not reuse this session after moving footprints or changing pad geometry. Reroute and recheck instead.
