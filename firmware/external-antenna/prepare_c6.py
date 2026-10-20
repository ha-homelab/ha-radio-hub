#!/usr/bin/env python3
"""Prepare MC2-C TinyC6[D] RCP with verified external RF selection; never flash."""
import argparse
from pathlib import Path
import shutil
from prepare import load_legacy
from mc2_contract import c6_pin_contract
from c6_identity import APP_VERSION


def prepare(output: Path, idf: Path) -> Path:
    pins = c6_pin_contract()
    # Reuse the pinned SDK/source copying and version validation, then select C6.
    result = load_legacy("prepare_h2").prepare(output, idf)
    path = result / "sdkconfig.defaults"
    text = path.read_text()
    replacements = {
        'CONFIG_IDF_TARGET="esp32h2"': 'CONFIG_IDF_TARGET="esp32c6"',
        'CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y': 'CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y',
        'CONFIG_OPENTHREAD_UART_RX_PIN=23': f'CONFIG_OPENTHREAD_UART_RX_PIN={pins["rx"]}',
        'CONFIG_OPENTHREAD_UART_TX_PIN=24': f'CONFIG_OPENTHREAD_UART_TX_PIN={pins["tx"]}',
        'CONFIG_LOG_DEFAULT_LEVEL_NONE=y': 'CONFIG_LOG_DEFAULT_LEVEL_ERROR=y',
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise RuntimeError("Pinned RCP defaults changed: " + old)
        text = text.replace(old, new)
    path.write_text(text + '\nCONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y\n'
                    'CONFIG_ESP_CONSOLE_SECONDARY_NONE=y\n'
                    'CONFIG_OPENTHREAD_PLATFORM_INFO="MC2-C TC6D-01 external antenna"\n')
    for name in ("tinyc6d_antenna.c", "tinyc6d_antenna.h"):
        shutil.copyfile(Path(__file__).parent / name, result / "main" / name)
    source = result / "main/esp_ot_rcp.c"
    code = source.read_text()
    entry = "void app_main(void)\n{"
    if code.count(entry) != 1:
        raise RuntimeError("Pinned RCP entry point changed")
    code = code.replace(entry, '#include "tinyc6d_antenna.h"\n#include "esp_log.h"\n\n' + entry + """
    const esp_err_t antenna_error = tinyc6d_select_external_antenna();
    if (antenna_error != ESP_OK) {
        ESP_LOGE("tinyc6d", "External antenna selection failed (%d); Thread radio stopped",
                 (int) antenna_error);
        return;
    }
""")
    source.write_text(code)
    (result / "main/CMakeLists.txt").write_text(
        'idf_component_register(SRCS "esp_ot_rcp.c" "tinyc6d_antenna.c" INCLUDE_DIRS "."\n'
        '    PRIV_REQUIRES esp_event nvs_flash openthread vfs esp_driver_i2c)\n')
    cmake = result / "CMakeLists.txt"
    cmake.write_text(f'set(PROJECT_VER "{APP_VERSION}")\n' + cmake.read_text())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--idf", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.output, args.idf))
