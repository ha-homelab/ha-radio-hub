"""Verify source guards and real ELF call routing for the narrow RMT wrapper."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

UPSTREAM_RMT_SHA256 = "3925a8f3ba3ace5b9843c068800f6d86fa6b5e57743ea5c64ab4f4f88cf89f82"
SDK_SHA256 = {
    "components/esp_driver_rmt/src/rmt_tx.c": "a8413610fb7f729e50a517980a24925fbfb1a28620999a1ad8f34bb71419e4c6",
    "components/esp_driver_gpio/src/gpio.c": "5533690740837025221a4ab64a9cf1557aeb2d7754f0ded630884e658464f291",
}


def function_body(disassembly: str, name: str) -> str:
    match = re.search(r"^[0-9a-f]+ <" + re.escape(name) + r">:\n(.*?)(?=^[0-9a-f]+ <|\Z)",
                      disassembly, re.MULTILINE | re.DOTALL)
    if not match:
        raise RuntimeError("ELF lacks function: " + name)
    return match[1]


def verify(build_root: Path, pin: int) -> dict:
    metadata = json.loads((build_root / "build/project_description.json").read_text())
    sdk = Path(metadata["idf_path"])
    for relative, digest in SDK_SHA256.items():
        if hashlib.sha256((sdk / relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError("RF startup: unreviewed SDK source: " + relative)
    component = build_root / "src/esphome/components"
    radio_sha = "15446e0bff5179238d118446c0cf4beb9dbca4bb2f4d8ddb39692ef91451620f"
    if hashlib.sha256((component / "cc1101/cc1101.cpp").read_bytes()).hexdigest() != radio_sha:
        raise RuntimeError("RF handoff: unreviewed CC1101 source")
    handoff = Path(__file__).resolve().parents[2] / "include/rf_radio_handoff.h"
    if (build_root / "src/rf_radio_handoff.h").read_bytes() != handoff.read_bytes():
        raise RuntimeError("RF handoff: compiled helper differs from checked source")
    generated = (build_root / "src/main.cpp").read_text()
    if "rf_bridge::prepare_radio_tx" not in generated or "rf_bridge::finish_radio_tx" not in generated:
        raise RuntimeError("RF handoff: generated scheduler lacks guarded transitions")
    if hashlib.sha256((component / "remote_transmitter/remote_transmitter_rmt.cpp").read_bytes()).hexdigest() != UPSTREAM_RMT_SHA256:
        raise RuntimeError("RF startup: unreviewed upstream transmitter source")
    compiled_source = component / "rf_tx_startup/rf_tx_startup.cpp"
    source = Path(__file__).with_name("rf_tx_startup.cpp")
    if compiled_source.read_bytes() != source.read_bytes():
        raise RuntimeError("RF startup: built wrapper differs from the checked source")
    defines = (build_root / "src/esphome/core/defines.h").read_text()
    if not re.search(r"^#define RF_TX_STARTUP_PIN " + str(pin) + r"$", defines, re.MULTILINE):
        raise RuntimeError("RF startup: unexpected protected GPIO")
    if "-Wl,--wrap=rmt_new_tx_channel" not in (build_root / "src/CMakeLists.txt").read_text():
        raise RuntimeError("RF startup: linker wrapping option missing")
    compiler = Path(metadata["c_compiler"])
    objdump = compiler.with_name(compiler.name.removesuffix("gcc") + "objdump")
    elf = build_root / "build" / metadata["app_elf"]
    disassembly = subprocess.check_output([str(objdump), "-d", "-C", str(elf)], text=True)
    caller = function_body(disassembly, "esphome::remote_transmitter::RemoteTransmitterComponent::configure_rmt_()")
    if "<__wrap_rmt_new_tx_channel>" not in caller:
        raise RuntimeError("RF startup: actual transmitter call is not routed through the wrapper")
    wrapper = function_body(disassembly, "__wrap_rmt_new_tx_channel")
    if "<rmt_new_tx_channel>" not in wrapper:
        raise RuntimeError("RF startup: wrapper does not delegate to the real IDF allocator")
    for function in ("gpio_set_level", "gpio_od_enable"):
        if "<" + function + ">" not in wrapper:
            raise RuntimeError("RF startup: wrapper does not call " + function)
    return {"protected_gpio": pin, "cc1101_source_sha256": radio_sha,
            "handoff_sha256": hashlib.sha256(handoff.read_bytes()).hexdigest(), "stock_transmitter_sha256": UPSTREAM_RMT_SHA256,
            "sdk_source_sha256": SDK_SHA256,
            "wrapper_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "elf_sha256": hashlib.sha256(elf.read_bytes()).hexdigest(),
            "linked_call_verified": True, "hardware_tested": False}
