"""Single application/board identity used by preparation, verification and updates."""
import struct

BOARD = "Unexpected Maker TinyC6[D]"
SKU = "TC6D-01"
APP_VERSION = "mc2c-tc6d-ext-v1"
ANTENNA = {
    "mode": "external",
    "rf_path": "U.FL",
    "expander": "FXL6408",
    "i2c_address": 67,
    "sda": 6,
    "scl": 7,
    "select_pin": "XIO0",
    "select_level": 1,
    "initialized_before_radio": True,
}


def verify_c6_image(data):
    """Inspect the IDF image header and app descriptor, not a filename or label."""
    if len(data) < 288 or data[0] != 0xE9 or len(data) > 1024 * 1024:
        raise ValueError("Invalid/oversized C6 application image")
    if struct.unpack_from("<H", data, 12)[0] != 13 or data[3] >> 4 != 3:
        raise ValueError("C6 application must target ESP32-C6 with 8 MB flash")
    if struct.unpack_from("<I", data, 32)[0] != 0xABCD5432:
        raise ValueError("Missing IDF application descriptor")
    version = data[48:80].split(b"\0", 1)[0]
    project = data[80:112].split(b"\0", 1)[0]
    if version != APP_VERSION.encode() or project != b"esp_ot_rcp":
        raise ValueError("C6 application must identify the MC2-C TC6D-01 external-antenna build")
    return {"chip_id": 13, "flash_bytes": 8388608, "project": "esp_ot_rcp",
            "version": APP_VERSION}
