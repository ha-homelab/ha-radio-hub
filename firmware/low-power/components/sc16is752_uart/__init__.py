"""One SC16IS752 channel, fixed 115200 8N1, for the low-power ZAC93 bridge."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import spi, uart
import esphome.final_validate as fv
from esphome.const import CONF_ID, CONF_INTERRUPT_PIN, CONF_BAUD_RATE

DEPENDENCIES = ["esp32", "spi"]
AUTO_LOAD = ["uart"]
ns = cg.esphome_ns.namespace("sc16is752_uart")
SC16IS752UART = ns.class_("SC16IS752UART", cg.Component, uart.UARTComponent, spi.SPIDevice)

def validate(config):
    if config.get("data_rate", 4000000) > 4000000:
        raise cv.Invalid("SC16IS752 supports at most 4 MHz SPI")
    if config.get("spi_mode") != "MODE0":
        raise cv.Invalid("SC16IS752 requires SPI mode 0")
    if config.get("release_device", False):
        raise cv.Invalid("The background UART worker requires a persistent SPI device")
    if config[CONF_INTERRUPT_PIN].get("inverted", False):
        raise cv.Invalid("SC16IS752 IRQ must be a non-inverted input with an external 1k pull-up")
    return config

CONFIG_SCHEMA = cv.All(cv.Schema({
    cv.GenerateID(): cv.declare_id(SC16IS752UART),
    cv.Required(CONF_INTERRUPT_PIN): pins.internal_gpio_input_pin_schema,
    cv.Optional("crystal_frequency", default=3686400): cv.one_of(1843200, 3686400, int=True),
    cv.Optional(CONF_BAUD_RATE, default=115200): cv.one_of(115200, int=True),
}).extend(cv.COMPONENT_SCHEMA).extend(spi.spi_device_schema(
    default_data_rate=4000000, default_mode="MODE0")), cv.only_with_framework("esp-idf"), validate)
def final_validate(config):
    # ID-match validators return the bus declaration, not the original ID.
    # Invoke independently rather than feeding that result through cv.All.
    spi.final_validate_device_schema("sc16is752_uart", require_mosi=True, require_miso=True)(config)
    cv.Schema({cv.Required("spi_id"): fv.id_declaration_match_schema({
        cv.Required("interface_index", msg="SC16 UART worker requires a hardware SPI bus"): cv.valid
    })}, extra=cv.ALLOW_EXTRA)(config)
    return config

FINAL_VALIDATE_SCHEMA = final_validate

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await spi.register_spi_device(var, config)
    cg.add(var.set_interrupt_pin(await cg.gpio_pin_expression(config[CONF_INTERRUPT_PIN])))
    cg.add(var.set_crystal_frequency(config["crystal_frequency"]))
    cg.add(var.set_baud_rate(config[CONF_BAUD_RATE]))
    cg.add(var.set_data_bits(8))
    cg.add(var.set_stop_bits(1))
