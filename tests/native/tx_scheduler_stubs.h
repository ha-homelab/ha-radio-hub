#pragma once
// Deterministic host scheduler seam: production YAML lambdas compile unchanged.
// RF encoding and ESPHome scheduling internals are covered by firmware compile,
// not simulated here. Delay/wait/single-worker ordering is driven by fake time.
#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <string>
#include <utility>
#include <vector>
#include "rf_tx_validation.h"

inline uint64_t now_ms = 0;
inline bool rf_tx_active = false, rf_tx_complete = false, rf_tx_error = false, rf_tx_fault = false;
inline bool worker_running = false, waiting = false, cooldown = false, tx_pending = false;
inline uint64_t wait_deadline = 0, ready_at = 0, tx_due = 0, next_tx_delay = 1000;
inline unsigned tx_count = 0;
inline std::vector<std::string> trace;
inline void record(const char *text) { trace.push_back(text); }
struct Radio {
  bool failed = false;
  bool is_failed() const { return failed; }
  void set_idle() { record("radio.idle"); }
  void begin_tx() { record("radio.tx"); }
  void begin_rx() { record("radio.rx"); }
};
struct Transmitter {
  bool failed = false, warning = false;
  bool is_failed() const { return failed; }
  bool status_has_warning() const { return warning; }
  void digital_write(bool high) { record(high ? "pin.release" : "pin.low"); }
};
struct Receiver {
  bool enabled = true, fail_suspend = false, fail_resume = false;
  bool suspend() { record("receiver.suspend"); enabled = false; return !fail_suspend; }
  bool resume() { record("receiver.resume"); enabled = !fail_resume; return !fail_resume; }
};
inline Radio rf_radio;
inline Transmitter rf_transmitter;
inline Receiver rf_receiver;
#define id(name) name
inline std::string quote(const std::string &value) {
  std::string result = "\"";
  for (char c : value) {
    if (c == '\\' || c == '"') result += '\\';
    result += c;
  }
  return result + "\"";
}
struct Json {
  std::map<std::string, std::string> fields;
  struct Slot {
    Json &json;
    std::string key;
    void operator=(const std::string &value) { json.fields[key] = quote(value); }
    void operator=(const char *value) { json.fields[key] = quote(value); }
    void operator=(int value) { json.fields[key] = std::to_string(value); }
    void operator=(bool value) { json.fields[key] = value ? "true" : "false"; }
  };
  Slot operator[](const char *key) { return {*this, key}; }
  std::string str() const {
    std::string result = "{";
    for (const auto &entry : fields) {
      if (result.size() > 1) result += ',';
      result += quote(entry.first) + ':' + entry.second;
    }
    return result + '}';
  }
};
inline std::vector<Json> messages;
inline void publish(const char *topic, int qos, bool retain, const Json &root) {
  assert(qos == 0 && !retain);
  messages.push_back(root);
  std::cout << "MQTT " << now_ms << ' ' << topic << ' ' << root.str() << '\n';
}
namespace esphome::remote_base { inline int RC_SWITCH_PROTOCOLS[9] = {0, 1, 2, 3, 4, 5, 6, 7, 8}; }
inline std::vector<std::string> encoded_requests;
inline void capture_rc(const std::string &code, int protocol, int repeats) {
  encoded_requests.push_back("rc:" + code + ":" + std::to_string(protocol) + ":" + std::to_string(repeats));
}
inline void capture_dooya(int remote, int channel, int button, int check, int repeats) {
  encoded_requests.push_back("dooya:" + std::to_string(remote) + ":" + std::to_string(channel) +
                            ":" + std::to_string(button) + ":" + std::to_string(check) + ":" + std::to_string(repeats));
}
