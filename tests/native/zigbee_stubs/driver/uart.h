#pragma once
#include <cstddef>
#include <cstdint>
#include "freertos/FreeRTOS.h"
using esp_err_t = int;
using uart_port_t = int;
constexpr int ESP_OK = 0, ESP_FAIL = -1, ESP_ERR_TIMEOUT = 0x107;
constexpr int UART_NUM_1 = 1, UART_DATA_8_BITS = 3, UART_PARITY_DISABLE = 0;
constexpr int UART_STOP_BITS_1 = 1, UART_HW_FLOWCTRL_CTS_RTS = 3, UART_SCLK_DEFAULT = 1;
struct uart_config_t {
  int baud_rate{}, data_bits{}, parity{}, stop_bits{}, flow_ctrl{};
  uint8_t rx_flow_ctrl_thresh{};
  int source_clk{};
};
bool uart_is_driver_installed(uart_port_t);
esp_err_t uart_param_config(uart_port_t, const uart_config_t *);
esp_err_t uart_set_pin(uart_port_t, int, int, int, int);
esp_err_t uart_driver_install(uart_port_t, int, int, int, void *, int);
esp_err_t uart_driver_delete(uart_port_t);
esp_err_t uart_flush_input(uart_port_t);
esp_err_t uart_wait_tx_done(uart_port_t, TickType_t);
int uart_tx_chars(uart_port_t, const char *, uint32_t);
int uart_read_bytes(uart_port_t, void *, uint32_t, TickType_t);
