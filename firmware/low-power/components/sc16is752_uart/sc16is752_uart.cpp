#include "sc16is752_uart.h"
#include "esphome/core/log.h"
#include "esp_attr.h"

namespace esphome::sc16is752_uart {
static const char *const TAG="sc16is752_uart";
uint8_t SC16IS752UART::read(uint8_t reg) {
  this->enable(); this->transfer_byte(command(reg,true));
  const uint8_t value=this->transfer_byte(0); this->disable(); return value;
}
void SC16IS752UART::write(uint8_t reg,uint8_t value) {
  this->enable(); this->transfer_byte(command(reg,false)); this->transfer_byte(value); this->disable();
}
void SC16IS752UART::setup() {
  this->spi_setup();
  if (!initialize(*this,crystal_,this->baud_rate_)) {
    ESP_LOGE(TAG,"Register check/configuration failed"); this->mark_failed(); return;
  }
  rx_=xQueueCreate(2048,sizeof(uint8_t)); tx_=xQueueCreate(2048,sizeof(uint8_t));
  if (!rx_ || !tx_) {
    if (rx_) vQueueDelete(rx_);
    if (tx_) vQueueDelete(tx_);
    rx_=tx_=nullptr;
    this->mark_failed(); return;
  }
  interrupt_pin_->setup();
  // The worker owns this SPI device; ESP-IDF serializes it against other devices
  // on the shared hardware SPI bus (CC1101 has a different device/CS).
  ready_.store(true);
  if (xTaskCreate(task_,"sc16_uart",4096,this,2,&task_handle_)!=pdPASS) {
    ready_.store(false);
    vQueueDelete(rx_); vQueueDelete(tx_); rx_=tx_=nullptr;
    this->mark_failed(); return;
  }
  interrupt_pin_->attach_interrupt(irq_,this,gpio::INTERRUPT_FALLING_EDGE);
  xTaskNotifyGive(task_handle_);
}
void IRAM_ATTR SC16IS752UART::irq_(SC16IS752UART *self) {
  BaseType_t wake=pdFALSE;
  vTaskNotifyGiveFromISR(self->task_handle_,&wake);
  if (wake) portYIELD_FROM_ISR();
}
void SC16IS752UART::task_(void *arg) { static_cast<SC16IS752UART *>(arg)->worker_(); }
void SC16IS752UART::worker_() {
  uint32_t last_check=millis();
  for (;;) {
    if (fault_.load()) {
      // Keep task alive: an IRQ can still refer to its handle until reboot.
      vTaskDelay(pdMS_TO_TICKS(100)); continue;
    }
    const uint32_t generation=tx_generation_.load();
    const bool ok=service(*this,
      [this](uint8_t v) { return xQueueSend(rx_,&v,0)==pdTRUE; },
      [this](uint8_t &v) { return xQueueReceive(tx_,&v,0)==pdTRUE; });
    if (!ok) { fault_.store(true); continue; }
    if (millis()-last_check>=1000) {
      if (read(SPR)!=0xa5) { fault_.store(true); continue; }
      last_check=millis();
    }
    // LSR reads clear sticky error bits: an idle check must not swallow a
    // receive error that arrived after service() drained the previous batch.
    const uint8_t line_status=read(LSR);
    if (line_status&0x9e) { fault_.store(true); continue; }
    const bool idle=uxQueueMessagesWaiting(tx_)==0 && (line_status&0x40);
    tx_idle_.store(idle);
    if (idle) completed_generation_.store(generation);
    if (read(RXLVL)>0) continue;
    // IRQ wakes promptly on RX; timed polling also detects disconnected hardware.
    ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(idle?20:1));
  }
}
void SC16IS752UART::loop() {
  if (fault_.load() && !this->is_failed()) {
    ESP_LOGE(TAG,"UART stream lost (FIFO/line/queue/register fault); reboot required");
    this->mark_failed();
  }
}
void SC16IS752UART::write_array(const uint8_t *data,size_t len) {
  if (!len || !is_connected()) return;
  // Single producer: the ESPHome main/API loop. Do not enqueue a partial frame.
  if (len>uxQueueSpacesAvailable(tx_)) { fault_.store(true); return; }
  tx_idle_.store(false);
  for (size_t i=0;i<len;++i) {
    if (xQueueSend(tx_,data+i,0)!=pdTRUE) { fault_.store(true); return; }
  }
  tx_generation_.fetch_add(1);
  xTaskNotifyGive(task_handle_);
}
size_t SC16IS752UART::available() { return is_connected()?uxQueueMessagesWaiting(rx_):0; }
bool SC16IS752UART::peek_byte(uint8_t *value) { return is_connected() && xQueuePeek(rx_,value,0)==pdTRUE; }
bool SC16IS752UART::read_array(uint8_t *data,size_t len) {
  if (!is_connected() || available()<len) return false;
  for (size_t i=0;i<len;++i) if (xQueueReceive(rx_,data+i,0)!=pdTRUE) return false;
  return true;
}
uart::UARTFlushResult SC16IS752UART::flush() {
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
void SC16IS752UART::load_settings(bool dump) {
  if (this->baud_rate_!=115200 || this->data_bits_!=8 || this->stop_bits_!=1 ||
      this->parity_!=uart::UART_CONFIG_PARITY_NONE) fault_.store(true);
  if (dump) dump_config();
}
void SC16IS752UART::dump_config() {
  ESP_LOGCONFIG(TAG,"SC16IS752 channel A: 115200 8N1; crystal %u Hz",unsigned(crystal_));
  LOG_SPI_DEVICE(this);
  LOG_PIN("  IRQ: ",interrupt_pin_);
}
}  // namespace esphome::sc16is752_uart
