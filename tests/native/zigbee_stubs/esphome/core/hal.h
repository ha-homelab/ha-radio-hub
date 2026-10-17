#pragma once
#include <atomic>
#include <cstdint>
namespace esphome {
extern std::atomic<uint32_t> test_now;
inline uint32_t millis() { return test_now.load(); }
}
