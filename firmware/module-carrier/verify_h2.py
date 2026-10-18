#!/usr/bin/env python3
"""Check the completed MC1 H2 build and print portable artifact evidence."""
import argparse
import hashlib
import json
from pathlib import Path

def verify(root: Path):
    config=dict(line.split("=",1) for line in (root/"sdkconfig").read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)
    required={"CONFIG_IDF_TARGET":'"esp32h2"',"CONFIG_ESPTOOLPY_FLASHSIZE_4MB":"y",
              "CONFIG_OPENTHREAD_RCP_UART":"y","CONFIG_OPENTHREAD_RADIO_NATIVE":"y",
              "CONFIG_OPENTHREAD_UART_PIN_MANUAL":"y","CONFIG_OPENTHREAD_UART_RX_PIN":"4",
              "CONFIG_OPENTHREAD_UART_TX_PIN":"5","CONFIG_FREERTOS_HZ":"1000"}
    for key,value in required.items():
        if config.get(key)!=value:
            raise RuntimeError(f"Wrong MC1 RCP option: {key}={value}")
    header=(root/"main/esp_ot_config.h").read_text()
    for value in [".baud_rate =  460800","UART_DATA_8_BITS","UART_PARITY_DISABLE",
                  "UART_STOP_BITS_1","UART_HW_FLOWCTRL_DISABLE"]:
        if value not in header:
            raise RuntimeError("RCP UART defaults changed: "+value)
    result={"compiled":True,"hardware_tested":False,"esp_idf":"5.5.5",
            "sdkconfig_verified":required,"uart":{"baud":460800,"format":"8N1","flow_control":False},
            "artifacts":{}}
    for name in ["esp_ot_rcp.bin","bootloader/bootloader.bin","partition_table/partition-table.bin"]:
        data=(root/"build"/name).read_bytes()
        result["artifacts"][name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build",type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.build),indent=2))
