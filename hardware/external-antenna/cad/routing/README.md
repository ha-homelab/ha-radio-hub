# Frozen routing session

`mc2.ses` was created from MC2-B’s `.build/mc2.dsn` with Freerouting1.9.0 (`-mp 30 -mt 1`). It routes all 33 nets, including R3’s C6-local GPIO8 pull-up and R4/R5 host boot pull-downs. The session is specific to these exact placements. Import with `finalize.py`, then require native ERC, DRC, connectivity and schematic parity to pass with zero findings.

MC2-C preserves those electrical routes and all hole centers. Only the session label and U2 footprint identifier change to `TinyC6_D`; the current D-series envelope, pin names and RF selection contract are regenerated from `design.py`. Fresh native checks are required after importing this session.
