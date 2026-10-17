"""W5500 PHY policy, separate from the SPI clock."""
import esphome.codegen as cg
import esphome.config_validation as cv
import esphome.final_validate as fv
from esphome.const import CONF_ID
DEPENDENCIES = ["ethernet", "esp32"]
ns = cg.esphome_ns.namespace("low_power_ethernet")
LowPowerEthernet = ns.class_("LowPowerEthernet", cg.Component)
CONFIG_SCHEMA = cv.Schema({cv.GenerateID(): cv.declare_id(LowPowerEthernet)}).extend(cv.COMPONENT_SCHEMA)
def final_validate(config):
    if fv.full_config.get()["ethernet"]["type"] != "W5500":
        raise cv.Invalid("low_power_ethernet requires W5500")
    return config
FINAL_VALIDATE_SCHEMA = final_validate
async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
