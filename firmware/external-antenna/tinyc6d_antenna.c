/*
 * TinyC6[D] TC6D-01: FXL6408 XIO0 drives the external antenna selector.
 * Board/register reference: UnexpectedMaker/um-series-d at
 * 70a46b4c649ec0f8b1087ffb1bebe6ff5ff450e3, ESP-IDF helper and schematic.
 * This deliberately initializes only the RF selector, not the LED/fuel gauge.
 */
#include "tinyc6d_antenna.h"
#include "driver/i2c_master.h"
#include <stddef.h>
#include <stdint.h>

enum {
    FXL_DEVICE_ID = 0x01, FXL_DIRECTION = 0x03,
    FXL_OUTPUT = 0x05, FXL_HIGH_Z = 0x07,
    RF_MASK = 0x01, TIMEOUT_MS = 100,
};

static esp_err_t read_reg(i2c_master_dev_handle_t device, uint8_t reg, uint8_t *value)
{
    return i2c_master_transmit_receive(device, &reg, 1, value, 1, TIMEOUT_MS);
}

static esp_err_t update_rf_bit(i2c_master_dev_handle_t device, uint8_t reg, int high)
{
    uint8_t data[2] = {reg, 0};
    esp_err_t error = read_reg(device, reg, &data[1]);
    if (error != ESP_OK)
        return error;
    data[1] = high ? (data[1] | RF_MASK) : (data[1] & (uint8_t) ~RF_MASK);
    return i2c_master_transmit(device, data, sizeof(data), TIMEOUT_MS);
}

esp_err_t tinyc6d_select_external_antenna(void)
{
    i2c_master_bus_handle_t bus = NULL;
    i2c_master_dev_handle_t device = NULL;
    const i2c_master_bus_config_t bus_config = {
        .i2c_port = 0,
        .sda_io_num = 6,
        .scl_io_num = 7,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    const i2c_device_config_t device_config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x43,
        .scl_speed_hz = 400000,
    };
    esp_err_t error = i2c_new_master_bus(&bus_config, &bus);
    if (error != ESP_OK)
        return error;
    error = i2c_master_bus_add_device(bus, &device_config, &device);
    if (error != ESP_OK)
        goto cleanup;
    uint8_t value;
    error = read_reg(device, FXL_DEVICE_ID, &value);
    if (error != ESP_OK)
        goto cleanup;
    if ((value >> 5) != 0x05) {
        error = ESP_ERR_NOT_FOUND;
        goto cleanup;
    }
    /* Preload HIGH before enabling output; preserve all other expander pins. */
    error = update_rf_bit(device, FXL_OUTPUT, 1);
    if (error != ESP_OK)
        goto cleanup;
    error = update_rf_bit(device, FXL_DIRECTION, 1);
    if (error != ESP_OK)
        goto cleanup;
    error = update_rf_bit(device, FXL_HIGH_Z, 0);
    if (error != ESP_OK)
        goto cleanup;
    /*
     * Check all three output configuration registers, not just I2C ACK.
     * FXL6408 Table 17 does not define input-status feedback for an output,
     * so reading 0x0f must not gate boot or claim to measure the physical pin.
     * https://www.onsemi.com/download/data-sheet/pdf/fxl6408-d.pdf
     */
    const uint8_t registers[] = {FXL_OUTPUT, FXL_DIRECTION, FXL_HIGH_Z};
    for (size_t i = 0; i < sizeof(registers); ++i) {
        error = read_reg(device, registers[i], &value);
        if (error != ESP_OK)
            goto cleanup;
        const uint8_t expected = registers[i] == FXL_HIGH_Z ? 0 : RF_MASK;
        if ((value & RF_MASK) != expected) {
            error = ESP_ERR_INVALID_STATE;
            goto cleanup;
        }
    }
cleanup:
    /* The expander retains its driven output after the I2C controller is freed. */
    if (device != NULL) {
        esp_err_t cleanup_error = i2c_master_bus_rm_device(device);
        if (error == ESP_OK)
            error = cleanup_error;
    }
    esp_err_t cleanup_error = i2c_del_master_bus(bus);
    return error == ESP_OK ? cleanup_error : error;
}
