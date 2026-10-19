"""Experimental ESPHome + ESP Thread BR integration; pinned to one tested ABI."""
from pathlib import Path

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import esp32, ethernet
from esphome.const import CONF_ID, __version__
import esphome.final_validate as fv
from esphome.core import CORE

DEPENDENCIES = ["esp32", "ethernet", "psram"]
AUTO_LOAD = ["network"]
ns = cg.esphome_ns.namespace("low_power_otbr")
LowPowerOTBR = ns.class_("LowPowerOTBR", cg.Component)

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(LowPowerOTBR),
    cv.Required("server_component_path"): cv.directory,
    cv.Required("tx_pin"): pins.internal_gpio_output_pin_number,
    cv.Required("rx_pin"): pins.internal_gpio_input_pin_number,
    cv.Required("reset_pin"): pins.internal_gpio_output_pin_number,
    cv.Required("boot_pin"): pins.internal_gpio_output_pin_number,
    cv.Optional("rest_port", default=8081): cv.port,
}).extend(cv.COMPONENT_SCHEMA)


def final_validate(config):
    full = fv.full_config.get()
    framework = full["esp32"]["framework"]
    if __version__ != "2026.9.1" or framework["type"] != "esp-idf" or framework["version"] != "5.5.5":
        raise cv.Invalid("Unified OTBR requires ESPHome 2026.9.1 and ESP-IDF 5.5.5; revalidate before upgrading")
    if "wifi" in full or "openthread" in full:
        raise cv.Invalid("Unified OTBR owns Thread and requires Ethernet as its only ESPHome network interface")
    if not full.get("network", {}).get("enable_ipv6", False):
        raise cv.Invalid("network.enable_ipv6 must be true for the Thread backbone")
    uarts = full.get("uart", [])
    radar_pins = [(u.get("tx_pin", {}).get("number"), u.get("rx_pin", {}).get("number")) for u in uarts]
    if radar_pins not in [[(39, 40)], [(8, 38)], [(8, 40)], [(23, 18)]]:
        raise cv.Invalid("Only LD2450 on legacy GPIO39/40, MC1 GPIO8/38 MC2-A GPIO8/40 or MC2-B GPIO23/18 may use ESPHome native UART; UART1/2 belong to Zigbee/Thread RCP")
    if full.get("logger", {}).get("baud_rate", 0) != 0:
        raise cv.Invalid("UART logging must be disabled; use network logs (native USB is only available on S3)")
    return config

FINAL_VALIDATE_SCHEMA = final_validate


async def to_code(config):
    if esp32.get_esp32_variant() not in (esp32.VARIANT_ESP32S3, esp32.VARIANT_ESP32):
        raise cv.Invalid("This integration supports only the pinned ESP32-S3 and classic ESP32 profiles")
    server = Path(CORE.relative_config_path(config["server_component_path"])).resolve()
    if not (server / "CMakeLists.txt").is_file():
        raise cv.Invalid("Run low-power/prepare.py to prepare the pinned REST component")
    esp32.add_idf_component(name="esp_ot_br_server", path=str(server))
    for component in ("openthread", "esp_http_server", "json", "spiffs", "fatfs", "vfs", "esp_wifi"):
        esp32.include_builtin_idf_component(component)
    options = {
        "CONFIG_OPENTHREAD_ENABLED": True,
        "CONFIG_OPENTHREAD_FTD": True,
        "CONFIG_OPENTHREAD_COMMISSIONER": True,
        "CONFIG_OPENTHREAD_JOINER": True,
        "CONFIG_VFS_SUPPORT_IO": True,
        "CONFIG_VFS_SUPPORT_DIR": True,
        "CONFIG_VFS_SUPPORT_SELECT": True,
        "CONFIG_LWIP_USE_ONLY_LWIP_SELECT": False,
        "CONFIG_OPENTHREAD_BORDER_ROUTER": True,
        "CONFIG_OPENTHREAD_RADIO_SPINEL_UART": True,
        "CONFIG_OPENTHREAD_RADIO_NATIVE": False,
        "CONFIG_OPENTHREAD_CLI": False,
        "CONFIG_OPENTHREAD_CONSOLE_ENABLE": False,
        "CONFIG_OPENTHREAD_TASK_SIZE": 8192,
        "CONFIG_OPENTHREAD_NETWORK_AUTO_START": False,
        "CONFIG_LWIP_IPV6": True,
        "CONFIG_LWIP_IPV6_FORWARD": True,
        "CONFIG_LWIP_IPV6_NUM_ADDRESSES": 12,
        "CONFIG_LWIP_MULTICAST_PING": True,
        "CONFIG_LWIP_NETIF_STATUS_CALLBACK": True,
        "CONFIG_LWIP_HOOK_IP6_ROUTE_DEFAULT": True,
        "CONFIG_LWIP_HOOK_ND6_GET_GW_DEFAULT": True,
        "CONFIG_LWIP_HOOK_IP6_INPUT_CUSTOM": True,
        "CONFIG_LWIP_IPV6_AUTOCONFIG": True,
        "CONFIG_LWIP_HOOK_IP6_SELECT_SRC_ADDR_CUSTOM": True,
        "CONFIG_LWIP_FORCE_ROUTER_FORWARDING": True,
        "CONFIG_MDNS_MULTIPLE_INSTANCE": True,
        "CONFIG_MDNS_MAX_SERVICES": 24,
        "CONFIG_LWIP_MAX_SOCKETS": 24,
        "CONFIG_HTTPD_MAX_REQ_HDR_LEN": 1024,
        "CONFIG_MBEDTLS_CMAC_C": True,
        "CONFIG_MBEDTLS_SSL_PROTO_DTLS": True,
        "CONFIG_MBEDTLS_KEY_EXCHANGE_ECJPAKE": True,
        "CONFIG_MBEDTLS_ECJPAKE_C": True,
    }
    for key, value in options.items():
        esp32.add_idf_sdkconfig_option(key, value)
    cg.add_build_flag(f"-DLOW_POWER_OTBR_REST_PORT={config['rest_port']}")
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_pins(config["tx_pin"], config["rx_pin"], config["reset_pin"], config["boot_pin"]))
