#pragma once
#include <cstddef>
#include <cstdint>
#include <string>

namespace esphome::low_power_otbr {
inline bool valid_update_token(const std::string &token) {
  if (token.size() != 32) return false;
  for (char c : token) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  return true;
}
inline bool equal_update_token(const char *expected, const char *received) {
  uint8_t difference = 0;
  for (size_t i = 0; i < 32; ++i) difference |= uint8_t(expected[i] ^ received[i]);
  return difference == 0;
}
inline bool update_window_open(uint32_t now, uint32_t start, uint32_t limit) {
  return uint32_t(now - start) < limit;
}
inline bool update_may_arm(bool maintenance, bool durable, bool launched, bool online, uint32_t phase) {
  return maintenance && durable && !launched && online && phase == 0;
}
}
