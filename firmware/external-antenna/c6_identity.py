"""Single application/board identity used by preparation, verification and updates."""
import struct

BOARD = "Seeed Studio XIAO ESP32C6"
SKU = "102010636"
APP_VERSION = "mc2d-xiaoc6-ext-v1"
ANTENNA = {
    "mode": "external",
    "rf_path": "U.FL",
    "enable_gpio": 3,
    "enable_level": 0,
    "select_gpio": 14,
    "select_level": 1,
    "initialized_before_radio": True,
}
DOWNLOAD_STRAP = {
    "gpio": 8, "level": 1, "pullup_ohms": 5100,
    "rail": "C6_LOCAL_3V3", "location": "XIAO onboard; no carrier resistor",
}

RECOVERY_HARNESS = {
    "reset": {"carrier_pin": "J10.1", "module_pad": "TP8", "net": "EN"},
    "boot": {"carrier_pin": "J10.2", "module_pad": "TP2", "gpio": 9},
}


def verify_c6_image(data):
    """Inspect the IDF image header and app descriptor, not a filename or label."""
    if len(data) < 288 or data[0] != 0xE9 or len(data) > 1024 * 1024:
        raise ValueError("Invalid/oversized C6 application image")
    if struct.unpack_from("<H", data, 12)[0] != 13 or data[3] >> 4 != 2:
        raise ValueError("C6 application must target ESP32-C6 with 4 MB flash")
    if struct.unpack_from("<I", data, 32)[0] != 0xABCD5432:
        raise ValueError("Missing IDF application descriptor")
    version = data[48:80].split(b"\0", 1)[0]
    project = data[80:112].split(b"\0", 1)[0]
    if version != APP_VERSION.encode() or project != b"esp_ot_rcp":
        raise ValueError("C6 application must identify the MC2-D 102010636 external-antenna build")
    return {"chip_id": 13, "flash_bytes": 4194304, "project": "esp_ot_rcp",
            "version": APP_VERSION}
