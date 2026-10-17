#pragma once
#include <cstdint>
#include <vector>
namespace esphome::remote_base {
using RawTimings = std::vector<int32_t>;
enum ToleranceMode { TOLERANCE_MODE_PERCENTAGE };
inline uint64_t injected_value = 0;
inline uint8_t injected_bits = 0;
inline unsigned matching_protocols = 0;
struct RemoteReceiveData {
  RemoteReceiveData(const RawTimings &, uint32_t, ToleranceMode) {}
  void reset() {}
};
struct ProtocolDouble {
  unsigned index;
  bool decode(RemoteReceiveData &, uint64_t *value, uint8_t *bits) const {
    if (!(matching_protocols & (1U << index))) return false;
    *value = injected_value;
    *bits = injected_bits;
    return true;
  }
};
inline const ProtocolDouble RC_SWITCH_PROTOCOLS[9] = {
  {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}
};
}
