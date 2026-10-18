#!/usr/bin/env python3
"""Prepare MC2 TinyC6-U-01 RCP on its ROM UART17/16; never flash."""
import argparse
from pathlib import Path
from prepare import load_legacy
from mc2_contract import c6_pin_contract


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
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise RuntimeError("Pinned RCP defaults changed: " + old)
        text = text.replace(old, new)
    path.write_text(text)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--idf", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.output, args.idf))
