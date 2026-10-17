#include "low_power_ethernet.h"
#include "esphome/components/ethernet/ethernet_component.h"
#include "esphome/core/log.h"
#include "esp_eth.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
namespace esphome::low_power_ethernet {
void LowPowerEthernet::setup() {
  static const char *const TAG = "low_power_ethernet";
  auto *eth = ethernet::global_eth_component;
  auto handle = eth->get_eth_handle();
  if (eth->is_failed() || handle == nullptr) { mark_failed(); return; }
  esp_err_t err = esp_eth_stop(handle);
  bool automatic = false;
  if (err == ESP_OK) err = esp_eth_ioctl(handle, ETH_CMD_S_AUTONEGO, &automatic);
  // W5500 register map = offset << 16 | block << 3; common block is zero.
  // Set the complete mode atomically: OPMD=1, OPMDC=000 => 10BASE-T half
  // duplex without autonegotiation. A partner using parallel detection will
  // also choose half duplex. Do not force full duplex against an auto peer.
  // Using separate speed/duplex ioctls can read stale link-status bits.
  uint32_t value = 0;
  esp_eth_phy_reg_rw_data_t reg{0x002EUL << 16, &value};
  if (err == ESP_OK) err = esp_eth_ioctl(handle, ETH_CMD_READ_PHY_REG, &reg);
  if (err == ESP_OK) {
    value = (value & 0x07U) | 0x40U;  // mode 000, PHY reset asserted (active low)
    err = esp_eth_ioctl(handle, ETH_CMD_WRITE_PHY_REG, &reg);
  }
  if (err == ESP_OK) {
    vTaskDelay(pdMS_TO_TICKS(10));
    value |= 0x80U;
    err = esp_eth_ioctl(handle, ETH_CMD_WRITE_PHY_REG, &reg);
  }
  if (err == ESP_OK) {
    err = esp_eth_ioctl(handle, ETH_CMD_READ_PHY_REG, &reg);
    if (err == ESP_OK && (value & 0xF8U) != 0xC0U) err = ESP_FAIL;
  }
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "Cannot set W5500 PHY policy: %s; Ethernet stays stopped", esp_err_to_name(err));
    mark_failed();
    return;
  }
  err = esp_eth_start(handle);
  if (err != ESP_OK) { mark_failed(); return; }
  ESP_LOGI(TAG, "W5500 PHY configured: 10 Mbit/s half duplex (SPI clock independent)");
}
}
