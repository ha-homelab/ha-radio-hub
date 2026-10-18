# Frozen centered MC1 routing

`mc1.ses` is the FreeRouting 1.9.0 session for the 47.5 × 75 mm single-retainer carrier, `nano-single-anchor-rails`. Native rear footprints use real flipped pin coordinates. This session is incompatible with earlier placements.

`../manual-route.json` completes the connections recorded in its explicit net list with explicit 0.25 mm centerlines. ZB_RX uses only the permitted bottom-edge XIAO trace pocket. `finalize.py` imports the session and adds ground pours; `apply_manual_route.py` adds these paths. All native writes restore the original project rules.

Native electrical/routing checks are clear, but raw DRC retains 41 opposite-side PTH/body projections. `validate_drc.py` classifies only exact reviewed identities and rejects all other findings. Physical Z clearance and solder workmanship remain unmeasured. No native DRC rule or severity is suppressed.

The geometry test requires every rear component, including WIZ, to be solderable before any front module. `reproduce_check.py` regenerates in a clean temporary copy and checks classification, connectivity, parity, ERC and regressions. A fresh autorouter run is not an identical reproduction.
