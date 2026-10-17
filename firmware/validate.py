#!/usr/bin/env python3
"""Validate in an isolated directory with disposable credentials; never flash."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true", help="also compile and discard the test binary")
    parser.add_argument("--esphome", default="esphome", help="ESPHome executable")
    parser.add_argument("--config", choices=("hub-s3-eth.yaml", "rf-ethernet.experimental.yaml"), default="hub-s3-eth.yaml")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="ha-radio-hub-validation-") as temporary:
        target = Path(temporary)
        shutil.copy(root / args.config, target)
        shutil.copytree(root / "packages", target / "packages")
        key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        (target / "secrets.yaml").write_text(
            f'api_encryption_key: "{key}"\nota_password: "{secrets.token_hex(24)}"\n',
            encoding="utf-8",
        )
        # `config` prints expanded secrets in some versions. Suppress stdout;
        # validation diagnostics remain on stderr and credentials are disposable.
        subprocess.run(
            [args.esphome, "config", str(target / args.config)],
            check=True, stdout=subprocess.DEVNULL,
        )
        print("ESPHome schema validation passed (isolated disposable secrets).")
        if args.compile:
            subprocess.run(
                [args.esphome, "compile", str(target / args.config)], check=True,
            )
            print("ESPHome compile passed. Disposable test binary was not flashed and will be deleted.")


if __name__ == "__main__":
    main()
