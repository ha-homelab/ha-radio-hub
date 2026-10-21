#!/usr/bin/env python3
"""Validate or compile MC2 in an isolated directory. Never upload to a device."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from prepare import prepare, load_legacy
from mc2_contract import (verify_generated, verify_shared_spi_sources, verify_partitions,
                          actual_partition_csv, verify_uart_sources, verify_app_header)

RECIPE_INPUTS = (
    "hub.yaml", "health.yaml", "pin-plan.json", "mc2_contract.py", "c6_identity.py", "validate.py",
    "../packages/rf-airbridge.yaml", "../include/rf_radio_handoff.h",
    "../components/rf_tx_startup/__init__.py", "../components/rf_tx_startup/rf_tx_startup.cpp",
    "../components/rf_tx_startup/verify.py",
    "../module-carrier/components/wk2132_uart/__init__.py",
    "../module-carrier/components/wk2132_uart/address_plan.py",
    "../module-carrier/components/wk2132_uart/transport.h",
    "../module-carrier/components/wk2132_uart/wk2132_uart.h",
    "../module-carrier/components/wk2132_uart/wk2132_uart.cpp",
)

def verify_recipe_inputs(prepared: Path, build_root: Path):
    """Bind evidence to the prepared inputs and actual compiled local sources."""
    result = {}
    for name in RECIPE_INPUTS:
        data = (prepared / name).read_bytes()
        if data != (Path(__file__).parent / name).read_bytes():
            raise RuntimeError("Prepared recipe differs from current source: " + name)
        result[name] = hashlib.sha256(data).hexdigest()
    compiled = {
        "../include/rf_radio_handoff.h": "rf_radio_handoff.h",
        "../components/rf_tx_startup/rf_tx_startup.cpp": "esphome/components/rf_tx_startup/rf_tx_startup.cpp",
    }
    for name in ("transport.h", "wk2132_uart.h", "wk2132_uart.cpp"):
        compiled["../module-carrier/components/wk2132_uart/" + name] = "esphome/components/wk2132_uart/" + name
    for name, destination in compiled.items():
        if (prepared / name).read_bytes() != (build_root / "src" / destination).read_bytes():
            raise RuntimeError("Compiled local source differs from prepared recipe: " + name)
    return result

def verify_service_gpio(source: str):
    # Check the source actually copied into the image, not just the YAML pins.
    steps=[
        "gpio_set_level(static_cast<gpio_num_t>(boot_), 1);",
        "gpio_set_direction(static_cast<gpio_num_t>(boot_), GPIO_MODE_OUTPUT_OD);",
        "gpio_set_level(static_cast<gpio_num_t>(reset_), 0);",
        "gpio_set_direction(static_cast<gpio_num_t>(reset_), GPIO_MODE_OUTPUT_OD);",
        "vTaskDelay(pdMS_TO_TICKS(10));",
        "gpio_set_level(static_cast<gpio_num_t>(reset_), 1);",
    ]
    position=-1
    for step in steps:
        found=source.find(step,position+1)
        if found<0:
            raise RuntimeError("C6 open-drain service contract changed: "+step)
        position=found
    if "GPIO_MODE_OUTPUT)" in source:
        raise RuntimeError("Push-pull control found in C6 service source")
    return {"reset_gpio":27,"boot_gpio":15,"mode":"open_drain",
            "idle_level":1,"reset_low_ms":10,"c6_firmware_update_supported":True,
            "source_sha256":hashlib.sha256(source.encode()).hexdigest()}

def verify(profile: Path):
    name="mc2-classic-hub"
    root=profile.parent/".esphome/build"/name
    config=dict(line.split("=",1) for line in (root/("sdkconfig."+name)).read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)
    required={k: v for k, v in load_legacy("validate").REQUIRED_SDKCONFIG.items()
              if k != "CONFIG_SPIRAM_MODE_OCT"} | {
        "CONFIG_IDF_TARGET": '"esp32"', "CONFIG_ESP32_REV_MIN_FULL":"300",
        "CONFIG_SPIRAM_MODE_QUAD":"y", "CONFIG_SPIRAM_SPEED_40M":"y",
        "CONFIG_ESP_CONSOLE_NONE":"y",
        "CONFIG_BTDM_CTRL_MODE_BLE_ONLY":"y", "CONFIG_BTDM_CTRL_BLE_MAX_CONN":"3",
        "CONFIG_BTDM_CTRL_BLE_MAX_CONN_EFF":"3",
        "CONFIG_ESPTOOLPY_FLASHSIZE_8MB":"y", "CONFIG_FREERTOS_HZ":"1000",
        "CONFIG_COMPILER_OPTIMIZATION_ASSERTIONS_ENABLE":"y",
        "CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT":"y",
        "CONFIG_SPIRAM_USE_CAPS_ALLOC":"y",
        "CONFIG_OPENTHREAD_PLATFORM_MALLOC_CAP_SPIRAM":"y",
        "CONFIG_OPENTHREAD_PLATFORM_MSGPOOL_MANAGEMENT":"y"}
    for key,value in required.items():
        if config.get(key)!=value:
            raise RuntimeError(f"Required option missing: {key}={value}")
    startup_path=Path(__file__).resolve().parents[1]/"components/rf_tx_startup/verify.py"
    startup_spec=importlib.util.spec_from_file_location("rf_startup_verify",startup_path)
    startup=importlib.util.module_from_spec(startup_spec)
    startup_spec.loader.exec_module(startup)
    startup_checks=startup.verify(root, 25)
    generated=(root/"src/main.cpp").read_text()
    pin_checks=verify_generated(generated)
    spi_checks=verify_shared_spi_sources(root/"src/esphome")
    uart_checks=verify_uart_sources(root/"src/esphome")
    service=verify_service_gpio((root/"src/esphome/components/low_power_otbr/low_power_otbr.cpp").read_text())
    artifacts={}
    for name in ("mc2-classic-hub.bin","firmware.factory.bin","firmware.ota.bin"):
        data=(root/"build"/name).read_bytes()
        artifacts[name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    partition_binary=root/"build/partition_table/partition-table.bin"
    partitions=verify_partitions(actual_partition_csv(partition_binary),artifacts["firmware.ota.bin"]["bytes"],8388608)
    sizes=json.loads((root/"build/esp_idf_size.json").read_text())
    ram=sizes["memory_types"].get("DRAM") or sizes["memory_types"].get("DIRAM")
    iram=sizes["memory_types"]["IRAM"]
    header=verify_app_header((root/"build/firmware.ota.bin").read_bytes())
    source_hashes={}
    for filename in ("low_power_otbr.cpp","low_power_otbr.h","thread_guard.h","rcp_probe.h","uart_update.cpp","update_session.h"):
        source_hashes[filename]=hashlib.sha256((root/"src/esphome/components/low_power_otbr"/filename).read_bytes()).hexdigest()
    result={"compiled":True,"hardware_tested":False,"esphome":"2026.9.1","esp_idf":"5.5.5",
            "profile":"MC2-D classic ESP32 external antenna", "board":"ESP32-DevKitC-VIE",
            "rf_tx_startup":startup_checks,"sdkconfig_verified":required,"artifacts":artifacts,"c6_service_gpio":service,
            "generated_pin_checks":pin_checks,"shared_spi_source_sha256":spi_checks,
            "uart_source_sha256":uart_checks,"application_header":header,
            "partitions":partitions,"thread_source_sha256":source_hashes,
            "linked_memory":{"static_ram_bytes":ram["used"],"linker_ram_bytes":ram["size"],
                             "dram_headroom_bytes":ram["size"]-ram["used"],
                             "iram_used_bytes":iram["used"],"iram_size_bytes":iram["size"],
                             "iram_headroom_bytes":iram["size"]-iram["used"],
                             "psram_installed_bytes":8388608,"psram_direct_mapping_limit_bytes":4194304,
                             "runtime_measured":False},
            "c6_update":{"transport":"authenticated temporary TCP6639 to ROM UART", "baud":115200,
                         "requires_durable_maintenance":True,"max_arm_ms":60000,"max_session_ms":600000,
                         "hardware_tested":False},
            "framework_cache_manually_modified":False,"sdk_patches_applied":False}
    result["recipe_sha256"] = verify_recipe_inputs(profile.parent, root)
    (profile.parent/"build-result.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--esphome",default="esphome")
    parser.add_argument("--upstream",type=Path)
    parser.add_argument("--compile",action="store_true")
    args=parser.parse_args()
    profile=prepare(args.output,args.upstream)
    subprocess.run([args.esphome,"compile" if args.compile else "config",str(profile)],check=True)
    if args.compile:
        print(json.dumps(verify(profile),indent=2))
