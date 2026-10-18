#include "low_power_otbr.h"
#include "rcp_probe.h"
#include "esphome/components/ethernet/ethernet_component.h"
#include "esphome/core/application.h"
#include "esphome/core/log.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_attr.h"
#include "esp_system.h"
#include "esp_openthread.h"
#include "esp_openthread_border_router.h"
#include "esp_openthread_lock.h"
#include "esp_openthread_netif_glue.h"
#include "esp_openthread_spinel.h"
#include "esp_vfs_eventfd.h"
#include "openthread/dataset_ftd.h"
#include "openthread/thread.h"
#include "freertos/task.h"
#include <cstring>
extern "C" {
#include "esp_br_web.h"
void esp_br_web_start_immediate(char *base_path);
}

namespace esphome::low_power_otbr {
static const char *const TAG = "low_power_otbr";
// Secondary retention if a flash write fails during a terminal callback. Normal
// operation uses NVS; RTC alone is not claimed to survive complete power removal.
RTC_NOINIT_ATTR static uint32_t retained_words[8];
static_assert(sizeof(ThreadRecord) == 6 * sizeof(uint32_t), "RTC guard record layout changed");
static void retain_fault(const ThreadRecord &record) {
  retained_words[6] = 0;
  std::memcpy(retained_words, &record, sizeof(record));
  uint32_t check = 0xa14e930d;
  for (size_t i = 0; i < 6; ++i) check = (check << 5 | check >> 27) ^ retained_words[i];
  retained_words[7] = check;
  std::atomic_thread_fence(std::memory_order_seq_cst);
  retained_words[6] = 0x52435032;
}
static void clear_retained() { retained_words[6] = 0; }
static bool read_retained(ThreadRecord &record) {
  if (retained_words[6] != 0x52435032) return false;
  uint32_t check = 0xa14e930d;
  for (size_t i = 0; i < 6; ++i) check = (check << 5 | check >> 27) ^ retained_words[i];
  if (retained_words[7] != check) return false;
  std::memcpy(&record, retained_words, sizeof(record));
  return valid_record(record) && record.quarantined;
}
LowPowerOTBR *LowPowerOTBR::instance_ = nullptr;

void LowPowerOTBR::publish_locked_() {
  quarantined_ = guard_.record.quarantined;
  fault_ = guard_.record.fault;
  faults_ = guard_.record.faults;
  retries_ = guard_.record.retries;
}
bool LowPowerOTBR::save_locked_() {
  if (!storage_ready_) { durable_ = false; return false; }
  const bool saved = write_verified_record(guard_.record,
    [&](const ThreadRecord &record) { return nvs_set_blob(storage_, "guard", &record, sizeof(record)) == ESP_OK; },
    [&]() { return nvs_commit(storage_) == ESP_OK; },
    [&](ThreadRecord &record) {
      size_t size = sizeof(record);
      return nvs_get_blob(storage_, "guard", &record, &size) == ESP_OK && size == sizeof(record);
    });
  durable_ = saved;
  return saved;
}
void LowPowerOTBR::setup() {
  instance_ = this;
  guard_mutex_ = xSemaphoreCreateMutex();
  ThreadRecord record{};
  storage_ready_ = guard_mutex_ != nullptr && nvs_open("hub_thread", NVS_READWRITE, &storage_) == ESP_OK;
  if (storage_ready_) {
    size_t size = sizeof(record);
    const auto err = nvs_get_blob(storage_, "guard", &record, &size);
    if (err == ESP_ERR_NVS_NOT_FOUND) record = {};
    else if (err != ESP_OK || size != sizeof(record) || !valid_record(record)) storage_ready_ = false;
  }
  const auto reason = esp_reset_reason();
  const bool abnormal = reason == ESP_RST_PANIC || reason == ESP_RST_INT_WDT ||
                        reason == ESP_RST_TASK_WDT || reason == ESP_RST_WDT || reason == ESP_RST_CPU_LOCKUP;
  bool changed = guard_.restore(record, abnormal);
  ThreadRecord retained{};
  if (reason != ESP_RST_POWERON && reason != ESP_RST_BROWNOUT && read_retained(retained)) {
    guard_.record = retained;
    changed = true;
  }
  if (!storage_ready_) { guard_.quarantine(ThreadFault::STORAGE); changed = true; }
  durable_ = storage_ready_;
  if (changed) {
    retain_fault(guard_.record);
    if (save_locked_()) clear_retained();
    else if (!guard_.record.quarantined) {
      // Do not continue with an old durable armed marker if clearing it failed.
      guard_.quarantine(ThreadFault::STORAGE);
      retain_fault(guard_.record);
    }
  }
  publish_locked_();
  ESP_LOGI(TAG, "Thread guard: %s; fault=%s, faults=%u, retries=%u", status(), fault(),
           static_cast<unsigned>(fault_count()), static_cast<unsigned>(retry_count()));
}
const char *LowPowerOTBR::status() const {
  if (quarantined_) return fault_.load() == static_cast<uint32_t>(ThreadFault::MAINTENANCE) ? "maintenance" : "quarantined";
  switch (phase_.load()) {
    case 0: return "waiting_for_ethernet";
    case 1: return "checking_rcp";
    case 2: return "starting_stack";
    case 3: return online_ ? (role_.load() == 0 ? "ready_uncommissioned_or_disabled" :
                            role_.load() == 1 ? "ready_detached" : "routing") : "backbone_disconnected";
    default: return "unavailable";
  }
}
void LowPowerOTBR::loop() {
  online_ = ethernet::global_eth_component->is_connected();
  if (!launched_ && !quarantined_ && storage_ready_ && online_) {
    launched_ = true;
    phase_ = 1;
    start_ms_ = millis();
    if (xTaskCreate(launch_task, "otbr_start", 6144, this, 4, nullptr) != pdPASS)
      quarantine_(ThreadFault::STACK_ERROR);
  }
  // Preflight is <=5 property requests x1s. The stack has its own deadline.
  // Never kill an OT task while it may hold locks or serve REST requests.
  if (!quarantined_ && phase_ == 2 && millis() - start_ms_.load() > 20000)
    terminal_(ThreadFault::START_TIMEOUT);
}
void LowPowerOTBR::on_shutdown() {
  if (!guard_mutex_ || terminal_started_) return;
  xSemaphoreTake(guard_mutex_, portMAX_DELAY);
  guard_.normal_shutdown();
  save_locked_();
  xSemaphoreGive(guard_mutex_);
}
void LowPowerOTBR::retry() {
  if (update_phase_ != 0) { ESP_LOGW(TAG, "Cancel UART update before retrying Thread"); return; }
  if (!quarantined_ || !storage_ready_ || !guard_mutex_) {
    ESP_LOGW(TAG, "Retry ignored: Thread is not quarantined or guard storage is unavailable");
    return;
  }
  xSemaphoreTake(guard_mutex_, portMAX_DELAY);
  const bool saved = guard_.retry_if_durable([&]() { return save_locked_(); });
  if (saved) clear_retained();
  publish_locked_();
  xSemaphoreGive(guard_mutex_);
  if (saved) { ESP_LOGW(TAG, "Explicit Thread retry: restarting hub once"); App.safe_reboot(); }
  else ESP_LOGE(TAG, "Retry refused: guard could not be durably cleared");
}
void LowPowerOTBR::pause_for_service() {
  if (!storage_ready_ || !guard_mutex_) {
    ESP_LOGE(TAG, "Cannot establish durable maintenance pause: guard storage unavailable");
    return;
  }
  if (quarantined_ && fault_ == static_cast<uint32_t>(ThreadFault::MAINTENANCE)) return;
  // Elective maintenance requires durable storage; unlike emergency fault
  // containment it must not silently rely on RTC-only retention.
  xSemaphoreTake(guard_mutex_, portMAX_DELAY);
  const bool saved = guard_.pause_if_durable([&]() { return save_locked_(); });
  if (saved) clear_retained();
  publish_locked_();
  xSemaphoreGive(guard_mutex_);
  if (!saved) { ESP_LOGE(TAG, "Maintenance pause refused: guard write could not be verified"); return; }
  terminal_started_ = true;
  ESP_LOGW(TAG, "Durable maintenance pause saved; restarting hub once before RCP service");
  esp_restart();
}
void LowPowerOTBR::quarantine_(ThreadFault fault) {
  if (!guard_mutex_) { quarantined_ = true; fault_ = static_cast<uint32_t>(ThreadFault::STORAGE); return; }
  xSemaphoreTake(guard_mutex_, portMAX_DELAY);
  guard_.quarantine(fault);
  retain_fault(guard_.record);
  const bool saved = save_locked_();
  if (saved) clear_retained();
  publish_locked_();
  xSemaphoreGive(guard_mutex_);
  ESP_LOGE(TAG, "Thread quarantined: %s; durable=%s. Other services remain configured.", this->fault(), saved ? "yes" : "no");
}
[[noreturn]] void LowPowerOTBR::terminal_(ThreadFault fault) {
  if (!terminal_started_.exchange(true)) {
    quarantine_(fault);
    ESP_LOGW(TAG, "Thread stop (%s): restarting the entire hub once; Thread remains paused", this->fault());
    esp_restart();
  }
  while (true) vTaskDelay(pdMS_TO_TICKS(1000));
}
void LowPowerOTBR::launch_task(void *arg) {
  static_cast<LowPowerOTBR *>(arg)->launch_();
  vTaskDelete(nullptr);
}
void LowPowerOTBR::reset_radio_() {
  // BOOT and EN are released open-drain; onboard RCP service remains possible.
  gpio_set_level(static_cast<gpio_num_t>(boot_), 1);
  gpio_set_direction(static_cast<gpio_num_t>(boot_), GPIO_MODE_OUTPUT_OD);
  gpio_set_level(static_cast<gpio_num_t>(reset_), 0);
  gpio_set_direction(static_cast<gpio_num_t>(reset_), GPIO_MODE_OUTPUT_OD);
  vTaskDelay(pdMS_TO_TICKS(10));
  gpio_set_level(static_cast<gpio_num_t>(reset_), 1);
  vTaskDelay(pdMS_TO_TICKS(100));
  ++resets_;
}
void LowPowerOTBR::reset_rcp() { instance_->reset_radio_(); }
void LowPowerOTBR::reset_failed() { instance_->terminal_(ThreadFault::RESET_FAILED); }
void LowPowerOTBR::incompatible() { instance_->terminal_(ThreadFault::INCOMPATIBLE); }
void LowPowerOTBR::state_changed(uint32_t, void *context) {
  static_cast<LowPowerOTBR *>(context)->role_ = otThreadGetDeviceRole(esp_openthread_get_instance());
}
ThreadFault LowPowerOTBR::preflight_() {
  if (uart_is_driver_installed(UART_NUM_2)) return ThreadFault::UART;
  uart_config_t config{};
  config.baud_rate = 460800;
  config.data_bits = UART_DATA_8_BITS;
  config.parity = UART_PARITY_DISABLE;
  config.stop_bits = UART_STOP_BITS_1;
  config.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
  config.source_clk = UART_SCLK_DEFAULT;
  if (uart_param_config(UART_NUM_2, &config) != ESP_OK ||
      uart_set_pin(UART_NUM_2, tx_, rx_, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE) != ESP_OK ||
      uart_driver_install(UART_NUM_2, 1024, 0, 0, nullptr, 0) != ESP_OK) return ThreadFault::UART;
  reset_radio_();
  auto query = [&](uint32_t property, uint8_t *data, size_t capacity, size_t &size) {
    uint8_t request[8]{0x81, 2}; // IID0, TID1, PROP_VALUE_GET; never writes a dataset.
    const size_t count = 2 + packed_write(property, request + 2);
    uint8_t wire[24]{};
    const size_t bytes = encode_hdlc(request, count, wire, sizeof(wire));
    uart_flush_input(UART_NUM_2);
    if (uart_write_bytes(UART_NUM_2, wire, bytes) != static_cast<int>(bytes)) return false;
    HdlcReceiver decoder;
    const TickType_t start = xTaskGetTickCount();
    bool resent = false;
    while (xTaskGetTickCount() - start < pdMS_TO_TICKS(1000)) {
      // A still-booting RCP can miss the first query. One resend stays inside
      // the original deadline and never sends configuration-changing commands.
      if (!resent && xTaskGetTickCount() - start > pdMS_TO_TICKS(500)) {
        if (uart_write_bytes(UART_NUM_2, wire, bytes) != static_cast<int>(bytes)) return false;
        resent = true;
      }
      uint8_t received[64];
      const int n = uart_read_bytes(UART_NUM_2, received, sizeof(received), pdMS_TO_TICKS(20));
      for (int i = 0; i < n; ++i) {
        const size_t length = decoder.push(received[i]);
        if (length < 3 || decoder.frame[0] != 0x81) continue;
        size_t at = 1;
        uint32_t command = 0, response_property = 0;
        if (!packed_read(decoder.frame.data(), length, at, command) || command != 6 ||
            !packed_read(decoder.frame.data(), length, at, response_property) || response_property != property) continue;
        size = length - at;
        if (size > capacity) return false;
        std::memcpy(data, decoder.frame.data() + at, size);
        return true;
      }
    }
    return false;
  };
  uint32_t caps = 0xff;
#if CONFIG_OPENTHREAD_RX_ON_WHEN_IDLE
  caps |= 0x100;
#endif
  const ThreadFault result = probe_rcp(query, caps);
  if (uart_driver_delete(UART_NUM_2) != ESP_OK) return ThreadFault::UART;
  return result;
}
void LowPowerOTBR::launch_() {
  const ThreadFault probe = preflight_();
  if (probe != ThreadFault::NONE) { quarantine_(probe); return; }
  xSemaphoreTake(guard_mutex_, portMAX_DELAY);
  guard_.arm();
  const bool armed = save_locked_();
  xSemaphoreGive(guard_mutex_);
  if (!armed) { quarantine_(ThreadFault::STORAGE); return; }
  // These callbacks never return into SDK DieNow. Other SDK aborts are caught
  // by the persisted armed flag + abnormal reset reason on the next boot.
  esp_openthread_set_coprocessor_reset_failure_callback(reset_failed);
  esp_openthread_set_compatibility_error_callback(incompatible);
  esp_openthread_register_rcp_failure_handler(reset_rcp);
  start_ms_ = millis();
  phase_ = 2;
  const esp_vfs_eventfd_config_t eventfd = {.max_fds = 3};
  if (esp_vfs_eventfd_register(&eventfd) != ESP_OK) terminal_(ThreadFault::STACK_ERROR);
  esp_openthread_config_t config{};
  config.netif_config = ESP_NETIF_DEFAULT_OPENTHREAD();
  config.platform_config.radio_config.radio_mode = RADIO_MODE_UART_RCP;
  auto &radio = config.platform_config.radio_config.radio_uart_config;
  radio.port = UART_NUM_2;
  radio.uart_config.baud_rate = 460800;
  radio.uart_config.data_bits = UART_DATA_8_BITS;
  radio.uart_config.parity = UART_PARITY_DISABLE;
  radio.uart_config.stop_bits = UART_STOP_BITS_1;
  radio.uart_config.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
  radio.uart_config.source_clk = UART_SCLK_DEFAULT;
  radio.tx_pin = static_cast<gpio_num_t>(tx_);
  radio.rx_pin = static_cast<gpio_num_t>(rx_);
  config.platform_config.host_config.host_connection_mode = HOST_CONNECTION_MODE_NONE;
  config.platform_config.port_config.storage_partition_name = "nvs";
  config.platform_config.port_config.netif_queue_size = 10;
  config.platform_config.port_config.task_queue_size = 10;
  if (esp_openthread_start(&config) != ESP_OK) terminal_(ThreadFault::STACK_ERROR);
  esp_openthread_lock_acquire(portMAX_DELAY);
  esp_openthread_set_backbone_netif(ethernet::global_eth_component->get_esp_netif());
  esp_err_t err = esp_openthread_border_router_init();
  if (err == ESP_OK) {
    if (otSetStateChangedCallback(esp_openthread_get_instance(), state_changed, this) != OT_ERROR_NONE)
      ESP_LOGW(TAG, "Thread role telemetry callback could not be registered");
    otOperationalDatasetTlvs dataset{};
    if (otDatasetGetActiveTlvs(esp_openthread_get_instance(), &dataset) == OT_ERROR_NONE)
      err = esp_openthread_auto_start(&dataset);
    else ESP_LOGI(TAG, "No stored Thread dataset; awaiting configuration through REST");
    role_ = otThreadGetDeviceRole(esp_openthread_get_instance());
  }
  esp_openthread_lock_release();
  if (err != ESP_OK) terminal_(ThreadFault::STACK_ERROR);
  static char rest_path[] = "/otbr";
  esp_br_web_start_immediate(rest_path);
  if (!esp_br_web_is_server_started()) terminal_(ThreadFault::STACK_ERROR);
  phase_ = 3;
  ESP_LOGI(TAG, "Thread REST ready on port %d", LOW_POWER_OTBR_REST_PORT);
}
void LowPowerOTBR::dump_config() {
  ESP_LOGCONFIG(TAG, "Thread BR: RCP UART2 460800, REST %d, status %s, fault %s", LOW_POWER_OTBR_REST_PORT, status(), fault());
}
}
