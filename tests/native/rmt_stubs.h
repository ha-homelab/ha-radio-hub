#pragma once
// Narrow ESP-IDF/ESPHome doubles. The production RMT driver is compiled intact.
// They expose lifecycle calls and allow a pending ISR to run during disable.
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <cassert>
#include <functional>
#include <string>
#include <vector>
#define IRAM_ATTR
#define HOT
#define SOC_RMT_SUPPORTED 1
struct portMUX_TYPE { int depth = 0; };
#define portMUX_INITIALIZER_UNLOCKED {}
inline unsigned critical_depth = 0;
inline void portENTER_CRITICAL(portMUX_TYPE *lock) { assert(lock->depth++ == 0); ++critical_depth; }
inline void portEXIT_CRITICAL(portMUX_TYPE *lock) { assert(--lock->depth == 0); --critical_depth; }
inline void portENTER_CRITICAL_ISR(portMUX_TYPE *lock) { portENTER_CRITICAL(lock); }
inline void portEXIT_CRITICAL_ISR(portMUX_TYPE *lock) { portEXIT_CRITICAL(lock); }
using esp_err_t = int;
inline constexpr esp_err_t ESP_OK = 0, ESP_FAIL = -1, ESP_ERR_NOT_FOUND = 1,
                          ESP_ERR_INVALID_STATE = 2;
using gpio_num_t = int;
using soc_module_clk_t = int;
inline constexpr int RMT_CLK_SRC_DEFAULT = 1, ESP_CLK_TREE_SRC_FREQ_PRECISION_CACHED = 1;
struct rmt_symbol_word_t {
  uint32_t duration0 : 15;
  uint32_t level0 : 1;
  uint32_t duration1 : 15;
  uint32_t level1 : 1;
};
struct rmt_rx_done_event_data_t { rmt_symbol_word_t *received_symbols; size_t num_symbols; };
struct rmt_receive_config_t { uint32_t signal_range_min_ns, signal_range_max_ns; };
struct rmt_rx_channel_config_t {
  int clk_src;
  uint32_t resolution_hz;
  size_t mem_block_symbols;
  gpio_num_t gpio_num;
  int intr_priority;
  struct { unsigned invert_in, with_dma; } flags;
};
struct rmt_carrier_config_t {
  uint32_t frequency_hz;
  float duty_cycle;
  struct { bool polarity_active_low; } flags;
};
struct TestRmtChannel;
using rmt_channel_handle_t = TestRmtChannel *;
using ReceiveCallback = bool (*)(rmt_channel_handle_t, const rmt_rx_done_event_data_t *, void *);
struct rmt_rx_event_callbacks_t { ReceiveCallback on_recv_done; };
struct TestRmtChannel {
  bool enabled = false;
  void *buffer = nullptr;
  size_t buffer_size = 0;
  void *context = nullptr;
  ReceiveCallback callback = nullptr;
};
namespace test_rmt {
inline TestRmtChannel channel;
inline unsigned creates = 0, enables = 0, disables = 0, receives = 0, registers = 0;
inline bool pending_during_disable = false;
inline esp_err_t next_enable_error = ESP_OK, next_disable_error = ESP_OK, next_receive_error = ESP_OK;
inline std::vector<std::string> calls;
inline rmt_symbol_word_t stale_symbols[] = {{500, 1, 1500, 0}, {1500, 1, 500, 0}};
inline rmt_rx_done_event_data_t stale_event{stale_symbols, 2};
inline void callback_stale() {
  channel.callback(&channel, &stale_event, channel.context);
}
inline esp_err_t take_error(esp_err_t &error) { auto value = error; error = ESP_OK; return value; }
}
inline esp_err_t rmt_new_rx_channel(const rmt_rx_channel_config_t *, rmt_channel_handle_t *out) {
  ++test_rmt::creates;
  *out = &test_rmt::channel;
  return ESP_OK;
}
inline esp_err_t rmt_enable(rmt_channel_handle_t channel) {
  assert(critical_depth == 0);
  ++test_rmt::enables;
  test_rmt::calls.push_back("enable");
  if (const auto error = test_rmt::take_error(test_rmt::next_enable_error)) return error;
  if (channel->enabled) return ESP_ERR_INVALID_STATE;
  channel->enabled = true;
  return ESP_OK;
}
inline esp_err_t rmt_disable(rmt_channel_handle_t channel) {
  assert(critical_depth == 0);
  ++test_rmt::disables;
  test_rmt::calls.push_back("disable");
  if (const auto error = test_rmt::take_error(test_rmt::next_disable_error)) return error;
  if (!channel->enabled) return ESP_ERR_INVALID_STATE;
  if (test_rmt::pending_during_disable) test_rmt::callback_stale();
  channel->enabled = false;
  return ESP_OK;
}
inline esp_err_t rmt_receive(rmt_channel_handle_t channel, void *buffer, size_t size,
                             const rmt_receive_config_t *) {
  ++test_rmt::receives;
  test_rmt::calls.push_back("receive");
  if (const auto error = test_rmt::take_error(test_rmt::next_receive_error)) return error;
  if (!channel->enabled) return ESP_ERR_INVALID_STATE;
  channel->buffer = buffer;
  channel->buffer_size = size;
  return ESP_OK;
}
inline esp_err_t rmt_rx_register_event_callbacks(rmt_channel_handle_t channel,
                                                const rmt_rx_event_callbacks_t *callbacks, void *context) {
  ++test_rmt::registers;
  channel->callback = callbacks->on_recv_done;
  channel->context = context;
  return ESP_OK;
}
inline esp_err_t rmt_apply_carrier(rmt_channel_handle_t, const rmt_carrier_config_t *) { return ESP_OK; }
inline void gpio_pullup_en(gpio_num_t) {}
inline void gpio_pullup_dis(gpio_num_t) {}
inline const char *esp_err_to_name(esp_err_t) { return "test-error"; }
inline esp_err_t esp_clk_tree_src_get_freq_hz(soc_module_clk_t, int, uint32_t *frequency) {
  *frequency = 80000000;
  return ESP_OK;
}
namespace esphome {
namespace gpio { enum Flags { FLAG_INPUT = 1, FLAG_PULLUP = 2 }; }
class InternalGPIOPin {
 public:
  int get_pin() { return 5; }
  int get_flags() { return gpio::FLAG_INPUT; }
  bool is_inverted() { return false; }
};
class Component {
 public:
  bool enabled = true;
  bool failed = false;
  virtual ~Component() = default;
  virtual void setup() {}
  virtual void dump_config() {}
  virtual void loop() {}
  void disable_loop() { enabled = false; }
  void enable_loop() { enabled = true; }
  void mark_failed() { failed = true; enabled = false; }
  bool is_failed() const { return failed; }
};
namespace remote_base {
enum { TOLERANCE_MODE_PERCENTAGE, TOLERANCE_MODE_TIME };
class RemoteRMTChannel {
 protected:
  uint32_t clock_resolution_ = 1000000, rmt_symbols_ = 64;
  uint32_t from_microseconds_(uint32_t value) { return value; }
  uint32_t to_microseconds_(uint32_t value) { return value; }
};
class RemoteReceiverBase {
 public:
  explicit RemoteReceiverBase(InternalGPIOPin *pin) : pin_(pin) {}
  std::vector<std::vector<int32_t>> delivered;
  std::function<void()> on_delivery;
 protected:
  void call_listeners_dumpers_() {
    delivered.push_back(temp_);
    if (on_delivery) on_delivery();
  }
  InternalGPIOPin *pin_;
  std::vector<int32_t> temp_;
  uint32_t tolerance_ = 30;
  int tolerance_mode_ = TOLERANCE_MODE_PERCENTAGE;
};
}
}
