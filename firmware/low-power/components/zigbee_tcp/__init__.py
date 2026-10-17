"""One-client transparent hardware-flow-controlled NCP bridge."""
from esphome import pins
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID

DEPENDENCIES = ["esp32", "ethernet"]
ns = cg.esphome_ns.namespace("zigbee_tcp")
ZigbeeTCP = ns.class_("ZigbeeTCP", cg.Component)
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(ZigbeeTCP),
    cv.Required("tx_pin"): pins.internal_gpio_output_pin_number,
    cv.Required("rx_pin"): pins.internal_gpio_input_pin_number,
    cv.Required("rts_pin"): pins.internal_gpio_output_pin_number,
    cv.Required("cts_pin"): pins.internal_gpio_input_pin_number,
    cv.Optional("port", default=6638): cv.port,
}).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_pins(config["tx_pin"], config["rx_pin"], config["rts_pin"], config["cts_pin"]))
    cg.add(var.set_port(config["port"]))
