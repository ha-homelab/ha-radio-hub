#!/usr/bin/env python3
"""Check the completed MC2 C6 build and print portable artifact evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from mc2_contract import c6_pin_contract
from c6_identity import ANTENNA, APP_VERSION, BOARD, SKU, verify_c6_image

def verify(root: Path):
    pins=c6_pin_contract()
    config=dict(line.split("=",1) for line in (root/"sdkconfig").read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)
    required={"CONFIG_IDF_TARGET":'"esp32c6"',"CONFIG_ESPTOOLPY_FLASHSIZE_4MB":"y",
              "CONFIG_OPENTHREAD_RCP_UART":"y","CONFIG_OPENTHREAD_RADIO_NATIVE":"y",
              "CONFIG_OPENTHREAD_UART_PIN_MANUAL":"y","CONFIG_OPENTHREAD_UART_RX_PIN":str(pins['rx']),
              "CONFIG_OPENTHREAD_UART_TX_PIN":str(pins['tx']),"CONFIG_FREERTOS_HZ":"1000",
              "CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG":"y",
              "CONFIG_ESP_CONSOLE_UART_NUM":"-1",
              "CONFIG_ESP_CONSOLE_SECONDARY_NONE":"y", "CONFIG_LOG_DEFAULT_LEVEL_ERROR":"y",
              "CONFIG_OPENTHREAD_PLATFORM_INFO":'"MC2-D 102010636 external antenna"'}
    for key,value in required.items():
        if config.get(key)!=value:
            raise RuntimeError(f"Wrong MC2 RCP option: {key}={value}")
    header=(root/"main/esp_ot_config.h").read_text()
    for value in [".baud_rate =  460800","UART_DATA_8_BITS","UART_PARITY_DISABLE",
                  "UART_STOP_BITS_1","UART_HW_FLOWCTRL_DISABLE"]:
        if value not in header:
            raise RuntimeError("RCP UART defaults changed: "+value)
    table=(root/"build/partition_table/partition-table.bin").read_bytes()
    entries=[]
    for offset in range(0,len(table)-31,32):
        magic,kind,subtype,start,size,name,flags=struct.unpack_from("<HBBII16sI",table,offset)
        if magic==0x50AA and kind==0:
            entries.append((subtype,start,size))
    if entries != [(0,65536,1048576)]:
        raise RuntimeError("C6 host updater requires the verified factory app at0x10000, size1MiB")
    source = (root / "main/esp_ot_rcp.c").read_text()
    entry = source.index("void app_main(void)")
    selector = source.index("const esp_err_t antenna_error = xiaoc6_select_external_antenna();", entry)
    radio = source.index("ESP_ERROR_CHECK(esp_openthread_start(&config));", entry)
    if selector >= radio or 'if (antenna_error != ESP_OK)' not in source[selector:radio] or 'return;' not in source[selector:radio]:
        raise RuntimeError("External antenna must be selected before radio initialization and stop on failure")
    antenna_sources = {}
    for name in ("xiaoc6_antenna.c", "xiaoc6_antenna.h"):
        data = (root / "main" / name).read_bytes()
        if data != (Path(__file__).parent / name).read_bytes():
            raise RuntimeError("Prepared antenna source differs from verified recipe: " + name)
        antenna_sources[name] = hashlib.sha256(data).hexdigest()
    description = json.loads((root / "build/project_description.json").read_text())
    if description["project_version"] != APP_VERSION:
        raise RuntimeError("Wrong C6 board application identity")
    image_header = verify_c6_image((root / "build/esp_ot_rcp.bin").read_bytes())
    result={"compiled":True,"hardware_tested":False,"esp_idf":"5.5.5",
            "board":BOARD, "board_sku":SKU, "hardware_revision":"MC2-D", "antenna":ANTENNA,
            "application_header":image_header, "antenna_source_sha256":antenna_sources,
            "required_download_strap":pins["download_strap"],
            "required_recovery_harness":pins["recovery_harness"],
            "sdkconfig_verified":required,"uart":{"baud":460800,"format":"8N1","flow_control":False},
            "application_flash_offset":65536, "rom_uart_connected":True, "artifacts":{}}
    for name in ["esp_ot_rcp.bin","bootloader/bootloader.bin","partition_table/partition-table.bin"]:
        data=(root/"build"/name).read_bytes()
        result["artifacts"][name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    result["recipe_sha256"] = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                               for name in ("prepare_c6.py", "verify_c6.py", "pin-plan.json", "mc2_contract.py",
                                            "c6_identity.py", "xiaoc6_antenna.c", "xiaoc6_antenna.h")}
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build",type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.build),indent=2))
