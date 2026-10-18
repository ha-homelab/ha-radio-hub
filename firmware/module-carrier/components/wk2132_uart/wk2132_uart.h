#pragma once
#include <atomic>
#include "esphome/core/component.h"
#include "esphome/core/helpers.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/uart/uart_component.h"
#include "transport.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

namespace esphome::wk2132_uart {
class WK2132UART : public Component, public uart::UARTComponent, public i2c::I2CDevice {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::BUS-1; }
  void write_array(const uint8_t *data, size_t len) override;
  bool peek_byte(uint8_t *value) override;
  bool read_array(uint8_t *data, size_t len) override;
  size_t available() override;
  uart::UARTFlushResult flush() override;
  bool is_connected() override { return ready_.load() && fault_.load()==Fault::NONE; }
  void load_settings(bool dump_config) override;
  void set_flush_timeout(uint32_t ms) override { flush_ms_=ms ? ms : 1000; }
  bool reg_read(uint8_t reg, uint8_t &value) { return read_register(reg,&value,1)==i2c::ERROR_OK; }
  bool reg_write(uint8_t reg, uint8_t value) { return write_register(reg,&value,1)==i2c::ERROR_OK; }
  bool fifo_read(uint8_t *data, size_t len) {
    return bus_->write_readv(address_|1,nullptr,0,data,len)==i2c::ERROR_OK;
  }
  bool fifo_write(const uint8_t *data, size_t len) {
    return bus_->write_readv(address_|1,data,len,nullptr,0)==i2c::ERROR_OK;
  }
  void pause() { delay(1); }
 protected:
  void check_logger_conflict() override {}
  void report_fault_();
  static void task_(void *arg);
  void worker_();
  // Only setup and then the worker access this staging core and the I2C device.
  BasicTransport<256> transport_;
  QueueHandle_t rx_{nullptr}, tx_{nullptr};
  TaskHandle_t task_handle_{nullptr};
  uint32_t flush_ms_{1000};
  std::atomic<bool> ready_{false};
  std::atomic<Fault> fault_{Fault::NONE};
  std::atomic<uint32_t> tx_generation_{0}, completed_generation_{0};
};
}  // namespace esphome::wk2132_uart
