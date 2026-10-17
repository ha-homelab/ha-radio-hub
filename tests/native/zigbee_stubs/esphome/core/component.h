#pragma once
#include <cstdint>
namespace esphome {
namespace setup_priority { constexpr float AFTER_WIFI = 200.0f; }
class Component {
 public:
  virtual ~Component() = default;
  virtual void setup() {}
  virtual void loop() {}
  virtual void dump_config() {}
  virtual float get_setup_priority() const { return 0; }
  void mark_failed() { component_failed_ = true; }
  bool is_failed() const { return component_failed_; }
 private:
  bool component_failed_{false};
};
}
