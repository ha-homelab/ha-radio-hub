#!/usr/bin/env python3
"""Build the complete low-power profile with disposable secrets, without flashing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from prepare import prepare


REQUIRED_SDKCONFIG = {
    "CONFIG_OPENTHREAD_FTD": "y",
    "CONFIG_OPENTHREAD_COMMISSIONER": "y",
    "CONFIG_OPENTHREAD_JOINER": "y",
    "CONFIG_VFS_SUPPORT_IO": "y",
    "CONFIG_VFS_SUPPORT_DIR": "y",
    "CONFIG_VFS_SUPPORT_SELECT": "y",
    "CONFIG_OPENTHREAD_RADIO_SPINEL_UART": "y",
    "CONFIG_OPENTHREAD_BORDER_ROUTER": "y",
    "CONFIG_OPENTHREAD_BORDER_AGENT_ENABLE": "y",
    "CONFIG_LWIP_IPV6": "y",
    "CONFIG_LWIP_IPV6_FORWARD": "y",
    "CONFIG_LWIP_IPV6_NUM_ADDRESSES": "12",
    "CONFIG_LWIP_HOOK_IP6_INPUT_CUSTOM": "y",
    "CONFIG_LWIP_HOOK_IP6_SELECT_SRC_ADDR_CUSTOM": "y",
    "CONFIG_LWIP_FORCE_ROUTER_FORWARDING": "y",
    "CONFIG_MDNS_MULTIPLE_INSTANCE": "y",
    "CONFIG_BT_BLUEDROID_ENABLED": "y",
    "CONFIG_SPIRAM_MODE_OCT": "y",
    "CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ": "160",
}


def verify_build(profile: Path) -> None:
    root = profile.parent / ".esphome/build/low-power-hub-proof"
    config = dict(line.split("=", 1) for line in
                  (root / "sdkconfig.low-power-hub-proof").read_text().splitlines()
                  if line.startswith("CONFIG_") and "=" in line)
    for key, value in REQUIRED_SDKCONFIG.items():
        if config.get(key) != value:
            raise RuntimeError(f"Required build option was not applied: {key}={value}")
    artifacts = {}
    for name in ("low-power-hub-proof.bin", "firmware.factory.bin", "firmware.ota.bin"):
        path = root / "build" / name
        data = path.read_bytes()
        artifacts[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    report = {"compiled": True, "hardware_tested": False,
              "sdkconfig_verified": REQUIRED_SDKCONFIG, "artifacts": artifacts}
    (profile.parent / "build-result.json").write_text(json.dumps(report, indent=2) + "\n")


def run(esphome: str, compile_firmware: bool, output: Path, upstream: Path | None) -> None:
    profile = prepare(output, upstream)
    subprocess.run([esphome, "compile" if compile_firmware else "config", str(profile)], check=True)
    if compile_firmware:
        verify_build(profile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--esphome", default="esphome")
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--output", type=Path, help="New directory; retain build/artifacts here")
    parser.add_argument("--upstream", type=Path, help="Existing pinned upstream clone")
    args = parser.parse_args()
    if args.output:
        run(args.esphome, args.compile, args.output.resolve(), args.upstream)
    else:
        with tempfile.TemporaryDirectory(prefix="ha-radio-hub-low-power-") as temporary:
            run(args.esphome, args.compile, Path(temporary) / "snapshot", args.upstream)
