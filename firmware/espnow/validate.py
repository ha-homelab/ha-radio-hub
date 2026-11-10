#!/usr/bin/env python3
"""Prepare/check ESP-NOW firmware with disposable secrets. Never flash a device."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ESPHOME_VERSION = "2026.10.2"
PROFILES = {
    "hub": ("hub.yaml", "mc2-classic-hub"),
    "climate": ("sensor-bme280.yaml", "espnow-climate"),
    "probe": ("sensor-ds18b20.yaml", "espnow-probe"),
    "contact": ("sensor-contact.yaml", "espnow-contact"),
}
REQUIRED_RADIO_SDKCONFIG = {
    "CONFIG_ESP_WIFI_ENABLED": "y",
    "CONFIG_ESP_COEX_SW_COEXIST_ENABLE": "y",
}


def load_mc2():
    """Reuse the existing full-hub verifier, including real linker evidence."""
    directory = HERE.parent / "external-antenna"
    spec = importlib.util.spec_from_file_location("mc2_espnow_validate", directory / "validate.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(directory))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def prepare(output: Path, upstream: Path | None = None) -> Path:
    spec = importlib.util.spec_from_file_location("espnow_profile_prepare", HERE / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.prepare(output, upstream).parent


def sdkconfig(build: Path, name: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in (build / f"sdkconfig.{name}").read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)


def require_options(options: dict[str, str], required: dict[str, str]) -> None:
    for key, value in required.items():
        if options.get(key) != value:
            raise RuntimeError(f"Required ESP-NOW option missing: {key}={value}")


def verify_codegen(directory: Path, kind: str) -> dict:
    """Generated configuration is evidence of composition, not of compilation."""
    _, name = PROFILES[kind]
    build = directory / ".esphome/build" / name
    main = (build / "src/main.cpp").read_text()
    defines = (build / "src/esphome/core/defines.h").read_text()
    options = sdkconfig(build, name)
    for define in ("USE_ESPNOW",):
        if f"#define {define}\n" not in defines:
            raise RuntimeError(f"Missing generated feature: {define}")
    if "#define USE_WIFI\n" in defines:
        raise RuntimeError("ESP-NOW profiles must not introduce ESPHome Wi-Fi/IP routing")
    if "espnow_radio->set_auto_add_peer(false);" not in main:
        raise RuntimeError("Unsolicited ESP-NOW peer registration must remain disabled")
    if "espnow::ESPNowTransport();" not in main:
        raise RuntimeError("The native packet transport must be included")
    if "#define USE_ESPNOW_MAX_PAYLOAD_SIZE 250\n" not in defines:
        raise RuntimeError("ESP-NOW payload allocation must remain bounded to 250 bytes")
    result = {"generated": True, "compiled": False, "hardware_tested": False,
              "profile": kind, "esphome": ESPHOME_VERSION, "esp_idf": "5.5.5"}
    if kind == "hub":
        require_options(options, REQUIRED_RADIO_SDKCONFIG)
        result["generated_pin_checks"] = load_mc2().verify_generated(main)
    return result


def verify_recipe(directory: Path) -> dict[str, str]:
    """Fail if a disposable recipe diverged from the source being reviewed."""
    hashes = {}
    for source in sorted(HERE.rglob("*")):
        relative = source.relative_to(HERE)
        if (source.suffix not in (".yaml", ".py", ".h", ".cpp") or
                source.name == "secrets.yaml" or
                any(part in (".esphome", "__pycache__") for part in relative.parts)):
            continue
        data = source.read_bytes()
        if (directory / relative).read_bytes() != data:
            raise RuntimeError(f"Prepared ESP-NOW recipe differs from current source: {relative}")
        hashes[str(relative)] = hashlib.sha256(data).hexdigest()
    return hashes


def verify_compile(directory: Path, kind: str) -> dict:
    filename, name = PROFILES[kind]
    build = directory / ".esphome/build" / name
    generated = verify_codegen(directory, kind)
    recipe_hashes = verify_recipe(directory)
    if kind == "hub":
        # Same full-MC2 GPIO, UART, shared SPI, BLE slots, Thread, startup, app
        # header, two OTA slots and linked DRAM/IRAM checks as the base profile.
        result = load_mc2().verify(directory / filename,
                                   recipe_directory=directory.parent / "external-antenna")
        require_options(sdkconfig(build, name), REQUIRED_RADIO_SDKCONFIG)
        result["sdkconfig_verified"].update(REQUIRED_RADIO_SDKCONFIG)
        result["profile"] = "MC2-D with ESP-NOW sensor transport"
    else:
        require_options(sdkconfig(build, name), {"CONFIG_IDF_TARGET": '"esp32c3"',
                                                "CONFIG_ESP_WIFI_ENABLED": "y"})
        artifacts = {}
        for artifact in (f"{name}.bin", "firmware.factory.bin", "firmware.ota.bin"):
            data = (build / "build" / artifact).read_bytes()
            if not data:
                raise RuntimeError(f"Empty compiler artifact: {artifact}")
            artifacts[artifact] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        result = generated | {"compiled": True, "artifacts": artifacts}
    result["espnow_recipe_sha256"] = recipe_hashes
    result["espnow_source_sha256"] = {
        str(path.relative_to(build / "src/esphome")): hashlib.sha256(path.read_bytes()).hexdigest()
        for component in ("espnow", "packet_transport", "xxtea")
        for path in sorted((build / "src/esphome/components" / component).rglob("*"))
        if path.suffix in (".h", ".cpp")
    }
    rendered = json.dumps(result, indent=2) + "\n"
    (directory / f"{kind}-build-result.json").write_text(rendered)
    if kind == "hub":
        (directory / "build-result.json").write_text(rendered)
    return result


def run(output: Path, esphome: str, upstream: Path | None, profile: str,
        compile_firmware: bool, only_generate: bool) -> dict:
    version = subprocess.check_output([esphome, "version"], text=True).strip()
    if version != f"Version: {ESPHOME_VERSION}":
        raise RuntimeError(f"Use pinned ESPHome {ESPHOME_VERSION}; got {version}")
    directory = prepare(output, upstream)
    results = {}
    for kind in PROFILES if profile == "all" else (profile,):
        command = [esphome, "compile" if compile_firmware or only_generate else "config"]
        if only_generate:
            command.append("--only-generate")
        subprocess.run(command + [str(directory / PROFILES[kind][0])], check=True)
        if compile_firmware:
            results[kind] = verify_compile(directory, kind)
        elif only_generate:
            results[kind] = verify_codegen(directory, kind)
        else:
            results[kind] = {"configuration_valid": True, "compiled": False, "hardware_tested": False}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New private directory for prepared files and build evidence")
    parser.add_argument("--esphome", default="esphome")
    parser.add_argument("--upstream", type=Path, help="Existing clone containing the pinned ESP Thread BR commit")
    parser.add_argument("--profile", choices=("all", *PROFILES), default="all")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--compile", action="store_true")
    mode.add_argument("--only-generate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.esphome, args.upstream, args.profile,
                         args.compile, args.only_generate), indent=2))
