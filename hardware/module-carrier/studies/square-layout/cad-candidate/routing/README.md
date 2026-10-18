# Frozen square-study routing

`mc1.ses` is the saved FreeRouting session for the separate 100 × 100 mm geometry study. H2 is vertical in the middle; WIZ850io is below it with RJ45 facing the bottom edge. Six remaining Ethernet signal centerlines are stored in `../manual-route.json` and applied after session import. This session must not be used for the active 100 × 90 mm carrier.

Use the candidate's `reproduce_check.py` for a clean native rebuild and rule check. See `../verification.json` and `../checks/reproduction.json` for current results. Native writers reapply `project_rules.py`; no DRC exceptions are added.
