#!/usr/bin/env python3
"""Prepare the pinned IDF 5.5.5 H2 RCP example; does not build or flash."""
import argparse
from pathlib import Path
import shutil
import re
import subprocess

IDF_COMMIT = "b774170ff46c393eeb5e495ea37936038d3f4f4f"

def prepare(output: Path, idf: Path) -> Path:
    output, idf = output.resolve(), idf.resolve()
    source = idf / "examples/openthread/ot_rcp"
    if output.is_relative_to(source):
        raise ValueError("H2 build output must be outside the source example tree")
    version = (idf / "tools/cmake/version.cmake").read_text()
    for key, value in (("MAJOR", 5), ("MINOR", 5), ("PATCH", 5)):
        if not re.search(r"set\(IDF_VERSION_" + key + r"\s+" + str(value) + r"\)", version):
            raise ValueError("H2 requires ESP-IDF 5.5.5")
    if (idf / ".git").exists():
        commit = subprocess.check_output(["git", "-C", str(idf), "rev-parse", "HEAD"], text=True).strip()
        if commit != IDF_COMMIT:
            raise ValueError("Unexpected IDF commit; use the pinned 5.5.5 release")
    shutil.copytree(source, output, ignore=shutil.ignore_patterns(
        "build", "sdkconfig", "sdkconfig.old", "managed_components", "dependencies.lock"))
    (output / "main/CMakeLists.txt").write_text(
        'idf_component_register(SRCS "esp_ot_rcp.c" INCLUDE_DIRS "."\n'
        '    PRIV_REQUIRES esp_event nvs_flash openthread vfs)\n')
    # These example-only command dependencies are unused with both console and
    # external coexistence disabled. Keep the RCP source unchanged.
    (output / "main/idf_component.yml").write_text('dependencies:\n  idf: "==5.5.5"\n')
    with (output / "sdkconfig.defaults").open("a") as handle:
        handle.write("""
CONFIG_IDF_TARGET="esp32h2"
CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y
CONFIG_OPENTHREAD_RCP_UART=y
CONFIG_OPENTHREAD_RCP_SPI=n
CONFIG_OPENTHREAD_RCP_USB_SERIAL_JTAG=n
CONFIG_OPENTHREAD_UART_PIN_MANUAL=y
CONFIG_OPENTHREAD_UART_RX_PIN=23
CONFIG_OPENTHREAD_UART_TX_PIN=24
CONFIG_OPENTHREAD_RCP_SPINEL_CONSOLE=n
CONFIG_ESP_COEX_EXTERNAL_COEXIST_ENABLE=n
""")
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--idf", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.output.resolve(), args.idf.resolve()))
