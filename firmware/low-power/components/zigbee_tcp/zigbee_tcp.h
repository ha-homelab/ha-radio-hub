#pragma once
#include "esphome/core/component.h"
#include <atomic>

namespace esphome::zigbee_tcp {
class ZigbeeTCP : public Component {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
  void set_pins(int tx, int rx, int rts, int cts) { tx_ = tx; rx_ = rx; rts_ = rts; cts_ = cts; }
  void set_port(uint16_t port) { port_ = port; }
 protected:
  static void worker(void *arg);
  void run_();
  bool configure_uart_();
  int tx_{-1}, rx_{-1}, rts_{-1}, cts_{-1};
  uint16_t port_{6638};
  bool launched_{false};
  std::atomic<bool> failed_{false};
};
}
