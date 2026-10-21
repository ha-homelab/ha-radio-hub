#include "wk2132_uart.h"
#include "esphome/core/hal.h"
#include "esphome/core/log.h"

namespace esphome::wk2132_uart {
static const char *const TAG="wk2132_uart";
void WK2132UART::setup() {
  load_settings(false);
  if (fault_.load()!=Fault::NONE) { report_fault_(); return; }
  if (!transport_.initialize(*this)) {
    fault_.store(transport_.fault()); report_fault_(); return;
  }
  rx_=xQueueCreate(2048,sizeof(uint8_t));
  tx_=xQueueCreate(2048,sizeof(uint8_t));
  if (!rx_ || !tx_) {
    if (rx_) vQueueDelete(rx_);
    if (tx_) vQueueDelete(tx_);
    rx_=tx_=nullptr;
    mark_failed(); return;
  }
  ready_.store(true);
  if (xTaskCreate(task_,"wk2132_uart",4096,this,2,&task_handle_)!=pdPASS) {
    ready_.store(false);
    vQueueDelete(rx_); vQueueDelete(tx_); rx_=tx_=nullptr;
    mark_failed();
  }
}
void WK2132UART::task_(void *arg) { static_cast<WK2132UART *>(arg)->worker_(); }
void WK2132UART::worker_() {
  uint32_t last_health=millis();
  for (;;) {
    if (fault_.load()!=Fault::NONE) { vTaskDelay(pdMS_TO_TICKS(100)); continue; }
    const uint32_t generation=tx_generation_.load();
    uint8_t data[256];
    size_t n=0;
    const size_t limit=std::min(transport_.tx_free(),sizeof(data));
    while (n<limit && xQueueReceive(tx_,data+n,0)==pdTRUE) ++n;
    if (n) transport_.enqueue(data,n);
    transport_.service(*this);
    if (transport_.good() && millis()-last_health>=500) {
      transport_.health(*this);
      last_health=millis();
    }
    while (transport_.good() && (n=std::min(transport_.available(),sizeof(data)))) {
      if (n>uxQueueSpacesAvailable(rx_)) { transport_.fail(Fault::RX_OVERFLOW); break; }
      transport_.receive(data,n);
      for (size_t i=0;i<n;++i) {
        if (xQueueSend(rx_,data+i,0)!=pdTRUE) { transport_.fail(Fault::RX_OVERFLOW); break; }
      }
    }
    if (!transport_.good()) { fault_.store(transport_.fault()); continue; }
    if (transport_.idle() && uxQueueMessagesWaiting(tx_)==0)
      completed_generation_.store(generation);
    // TX enqueue wakes immediately; RX has a dedicated two-ms poll, independent
    // of ESPHome's application loop. IDF serializes individual I2C transactions
    // using its bus semaphore; BME uses the same bus but a different address.
    ulTaskNotifyTake(pdTRUE,std::max(TickType_t(1),pdMS_TO_TICKS(2)));
  }
}
void WK2132UART::loop() { report_fault_(); }
void WK2132UART::report_fault_() {
  if (fault_.load()==Fault::NONE || is_failed()) return;
  ESP_LOGE(TAG,"UART stream invalid, fault=%u; reconnect requires device restart",unsigned(fault_.load()));
  mark_failed();
}
void WK2132UART::write_array(const uint8_t *data, size_t len) {
  if (!len || !is_connected()) return;
  // Single producer: the ESPHome API/main loop; worker only removes TX bytes.
  if (len>uxQueueSpacesAvailable(tx_)) { fault_.store(Fault::TX_OVERFLOW); return; }
  for (size_t i=0;i<len;++i)
    if (xQueueSend(tx_,data+i,0)!=pdTRUE) { fault_.store(Fault::TX_OVERFLOW); return; }
  tx_generation_.fetch_add(1);
  xTaskNotifyGive(task_handle_);
}
size_t WK2132UART::available() { return is_connected()?uxQueueMessagesWaiting(rx_):0; }
bool WK2132UART::peek_byte(uint8_t *value) {
  return is_connected() && xQueuePeek(rx_,value,0)==pdTRUE;
}
bool WK2132UART::read_array(uint8_t *data,size_t len) {
  if (!is_connected() || available()<len) return false;
  for (size_t i=0;i<len;++i) if (xQueueReceive(rx_,data+i,0)!=pdTRUE) return false;
  return true;
}
uart::UARTFlushResult WK2132UART::flush() {
  const uint32_t start=millis();
  const uint32_t generation=tx_generation_.load();
  while (is_connected()) {
    if (uxQueueMessagesWaiting(tx_)==0 && completed_generation_.load()==generation)
      return uart::UARTFlushResult::UART_FLUSH_RESULT_SUCCESS;
    if (millis()-start>=flush_ms_) return uart::UARTFlushResult::UART_FLUSH_RESULT_TIMEOUT;
    vTaskDelay(1);
  }
  return uart::UARTFlushResult::UART_FLUSH_RESULT_FAILED;
}
void WK2132UART::load_settings(bool dump) {
  if (baud_rate_!=115200 || data_bits_!=8 || stop_bits_!=1 || parity_!=uart::UART_CONFIG_PARITY_NONE)
    fault_.store(Fault::SETTINGS);
  if (dump) dump_config();
}
void WK2132UART::dump_config() {
  ESP_LOGCONFIG(TAG,"DFR0627 UART1: 115200 8N1, register0x%02X/FIFO0x%02X, dedicated 2ms worker",
                this->address_, this->address_ | 1);
  ESP_LOGCONFIG(TAG,"  2048-byte queues, 64-byte checked transfers; no silent truncation/replay");
  ESP_LOGCONFIG(TAG,"  Scheduler latency and concurrent radio traffic require hardware qualification");
}
}  // namespace esphome::wk2132_uart
