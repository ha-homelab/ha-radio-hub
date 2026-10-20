"""Compile the production selector against an I2C model, including bus failures."""
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
#define ESP_ERR_NOT_FOUND 1
#define ESP_ERR_INVALID_STATE 2
"""
DRIVER = """
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"
typedef void *i2c_master_bus_handle_t;
typedef void *i2c_master_dev_handle_t;
typedef struct {
    int i2c_port, sda_io_num, scl_io_num, clk_source, glitch_ignore_cnt;
    struct { bool enable_internal_pullup; } flags;
} i2c_master_bus_config_t;
typedef struct {
    int dev_addr_length, device_address, scl_speed_hz;
} i2c_device_config_t;
#define I2C_CLK_SRC_DEFAULT 0
#define I2C_ADDR_BIT_LEN_7 0
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *, i2c_master_bus_handle_t *);
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t, const i2c_device_config_t *, i2c_master_dev_handle_t *);
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t, const uint8_t *, size_t, uint8_t *, size_t, int);
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t, const uint8_t *, size_t, int);
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t);
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t);
"""
MODEL = """
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "tinyc6d_antenna.h"
#include "driver/i2c_master.h"
static int operations, fail_at, corrupt_reg, written, writes, buses, devices;
static uint8_t regs[256], initial[256];
static const uint8_t expected_order[] = {5, 3, 7};
static int step(void) { return ++operations == fail_at ? 99 : 0; }
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *cfg, i2c_master_bus_handle_t *bus) {
    assert(cfg->i2c_port == 0 && cfg->sda_io_num == 6 && cfg->scl_io_num == 7);
    assert(cfg->flags.enable_internal_pullup);
    if (step()) return 99;
    *bus = (void *)1; buses++; return 0;
}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus, const i2c_device_config_t *cfg, i2c_master_dev_handle_t *dev) {
    assert(bus && cfg->device_address == 0x43 && cfg->scl_speed_hz == 400000);
    if (step()) return 99;
    *dev = (void *)2; devices++; return 0;
}
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t dev, const uint8_t *reg, size_t tx, uint8_t *out, size_t rx, int timeout) {
    assert(dev && tx == 1 && rx == 1 && timeout == 100);
    /* Input-status feedback is undefined for output pins (datasheet Table 17). */
    assert(*reg != 0x0f);
    if (step()) return 99;
    *out = regs[*reg];
    if (written && *reg == corrupt_reg) *out ^= 1;
    return 0;
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev, const uint8_t *data, size_t length, int timeout) {
    assert(dev && length == 2 && timeout == 100 && writes < 3);
    if (step()) return 99;
    assert(data[0] == expected_order[writes++]);
    assert((data[1] & 0xfe) == (initial[data[0]] & 0xfe));
    regs[data[0]] = data[1];
    if (writes == 3) written = 1;
    return 0;
}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev) {
    assert(dev); devices--; return step();
}
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t bus) {
    assert(bus); buses--; return step();
}
static void reset(int active) {
    operations = written = writes = buses = devices = 0;
    memset(regs, 0, sizeof(regs));
    regs[1] = 0xa0; regs[5] = active ? 0xa5 : 0xa4;
    regs[3] = active ? 0x59 : 0x58; regs[7] = active ? 0x96 : 0x97;
    memcpy(initial, regs, sizeof(regs));
}
int main(int argc, char **argv) {
    assert(argc == 2);
    if (!strcmp(argv[1], "reset_and_warm_boot")) {
        for (int active = 0; active < 2; active++) {
            reset(active);
            assert(tinyc6d_select_external_antenna() == ESP_OK);
            assert((regs[5] & regs[3] & ~regs[7] & 1) == 1);
            assert(writes == 3 && buses == 0 && devices == 0);
        }
    } else if (!strcmp(argv[1], "input_status_is_not_output_feedback")) {
        for (int status = 0; status < 2; status++) {
            reset(1); regs[15] = status;
            assert(tinyc6d_select_external_antenna() == ESP_OK);
            assert((regs[5] & regs[3] & ~regs[7] & 1) == 1);
        }
    } else if (!strcmp(argv[1], "all_bus_errors")) {
        reset(0);
        assert(tinyc6d_select_external_antenna() == 0);
        const int total = operations;
        for (fail_at = 1; fail_at <= total; fail_at++) {
            reset(0);
            assert(tinyc6d_select_external_antenna() == 99);
            assert(buses == 0 && devices == 0);
        }
    } else if (!strcmp(argv[1], "wrong_identity")) {
        reset(0); regs[1] = 0;
        assert(tinyc6d_select_external_antenna() == ESP_ERR_NOT_FOUND);
        assert(writes == 0 && buses == 0 && devices == 0);
    } else if (!strcmp(argv[1], "readback_errors")) {
        const int bad[] = {5, 3, 7};
        for (unsigned i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i) {
            reset(0); corrupt_reg = bad[i];
            assert(tinyc6d_select_external_antenna() == ESP_ERR_INVALID_STATE);
            assert(buses == 0 && devices == 0);
        }
    } else { assert(0); }
}
"""


class AntennaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="mc2-c6d-antenna-")
        cls.addClassCleanup(cls.tmp.cleanup)
        root = Path(cls.tmp.name)
        (root / "driver").mkdir()
        (root / "esp_err.h").write_text(ERRORS)
        (root / "driver/i2c_master.h").write_text(DRIVER)
        (root / "model.c").write_text(MODEL)
        cls.binary = root / "test-antenna"
        flags = ["-std=c11", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([shutil.which("cc"), *flags, "-I", str(root), "-I", str(ROOT),
                        str(root / "model.c"), str(ROOT / "tinyc6d_antenna.c"),
                        "-o", str(cls.binary)], check=True)


for case in ("reset_and_warm_boot", "input_status_is_not_output_feedback",
             "all_bus_errors", "wrong_identity", "readback_errors"):
    def test(self, case=case):
        subprocess.run([str(self.binary), case], check=True)
    setattr(AntennaTests, "test_" + case, test)


if __name__ == "__main__":
    unittest.main()
