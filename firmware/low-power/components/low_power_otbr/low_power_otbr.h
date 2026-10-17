#pragma once

#include "esphome/core/component.h"
#include <atomic>

namespace esphome::low_power_otbr {
class LowPowerOTBR : public Component {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
  void set_pins(int tx, int rx, int reset, int boot) { tx_ = tx; rx_ = rx; reset_ = reset; boot_ = boot; }
 protected:
  static void launch_task(void *arg);
  void launch_();
  int tx_{-1}, rx_{-1}, reset_{-1}, boot_{-1};
  bool launched_{false};
  std::atomic<int> state_{0};
};
}
