# Frozen routing session

`mc2.ses` was created from MC2-B’s `.build/mc2.dsn` with Freerouting1.9.0 (`-mp 30 -mt 1`). It routes all 33 nets, including R3’s C6-local GPIO8 pull-up and R4/R5 host boot pull-downs. The session is specific to these exact placements. Import with `finalize.py`, then require native ERC, DRC, connectivity and schematic parity to pass with zero findings.
