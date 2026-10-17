// Linked to the actual installed ESPHome RCSwitch implementation and exact
// RemoteReceiveData methods, plus the production RF Airbridge Receiver.
#include "esphome/core/hal.h"
#define millis() esphome::millis()
#include "rf_receiver.h"
#include <cassert>
#include <iostream>
struct Sink {
  bool is_connected() const { return true; }
  bool publish(const char *topic, const char *payload, size_t length, uint8_t qos, bool retain) {
    assert(std::string(topic) == "rf/received" && qos == 0 && !retain);
    std::cout << std::string(payload, length) << '\n';
    return true;
  }
};
int main() {
  esphome::remote_base::RawTimings timings;
  int32_t value;
  while (std::cin >> value) timings.push_back(value);
  rf_bridge::Receiver receiver;
  Sink sink;
  receiver.on_receive(timings, sink);
}
