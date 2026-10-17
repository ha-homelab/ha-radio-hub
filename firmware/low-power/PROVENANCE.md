# Low-power integration provenance

The local integration code in this directory is part of this repository's MIT-licensed work. It uses the existing RF package and its separately licensed ESPHome receiver patch; the combined binary is not described as MIT-only. See `../../THIRD_PARTY_NOTICES.md`.

`prepare.py` exports `components/esp_ot_br_server` and `LICENSE` from Espressif's Apache-2.0 `esp-thread-br`, commit `29a2345e3f0c61bba9307f3daea5ed0c94388ed3`. Copyright/SPDX headers remain in the exported source. The root upstream license is copied into the generated component. The unmodified component is retained in the prepared output as `upstream-original/`.

The generated component differs from upstream only in:

1. Its CMake source/dependency list: REST C implementation and favicon, without the Wi-Fi provisioning source or browser filesystem image.
2. Removal of an unused `protocol_examples_common.h` include.
3. An explicit configurable HTTP server port supplied by the ESPHome component.
4. HTTP status 404 in the unknown-URL handler, required by `python-otbr-api` protocol detection.
5. A small exported entry point that starts the server after ESPHome's Ethernet interface and the OpenThread instance exist. This avoids relying on an IP event that may already have occurred.

Patch application checks exact expected source contexts. No upstream code is downloaded at device runtime. The generated component remains Apache-2.0-licensed.

The H2 preparer copies ESP-IDF 5.5.5's CC0-1.0 `examples/openthread/ot_rcp` example. The expected official SDK commit is `b774170ff46c393eeb5e495ea37936038d3f4f4f`. Its C source is unchanged; local changes are explicit build dependencies and configuration for 4MB flash and UART RX23/TX24. Git SDK checkouts must match that commit; an ESPHome-managed SDK archive can be version-checked but has no Git identity. ESP-IDF and its components retain their own licenses.
