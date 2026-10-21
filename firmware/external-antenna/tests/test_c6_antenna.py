"""Compile the production RF selector against GPIO logic and injected failures."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ERRORS = """
#pragma once
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_ERR_INVALID_STATE 2
"""
DRIVER = """
#pragma once
#include <stdint.h>
#include "esp_err.h"
typedef int gpio_num_t;
#define GPIO_NUM_3 3
#define GPIO_NUM_14 14
#define GPIO_MODE_INPUT_OUTPUT 3
#define GPIO_PULLUP_DISABLE 0
#define GPIO_PULLDOWN_DISABLE 0
#define GPIO_INTR_DISABLE 0
typedef struct {
    uint64_t pin_bit_mask;
    int mode, pull_up_en, pull_down_en, intr_type;
} gpio_config_t;
esp_err_t gpio_set_level(gpio_num_t, uint32_t);
esp_err_t gpio_config(const gpio_config_t *);
int gpio_get_level(gpio_num_t);
"""
MODEL = """
#include <assert.h>
#include <string.h>
#include "xiaoc6_antenna.h"
#include "driver/gpio.h"
static int calls, fail_at, corrupt_pin, configured, waited;
static int levels[15];
static int step(void) { return ++calls == fail_at ? 99 : 0; }
esp_err_t gpio_set_level(gpio_num_t pin, uint32_t level) {
    assert(pin == 3 || pin == 14);
    if (step()) return 99;
    if (!configured) assert(level == 1); /* disabled until both outputs are set */
    else assert(pin == 3 && level == 0 && levels[14] == 1);
    levels[pin] = level;
    return ESP_OK;
}
esp_err_t gpio_config(const gpio_config_t *cfg) {
    assert(cfg->pin_bit_mask == ((1ULL << 3) | (1ULL << 14)));
    assert(cfg->mode == GPIO_MODE_INPUT_OUTPUT);
    assert(!cfg->pull_up_en && !cfg->pull_down_en && !cfg->intr_type);
    assert(levels[3] == 1 && levels[14] == 1);
    if (step()) return 99;
    configured = 1;
    return ESP_OK;
}
void vTaskDelay(int ticks) {
    assert(ticks == 100 && configured && levels[3] == 0 && levels[14] == 1);
    waited++;
}
int gpio_get_level(gpio_num_t pin) {
    assert(waited && (pin == 3 || pin == 14));
    return levels[pin] ^ (pin == corrupt_pin);
}
static void reset(int warm) {
    calls = configured = waited = 0;
    levels[3] = !warm; levels[14] = warm;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    if (!strcmp(argv[1], "cold_and_warm_boot")) {
        for (int warm = 0; warm < 2; warm++) {
            reset(warm);
            assert(xiaoc6_select_external_antenna() == ESP_OK);
            assert(levels[3] == 0 && levels[14] == 1 && waited == 1);
        }
    } else if (!strcmp(argv[1], "gpio_errors")) {
        for (fail_at = 1; fail_at <= 4; fail_at++) {
            reset(0);
            assert(xiaoc6_select_external_antenna() == 99);
            assert(!waited && calls == fail_at);
        }
    } else if (!strcmp(argv[1], "readback_errors")) {
        const int pins[] = {3, 14};
        for (unsigned i = 0; i < sizeof(pins) / sizeof(pins[0]); i++) {
            reset(0); corrupt_pin = pins[i];
            assert(xiaoc6_select_external_antenna() == ESP_ERR_INVALID_STATE);
        }
    } else { assert(0); }
}
"""

class AntennaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="mc2-xiaoc6-antenna-")
        cls.addClassCleanup(cls.tmp.cleanup)
        root = Path(cls.tmp.name)
        (root / "driver").mkdir()
        (root / "freertos").mkdir()
        (root / "esp_err.h").write_text(ERRORS)
        (root / "driver/gpio.h").write_text(DRIVER)
        (root / "freertos/FreeRTOS.h").write_text("#define pdMS_TO_TICKS(value) (value)\n")
        (root / "freertos/task.h").write_text("void vTaskDelay(int);\n")
        (root / "model.c").write_text(MODEL)
        cls.binary = root / "test-antenna"
        flags = ["-std=c11", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([shutil.which("cc"), *flags, "-I", str(root), "-I", str(ROOT),
                        str(root / "model.c"), str(ROOT / "xiaoc6_antenna.c"),
                        "-o", str(cls.binary)], check=True)

for case in ("cold_and_warm_boot", "gpio_errors", "readback_errors"):
    def test(self, case=case):
        subprocess.run([str(self.binary), case], check=True)
    setattr(AntennaTests, "test_" + case, test)

if __name__ == "__main__":
    unittest.main()
