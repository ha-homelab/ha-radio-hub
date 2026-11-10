# ESPHome 2026.10 compatibility review

The supported tool is ESPHome 2026.10.2, with ESP-IDF **5.5.5** retained for the RF/OTBR profiles. The initial 2026.10.0 compatibility reference is commit [`704551a6c93c29a311802f7ee97d67a9e9bce718`](https://github.com/esphome/esphome/tree/704551a6c93c29a311802f7ee97d67a9e9bce718). This is a source and build compatibility change; historical build evidence and hardware acceptance remain separate.

- Receiver registration now requires counted `remote_base.add_listener` / `add_dumper` calls. Calling only the C++ registration methods omits the required fixed storage. The local Python generator uses the counted helpers; the patched C++ suspend/resume implementation is unchanged.
- The stock decoder harness uses C++20 and the installed non-ESP8266 `progmem_memcpy` implementation, retaining unmodified upstream RC-switch decoder sources. ESP32 flash tables are directly addressable.
- Upstream RMT completion also fires synchronously on setup/carrier and enqueue failure. The scheduler checks both failed and warning status. A failed transmitter leaves the radio idle and receive suspended, latches a fault, and never reports a successful send or invokes another RMT write through a failed channel. The existing late-completion/timeout guard remains.
- The upstream RMT allocator still runs before the open-drain release write. The wrapper is therefore still required: preload HIGH, enable open drain, then allocate with HIGH initial level. Its C++ implementation and exact IDF source hashes are unchanged.
- CC1101 now detaches GDO0 interrupts in packet mode. This profile still rejects packet mode and a CC1101-owned GDO0 pin, retaining the separate asynchronous RX/TX contract.
- ESPHome now trims unrequested TLS and crypto features. The custom OTBR integration explicitly requests TLS, its server role, ECP, AES-CCM and deterministic ECDSA through the upstream capability APIs, matching the built-in OpenThread requirements. Generated configuration must not disable them, and the compiled SDK checks require each feature to be enabled.
- ESPHome's platform mapping for explicit IDF 5.5.5 changes to pioarduino 55.03.312. The guarded RF/OTBR profiles retain explicit IDF 5.5.5; the separate sensor-only profile uses the upstream default. The OTBR version guard and generated SDK/source checks must pass on 5.5.5; an unexpected SDK source still fails the build.

The two reviewed upstream SHA-256 values are enforced during configuration and again against the compiled source:

```
remote_transmitter_rmt.cpp  3a82caf436a651d0c94f27aabf6b9544fb9160b7aa94633903314faadcb18e21
cc1101.cpp                  ed86211b9450a189f43bcc61d4a1e36ad3e641f02f081b18bfff5aeb1e3c8d83
```

The generated receiver regression covers classic ESP32 and ESP32-S3; scheduler tests cover immediate failure and delayed completion. Full CI additionally compiles the RF migration, S3 OTBR, MC1, MC2, and companion radio images with the existing generated-code, SDK and ELF checks. No device is flashed by these checks.

## 2026.10.1 patch qualification

The updated tool is pinned to [ESPHome 2026.10.1, commit `4ea26ed65fefaf6ec9d1347285253801db096ee5`](https://github.com/esphome/esphome/tree/4ea26ed65fefaf6ec9d1347285253801db096ee5). The [complete upstream comparison](https://github.com/esphome/esphome/compare/2026.10.0...2026.10.1) leaves `remote_receiver`, `remote_base`, `remote_transmitter`, `cc1101` and the OpenThread component unchanged. Both enforced source hashes above are unchanged, as are the local receiver C++ lifecycle patch and RF startup wrapper. The exact version guards advance together; unreviewed versions and a different IDF still fail closed.

The patch changes generated include ordering and disables precompiled headers with affected older ccache versions to prevent stale object reuse. These build changes require the real installed-tool receiver generation and stock decoder tests, followed by all existing firmware compilation, SDK and source-hash checks. The guarded profiles still pin ESP-IDF 5.5.5. This qualification does not assert physical RF timing, audio, enclosure fit or new hardware acceptance.

MC2 recipe changes also invalidate the committed compilation evidence and its fabrication manifest. After both MC2 builds pass, use the `mc2-compilation-evidence` artifact from that exact source revision to update `firmware/external-antenna/build-evidence.json` and `c6-build-evidence.json`; verify every `recipe_sha256` against the current files first. Regenerate the fabrication package with pinned KiCad 10.0.6 using `python3 hardware/external-antenna/fabrication/package.py --cli kicad-cli`, then require a fresh complete CI run on the committed outputs. Do not update receipt hashes by hand or use assembly-only evidence refresh for a firmware change. The ordinary PCB check remains read-only and rejects stale evidence.


## 2026.10.2 patch qualification

The current tool is pinned to [ESPHome 2026.10.2, commit `9a78022ded2285861f10de50168a0aa71e2a4322`](https://github.com/esphome/esphome/tree/9a78022ded2285861f10de50168a0aa71e2a4322). The [complete upstream comparison](https://github.com/esphome/esphome/compare/2026.10.1...2026.10.2) does not change `remote_receiver`, `remote_base`, `remote_transmitter`, `cc1101`, `openthread`, `espnow` or `packet_transport`. The two source hashes above, local C++ lifecycle patch and RF startup wrapper remain unchanged. Exact host-version guards, generated build metadata and regression fixtures advance together; ESP-IDF stays at **5.5.5** and unreviewed versions still fail closed.

This patch fixes Bluetooth proxy connection release when a new API client replaces the subscriber. It also changes ESP32 TLS configuration reconciliation to retain the peer certificate when TLS 1.3 requires it. The real installed-tool OTBR code-generation test must continue to preserve Thread crypto and DTLS server support. Receiver generation, stock decoder, RF startup and ESP-NOW code-generation regressions remain required before the complete firmware compile matrix. The Apple Silicon compiler wrapper and unrelated host/LibreTiny updates do not justify changing our board targets or SDK pins.

Committed historical build reports retain the version they actually compiled. Regenerate MC2 compilation evidence and the fabrication manifest only from the successful builds of the revised recipes, following the evidence-refresh procedure above. Source review and automated tests do not establish hardware RF timing, radio coexistence or completed device flashing.
