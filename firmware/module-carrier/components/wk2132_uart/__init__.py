"""Fault-aware DFR0627 UART1 for the fixed 115200 8N1 ZAC93 link."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import i2c, uart
from esphome.const import CONF_ID

DEPENDENCIES = ["esp32", "i2c"]
AUTO_LOAD = ["uart"]
ns = cg.esphome_ns.namespace("wk2132_uart")
WK2132UART = ns.class_("WK2132UART", cg.Component, uart.UARTComponent, i2c.I2CDevice)

CONFIG_SCHEMA = cv.All(cv.Schema({
    cv.GenerateID(): cv.declare_id(WK2132UART),
}).extend(cv.COMPONENT_SCHEMA).extend(i2c.i2c_device_schema(0x70)),
    cv.only_with_framework("esp-idf"))

def final_validate(config):
    if config["address"] != 0x70:
        raise cv.Invalid("MC1 requires DFR0627 UART1 with IA1=1, IA0=1, address 0x70")
    i2c.final_validate_device_schema("wk2132_uart", min_frequency="400kHz", max_frequency="400kHz")(config)
    return config

FINAL_VALIDATE_SCHEMA = final_validate

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)
    cg.add(var.set_baud_rate(115200))
    cg.add(var.set_data_bits(8))
    cg.add(var.set_stop_bits(1))
    cg.add(var.set_parity(uart.UARTParityOptions.UART_CONFIG_PARITY_NONE))
