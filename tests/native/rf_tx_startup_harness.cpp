#include "rf_tx_startup_stubs.h"
#include <cassert>
#include <string>
#include <vector>
#include "rf_tx_startup.cpp"

static bool od, output_enabled, signal_level, drove_before_tx;
static int level_error, od_error, allocation_error, calls;
static std::vector<std::string> events;
static rmt_tx_channel_config_t received;
void assess() { drove_before_tx |= output_enabled && (!od || !signal_level); }
esp_err_t gpio_set_level(gpio_num_t pin, uint32_t level) {
  assert(pin == RF_TX_STARTUP_PIN); events.emplace_back("latch");
  if (level_error) return level_error;
  signal_level = level; assess(); return ESP_OK;
}
esp_err_t gpio_od_enable(gpio_num_t pin) {
  assert(pin == RF_TX_STARTUP_PIN); events.emplace_back("od");
  if (od_error) return od_error;
  od = true; assess(); return ESP_OK;
}
extern "C" esp_err_t __real_rmt_new_tx_channel(const rmt_tx_channel_config_t *cfg,
                                               rmt_channel_handle_t *channel) {
  ++calls; events.emplace_back("allocate");
  if (!cfg || !channel) return ESP_ERR_INVALID_ARG;
  received = *cfg;
  if (allocation_error) return allocation_error;
  // ESP-IDF 5.5.5: rmt_tx.c sets idle, routes/enables pad, THEN applies OD.
  signal_level = cfg->flags.init_level;
  output_enabled = true;
  assess();
  if (cfg->flags.io_od_mode) od = true;
  assess();
  *channel = reinterpret_cast<void *>(1);
  return ESP_OK;
}
int main(int argc, char **argv) {
  assert(argc == 2);
  const std::string mode = argv[1];
  rmt_tx_channel_config_t cfg{};
  cfg.gpio_num = RF_TX_STARTUP_PIN;
  cfg.resolution_hz = 1000000;
  cfg.flags.io_od_mode = true;
  rmt_channel_handle_t channel = nullptr;
  if (mode == "unguarded" || mode == "init_only") {
    cfg.flags.init_level = mode == "init_only";
    assert(__real_rmt_new_tx_channel(&cfg, &channel) == ESP_OK);
    assert(drove_before_tx);  // Both old behavior and half-fix reproduce drive.
  } else if (mode == "safe") {
    assert(__wrap_rmt_new_tx_channel(&cfg, &channel) == ESP_OK);
    assert(!drove_before_tx && od && signal_level && output_enabled);
    assert(events == std::vector<std::string>({"latch", "od", "allocate"}));
    assert(cfg.flags.init_level == 0);  // Caller config is not modified.
    assert(received.flags.init_level && received.flags.io_od_mode);
    assert(received.resolution_hz == cfg.resolution_hz && channel != nullptr);
  } else if (mode == "other_gpio") {
    cfg.gpio_num = 26; cfg.flags.io_od_mode = false;
    assert(__wrap_rmt_new_tx_channel(&cfg, &channel) == ESP_OK);
    assert(events == std::vector<std::string>({"allocate"}));
    assert(!received.flags.io_od_mode && !received.flags.init_level);
  } else if (mode == "reject_pushpull" || mode == "reject_inverted" || mode == "null_handle") {
    if (mode == "reject_pushpull") cfg.flags.io_od_mode = false;
    if (mode == "reject_inverted") cfg.flags.invert_out = true;
    assert(__wrap_rmt_new_tx_channel(&cfg, mode == "null_handle" ? nullptr : &channel) == ESP_ERR_INVALID_ARG);
    assert(events.empty() && !drove_before_tx && calls == 0);
  } else if (mode == "null_config") {
    assert(__wrap_rmt_new_tx_channel(nullptr, &channel) == ESP_ERR_INVALID_ARG);
    assert(calls == 1 && events == std::vector<std::string>({"allocate"}));
  } else if (mode == "level_error" || mode == "od_error" || mode == "allocation_error") {
    if (mode == "level_error") level_error = 17;
    if (mode == "od_error") od_error = 17;
    if (mode == "allocation_error") allocation_error = 17;
    assert(__wrap_rmt_new_tx_channel(&cfg, &channel) == 17);
    assert(!drove_before_tx && channel == nullptr);
    assert(calls == (mode == "allocation_error" ? 1 : 0));
  } else { assert(false); }
}
