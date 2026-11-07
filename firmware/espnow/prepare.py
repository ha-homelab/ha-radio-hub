#!/usr/bin/env python3
"""Prepare an isolated full ESP-NOW hub and satellite build; never flash."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import secrets


def prepare(output: Path, upstream: Path | None = None) -> Path:
    """Reuse the pinned MC2-D source preparation without reading live secrets.

    The existing preparer excludes every secrets.yaml and creates disposable hub
    credentials. Only documentation MAC addresses and fresh random provider keys
    are added here. These builds are for validation, not installation as-is.
    """
    base_path = Path(__file__).resolve().parents[1] / "external-antenna/prepare.py"
    spec = importlib.util.spec_from_file_location("espnow_mc2d_prepare", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base_profile = base.prepare(output, upstream)
    profile = base_profile.parent.parent / "espnow/hub.yaml"

    # The MAC placeholders are public examples; actual station addresses must be
    # enrolled explicitly before any hardware installation.
    example = Path(__file__).with_name("secrets.example.yaml").read_text()
    public_macs = [line for line in example.splitlines()
                   if line.startswith("espnow_") and "_mac:" in line]
    values = [f"espnow_{name}_key: {json.dumps(secrets.token_hex(32))}"
              for name in ("climate", "probe", "contact")]
    secret_file = profile.with_name("secrets.yaml")
    secret_file.write_text(
        base_profile.with_name("secrets.yaml").read_text()
        + "\n# Validation-only station addresses and keys. Replace before flashing.\n"
        + "\n".join(public_macs + values) + "\n"
    )
    secret_file.chmod(0o600)
    return profile


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path,
                        help="New build directory outside the source firmware tree")
    parser.add_argument("--upstream", type=Path,
                        help="Existing esp-thread-br clone containing the pinned commit")
    args = parser.parse_args()
    print(prepare(args.output, args.upstream))
