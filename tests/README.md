# RF Ethernet regression tests

Run from the repository root, using the pinned firmware environment and a C++17 compiler:

```sh
python3 -m venv .venv
.venv/bin/pip install -r firmware/requirements.txt
RF_CPP_SANITIZERS=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Tests never contact a broker, Home Assistant, a radio or a live ESPHome node. All RF codes, credentials and identities in fixtures are synthetic. Native build products and importer outputs live in temporary directories. Missing compilers or missing/wrong ESPHome versions fail the run; these tests do not silently skip the native checks.

## Compatibility reference

The independent expected payloads in `fixtures/rf_contract.json` describe [RF Airbridge at c96777d0df65a7420e4883d79187f31eb1b98c9b](https://github.com/ha-homelab/rf-airbridge/tree/c96777d0df65a7420e4883d79187f31eb1b98c9b), specifically its receive and Dooya documentation and package API. These are expected outputs, not generated from the Ethernet implementation under test. The initial receiver/validator suite was also run against those upstream headers.

- `test_rf_contract.py` compiles the production Receiver, RM433 decoder and transmit validators. It verifies exact MQTT fields/types, leading zeroes, maximum uint64 values as strings, first matching protocol, native-before-MQTT delivery, offline/failure/reconnect behavior, sliding RM433 deduplication, timer rollover, raw opt-in/limits/rate limiting and invalid signed transmit inputs. A controlled RCSwitch decoder double isolates the transport policy; RM433 uses its real decoder and a literal pulse fixture.
- `test_stock_rc_switch.py` additionally compiles the **installed ESPHome 2026.9.1** `rc_switch_protocol.cpp/.h` unmodified and verbatim RemoteReceiveData declarations/methods extracted from its `remote_base` files. It checks independent pulse vectors, 24-bit leading zeroes, 64-bit maximum values, RM433 precedence and the stock decoder's acceptance of valid prefixes. Automation base classes, clock, entropy and MQTT remain host doubles. Upstream source is read at test time and is not redistributed in this test directory.
- `test_rmt_lifecycle.py` compiles the actual vendored ESP32 RMT driver against ESP-IDF doubles. It covers a pending ISR during disable, a late callback while suspended, flushing pre-transmit captures, receiving fresh post-transmit pulses, a listener starting transmission while the ring is being drained, repeated lifecycle transitions and driver-error paths. The doubles assert that potentially blocking enable/disable operations run outside the capture spinlock. They cannot establish real interrupt timing or electrical correctness.
- `test_tx_scheduler.py` compiles the actual package's C++ conditions, callbacks, validators and JSON builders. A narrow script/wait/delay scheduler seam supplies deterministic time and delayed RMT completion. All four RCSwitch/Dooya command combinations must reject concurrent commands, publish completion only after the callback, hold a further 750 ms cooldown and never replay rejected requests. Tests also check exact completion payloads, validation before busy checks, fail-closed timeout/rearm failure and GPIO/radio transition order. Unknown action types make the harness fail rather than being ignored. This is not an implementation of ESPHome's scheduler.
- `test_migrate_rf.py` exercises the offline importer with synthetic files. It checks existing entity definitions and string widths, private secret export and permissions, substituted identity, filter normalization, unsupported input rejection, reserved IDs, existing-output preservation and value-free CLI output.

The RCSwitch receive stream intentionally retains repeated decoded frames; only RM433 has the sliding 350 ms quiet-period guard. MQTT receive/result events use QoS 0 and are not retained. Upstream has no MQTT transmit-command subscription: transmit requests are native API actions. `send_failed` is an additive Ethernet-port outcome; it does not claim remote RF delivery.

Passing these tests plus full firmware compilation verifies software contracts. It does not replace a measured GDO0/GDO2 waveform test, repeated receive/transmit/receive testing, broker/API reconnect checks on the actual nodes or inspection of Home Assistant registry mappings during migration.
