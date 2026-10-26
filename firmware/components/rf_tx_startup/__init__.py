"""Keep the RF open-drain pad released while ESP-IDF allocates its RMT channel."""
import hashlib
from pathlib import Path

import esphome.codegen as cg
import esphome.config_validation as cv
import esphome.final_validate as fv
from esphome.components import cc1101, esp32, remote_transmitter
from esphome.const import __version__
from esphome.core import CORE

DEPENDENCIES = ["esp32", "remote_transmitter", "cc1101"]
SOURCE_SHA256 = "3a82caf436a651d0c94f27aabf6b9544fb9160b7aa94633903314faadcb18e21"
CC1101_SHA256 = "ed86211b9450a189f43bcc61d4a1e36ad3e641f02f081b18bfff5aeb1e3c8d83"
CONFIG_SCHEMA = cv.Schema({
    cv.Required("transmitter_id"): cv.use_id(remote_transmitter.RemoteTransmitterComponent),
    cv.Required("radio_id"): cv.use_id(cc1101.CC1101Component),
})


def transmitter_config(config, full):
    matches = [item for item in full["remote_transmitter"]
               if str(item["id"]) == str(config["transmitter_id"])]
    if len(matches) != 1:
        raise cv.Invalid("RF startup guard must identify exactly one transmitter")
    return matches[0]


def final_validate(config):
    full = fv.full_config.get()
    framework = full["esp32"]["framework"]
    if (__version__ != "2026.10.0" or framework["type"] != "esp-idf"
            or framework["version"] != "5.5.5"
            or esp32.get_esp32_variant() not in (esp32.VARIANT_ESP32, esp32.VARIANT_ESP32S3)):
        raise cv.Invalid("RF startup guard requires ESPHome 2026.10.0 / ESP-IDF 5.5.5 on ESP32 or ESP32-S3")
    source = Path(remote_transmitter.__file__).with_name("remote_transmitter_rmt.cpp")
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise cv.Invalid("RF startup guard: upstream RMT transmitter changed; review before building")
    radio_source = Path(cc1101.__file__).with_name("cc1101.cpp")
    if hashlib.sha256(radio_source.read_bytes()).hexdigest() != CC1101_SHA256:
        raise cv.Invalid("RF handoff guard: upstream CC1101 changed; review before building")
    radios = [item for item in full["cc1101"] if str(item["id"]) == str(config["radio_id"])]
    if len(radios) != 1 or "gdo0_pin" in radios[0] or radios[0].get("packet_mode", False):
        raise cv.Invalid("RF handoff guard requires separate GDO2 RX, no cc1101.gdo0_pin and asynchronous mode")
    pin = transmitter_config(config, full)["pin"]
    if not pin["mode"].get("open_drain") or pin.get("inverted", False):
        raise cv.Invalid("RF startup guard requires a non-inverted open-drain transmitter")
    return config


FINAL_VALIDATE_SCHEMA = final_validate


async def to_code(config):
    pin = transmitter_config(config, CORE.config)["pin"]["number"]
    cg.add_define("RF_TX_STARTUP_PIN", pin)
    cg.add_build_flag("-Wl,--wrap=rmt_new_tx_channel")
