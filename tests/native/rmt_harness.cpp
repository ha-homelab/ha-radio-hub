#include "rmt_stubs.h"
#include <cassert>
#include <iostream>
// Access instrumentation state, without changing the production implementation.
#define protected public
#include "remote_receiver_rmt.cpp"
#undef protected

int main(int argc, char **argv) {
  assert(argc == 2);
  const std::string scenario = argv[1];
  using namespace esphome;
  InternalGPIOPin pin;
  remote_receiver::RemoteReceiverComponent receiver(&pin);
  receiver.suspend();
  receiver.resume();
  assert(test_rmt::creates == 0 && test_rmt::receives == 0);
  receiver.set_buffer_size(2048);
  receiver.set_receive_symbols(64);
  receiver.set_filter_us(150);
  receiver.set_idle_us(4000);
  receiver.setup();
  assert(!receiver.is_failed());
  auto *const buffer = receiver.store_.buffer;
  auto *const context = test_rmt::channel.context;
  auto emit_fresh = [&]() {
    // Simulate a completed DMA-free RMT receive into the armed caller buffer.
    auto *symbols = static_cast<rmt_symbol_word_t *>(test_rmt::channel.buffer);
    symbols[0] = {240, 1, 720, 0};
    symbols[1] = {720, 1, 240, 0};
    rmt_rx_done_event_data_t event{symbols, 2};
    test_rmt::channel.callback(&test_rmt::channel, &event, context);
  };

  if (scenario == "flush") {
    emit_fresh();
    assert(receiver.store_.buffer_read != receiver.store_.buffer_write);
    receiver.store_.overflow = true;
    receiver.suspend();
    const auto receives = test_rmt::receives;
    receiver.loop();
    assert(receiver.delivered.empty());
    test_rmt::callback_stale();
    assert(test_rmt::receives == receives); // Suspended ISR cannot re-arm capture.
    receiver.resume();
    receiver.loop();
    assert(receiver.delivered.empty()); // Pre-TX ring is never replayed.
    assert(!receiver.store_.overflow);
    emit_fresh();
    receiver.loop();
    assert(receiver.delivered.size() == 1);
    assert((receiver.delivered[0] == std::vector<int32_t>{240, -720, 720, -240, 4000}));
  } else if (scenario == "pending_isr") {
    const auto receives = test_rmt::receives;
    test_rmt::pending_during_disable = true;
    receiver.suspend();
    assert(test_rmt::receives == receives);
    receiver.resume();
    assert(test_rmt::receives == receives + 1);
    receiver.loop();
    assert(receiver.delivered.empty());
  } else if (scenario == "idempotent") {
    const auto setup_receives = test_rmt::receives;
    for (int i = 0; i < 1000; ++i) {
      receiver.suspend(); receiver.suspend();
      assert(!test_rmt::channel.enabled && receiver.store_.suspended);
      receiver.resume(); receiver.resume();
      assert(test_rmt::channel.enabled && receiver.enabled);
      assert(receiver.store_.buffer == buffer && test_rmt::channel.context == context);
    }
    assert(test_rmt::creates == 1 && test_rmt::registers == 1);
    assert(test_rmt::disables == 1000 && test_rmt::enables == 1001);
    assert(test_rmt::receives == setup_receives + 1000);
    emit_fresh(); receiver.loop();
    assert(receiver.delivered.size() == 1);
  } else if (scenario == "listener_flush") {
    emit_fresh(); emit_fresh();
    unsigned triggered = 0;
    receiver.on_delivery = [&]() {
      if (triggered++ == 0) {
        assert(receiver.suspend());
        assert(receiver.resume());
      }
    };
    receiver.loop();
    assert(receiver.delivered.size() == 1);
    // The second pre-TX event was discarded and no stale write snapshot ran.
    emit_fresh(); receiver.loop();
    assert(receiver.delivered.size() == 2);
  } else if (scenario == "enable_error") {
    receiver.suspend();
    const auto receives = test_rmt::receives;
    test_rmt::next_enable_error = ESP_FAIL;
    receiver.resume();
    assert(receiver.is_failed() && !receiver.enabled);
    assert(test_rmt::receives == receives);
  } else if (scenario == "receive_error") {
    receiver.suspend();
    test_rmt::next_receive_error = ESP_FAIL;
    receiver.resume();
    assert(receiver.is_failed() && !receiver.enabled);
  } else if (scenario == "disable_error") {
    test_rmt::next_disable_error = ESP_FAIL;
    receiver.suspend();
    assert(receiver.is_failed() && !receiver.enabled);
  } else {
    assert(false);
  }
  assert(critical_depth == 0);
  delete[] buffer;
}
