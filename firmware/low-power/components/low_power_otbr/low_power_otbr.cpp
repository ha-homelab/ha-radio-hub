#include "low_power_otbr.h"
#include "esphome/components/ethernet/ethernet_component.h"
#include "esphome/core/log.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_openthread.h"
#include "esp_openthread_border_router.h"
#include "esp_openthread_lock.h"
#include "esp_openthread_netif_glue.h"
#include "esp_vfs_eventfd.h"
#include "openthread/dataset_ftd.h"
#include "openthread/thread.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
extern "C" {
#include "esp_br_web.h"
void esp_br_web_start_immediate(char *base_path);
}

namespace esphome::low_power_otbr {
static const char *const TAG = "low_power_otbr";

void LowPowerOTBR::setup() {
  // Ethernet, mDNS, NVS and the default event loop belong to ESPHome.
  // Do not initialize them again or replace ESPHome's hostname/default netif.
  ESP_LOGI(TAG, "Waiting for Ethernet before starting the Thread border router");
}

void LowPowerOTBR::loop() {
  if (!launched_ && ethernet::global_eth_component->is_connected()) {
    launched_ = true;
    if (xTaskCreate(launch_task, "otbr_start", 6144, this, 4, nullptr) != pdPASS) {
      ESP_LOGE(TAG, "Cannot allocate OTBR initialization task");
      mark_failed();
    }
  }
  const int state = state_.exchange(0);
  if (state < 0) {
    ESP_LOGE(TAG, "OTBR initialization failed; other ESPHome services remain available");
    mark_failed();
  } else if (state > 0) {
    ESP_LOGI(TAG, "Thread border router REST API ready on port %d", LOW_POWER_OTBR_REST_PORT);
  }
}

void LowPowerOTBR::launch_task(void *arg) {
  static_cast<LowPowerOTBR *>(arg)->launch_();
  vTaskDelete(nullptr);
}

void LowPowerOTBR::launch_() {
  auto fail = [this](const char *step, esp_err_t err) {
    ESP_LOGE(TAG, "%s failed: %s", step, esp_err_to_name(err));
    state_ = -1;
  };
  if (uart_is_driver_installed(UART_NUM_2)) {
    fail("UART2 already owned", ESP_ERR_INVALID_STATE);
    return;
  }
  // H2 is separately flashed; this component never updates its firmware.
  // Open-drain control shares safely with service buttons/programmer reset.
  // Both nets require the external 10k pull-ups specified in the hardware map.
  gpio_set_level(static_cast<gpio_num_t>(boot_), 1);
  gpio_set_direction(static_cast<gpio_num_t>(boot_), GPIO_MODE_OUTPUT_OD);
  gpio_set_level(static_cast<gpio_num_t>(reset_), 0);
  gpio_set_direction(static_cast<gpio_num_t>(reset_), GPIO_MODE_OUTPUT_OD);
  vTaskDelay(pdMS_TO_TICKS(10));
  gpio_set_level(static_cast<gpio_num_t>(reset_), 1);
  vTaskDelay(pdMS_TO_TICKS(100));

  const esp_vfs_eventfd_config_t eventfd = {.max_fds = 3};
  esp_err_t err = esp_vfs_eventfd_register(&eventfd);
  if (err != ESP_OK) { fail("eventfd registration", err); return; }
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
  err = esp_openthread_start(&config);
  if (err != ESP_OK) { fail("OpenThread start", err); return; }
  esp_openthread_lock_acquire(portMAX_DELAY);
  esp_openthread_set_backbone_netif(ethernet::global_eth_component->get_esp_netif());
  err = esp_openthread_border_router_init();
  if (err == ESP_OK) {
    otOperationalDatasetTlvs dataset{};
    if (otDatasetGetActiveTlvs(esp_openthread_get_instance(), &dataset) == OT_ERROR_NONE) {
      err = esp_openthread_auto_start(&dataset);
    } else {
      // Never join a fixed demonstration network or invent a household dataset.
      // Home Assistant imports/creates the network through the REST API.
      ESP_LOGI(TAG, "No stored Thread dataset; awaiting configuration through REST");
    }
  }
  esp_openthread_lock_release();
  if (err != ESP_OK) { fail("Border router initialization", err); return; }
  static char rest_path[] = "/otbr";
  esp_br_web_start_immediate(rest_path);
  if (!esp_br_web_is_server_started()) { fail("REST server", ESP_FAIL); return; }
  state_ = 1;
}

void LowPowerOTBR::dump_config() {
  ESP_LOGCONFIG(TAG, "Thread BR: H2 RCP UART2 460800; REST TCP %d", LOW_POWER_OTBR_REST_PORT);
}
}
