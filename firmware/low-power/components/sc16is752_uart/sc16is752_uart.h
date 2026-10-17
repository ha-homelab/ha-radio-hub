#pragma once
#include <atomic>
#include "esphome/core/component.h"
#include "esphome/core/hal.h"
#include "esphome/components/spi/spi.h"
#include "esphome/components/uart/uart_component.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "registers.h"

namespace esphome::sc16is752_uart {
class SC16IS752UART : public Component, public uart::UARTComponent,
    public spi::SPIDevice<spi::BIT_ORDER_MSB_FIRST, spi::CLOCK_POLARITY_LOW,
                         spi::CLOCK_PHASE_LEADING, spi::DATA_RATE_4MHZ> {
 public:
  void set_interrupt_pin(InternalGPIOPin *pin) { interrupt_pin_=pin; }
  void set_crystal_frequency(uint32_t hz) { crystal_=hz; }
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::BUS - 1; }
  void write_array(const uint8_t *data, size_t len) override;
  bool peek_byte(uint8_t *value) override;
  bool read_array(uint8_t *data, size_t len) override;
  size_t available() override;
  uart::UARTFlushResult flush() override;
  bool is_connected() override { return ready_.load() && !fault_.load(); }
  void load_settings(bool dump_config) override;
  void set_flush_timeout(uint32_t ms) override { flush_ms_=ms ? ms : 1000; }

  // Core IO adapter, accessed by setup and subsequently ONLY by worker_.
  uint8_t read(uint8_t reg);
  void write(uint8_t reg,uint8_t value);
  void pause() { delay(1); }
 protected:
  void check_logger_conflict() override {}  // external SPI UART, never the console
  static void irq_(SC16IS752UART *self);
  static void task_(void *arg);
  void worker_();
  InternalGPIOPin *interrupt_pin_{nullptr};
  uint32_t crystal_{3686400}, flush_ms_{1000};
  QueueHandle_t rx_{nullptr}, tx_{nullptr};
  TaskHandle_t task_handle_{nullptr};
  std::atomic<bool> ready_{false}, fault_{false}, tx_idle_{true};
  std::atomic<uint32_t> tx_generation_{0}, completed_generation_{0};
};
}  // namespace esphome::sc16is752_uart
