#pragma once
#include "esphome/core/component.h"
#include "thread_guard.h"
#include <atomic>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "nvs.h"

namespace esphome::low_power_otbr {
class LowPowerOTBR : public Component {
 public:
  void setup() override;
  void loop() override;
  void on_shutdown() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
  void set_pins(int tx, int rx, int reset, int boot) { tx_ = tx; rx_ = rx; reset_ = reset; boot_ = boot; }
  void retry();
  void pause_for_service();
  const char *status() const;
  const char *fault() const { return fault_name(static_cast<ThreadFault>(fault_.load())); }
  bool quarantined() const { return quarantined_.load(); }
  bool guard_durable() const { return durable_.load(); }
  uint32_t fault_count() const { return faults_.load(); }
  uint32_t retry_count() const { return retries_.load(); }
  uint32_t reset_count() const { return resets_.load(); }
  uint32_t role() const { return role_.load(); }
 protected:
  static LowPowerOTBR *instance_;
  static void launch_task(void *arg);
  static void reset_rcp();
  static void reset_failed();
  static void incompatible();
  static void state_changed(uint32_t flags, void *context);
  void launch_();
  ThreadFault preflight_();
  void reset_radio_();
  bool save_locked_();
  void publish_locked_();
  void quarantine_(ThreadFault fault);
  [[noreturn]] void terminal_(ThreadFault fault);
  int tx_{-1}, rx_{-1}, reset_{-1}, boot_{-1};
  bool launched_{false}, storage_ready_{false};
  std::atomic<uint32_t> start_ms_{0};
  nvs_handle_t storage_{0};
  SemaphoreHandle_t guard_mutex_{nullptr};
  ThreadGuard guard_{};
  std::atomic<bool> quarantined_{false}, terminal_started_{false}, online_{false}, durable_{false};
  std::atomic<uint32_t> phase_{0}, fault_{0}, faults_{0}, retries_{0}, resets_{0}, role_{0};
};
}
