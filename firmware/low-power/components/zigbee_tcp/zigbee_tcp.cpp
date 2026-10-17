#include "zigbee_tcp.h"
#include "esphome/components/ethernet/ethernet_component.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lwip/sockets.h"
#include <algorithm>
#include <array>
#include <cerrno>
#include <cstring>
#include <fcntl.h>

namespace esphome::zigbee_tcp {
static const char *const TAG = "zigbee_tcp";
static constexpr uart_port_t PORT = UART_NUM_1;

void ZigbeeTCP::setup() {
  // UART0 is reserved for ESPHome's sole native UART (LD2450); UART2 for H2.
  if (uart_is_driver_installed(PORT) || !configure_uart_()) mark_failed();
}

bool ZigbeeTCP::configure_uart_() {
  uart_config_t config{};
  config.baud_rate = 115200;
  config.data_bits = UART_DATA_8_BITS;
  config.parity = UART_PARITY_DISABLE;
  config.stop_bits = UART_STOP_BITS_1;
  config.flow_ctrl = UART_HW_FLOWCTRL_CTS_RTS;
  config.rx_flow_ctrl_thresh = 96;
  config.source_clk = UART_SCLK_DEFAULT;
  return uart_param_config(PORT, &config) == ESP_OK &&
         uart_set_pin(PORT, tx_, rx_, rts_, cts_) == ESP_OK &&
         uart_driver_install(PORT, 4096, 0, 0, nullptr, 0) == ESP_OK;
}

void ZigbeeTCP::loop() {
  if (failed_) { mark_failed(); return; }
  if (!launched_ && ethernet::global_eth_component->is_connected()) {
    launched_ = true;
    if (xTaskCreate(worker, "zigbee_tcp", 6144, this, 3, nullptr) != pdPASS) mark_failed();
  }
}

void ZigbeeTCP::worker(void *arg) {
  static_cast<ZigbeeTCP *>(arg)->run_();
  static_cast<ZigbeeTCP *>(arg)->failed_ = true;
  vTaskDelete(nullptr);
}

void ZigbeeTCP::run_() {
  int server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  if (server < 0) return;
  int enabled = 1;
  setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &enabled, sizeof(enabled));
  sockaddr_in bind_address{};
  bind_address.sin_family = AF_INET;
  bind_address.sin_addr.s_addr = htonl(INADDR_ANY);
  bind_address.sin_port = htons(port_);
  if (bind(server, reinterpret_cast<sockaddr *>(&bind_address), sizeof(bind_address)) != 0 ||
      listen(server, 1) != 0 || fcntl(server, F_SETFL, O_NONBLOCK) != 0) {
    close(server); return;
  }
  int client = -1;
  std::array<uint8_t, 2048> network_out{};
  std::array<uint8_t, 512> serial_out{};
  size_t network_size = 0, network_offset = 0, serial_size = 0, serial_offset = 0;
  uint32_t last_tx_progress = millis();
  auto disconnect = [&]() {
    if (client >= 0) { shutdown(client, SHUT_RDWR); close(client); }
    client = -1;
    network_size = network_offset = serial_size = serial_offset = 0;
    // RX-only flush is insufficient: bytes can remain in the hardware TX FIFO
    // indefinitely while CTS is deasserted. A fresh driver resets BOTH FIFOs before
    // any new TCP session is accepted. No blocking wait on the previous peer.
    if (uart_driver_delete(PORT) != ESP_OK || !configure_uart_()) failed_ = true;
    last_tx_progress = millis();
  };
  auto retryable = []() { return errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR; };
  ESP_LOGI(TAG, "Zigbee NCP bridge listening on TCP %u; exactly one client", port_);
  while (!failed_.load()) {
    fd_set read_set, write_set;
    FD_ZERO(&read_set); FD_ZERO(&write_set);
    FD_SET(server, &read_set);
    int max_fd = server;
    if (client >= 0) {
      max_fd = std::max(server, client);
      if (serial_offset == serial_size) FD_SET(client, &read_set);
      if (network_offset < network_size) FD_SET(client, &write_set);
    }
    timeval timeout{0, 10000};
    int result = select(max_fd + 1, &read_set, &write_set, nullptr, &timeout);
    if (result < 0 && errno != EINTR) { disconnect(); break; }
    if (result > 0 && FD_ISSET(server, &read_set)) {
      int accepted = accept(server, nullptr, nullptr);
      if (accepted >= 0) {
        if (client >= 0 || fcntl(accepted, F_SETFL, O_NONBLOCK) != 0) {
          close(accepted);
        } else {
          uart_flush_input(PORT);
          client = accepted;
          last_tx_progress = millis();
          setsockopt(client, IPPROTO_TCP, TCP_NODELAY, &enabled, sizeof(enabled));
          setsockopt(client, SOL_SOCKET, SO_KEEPALIVE, &enabled, sizeof(enabled));
          // A physically vanished idle peer must not occupy the only slot for
          // lwIP's default multi-hour keepalive interval. Healthy idle peers
          // answer probes and remain connected indefinitely.
          int idle_seconds = 30, interval_seconds = 10, probe_count = 3;
          setsockopt(client, IPPROTO_TCP, TCP_KEEPIDLE, &idle_seconds, sizeof(idle_seconds));
          setsockopt(client, IPPROTO_TCP, TCP_KEEPINTVL, &interval_seconds, sizeof(interval_seconds));
          setsockopt(client, IPPROTO_TCP, TCP_KEEPCNT, &probe_count, sizeof(probe_count));
        }
      }
    }
    if (client < 0) {
      // No consumer: do not retain previous sessions' serial bytes indefinitely.
      uart_flush_input(PORT);
      continue;
    }
    if (result > 0 && FD_ISSET(client, &read_set)) {
      int received = recv(client, serial_out.data(), serial_out.size(), 0);
      if (received > 0) { serial_size = received; serial_offset = 0; }
      else if (received == 0 || !retryable()) { disconnect(); continue; }
    }
    if (serial_offset < serial_size) {
      // Never block on a deasserted NCP CTS: preserve unsent bytes and backpressure TCP.
      int written = uart_tx_chars(PORT, reinterpret_cast<const char *>(serial_out.data() + serial_offset),
                                  serial_size - serial_offset);
      if (written > 0) { serial_offset += written; last_tx_progress = millis(); }
      else if (written < 0) { disconnect(); continue; }
    }
    // Even when a full serial buffer applies TCP backpressure, release a dead
    // or permanently CTS-blocked session. Polling is bounded and never drains
    // old bytes after another session begins.
    const esp_err_t tx_state = uart_wait_tx_done(PORT, 0);
    if (tx_state != ESP_OK && tx_state != ESP_ERR_TIMEOUT) { disconnect(); continue; }
    if (serial_offset == serial_size && tx_state == ESP_OK) last_tx_progress = millis();
    else if (uint32_t(millis() - last_tx_progress) >= 5000) { disconnect(); continue; }
    if (network_offset == network_size) {
      int received = uart_read_bytes(PORT, network_out.data(), network_out.size(), 0);
      if (received > 0) { network_size = received; network_offset = 0; }
    }
    if (network_offset < network_size) {
      int written = send(client, network_out.data() + network_offset, network_size - network_offset, 0);
      if (written > 0) network_offset += written;
      else if (written == 0 || !retryable()) { disconnect(); continue; }
    }
  }
  close(server);
}

void ZigbeeTCP::dump_config() {
  ESP_LOGCONFIG(TAG, "Zigbee NCP: UART1 115200 8N1 RTS/CTS, TCP %u", port_);
}
}
