/*
 * Seeed Studio XIAO ESP32C6: GPIO3 LOW powers the RF switch, GPIO14 HIGH
 * selects U.FL. GPIO3 is not the host's GPIO3 (USB-UART).
 * https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#hardware-overview
 * Readback checks GPIO logic, not antenna attachment or RF performance.
 */
#include "xiaoc6_antenna.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

esp_err_t xiaoc6_select_external_antenna(void)
{
    /* Preload the switch disabled and its path external before enabling outputs. */
    esp_err_t error = gpio_set_level(GPIO_NUM_3, 1);
    if (error != ESP_OK)
        return error;
    error = gpio_set_level(GPIO_NUM_14, 1);
    if (error != ESP_OK)
        return error;
    const gpio_config_t config = {
        .pin_bit_mask = (1ULL << GPIO_NUM_3) | (1ULL << GPIO_NUM_14),
        .mode = GPIO_MODE_INPUT_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    error = gpio_config(&config);
    if (error != ESP_OK)
        return error;
    error = gpio_set_level(GPIO_NUM_3, 0);
    if (error != ESP_OK)
        return error;
    /* Manufacturer example gives the powered selector 100 ms to settle. */
    vTaskDelay(pdMS_TO_TICKS(100));
    if (gpio_get_level(GPIO_NUM_3) != 0 || gpio_get_level(GPIO_NUM_14) != 1)
        return ESP_ERR_INVALID_STATE;
    return ESP_OK;
}
