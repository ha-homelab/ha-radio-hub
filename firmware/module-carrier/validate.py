#!/usr/bin/env python3
"""Validate or compile MC1 in an isolated directory. Never upload to a device."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from prepare import prepare, load_legacy
from contract import verify_generated, verify_shared_spi_sources, verify_partitions, actual_partition_csv

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
            raise RuntimeError("H2 open-drain service contract changed: "+step)
        position=found
    if "GPIO_MODE_OUTPUT)" in source:
        raise RuntimeError("Push-pull control found in H2 service source")
    return {"reset_gpio":47,"boot_gpio":48,"mode":"open_drain",
            "idle_level":1,"reset_low_ms":10,"h2_firmware_update_supported":True,
            "source_sha256":hashlib.sha256(source.encode()).hexdigest()}

def verify(profile: Path):
    name="module-carrier-hub"
    root=profile.parent/".esphome/build"/name
    config=dict(line.split("=",1) for line in (root/("sdkconfig."+name)).read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)
    required=load_legacy("validate").REQUIRED_SDKCONFIG | {
        "CONFIG_ESPTOOLPY_FLASHSIZE_16MB":"y", "CONFIG_FREERTOS_HZ":"1000",
        "CONFIG_COMPILER_OPTIMIZATION_ASSERTIONS_ENABLE":"y",
        "CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT":"y",
        "CONFIG_SPIRAM_USE_CAPS_ALLOC":"y",
        "CONFIG_OPENTHREAD_PLATFORM_MALLOC_CAP_SPIRAM":"y"}
    for key,value in required.items():
        if config.get(key)!=value:
            raise RuntimeError(f"Required option missing: {key}={value}")
    startup_path=Path(__file__).resolve().parents[1]/"components/rf_tx_startup/verify.py"
    startup_spec=importlib.util.spec_from_file_location("rf_startup_verify",startup_path)
    startup=importlib.util.module_from_spec(startup_spec)
    startup_spec.loader.exec_module(startup)
    startup_checks=startup.verify(root, 4)
    generated=(root/"src/main.cpp").read_text()
    pin_checks=verify_generated(generated,"nano")
    spi_checks=verify_shared_spi_sources(root/"src/esphome")
    service=verify_service_gpio((root/"src/esphome/components/low_power_otbr/low_power_otbr.cpp").read_text())
    artifacts={}
    for name in ("module-carrier-hub.bin","firmware.factory.bin","firmware.ota.bin"):
        data=(root/"build"/name).read_bytes()
        artifacts[name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    partition_binary=root/"build/partition_table/partition-table.bin"
    partitions=verify_partitions(actual_partition_csv(partition_binary),artifacts["firmware.ota.bin"]["bytes"],16777216)
    memory=load_legacy("memory_report").read_memory_report(
        root/"build/esp_idf_size.json")
    ram=memory["ram"]
    source_hashes={}
    for filename in ("low_power_otbr.cpp","low_power_otbr.h","thread_guard.h","rcp_probe.h","uart_update.cpp","update_session.h"):
        source_hashes[filename]=hashlib.sha256((root/"src/esphome/components/low_power_otbr"/filename).read_bytes()).hexdigest()
    result={"compiled":True,"hardware_tested":False,"esphome":"2026.10.0","esp_idf":"5.5.5",
            "memory_report":json.loads((root/"build/esp_idf_size.json").read_text()),
            "rf_tx_startup":startup_checks,"sdkconfig_verified":required,"artifacts":artifacts,"h2_service_gpio":service,
            "generated_pin_checks":pin_checks,"shared_spi_source_sha256":spi_checks,
            "partitions":partitions,"thread_source_sha256":source_hashes,
            "linked_memory":{"static_ram_bytes":ram["used"],"linker_ram_bytes":ram["size"],"runtime_measured":False},
            "h2_update":{"transport":"authenticated temporary TCP6639 to ROM UART", "baud":115200,
                         "requires_durable_maintenance":True,"max_arm_ms":60000,"max_session_ms":600000,
                         "hardware_tested":False},
            "framework_cache_manually_modified":False,"sdk_patches_applied":False}
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
