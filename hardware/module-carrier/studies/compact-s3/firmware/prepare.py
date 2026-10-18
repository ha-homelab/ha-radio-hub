#!/usr/bin/env python3
"""Prepare a disposable full Nano (selected) or Mini comparison build; never flash."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require_historical_baseline():
    profile = ROOT / "firmware/module-carrier/hub.yaml"
    if hashlib.sha256(profile.read_bytes()).hexdigest() != "5d65e7d74cc29dfd806e94d72e4e37922d53fcaae4702ae2341186c3031d4ff6":
        raise SystemExit("Historical study helper: reproduce from revision 177a547c70bba11d5f48dee0bdc8595670a4fafb. "
                         "For the current Nano board, use firmware/module-carrier/validate.py.")


def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one original fragment in {path}: {old!r}")
    path.write_text(text.replace(old, new))


def prepare(output, upstream=None):
    require_historical_baseline()
    source = ROOT / "firmware/module-carrier/prepare.py"
    spec = importlib.util.spec_from_file_location("mc1_prepare", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profile = module.prepare(output, upstream)
    changes = [
        ("name: module-carrier-hub", "name: compact-s3-mini-hub"),
        ("board: esp32-s3-devkitc-1", "board: lolin_s3_mini"),
        ("flash_size: 8MB", "flash_size: 4MB"),
        ("mode: octal", "mode: quad"),
        ("tx_pin: GPIO41", "tx_pin: GPIO33"),
        ("rx_pin: GPIO42", "rx_pin: GPIO34"),
        ("reset_pin: GPIO47", "reset_pin: GPIO37"),
        ("boot_pin: GPIO48", "boot_pin: GPIO38"),
        ("tx_pin: GPIO39", "tx_pin: GPIO35"),
        ("rx_pin: GPIO40", "rx_pin: GPIO36"),
    ]
    for old, new in changes:
        replace_once(profile, old, new)
    # UART controller ownership remains unchanged: radar0, Zigbee1, Thread2.
    # Change only the old carrier's pin-specific final-validation guard.
    guard = profile.parent.parent / "low-power/components/low_power_otbr/__init__.py"
    for old, new in [
        ('get("number") != 39', 'get("number") != 35'),
        ('get("number") != 40', 'get("number") != 36'),
        ("GPIO39/40", "GPIO35/36"),
    ]:
        replace_once(guard, old, new)
    report = {
        "target": "LOLIN S3 Mini v1.0.0 / ESP32-S3FH4R2",
        "source_profile_sha256": hashlib.sha256((ROOT / "firmware/module-carrier/hub.yaml").read_bytes()).hexdigest(),
        "prepared_profile_sha256": hashlib.sha256(profile.read_bytes()).hexdigest(),
        "prepared_guard_sha256": hashlib.sha256(guard.read_bytes()).hexdigest(),
        "runtime_cpp_modified": False,
        "firmware_uploaded": False,
    }
    (profile.parent / "compact-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    return profile


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--board", choices=("nano", "mini"), default="nano")
    args = parser.parse_args()
    if args.board == "nano":
        from prepare_nano import prepare as prepare_selected
    else:
        prepare_selected = prepare
    print(prepare_selected(args.output, args.upstream))
