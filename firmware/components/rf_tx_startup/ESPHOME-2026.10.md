# ESPHome 2026.10 compatibility review

The supported tool is ESPHome 2026.10.0, with ESP-IDF **5.5.5** retained for the RF/OTBR profiles. The upstream reference is commit [`704551a6c93c29a311802f7ee97d67a9e9bce718`](https://github.com/esphome/esphome/tree/704551a6c93c29a311802f7ee97d67a9e9bce718). This is a source and build compatibility change; historical build evidence and hardware acceptance remain separate.

- Receiver registration now requires counted `remote_base.add_listener` / `add_dumper` calls. Calling only the C++ registration methods omits the required fixed storage. The local Python generator uses the counted helpers; the patched C++ suspend/resume implementation is unchanged.
- The stock decoder harness uses C++20 and the installed non-ESP8266 `progmem_memcpy` implementation, retaining unmodified upstream RC-switch decoder sources. ESP32 flash tables are directly addressable.
- Upstream RMT completion also fires synchronously on setup/carrier and enqueue failure. The scheduler checks both failed and warning status. A failed transmitter leaves the radio idle and receive suspended, latches a fault, and never reports a successful send or invokes another RMT write through a failed channel. The existing late-completion/timeout guard remains.
- The upstream RMT allocator still runs before the open-drain release write. The wrapper is therefore still required: preload HIGH, enable open drain, then allocate with HIGH initial level. Its C++ implementation and exact IDF source hashes are unchanged.
- CC1101 now detaches GDO0 interrupts in packet mode. This profile still rejects packet mode and a CC1101-owned GDO0 pin, retaining the separate asynchronous RX/TX contract.
- ESPHome's platform mapping for explicit IDF 5.5.5 changes to pioarduino 55.03.312. No profile is forced to the newer default IDF 5.5.6. The OTBR version guard and generated SDK/source checks must pass on 5.5.5; an unexpected SDK source still fails the build.

The two reviewed upstream SHA-256 values are enforced during configuration and again against the compiled source:

```
remote_transmitter_rmt.cpp  3a82caf436a651d0c94f27aabf6b9544fb9160b7aa94633903314faadcb18e21
cc1101.cpp                  ed86211b9450a189f43bcc61d4a1e36ad3e641f02f081b18bfff5aeb1e3c8d83
```

The generated receiver regression covers classic ESP32 and ESP32-S3; scheduler tests cover immediate failure and delayed completion. Full CI additionally compiles the RF migration, S3 OTBR, MC1, MC2, and companion radio images with the existing generated-code, SDK and ELF checks. No device is flashed by these checks.
