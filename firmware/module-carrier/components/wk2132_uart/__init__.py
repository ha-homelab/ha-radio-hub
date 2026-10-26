"""Fault-aware DFR0627 UART1 for the fixed 115200 8N1 ZAC93 link."""
import esphome.codegen as cg
import esphome.config_validation as cv
import esphome.final_validate as fv
from esphome.components import i2c, uart
from esphome.const import CONF_ID
from .address_plan import validate_address_plan

DEPENDENCIES = ["esp32", "i2c"]
AUTO_LOAD = ["uart"]
ns = cg.esphome_ns.namespace("wk2132_uart")
WK2132UART = ns.class_("WK2132UART", cg.Component, uart.UARTComponent, i2c.I2CDevice)

CONFIG_SCHEMA = cv.All(cv.Schema({
    cv.GenerateID(): cv.declare_id(WK2132UART),
}).extend(cv.COMPONENT_SCHEMA).extend(i2c.i2c_device_schema(0x50)),
    cv.only_with_framework("esp-idf"))

def final_validate(config):
    try:
        validate_address_plan(config, fv.full_config.get())
    except ValueError as error:
        raise cv.Invalid(str(error)) from error
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
