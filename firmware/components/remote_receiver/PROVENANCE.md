# Vendored ESPHome receiver

Source: [ESPHome 2026.9.1](https://github.com/esphome/esphome/tree/0b2b16e664ecfc0add37f3435db1c2140b8a687e/esphome/components/remote_receiver), commit `0b2b16e664ecfc0add37f3435db1c2140b8a687e`.

The adjacent LICENSE is the unmodified license from that commit: Python is MIT; C++ runtime is GPLv3. The local C++ changes use the same GPLv3 license. No ESP8266 RF Airbridge receiver patch is included.

Changes in `__init__.py` reject unreviewed ESPHome versions, non-ESP32-S3 targets and DMA. Runtime changes are limited to `remote_receiver.h` and `remote_receiver_rmt.cpp`: main-loop `suspend()`/`resume()` stop and restart the ESP32 RMT channel; an ISR/task spinlock gates ring publication and receive rearming; both transitions discard buffered captures. A generation counter prevents a listener that starts TX from leaving the current loop iterating an obsolete ring snapshot. Failure closes the gate and marks the component failed. Other supplied component files are unchanged.

Driver calls to enable/disable stay outside the capture lock; callback publication/rearming and the resume initial arm are serialized. The callback never invokes the control APIs. The firmware uses non-DMA ESP32-S3 RMT and calls pause/resume only on the ESPHome main loop. See [ESP-IDF RMT lifecycle](https://docs.espressif.com/projects/esp-idf/en/v5.5.1/esp32s3/api-reference/peripherals/rmt.html) and [driver source](https://github.com/espressif/esp-idf/blob/v5.5.1/components/esp_driver_rmt/src/rmt_rx.c).

Native lifecycle tests compile the actual modified C++ against driver doubles. They cannot replace testing ISR timing and RF self-echo on hardware. Keep this local component pinned until an upstream implementation provides equivalent capture ownership; review and rerun those tests before any ESPHome upgrade.
