#include "thread_guard.h"
#include "rcp_probe.h"
#include <cassert>
#include <cstring>
#include <map>
#include <string>
#include <vector>
using namespace esphome::low_power_otbr;
using Bytes = std::vector<uint8_t>;
static Bytes packed(std::initializer_list<uint32_t> values) {
  Bytes out;
  for (auto v : values) { uint8_t bytes[5]; auto n = packed_write(v, bytes); out.insert(out.end(), bytes, bytes + n); }
  return out;
}
struct FakeRadio {
  std::map<uint32_t, Bytes> values{{1, packed({4,3})}, {5, packed({34,513,64,65})},
    {0xb0, packed({11})}, {0xb1, packed({4})}, {0x120b, packed({0x1ff})}};
  unsigned queries{0};
  bool operator()(uint32_t property, uint8_t *data, size_t capacity, size_t &size) {
    ++queries;
    auto it = values.find(property);
    if (it == values.end() || it->second.size() > capacity) return false;
    size = it->second.size(); std::memcpy(data, it->second.data(), size); return true;
  }
  ThreadFault probe() { return probe_rcp([&](auto&&... args) { return (*this)(args...); }, 0x1ff); }
};
int main(int argc, char **argv) {
  assert(argc == 2);
  const std::string name = argv[1];
  ThreadGuard guard;
  FakeRadio radio;
  if (name == "fresh_without_ethernet") {
    assert(!guard.restore({}, false)); assert(!guard.record.quarantined && !guard.record.armed);
  } else if (name == "normal_power_cycles") {
    assert(guard.arm());
    for (unsigned i = 0; i < 100; ++i) { assert(guard.restore(guard.record, false)); assert(guard.arm()); }
    assert(!guard.record.quarantined && !guard.record.faults);
  } else if (name == "uncommissioned") {
    assert(radio.probe() == ThreadFault::NONE); assert(guard.arm());
    // No dataset is a separate application state, not a failed radio.
    assert(!guard.record.quarantined);
  } else if (name == "terminal_persists") {
    assert(guard.arm()); guard.quarantine(ThreadFault::RESET_FAILED);
    for (unsigned i = 0; i < 100; ++i) { assert(!guard.restore(guard.record, i % 2)); assert(!guard.arm()); }
    assert(guard.record.faults == 1);
  } else if (name == "generic_sdk_abort") {
    assert(guard.arm()); assert(guard.restore(guard.record, true)); assert(!guard.arm());
    assert(guard.record.fault == static_cast<uint32_t>(ThreadFault::HOST_CRASH));
  } else if (name == "unrelated_unarmed_abort") {
    assert(!guard.restore({}, true)); assert(!guard.record.quarantined);
  } else if (name == "normal_ota_reboot") {
    assert(guard.arm()); guard.normal_shutdown();
    assert(!guard.restore(guard.record, true)); assert(guard.arm());
  } else if (name == "repeat_explicit_retry") {
    for (unsigned i = 1; i <= 10; ++i) {
      guard.quarantine(ThreadFault::RESET_FAILED); assert(!guard.arm());
      guard.retry(); assert(guard.record.retries == i); assert(guard.arm());
      assert(guard.restore(guard.record, false));
    }
    assert(guard.record.faults == 10);
  } else if (name == "corrupt_guard") {
    ThreadRecord corrupt{}; corrupt.magic = 0;
    assert(guard.restore(corrupt, false)); assert(!guard.arm());
    assert(guard.record.fault == static_cast<uint32_t>(ThreadFault::STORAGE));
  } else if (name == "persistence_failures") {
    guard.quarantine(ThreadFault::RESET_FAILED);
    for (int failed = -1; failed < 4; ++failed) {
      ThreadRecord stored{};
      unsigned calls = 0;
      const bool result = write_verified_record(guard.record,
        [&](const ThreadRecord &value) { ++calls; stored = value; return failed != 0; },
        [&]() { ++calls; return failed != 1; },
        [&](ThreadRecord &value) { ++calls; value = stored; if (failed == 3) ++value.faults; return failed != 2; });
      assert(result == (failed == -1));
      assert(calls == (failed == 0 ? 1u : failed == 1 ? 2u : 3u));
    }
  } else if (name == "saturating_counters") {
    guard.record.faults = UINT32_MAX; guard.record.retries = UINT32_MAX;
    guard.quarantine(ThreadFault::RESET_FAILED); guard.retry();
    assert(guard.record.faults == UINT32_MAX && guard.record.retries == UINT32_MAX);
  } else if (name == "maintenance_pause") {
    assert(guard.arm()); guard.quarantine(ThreadFault::MAINTENANCE);
    assert(guard.record.faults == 0 && !guard.arm());
    for (unsigned i = 0; i < 10; ++i) { assert(!guard.restore(guard.record, false)); assert(!guard.arm()); }
    assert(guard.record.fault == static_cast<uint32_t>(ThreadFault::MAINTENANCE));
    guard.retry(); assert(guard.arm()); assert(guard.record.retries == 1 && guard.record.faults == 0);
  } else if (name == "refuse_unstored_maintenance_or_retry") {
    guard.arm();
    assert(!guard.pause_if_durable([]() { return false; }));
    assert(guard.record.armed && !guard.record.quarantined);
    assert(guard.pause_if_durable([]() { return true; }));
    assert(!guard.record.armed && guard.record.quarantined);
    assert(!guard.retry_if_durable([]() { return false; }));
    assert(guard.record.quarantined && guard.record.retries == 0);
    assert(guard.retry_if_durable([]() { return true; }));
    assert(!guard.record.quarantined && guard.record.retries == 1);
  } else if (name == "old_session_does_not_arm_waiting_boot") {
    guard.arm(); assert(guard.restore(guard.record, false));
    assert(!guard.record.armed);
    assert(!guard.restore(guard.record, true));
    assert(!guard.record.quarantined);
  } else if (name == "missing_rcp") {
    radio.values.clear(); assert(radio.probe() == ThreadFault::SILENT_RCP); assert(radio.queries == 1);
  } else if (name == "stale_protocol") {
    radio.values[1] = packed({4,2}); assert(radio.probe() == ThreadFault::PROTOCOL);
  } else if (name == "not_radio") {
    radio.values[5] = packed({32,513}); assert(radio.probe() == ThreadFault::CAPABILITIES);
  } else if (name == "missing_raw") {
    radio.values[5] = packed({34,64,65}); assert(radio.probe() == ThreadFault::CAPABILITIES);
  } else if (name == "stale_api") {
    radio.values[0xb0] = packed({3}); assert(radio.probe() == ThreadFault::API_VERSION);
  } else if (name == "too_new_host_requirement") {
    radio.values[0xb1] = packed({12}); assert(radio.probe() == ThreadFault::API_VERSION);
  } else if (name == "missing_radio_feature") {
    radio.values[0x120b] = packed({0x1fe}); assert(radio.probe() == ThreadFault::CAPABILITIES);
  } else if (name == "rcp_dies_during_probe") {
    for (uint32_t missing : {1u, 5u, 0xb0u, 0xb1u, 0x120bu}) {
      FakeRadio each; each.values.erase(missing); assert(each.probe() == ThreadFault::SILENT_RCP);
      assert(each.queries <= 5);
    }
  } else if (name == "good_rcp") {
    assert(radio.probe() == ThreadFault::NONE); assert(radio.queries == 5);
  } else if (name == "malformed_varints") {
    for (auto bytes : {Bytes{0x80}, Bytes{0xff,0xff,0xff,0xff,0x7f}, Bytes{4}}) {
      radio.values[1] = bytes; assert(radio.probe() == ThreadFault::PROTOCOL);
    }
  } else if (name == "hdlc_roundtrip") {
    for (unsigned byte = 0; byte < 256; ++byte) {
      const uint8_t source[]{0x81,6,1,static_cast<uint8_t>(byte)};
      uint8_t wire[64]; const auto n = encode_hdlc(source, sizeof(source), wire, sizeof(wire));
      HdlcReceiver receiver; size_t received = 0;
      for (size_t i = 0; i < n; ++i) received = receiver.push(wire[i]);
      assert(received == sizeof(source)); assert(!std::memcmp(source, receiver.frame.data(), received));
    }
  } else if (name == "hdlc_corrupt_and_resync") {
    const uint8_t source[]{0x81,6,1,4,3}; uint8_t wire[64];
    const auto n = encode_hdlc(source, sizeof(source), wire, sizeof(wire));
    HdlcReceiver receiver; wire[2] ^= 1;
    for (size_t i = 0; i < n; ++i) assert(receiver.push(wire[i]) == 0);
    wire[2] ^= 1; size_t received = 0;
    for (size_t i = 0; i < n; ++i) received = receiver.push(wire[i]);
    assert(received == sizeof(source));
  } else if (name == "hdlc_overflow") {
    HdlcReceiver receiver; for (int i = 0; i < 1024; ++i) assert(receiver.push(1) == 0);
    assert(receiver.push(0x7e) == 0);
    uint8_t output[2]; const uint8_t input[1]{1}; assert(encode_hdlc(input, 1, output, 2) == 0);
  } else return 2;
}
