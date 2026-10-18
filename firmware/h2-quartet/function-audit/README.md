# Function-audit evidence

Reviewed 2026-10-17. The full discussion is in [the function audit](../../../docs/h2-quartet-function-audit.md).

## Existing contract tests

From repository root, using the already installed ESPHome 2026.9.1 environment:

```sh
RF_CPP_SANITIZERS=1 python -m unittest discover -s tests -p 'test_*.py' -v
```

Result: **77 tests passed**, 14.591 seconds. This tests existing production source against offline models and fixtures. It does not exercise the proposed Quartet SPI transport, real UART/radio timing or a local H2 BR.

## Stock H2 local-BR build probe

`stock-br-probe/` is a deliberately minimal build-availability probe, not usable firmware. It calls the public BR initializer without attempting to create a network or initialize hardware. It must not be flashed.

With ESP-IDF **5.5.5** activated and its H2 toolchain installed, copy this directory to a temporary work directory before running:

```sh
idf.py -C /tmp/h2-stock-br-probe -DIDF_TARGET=esp32h2 reconfigure
cmake --build /tmp/h2-stock-br-probe/build --parallel 2
```

The first command succeeded. Its generated configuration enabled `OPENTHREAD_FTD`, `OPENTHREAD_RADIO_NATIVE`, `OPENTHREAD_PLATFORM_NETIF` and `OPENTHREAD_BORDER_ROUTER` for H2. The build exited **1** with:

```text
ninja: error: '<IDF_PATH>/components/openthread/lib/esp32h2/libopenthread_br.a', needed by 'h2_br_stock_link_probe.elf', missing and no known rule to make it
```

No objects needed to be compiled to reach this missing dependency. This confirms a limitation of the stock SDK path; it does not prove that a custom H2 BR implementation is impossible. The [successful H2 Ethernet/BLE probe](../README.md) remains a separate positive result.

No new SDK installation, firmware flashing, network migration or device configuration occurred. The probe source and compact result are retained here; machine-specific logs and generated build products are excluded.
