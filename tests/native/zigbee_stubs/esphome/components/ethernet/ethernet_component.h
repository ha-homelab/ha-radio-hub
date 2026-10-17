#pragma once
namespace esphome::ethernet {
class EthernetComponent {
 public:
  bool is_connected() const { return true; }
};
inline EthernetComponent test_ethernet;
inline EthernetComponent *global_eth_component = &test_ethernet;
}
