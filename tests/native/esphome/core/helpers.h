#pragma once
#include <cstdint>
namespace esphome {
// Repeatable diagnostic boot ID; not a source of test RF codes.
inline uint32_t test_random = 0x01234567;
inline uint32_t random_uint32() {
  const auto result = test_random;
  test_random = 0x89abcdef;
  return result;
}
}
