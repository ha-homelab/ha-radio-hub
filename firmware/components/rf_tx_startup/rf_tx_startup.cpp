// Copyright (c) 2026 HA Radio Hub contributors. SPDX-License-Identifier: MIT
#include "esphome/core/defines.h"
#include "driver/gpio.h"
#include "esp_private/gpio.h"
#include "driver/rmt_tx.h"
#include "esp_idf_version.h"

#if ESP_IDF_VERSION != ESP_IDF_VERSION_VAL(5, 5, 5)
#error "Review RF RMT startup ordering before changing ESP-IDF"
#endif

extern "C" esp_err_t __real_rmt_new_tx_channel(const rmt_tx_channel_config_t *, rmt_channel_handle_t *);

extern "C" esp_err_t __wrap_rmt_new_tx_channel(const rmt_tx_channel_config_t *config,
                                             rmt_channel_handle_t *channel) {
  // Other RMT consumers retain exactly their upstream configuration.
  if (config == nullptr || config->gpio_num != RF_TX_STARTUP_PIN)
    return __real_rmt_new_tx_channel(config, channel);
  if (channel == nullptr || !config->flags.io_od_mode || config->flags.invert_out)
    return ESP_ERR_INVALID_ARG;

  // IDF 5.5.5 routes/enables its initial RMT level before setting io_od_mode.
  // Preload a released GPIO latch without enabling the pad, then establish OD.
  // This prevents both a LOW sink and a brief push-pull HIGH on CC1101 GDO0,
  // which is an output (including its power-on clock) until RF enters TX.
  esp_err_t error = gpio_set_level(config->gpio_num, 1);
  if (error != ESP_OK)
    return error;
  error = gpio_od_enable(config->gpio_num);
  if (error != ESP_OK)
    return error;
  rmt_tx_channel_config_t released = *config;
  released.flags.init_level = 1;
  return __real_rmt_new_tx_channel(&released, channel);
}
