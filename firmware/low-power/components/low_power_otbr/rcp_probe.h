#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include "thread_guard.h"

namespace esphome::low_power_otbr {
inline uint16_t hdlc_crc(uint16_t crc, uint8_t byte) {
  crc ^= byte;
  for (int i = 0; i < 8; ++i) crc = (crc >> 1) ^ ((crc & 1) ? 0x8408 : 0);
  return crc;
}
inline size_t packed_write(uint32_t v, uint8_t *out) {
  size_t n = 0;
  do { out[n++] = (v & 0x7f) | (v > 0x7f ? 0x80 : 0); v >>= 7; } while (v);
  return n;
}
inline bool packed_read(const uint8_t *data, size_t size, size_t &at, uint32_t &out) {
  out = 0;
  for (unsigned shift = 0; shift < 35 && at < size; shift += 7) {
    const uint8_t b = data[at++];
    if (shift == 28 && (b & 0xf0)) return false;
    out |= static_cast<uint32_t>(b & 0x7f) << shift;
    if (!(b & 0x80)) return true;
  }
  return false;
}
inline size_t encode_hdlc(const uint8_t *data, size_t size, uint8_t *out, size_t capacity) {
  if (capacity < size * 2 + 6) return 0;
  size_t n = 0;
  out[n++] = 0x7e;
  auto emit = [&](uint8_t b) {
    if (b == 0x7e || b == 0x7d || b == 0x11 || b == 0x13 || b == 0xf8) {
      out[n++] = 0x7d; out[n++] = b ^ 0x20;
    } else out[n++] = b;
  };
  uint16_t crc = 0xffff;
  for (size_t i = 0; i < size; ++i) { crc = hdlc_crc(crc, data[i]); emit(data[i]); }
  crc ^= 0xffff;
  emit(crc & 0xff); emit(crc >> 8); out[n++] = 0x7e;
  return n;
}
class HdlcReceiver {
 public:
  // The returned frame excludes FCS and stays valid until the next push().
  size_t push(uint8_t byte) {
    if (byte == 0x7e) {
      const size_t result = !overflow_ && !escaped_ && size_ >= 3 && crc_ == 0xf0b8 ? size_ - 2 : 0;
      size_ = 0; crc_ = 0xffff; escaped_ = false; overflow_ = false;
      return result;
    }
    if (overflow_) return 0;
    if (byte == 0x7d) { if (escaped_) overflow_ = true; else escaped_ = true; return 0; }
    if (escaped_) { byte ^= 0x20; escaped_ = false; }
    if (size_ == frame.size()) { overflow_ = true; return 0; }
    frame[size_++] = byte; crc_ = hdlc_crc(crc_, byte); return 0;
  }
  std::array<uint8_t, 256> frame{};
 private:
  size_t size_{0};
  uint16_t crc_{0xffff};
  bool escaped_{false}, overflow_{false};
};
// Values are pinned to ESP-IDF 5.5.5 / its OpenThread Spinel 4.3, API 11/min4.
// This is only a read-only readiness check; the real stack still checks all caps.
template<typename Query> ThreadFault probe_rcp(Query query, uint32_t required_radio_caps) {
  std::array<uint8_t, 128> data{};
  size_t size = 0, at = 0;
  uint32_t first = 0, second = 0;
  if (!query(1, data.data(), data.size(), size)) return ThreadFault::SILENT_RCP;
  if (!packed_read(data.data(), size, at, first) || !packed_read(data.data(), size, at, second) ||
      at != size || first != 4 || second != 3) return ThreadFault::PROTOCOL;
  if (!query(5, data.data(), data.size(), size)) return ThreadFault::SILENT_RCP;
  at = 0;
  bool radio = false, raw = false, api = false, min_api = false;
  while (at < size) {
    if (!packed_read(data.data(), size, at, first)) return ThreadFault::CAPABILITIES;
    radio |= first == 34; raw |= first == 513; api |= first == 64; min_api |= first == 65;
  }
  if (!radio || !raw) return ThreadFault::CAPABILITIES;
  if (api) {
    if (!query(0xb0, data.data(), data.size(), size)) return ThreadFault::SILENT_RCP;
    at = 0;
    if (!packed_read(data.data(), size, at, first) || at != size || first < 4) return ThreadFault::API_VERSION;
  }
  if (min_api) {
    if (!query(0xb1, data.data(), data.size(), size)) return ThreadFault::SILENT_RCP;
    at = 0;
    if (!packed_read(data.data(), size, at, first) || at != size || first > 11) return ThreadFault::API_VERSION;
  }
  if (!query(0x120b, data.data(), data.size(), size)) return ThreadFault::SILENT_RCP;
  at = 0;
  if (!packed_read(data.data(), size, at, first) || at != size ||
      (first & required_radio_caps) != required_radio_caps) return ThreadFault::CAPABILITIES;
  return ThreadFault::NONE;
}
}  // namespace esphome::low_power_otbr
