#!/usr/bin/env python3
"""Mutation checks for compact-candidate validation against actual generated code."""
import argparse
import json
from pathlib import Path
from verify import verify_generated, verify_sdk, verify_partitions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path, help="Nano .esphome/build/compact-s3-nano-hub")
    args = parser.parse_args()
    source = (args.build / "src/main.cpp").read_text()
    sdk = (args.build / "sdkconfig.compact-s3-nano-hub").read_text()
    checks = []

    def reject(name, callback):
        try:
            callback()
        except RuntimeError:
            checks.append({"test": name, "passed": True})
        else:
            raise AssertionError(f"Mutation incorrectly accepted: {name}")

    verify_generated(source, "nano")
    verify_sdk(sdk, "nano")
    checks.append({"test": "accept actual generated Nano profile and SDK", "passed": True})
    reject("wrong H2 UART pins", lambda: verify_generated(source.replace("set_pins(43, 44, 47, 48)", "set_pins(42, 44, 47, 48)"), "nano"))
    reject("wrong shared SPI parent", lambda: verify_generated(source.replace("ethernet_ethernetcomponent_id->set_spi_parent(cc1101_spi)", "ethernet_ethernetcomponent_id->set_spi_parent(other_bus)"), "nano"))
    reject("runtime CC reset", lambda: verify_generated(source + "\nrf_radio->reset();\n", "nano"))
    reject("runtime CC reconfigure", lambda: verify_generated(source + "\nrf_radio->configure();\n", "nano"))
    reject("startup priority override", lambda: verify_generated(source + "\nrf_radio->set_setup_priority(200.0f);\n", "nano"))
    reject("unexpected second native UART", lambda: verify_generated(source + "\nnew(extra_uart) uart::IDFUARTComponent();\n", "nano"))
    reject("loss of RF TX open drain", lambda: verify_generated(source.replace("FLAG_OPEN_DRAIN", "FLAG_INPUT"), "nano"))
    reject("loss of IPv6 forwarding", lambda: verify_sdk(sdk.replace("CONFIG_LWIP_IPV6_FORWARD=y", "# CONFIG_LWIP_IPV6_FORWARD is not set"), "nano"))
    reject("wrong PSRAM bus mode", lambda: verify_sdk(sdk.replace("CONFIG_SPIRAM_MODE_OCT=y", "CONFIG_SPIRAM_MODE_QUAD=y"), "nano"))
    partitions = "app0,app,ota_0,0x10000,1792K\napp1,app,ota_1,0x1d0000,1792K\nnvs,data,nvs,0x390000,448K\n"
    verify_partitions(partitions, 1717296, 4194304)
    checks.append({"test": "OTA image fits both partitions", "passed": True})
    reject("OTA image exceeds slot", lambda: verify_partitions(partitions, 1835009, 4194304))
    reject("second OTA slot missing", lambda: verify_partitions(partitions.replace("app1,app,ota_1,0x1d0000,1792K\n", ""), 1717296, 4194304))
    reject("partition exceeds installed flash", lambda: verify_partitions(partitions, 1717296, 2097152))
    print(json.dumps({"tests_passed": len(checks), "hardware_tested": False, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
