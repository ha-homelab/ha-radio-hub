#include "low_power_otbr.h"
#include "update_session.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "freertos/task.h"
#include "lwip/sockets.h"
#include <algorithm>
#include <cerrno>
#include <fcntl.h>

namespace esphome::low_power_otbr {
static const char *const TAG = "h2_uart_update";
static constexpr uart_port_t UART = UART_NUM_2;
static constexpr uint16_t UPDATE_PORT = 6639;
const char *LowPowerOTBR::update_status() const {
  switch (update_phase_.load()) {
    case 1: return "waiting_authenticated_client";
    case 2: return "streaming_rom_uart";
    default: return "closed";
  }
}
void LowPowerOTBR::arm_uart_update(const std::string &token) {
  const bool maintenance = quarantined_ && fault_ == static_cast<uint32_t>(ThreadFault::MAINTENANCE);
  if (!valid_update_token(token) || !update_may_arm(maintenance, durable_, launched_, online_, update_phase_)) {
    ESP_LOGW(TAG, "Refused: require durable maintenance after reboot, Ethernet, and a fresh 128-bit hex token");
    return;
  }
  uint32_t idle = 0;
  if (!update_phase_.compare_exchange_strong(idle, 1)) return;
  std::copy(token.begin(), token.end(), update_token_.begin());
  update_cancel_ = false;
  if (xTaskCreate(update_task, "h2_update", 6144, this, 3, nullptr) != pdPASS) update_phase_ = 0;
}
void LowPowerOTBR::update_task(void *arg) {
  auto *self = static_cast<LowPowerOTBR *>(arg);
  self->run_uart_update_();
  self->update_token_.fill(0);
  self->update_phase_ = 0;
  vTaskDelete(nullptr);
}
void LowPowerOTBR::run_uart_update_() {
  int server = -1, client = -1;
  bool installed = false, entered_rom = false;
  const uint32_t armed_at = millis();
  auto again = []() { return errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR; };
  auto cleanup = [&]() {
    if (client >= 0) { shutdown(client, SHUT_RDWR); close(client); }
    if (server >= 0) close(server);
    if (installed) uart_driver_delete(UART);
    // Never resume OT here. The durable maintenance latch is left intact.
    if (entered_rom) reset_radio_();
  };
  server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  if (server < 0) return;
  int yes = 1;
  setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
  sockaddr_in address{};
  address.sin_family = AF_INET; address.sin_addr.s_addr = htonl(INADDR_ANY); address.sin_port = htons(UPDATE_PORT);
  if (bind(server, reinterpret_cast<sockaddr *>(&address), sizeof(address)) || listen(server, 1) ||
      fcntl(server, F_SETFL, O_NONBLOCK)) { cleanup(); return; }
  // A wrong/partial token never changes UART ownership or H2 reset state.
  for (unsigned attempts = 0; attempts < 4 && !update_cancel_ && update_window_open(millis(), armed_at, 60000);) {
    client = accept(server, nullptr, nullptr);
    if (client < 0) { if (!again()) break; vTaskDelay(pdMS_TO_TICKS(10)); continue; }
    ++attempts;
    if (fcntl(client, F_SETFL, O_NONBLOCK) != 0 ||
        setsockopt(client, IPPROTO_TCP, TCP_NODELAY, &yes, sizeof(yes)) != 0) {
      close(client); client = -1; continue;
    }
    char supplied[33]{};
    size_t count = 0;
    const uint32_t auth_at = millis();
    while (count < sizeof(supplied) && !update_cancel_ && update_window_open(millis(), auth_at, 5000) &&
           update_window_open(millis(), armed_at, 60000)) {
      int n = recv(client, supplied + count, sizeof(supplied) - count, 0);
      if (n > 0) count += n;
      else if (n == 0 || !again()) break;
      else vTaskDelay(pdMS_TO_TICKS(5));
    }
    if (count == sizeof(supplied) && supplied[32] == '\n' && equal_update_token(update_token_.data(), supplied)) break;
    close(client); client = -1;
  }
  if (client < 0 || update_cancel_ || !update_window_open(millis(), armed_at, 60000) || uart_is_driver_installed(UART)) {
    cleanup(); return;
  }
  close(server); server = -1; // Exactly one authenticated connection per arming.
  uart_config_t config{};
  config.baud_rate = 115200; config.data_bits = UART_DATA_8_BITS;
  config.parity = UART_PARITY_DISABLE; config.stop_bits = UART_STOP_BITS_1;
  config.flow_ctrl = UART_HW_FLOWCTRL_DISABLE; config.source_clk = UART_SCLK_DEFAULT;
  if (uart_param_config(UART, &config) != ESP_OK ||
      uart_set_pin(UART, tx_, rx_, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE) != ESP_OK ||
      uart_driver_install(UART, 4096, 0, 0, nullptr, 0) != ESP_OK) { cleanup(); return; }
  installed = true;
  gpio_set_level(static_cast<gpio_num_t>(boot_), 0);
  gpio_set_direction(static_cast<gpio_num_t>(boot_), GPIO_MODE_OUTPUT_OD);
  gpio_set_level(static_cast<gpio_num_t>(reset_), 0);
  gpio_set_direction(static_cast<gpio_num_t>(reset_), GPIO_MODE_OUTPUT_OD);
  entered_rom = true;
  vTaskDelay(pdMS_TO_TICKS(10));
  gpio_set_level(static_cast<gpio_num_t>(reset_), 1);
  vTaskDelay(pdMS_TO_TICKS(100));
  gpio_set_level(static_cast<gpio_num_t>(boot_), 1);
  // Small handshake still handles partial nonblocking writes.
  size_t ready = 0;
  const uint32_t connected_at = millis();
  while (ready < 6 && update_window_open(millis(), connected_at, 5000) && !update_cancel_) {
    int n = send(client, "READY\n" + ready, 6 - ready, 0);
    if (n > 0) ready += n;
    else if (n == 0 || !again()) { cleanup(); return; }
    else vTaskDelay(pdMS_TO_TICKS(5));
  }
  if (ready != 6 || update_cancel_) { cleanup(); return; }
  update_phase_ = 2;
  ESP_LOGI(TAG, "Authenticated H2 ROM session, 115200 baud, maximum 10 minutes; Thread stays paused");
  std::array<uint8_t, 2048> to_net{};
  std::array<uint8_t, 512> to_uart{};
  size_t net_size = 0, net_at = 0, uart_size = 0, uart_at = 0;
  uint32_t progress = millis();
  while (!update_cancel_ && update_window_open(millis(), connected_at, 600000) &&
         update_window_open(millis(), progress, 30000)) {
    bool advanced = false;
    if (uart_at == uart_size) {
      int n = recv(client, to_uart.data(), to_uart.size(), 0);
      if (n > 0) { uart_size = n; uart_at = 0; advanced = true; }
      else if (n == 0 || !again()) break;
    }
    if (uart_at < uart_size) {
      int n = uart_tx_chars(UART, reinterpret_cast<const char *>(to_uart.data() + uart_at), uart_size - uart_at);
      if (n < 0) break;
      if (n > 0) { uart_at += n; advanced = true; }
    }
    if (net_at == net_size) {
      int n = uart_read_bytes(UART, to_net.data(), to_net.size(), 0);
      if (n < 0) break;
      if (n > 0) { net_size = n; net_at = 0; advanced = true; }
    }
    if (net_at < net_size) {
      int n = send(client, to_net.data() + net_at, net_size - net_at, 0);
      if (n > 0) { net_at += n; advanced = true; }
      else if (n == 0 || !again()) break;
    }
    if (advanced) progress = millis();
    else vTaskDelay(pdMS_TO_TICKS(1));
  }
  cleanup();
  ESP_LOGI(TAG, "H2 UART session closed; flash result must be checked by the host tool before explicit Thread retry");
}
}
