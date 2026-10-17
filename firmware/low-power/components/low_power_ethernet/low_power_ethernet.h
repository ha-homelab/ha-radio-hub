#pragma once
#include "esphome/core/component.h"
namespace esphome::low_power_ethernet {
class LowPowerEthernet : public Component {
 public:
  void setup() override;
  // Immediately after ESPHome installs and starts the Ethernet driver.
  float get_setup_priority() const override { return setup_priority::ETHERNET - 1.0f; }
};
}
