// Runs the production bridge and RM433 decoder. Only the stock RCSwitch
// decoder, clock, entropy and MQTT transport are doubles. This is intentionally
// a serialization/delivery-policy test, not a test of ESPHome's RF decoder.
#include "esphome/core/hal.h"
#define millis() esphome::millis()
#include "rf_receiver.h"
#include "rf_tx_validation.h"
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

using rf_bridge::ReceiveResult;
using esphome::remote_base::RawTimings;
static const uint32_t CODES[8] = {
  0x123451, 0x123452, 0x123454, 0x123458,
  0x123453, 0x123456, 0x12345c, 0x123459
};
static void native(uint32_t code) {
  const char *type = rf_bridge::rm433_button_type(code, CODES);
  std::cout << "NATIVE " << code << ' ' << (type ? type : "unmapped") << '\n';
}
struct Sink {
  bool connected = true;
  bool success = true;
  bool is_connected() { return connected; }
  bool publish(const char *topic, const char *payload, size_t size, uint8_t qos, bool retain) {
    std::cout << "MQTT " << unsigned(qos) << ' ' << retain << ' ' << topic << ' '
              << std::string(payload, size) << '\n';
    return success;
  }
};
static const char *result_name(ReceiveResult r) {
  switch (r) {
#define CASE(name) case ReceiveResult::name: return #name;
    CASE(SUPPRESSED) CASE(REPEAT_SUPPRESSED) CASE(OFFLINE)
    CASE(INVALID_CONFIGURATION) CASE(UNDECODED) CASE(RAW_RATE_LIMITED)
    CASE(RAW_OUT_OF_BOUNDS) CASE(PAYLOAD_TOO_LARGE) CASE(PUBLISH_FAILED)
    CASE(DECODED_PUBLISHED) CASE(RAW_PUBLISHED)
#undef CASE
  }
  return "UNKNOWN";
}
int main() {
  rf_bridge::Receiver receiver;
  Sink sink;
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream input(line);
    std::string command;
    input >> command;
    if (command == "receive") {
      unsigned learning, suppress, callback, bits, mask;
      uint64_t value;
      input >> esphome::test_now >> sink.connected >> sink.success
            >> learning >> suppress >> callback >> bits >> value >> mask;
      if (!input) return 2;
      esphome::remote_base::injected_bits = bits;
      esphome::remote_base::injected_value = value;
      esphome::remote_base::matching_protocols = mask;
      RawTimings timings;
      int32_t duration;
      while (input >> duration) timings.push_back(duration);
      const auto r = receiver.on_receive(timings, sink, learning, suppress, callback ? native : nullptr);
      std::cout << "RESULT " << result_name(r) << '\n';
    } else if (command == "rc") {
      int protocol, repeats;
      input >> protocol >> repeats;
      std::string hex;
      input >> hex;
      std::string code;
      if (hex != "-") {
        for (size_t i = 0; i < hex.size(); i += 2)
          code.push_back(static_cast<char>(std::stoul(hex.substr(i, 2), nullptr, 16)));
      }
      std::cout << "VALID " << rf_bridge::valid_tx_request(code, protocol, repeats) << '\n';
    } else if (command == "dooya") {
      int remote, channel, button, check, repeats;
      input >> remote >> channel >> button >> check >> repeats;
      std::cout << "VALID " << rf_bridge::valid_dooya_request(remote, channel, button, check, repeats) << '\n';
    } else if (command == "decode") {
      RawTimings timings;
      int32_t duration;
      while (input >> duration) timings.push_back(duration);
      uint32_t code = 0xdeadbeef, pulse = 123;
      const bool valid = rf_bridge::decode_rm433_24(timings, code, pulse);
      std::cout << "DECODE " << valid << ' ' << code << ' ' << pulse << '\n';
    } else {
      return 3;
    }
  }
}
