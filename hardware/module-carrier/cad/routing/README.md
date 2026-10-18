# Frozen two-sided MC1 Nano routing

`mc1.ses` is the FreeRouting1.9.0 session for the51 ×75 mm two-sided layout, `nano-two-sided-51x75`. Native back-side footprints use real flipped pin coordinates. It is incompatible with earlier placements.

`../manual-route.json` completes THREAD_TX and ZB_RX with explicit0.25 mm centreline paths. ZB_RX uses only the permitted XIAO trace pocket. `finalize.py` imports the session and adds ground pours; `apply_manual_route.py` adds these two paths. All native writes restore the original project rules.

Native electrical/routing checks are clear, but raw DRC intentionally retains43 opposite-side PTH/body projections. `validate_drc.py` classifies only their exact reviewed identities and rejects all other findings. This is conditional mechanical evidence; actual Z clearance and solder workmanship remain unmeasured. No native DRC rule or severity is suppressed.

`reproduce_check.py` regenerates in a clean temporary copy and checks the same classification, connectivity, parity, ERC and regression suite. A fresh autorouter run is not an identical reproduction.
