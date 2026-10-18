#!/usr/bin/env python3
"""Validate or compile MC1 in an isolated directory. Never upload to a device."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from prepare import prepare, load_legacy

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
            "idle_level":1,"reset_low_ms":10,"h2_firmware_update_supported":False,
            "source_sha256":hashlib.sha256(source.encode()).hexdigest()}

def verify(profile: Path):
    name="module-carrier-hub"
    root=profile.parent/".esphome/build"/name
    config=dict(line.split("=",1) for line in (root/("sdkconfig."+name)).read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)
    required=load_legacy("validate").REQUIRED_SDKCONFIG | {
        "CONFIG_ESPTOOLPY_FLASHSIZE_8MB":"y","CONFIG_FREERTOS_HZ":"1000"}
    for key,value in required.items():
        if config.get(key)!=value:
            raise RuntimeError(f"Required option missing: {key}={value}")
    generated=(root/"src/main.cpp").read_text()
    for line in ["set_pins(41, 42, 47, 48)","set_pins(17, 18, 16, 21)"]:
        if line not in generated:
            raise RuntimeError("Wrong Thread carrier pin: "+line)
    service=verify_service_gpio((root/"src/esphome/components/low_power_otbr/low_power_otbr.cpp").read_text())
    artifacts={}
    for name in ("module-carrier-hub.bin","firmware.factory.bin","firmware.ota.bin"):
        data=(root/"build"/name).read_bytes()
        artifacts[name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    result={"compiled":True,"hardware_tested":False,"esphome":"2026.9.1","esp_idf":"5.5.5",
            "sdkconfig_verified":required,"artifacts":artifacts,"h2_service_gpio":service}
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
