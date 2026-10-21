#pragma once
#include <cstdint>
#define RF_TX_STARTUP_PIN 25
#define ESP_IDF_VERSION_VAL(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define ESP_IDF_VERSION ESP_IDF_VERSION_VAL(5,5,5)
using esp_err_t = int;
using gpio_num_t = int;
using rmt_channel_handle_t = void *;
constexpr int ESP_OK = 0, ESP_ERR_INVALID_ARG = 1;
struct rmt_tx_channel_config_t {
  gpio_num_t gpio_num{};
  uint32_t resolution_hz{};
  struct { unsigned io_od_mode:1; unsigned invert_out:1; unsigned init_level:1; } flags{};
};
esp_err_t gpio_set_level(gpio_num_t, uint32_t);
esp_err_t gpio_od_enable(gpio_num_t);
