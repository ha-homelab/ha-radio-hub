# Frozen routing session

`mc2.ses` is generated for **MC2-D** from `.build/mc2.dsn` with Freerouting 2.5.0 (`--router.autorouter.max_passes=100 --router.optimizer.max_threads=1 --router.automatic_neckdown=false --router.neck_width_um=0 --router.strict_drc=true -mt 1 -dct 0 -da`). It routes all 31 nets, including J10's mandatory EN/BOOT leads and R4/R5 host boot pull-downs. R3 is absent because XIAO already has a GPIO8 pull-up. The session includes the new U2 14-pin placement and avoids the real rounded access opening.

Import with `finalize.py`; require native ERC, DRC, connectivity and schematic parity all zero. The old TinyC6 session is incompatible. Source generation plus this exact session must reproduce the saved copper topology.
