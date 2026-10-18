#!/usr/bin/env python3
"""Prepare the complete Waveshare ESP32-S3-Nano-M candidate; never flash."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from prepare import ROOT, replace_once


def prepare(output, upstream=None):
    source = ROOT / "firmware/module-carrier/prepare.py"
    spec = importlib.util.spec_from_file_location("mc1_prepare", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profile = module.prepare(output, upstream)
    for old, new in [
        ("name: module-carrier-hub", "name: compact-s3-nano-hub"),
        ("flash_size: 8MB", "flash_size: 16MB"),
        ("  clk_pin: GPIO13\n  mosi_pin: GPIO11\n  miso_pin: GPIO12\n", "  spi_id: cc1101_spi\n"),
        ("tx_pin: GPIO41", "tx_pin: GPIO43"),
        ("rx_pin: GPIO42", "rx_pin: GPIO44"),
        ("tx_pin: GPIO39", "tx_pin: GPIO8"),
        ("rx_pin: GPIO40", "rx_pin: GPIO38"),
        ("  interface: spi3\n  clk_pin: GPIO7\n  mosi_pin: GPIO8\n  miso_pin: GPIO6", "  interface: spi2\n  clk_pin: GPIO13\n  mosi_pin: GPIO11\n  miso_pin: GPIO12"),
        ("rts_pin: GPIO16", "rts_pin: GPIO7"),
    ]:
        replace_once(profile, old, new)
    # Generic S3 build descriptor; the explicit pin map and memory configuration
    # target the Nano's ESP32-S3R8, not a physical DevKitC footprint.
    guard = profile.parent.parent / "low-power/components/low_power_otbr/__init__.py"
    for old, new in [
        ('get("number") != 39', 'get("number") != 8'),
        ('get("number") != 40', 'get("number") != 38'),
        ("GPIO39/40", "GPIO8/38"),
    ]:
        replace_once(guard, old, new)
    rf = profile.parent.parent / "packages/rf-airbridge.yaml"
    replace_once(rf, "cs_pin: GPIO15", "cs_pin: GPIO6")
    report = {
        "target": "Waveshare ESP32-S3-Nano-M / ESP32-S3R8 / 16MB flash + 8MB octal PSRAM",
        "source_profile_sha256": hashlib.sha256((ROOT / "firmware/module-carrier/hub.yaml").read_bytes()).hexdigest(),
        "prepared_profile_sha256": hashlib.sha256(profile.read_bytes()).hexdigest(),
        "prepared_guard_sha256": hashlib.sha256(guard.read_bytes()).hexdigest(),
        "prepared_rf_package_sha256": hashlib.sha256(rf.read_bytes()).hexdigest(),
        "runtime_cpp_modified": False,
        "shared_spi": True,
        "firmware_uploaded": False,
    }
    (profile.parent / "compact-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    return profile


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--upstream", type=Path)
    args = parser.parse_args()
    print(prepare(args.output, args.upstream))
