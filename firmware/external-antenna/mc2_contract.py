"""Generated-code and artifact checks for the MC2 external-antenna carrier."""
import hashlib
import json
import re
import struct
from pathlib import Path
STUDY = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def c6_pin_contract():
    """The carrier and network updater require C6's fixed ROM UART pins."""
    plan = json.loads((STUDY / "pin-plan.json").read_text())["external_controller_contract"]["c6"]
    expected = {"rx": 17, "tx": 16, "baud": 460800, "reset": "EN", "boot": 9}
    require({key: plan.get(key) for key in expected} == expected,
            "C6 plan must use ROM RX17/TX16, 460800 baud, EN and BOOT9")
    require(plan.get("board") == "Unexpected Maker TinyC6-U-01", "Wrong factory external-antenna C6 board")
    require(plan.get("download_strap") == {"gpio": 8, "level": 1, "pullup_ohms": 10000,
                                         "rail": "C6_LOCAL_3V3", "header_pin": "10"},
            "C6 ROM download requires GPIO8 pulled high from the C6-local 3.3 V rail")
    return plan

def verify_generated(main):
    c6_pin_contract()
    plan = json.loads((STUDY / "pin-plan.json").read_text())
    pins = {k: v["gpio"] for k, v in plan["assignments"].items()}
    code = "\n".join(line for line in main.splitlines() if not line.lstrip().startswith("//"))
    objects = {name: int(pin) for name, pin in re.findall(r"(\w+)->set_pin\(::GPIO_NUM_(\d+)\);", code)}

    def call(obj, method, expected):
        match = re.search(rf"{re.escape(obj)}->{method}\(([^;]*)\);", code)
        require(match is not None and match[1] == expected, f"Wrong generated {obj}.{method}; expected {expected}")

    def pin(obj, method, expected):
        match = re.search(rf"{re.escape(obj)}->{method}\(([^;]*)\);", code)
        require(match is not None and objects.get(match[1]) == expected, f"Wrong generated GPIO for {obj}.{method}")

    call("thread_border_router", "set_pins", ", ".join(str(pins[k]) for k in ("thread_tx", "thread_rx", "thread_reset", "thread_boot")))
    call("zigbee_tcp_zigbeetcp_id", "set_pins", ", ".join(str(pins[k]) for k in ("zigbee_tx", "zigbee_rx", "zigbee_rts", "zigbee_cts")))
    call("zigbee_tcp_zigbeetcp_id", "set_port", "6638")
    pin("radar_uart", "set_tx_pin", pins["radar_tx"])
    pin("radar_uart", "set_rx_pin", pins["radar_rx"])
    call("radar_uart", "set_baud_rate", "256000")
    call("logger_logger_id", "set_uart_selection", "logger::UART_SELECTION_USB_SERIAL_JTAG")
    for service in ("arm_c6_uart_update", "cancel_c6_uart_update", "pause_thread_for_c6_service"):
        require(f'PROGMEM = "{service}";' in code, f"MC2 C6 updater API missing: {service}")
    require('"C6 UART Update State"' in code, "MC2 C6 update diagnostic missing")
    require(code.count("uart::IDFUARTComponent();") == 1, "Radar must be the only ESPHome native UART; it owns UART0")
    for role, setter in (("sck", "set_clk"), ("mosi", "set_mosi"), ("miso", "set_miso")):
        pin("cc1101_spi", setter, pins["cc1101_" + role])
    call("cc1101_spi", "set_interface", "SPI2_HOST")
    call("rf_radio", "set_spi_parent", "cc1101_spi")
    pin("rf_radio", "set_cs_pin", pins["cc1101_cs"])
    for obj, suffix in (("rf_receiver", "gdo2_rx"), ("rf_transmitter", "gdo0_tx")):
        match = re.search(rf"new\({obj}\) [\w:]+\((\w+)\);", code)
        require(match is not None and objects.get(match[1]) == pins["cc1101_" + suffix], f"Wrong RF GPIO for {obj}")
        if obj == "rf_transmitter":
            flags = re.search(rf"{match[1]}->set_flags\(([^;]+)\);", code)
            require(flags is not None and "FLAG_OPEN_DRAIN" in flags[1], "RF TX must preserve open-drain mode")
    for key, setter in (("cs", "set_cs_pin"), ("irq", "set_interrupt_pin"), ("reset", "set_reset_pin")):
        call("ethernet_ethernetcomponent_id", setter, str(pins["ethernet_" + key]))
    call("ethernet_ethernetcomponent_id", "set_spi_parent", "cc1101_spi")
    require("ethernet_ethernetcomponent_id->set_clk_pin(" not in code, "Ethernet must not initialize a second SPI bus")
    require(not re.search(r"rf_radio->(?:reset|configure)\s*\(", code), "Runtime CC1101 reset/configure is unsafe on this shared-bus profile")
    require(not re.search(r"->set_setup_priority\(", code), "Setup-priority overrides invalidate the shared-bus startup proof")
    call("expansion_bus", "set_sda_pin", str(pins["i2c_sda"]))
    call("expansion_bus", "set_scl_pin", str(pins["i2c_scl"]))
    call("expansion_bus", "set_frequency", "400000")
    call("uart_zwave", "set_i2c_address", "0x70")
    call("uart_zwave", "set_baud_rate", "115200")
    call("zwave_radio", "set_uart_parent", "uart_zwave")
    require(code.count("->register_connection(") == 3, "BLE proxy must retain all three connection slots")
    require("rf_transmitter->set_non_blocking(true);" in code, "Nonblocking RF TX missing")
    require("rf_receiver->set_filter_us(150);" in code, "RF RX filter changed")
    return {"all_assigned_gpio_verified": True, "unique_gpio": len(set(pins.values())), "ble_slots": 3,
            "native_uart_ownership": {"0": "LD2450", "1": "MG24", "2": "C6"},
            "shared_spi": True, "runtime_cc1101_reset_absent": True}

def quantity(s):
    return int(s[:-1], 0) * 1024 if s.endswith("K") else int(s, 0)

def verify_shared_spi_sources(source):
    """Pin the startup/locking assumptions; fail closed when upstream changes."""
    checks = {
        "core/component.h": ("DATA = 600.0f", "ETHERNET = 250.0f", "BUS = 1000.0f"),
        "core/component.cpp": ("float Component::get_setup_priority() const { return setup_priority::DATA; }",),
        "components/ethernet/ethernet_component.h": ("return setup_priority::ETHERNET;",),
        "components/ethernet/ethernet_component_esp32.cpp": ("this->spi_parent_->get_interface()",),
        "components/spi/spi_esp_idf.cpp": ("spi_device_acquire_bus", "spi_device_release_bus"),
        "components/spi/spi.h": ("return setup_priority::BUS;",),
        "components/cc1101/cc1101.cpp": ("this->state_.GDO1_CFG = 0x2E;", "void CC1101Component::setup()", "this->configure();"),
    }
    hashes = {}
    for relative, fragments in checks.items():
        path = source / relative
        content = path.read_text()
        for fragment in fragments:
            require(fragment in content, f"Shared SPI source assumption changed: {relative}: {fragment}")
        hashes[relative] = sha(path)
    cc_header = source / "components/cc1101/cc1101.h"
    require("get_setup_priority" not in cc_header.read_text(), "CC1101 no longer uses default DATA priority")
    hashes["components/cc1101/cc1101.h"] = sha(cc_header)
    return hashes

def verify_partitions(text, ota_bytes, flash_bytes):
    entries = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = [s.strip() for s in line.split(",")]
        name, kind, subtype, offset, size = cells[:5]
        entry = {"name": name, "type": kind, "subtype": subtype, "offset": quantity(offset), "bytes": quantity(size)}
        require(entry["offset"] + entry["bytes"] <= flash_bytes, f"Partition outside flash: {name}")
        entries.append(entry)
    slots = [e for e in entries if e["subtype"] in ("ota_0", "ota_1")]
    require(len(slots) == 2, "Both OTA app slots are required")
    for entry in slots:
        require(ota_bytes <= entry["bytes"], f"OTA image does not fit {entry['name']}")
        entry["image_margin_bytes"] = entry["bytes"] - ota_bytes
    require(any(e["name"] == "nvs" for e in entries), "NVS missing")
    return entries

def actual_partition_csv(path):
    """Read resolved offsets from the IDF binary, including automatic alignment."""
    rows = []
    data = path.read_bytes()
    for offset in range(0, len(data) - 31, 32):
        magic, kind, subtype, start, size, raw_name, flags = struct.unpack_from("<HBBII16sI", data, offset)
        if magic != 0x50AA:  # MD5 trailer and erased padding are not partitions.
            continue
        name = raw_name.split(b"\0", 1)[0].decode("ascii")
        kind_name = {0: "app", 1: "data"}.get(kind, str(kind))
        subtype_name = {0x10: "ota_0", 0x11: "ota_1"}.get(subtype, str(subtype)) if kind == 0 else str(subtype)
        rows.append(f"{name},{kind_name},{subtype_name},{start},{size}")
    require(bool(rows), "No partitions found in the compiled binary table")
    return "\n".join(rows)
