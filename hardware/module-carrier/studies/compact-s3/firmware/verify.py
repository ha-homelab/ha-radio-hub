#!/usr/bin/env python3
"""Verify generated compact-candidate code, SDK configuration and OTA artifacts."""
import argparse
import ast
import hashlib
import json
import re
import subprocess
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
STUDY = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_generated(main, board):
    plan = json.loads((STUDY / ("pin-plan.json" if board == "nano" else "pin-plan-mini.json")).read_text())
    pins = {k: v["gpio"] for k, v in plan["assignments"].items()}
    code = "\n".join(line for line in main.splitlines() if not line.lstrip().startswith("//"))
    objects = {name: int(pin) for name, pin in re.findall(r"(\w+)->set_pin\(::GPIO_NUM_(\d+)\);", code)}

    def call(obj, method, expected):
        match = re.search(rf"{re.escape(obj)}->{method}\(([^;]*)\);", code)
        require(match is not None and match[1] == expected, f"Wrong generated {obj}.{method}; expected {expected}")

    def pin(obj, method, expected):
        match = re.search(rf"{re.escape(obj)}->{method}\(([^;]*)\);", code)
        require(match is not None and objects.get(match[1]) == expected, f"Wrong generated GPIO for {obj}.{method}")

    call("low_power_otbr_lowpowerotbr_id", "set_pins", ", ".join(str(pins[k]) for k in ("thread_tx", "thread_rx", "thread_reset", "thread_boot")))
    call("zigbee_tcp_zigbeetcp_id", "set_pins", ", ".join(str(pins[k]) for k in ("zigbee_tx", "zigbee_rx", "zigbee_rts", "zigbee_cts")))
    call("zigbee_tcp_zigbeetcp_id", "set_port", "6638")
    pin("radar_uart", "set_tx_pin", pins["radar_tx"])
    pin("radar_uart", "set_rx_pin", pins["radar_rx"])
    call("radar_uart", "set_baud_rate", "256000")
    call("logger_logger_id", "set_uart_selection", "logger::UART_SELECTION_USB_SERIAL_JTAG")
    require(code.count("uart::IDFUARTComponent();") == 1, "Radar must be the only ESPHome native UART; it owns UART0")
    for role, setter in (("sck", "set_clk"), ("mosi", "set_mosi"), ("miso", "set_miso")):
        pin("cc1101_spi", setter, pins["cc1101_" + role])
    call("cc1101_spi", "set_interface", "SPI2_HOST" if board == "nano" else "SPI3_HOST")
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
    if board == "nano":
        call("ethernet_ethernetcomponent_id", "set_spi_parent", "cc1101_spi")
        require("ethernet_ethernetcomponent_id->set_clk_pin(" not in code, "Ethernet must not initialize a second SPI bus")
        require(not re.search(r"rf_radio->(?:reset|configure)\s*\(", code), "Runtime CC1101 reset/configure is unsafe on this shared-bus profile")
        require(not re.search(r"->set_setup_priority\(", code), "Setup-priority overrides invalidate the shared-bus startup proof")
    else:
        for role, setter in (("sck", "set_clk_pin"), ("mosi", "set_mosi_pin"), ("miso", "set_miso_pin")):
            call("ethernet_ethernetcomponent_id", setter, str(pins["ethernet_" + role]))
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
            "native_uart_ownership": {"0": "LD2450", "1": "MG24", "2": "H2"},
            "shared_spi": board == "nano", "runtime_cc1101_reset_absent": True}


def verify_sdk(text, board):
    tree = ast.parse((ROOT / "firmware/low-power/validate.py").read_text())
    required = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REQUIRED_SDKCONFIG" for t in n.targets))
    if board == "mini":
        del required["CONFIG_SPIRAM_MODE_OCT"]
        required["CONFIG_SPIRAM_MODE_QUAD"] = "y"
    required["CONFIG_ESPTOOLPY_FLASHSIZE"] = '"16MB"' if board == "nano" else '"4MB"'
    required["CONFIG_SPIRAM_USE_CAPS_ALLOC"] = "y"
    required["CONFIG_OPENTHREAD_PLATFORM_MALLOC_CAP_SPIRAM"] = "y"
    required["CONFIG_FREERTOS_HZ"] = "1000"
    required["CONFIG_OPENTHREAD_NUM_MESSAGE_BUFFERS"] = "1024"
    actual = dict(line.split("=", 1) for line in text.splitlines() if line.startswith("CONFIG_") and "=" in line)
    for key, value in required.items():
        require(actual.get(key) == value, f"Required SDK configuration missing: {key}={value}")
    return required


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


def verify(profile, board, sdk_only=False):
    name = "compact-s3-" + board + "-hub"
    build = profile.parent / ".esphome/build" / name
    result = {"board": board, "compiled": not sdk_only, "hardware_tested": False, "uploaded": False,
              "peak_heap_measured": False, "stack_high_water_measured": False,
              "runtime_cpp_modified": False, "framework_cache_manually_modified": False,
              "upstream_rest_commit": "29a2345e3f0c61bba9307f3daea5ed0c94388ed3",
              "configured_flash_bytes": 16777216 if board == "nano" else 4194304,
              "expected_module_psram_bytes": 8388608 if board == "nano" else 2097152,
              "tool_versions": {"ESPHome": "2026.9.1", "ESP-IDF": "5.5.5"},
              "generated": verify_generated((build / "src/main.cpp").read_text(), board),
              "sdkconfig_verified": verify_sdk((build / ("sdkconfig." + name)).read_text(), board)}
    snapshot = profile.parents[2]
    runtime = {}
    for directory in ("firmware/low-power/components", "firmware/module-carrier/components", "firmware/components", "firmware/include"):
        for source in sorted((ROOT / directory).rglob("*")):
            if source.suffix not in (".cpp", ".h", ".hpp", ".c"):
                continue
            relative = source.relative_to(ROOT)
            prepared = snapshot / relative
            require(prepared.is_file() and sha(source) == sha(prepared), f"Runtime source changed: {relative}")
            runtime[str(relative)] = sha(source)
    result["unchanged_runtime_source_sha256"] = runtime
    for component, expected in (("low_power_otbr", "UART_NUM_2"), ("zigbee_tcp", "UART_NUM_1")):
        source = snapshot / "firmware/low-power/components" / component / (component + ".cpp")
        require(expected in source.read_text(), f"Wrong controller for {component}")
    pins = snapshot / "firmware/low-power/components/low_power_otbr/low_power_otbr.cpp"
    require("GPIO_MODE_OUTPUT_OD" in pins.read_text(), "H2 boot/reset must be open-drain")
    result["source_sha256"] = {"generated_main": sha(build / "src/main.cpp"), "profile": sha(profile), "prepare_manifest": sha(profile.parent / "compact-preparation.json")}
    description = json.loads((build / "build/project_description.json").read_text())
    require(description["project_version"] == "2026.9.1" and description["target"] == "esp32s3", "Unexpected generated build version/target")
    compiler = subprocess.check_output([description["c_compiler"], "--version"], text=True).splitlines()[0]
    result["tool_versions"]["compiler"] = compiler
    if board == "nano":
        result["shared_spi_source_sha256"] = verify_shared_spi_sources(build / "src/esphome")
    if not sdk_only:
        artifacts = {}
        for filename in (name + ".bin", "firmware.factory.bin", "firmware.ota.bin"):
            path = build / "build" / filename
            require(path.is_file(), f"Build artifact missing: {filename}")
            artifacts[filename] = {"bytes": path.stat().st_size, "sha256": sha(path)}
        result["artifacts"] = artifacts
        partition_binary = build / "build/partition_table/partition-table.bin"
        result["partitions"] = verify_partitions(actual_partition_csv(partition_binary), artifacts["firmware.ota.bin"]["bytes"], 16777216 if board == "nano" else 4194304)
        result["partition_table_sha256"] = sha(partition_binary)
        sizes = json.loads((build / "build/esp_idf_size.json").read_text())
        ram = sizes["memory_types"].get("DRAM") or sizes["memory_types"].get("DIRAM")
        require(ram is not None, "Linked RAM region missing from size report")
        result["linked_memory"] = {"image_unpadded_bytes": sizes["image_size"],
                                   "static_ram_bytes": ram["used"], "linker_ram_bytes": ram["size"],
                                   "runtime_heap_or_stack_measurement": False}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--board", choices=("nano", "mini"), default="nano")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sdk-only", action="store_true", help="Check generated sources before compilation completes")
    args = parser.parse_args()
    result = verify(args.profile.resolve(), args.board, args.sdk_only)
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized)
