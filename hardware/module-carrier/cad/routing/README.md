# Frozen MC1 Nano routing session

`mc1.ses` is the saved FreeRouting 1.9.0 session for the 80 × 90 mm Nano carrier. WIZ850io is at (76,82.9) mm, rotation 180°, with its RJ45 opening facing the bottom edge. It must not be applied to any previous placement.

The session is completed using `../manual-route.json`, which records a complete 0.25 mm ZB_RX centerline and one additional 0.8 mm +5V branch between the diode supply nodes. ZB_RX is completed through the narrow antenna escape pocket; other signal nets are in the stored router session. `../apply_manual_route.py` applies these centerlines after `../finalize.py` imports the session and restores schematic terminal metadata. Native DRC is the acceptance gate.

`../reproduce_check.py` reconstructs the result in a clean temporary copy and runs native DRC/parity/ERC plus all geometry/electrical tests. Every native-write stage restores the Default/Power classes using `../project_rules.py`. A fresh autorouter search may produce different paths; never apply these saved completions to a different result without rerouting and checking.
