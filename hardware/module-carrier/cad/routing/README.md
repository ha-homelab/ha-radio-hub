# Frozen compact MC1 routing session

`mc1.ses` is the committed FreeRouting session for the 100 × 90 mm compact carrier. WIZ850io is at (92.9,67) mm, rotated270° so its RJ45 opening faces the right edge. This session belongs to the current frozen footprint placement and must not be applied to an earlier layout.

The session leaves one signal, RF_MISO, unfinished. The exact remaining centerline is stored in `../manual-route.json`; `../apply_manual_route.py` applies it after `../finalize.py` imports the session and restores schematic terminal metadata. Native DRC then confirms zero remaining connections and zero rule or parity issues.

Use `../reproduce_check.py` to reconstruct and verify this route in a clean temporary copy. Each board-write stage reapplies `../project_rules.py`, preserving the Default and Power netclasses that standalone pcbnew otherwise replaces with its defaults. A new autorouter search is not guaranteed to produce the same route; do not apply the saved manual centerline blindly to a different session.
