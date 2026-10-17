#!/usr/bin/env python3
"""Render local configuration only. Does not install, start, or flash anything."""
from __future__ import annotations

import argparse
from ipaddress import IPv4Address
import os
from pathlib import Path
import re
import tempfile


def ipv4(value: str) -> str:
    ip = IPv4Address(value)
    if ip.is_unspecified or ip.is_multicast or ip.is_loopback:
        raise argparse.ArgumentTypeError("Use the specific LAN IPv4 address, not wildcard/loopback/multicast")
    return str(ip)


def serial_device(value: str) -> str:
    if (not re.fullmatch(r"/dev/serial/by-(?:id|path)/[A-Za-z0-9_.:+-]+", value)
            or value.rsplit("/", 1)[-1] in {".", ".."}):
        raise argparse.ArgumentTypeError("Use a stable /dev/serial/by-id/ or by-path/ symlink")
    return value


def write_private(path: Path, text: str) -> None:
    """Replace an output atomically, retaining mode 0600 on repeated renders."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".render-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def interface(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,15}", value):
        raise argparse.ArgumentTypeError("Unsupported interface name; use the Ethernet LAN interface")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hub-ip", required=True, type=ipv4)
    parser.add_argument("--ha-ip", required=True, type=ipv4, help="HA source IPv4 seen by this host")
    parser.add_argument("--interface", default="eth0", type=interface)
    parser.add_argument("--thread-device", required=True, type=serial_device)
    parser.add_argument("--zigbee-device", required=True, type=serial_device)
    parser.add_argument("--zigbee-baud", type=int, choices=(115200, 230400, 460800), default=115200)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "runtime")
    args = parser.parse_args()
    if args.thread_device == args.zigbee_device:
        parser.error("Thread and Zigbee must be different physical radios")
    args.output = args.output.expanduser().resolve()
    config_path = str(args.output / "ser2net.yaml")
    if any(char in config_path for char in "\r\n\\$"):
        parser.error("Output path cannot contain newline, backslash or dollar characters")
    for name in ("hub.env", "ser2net.yaml", "60-ha-radio-hub.conf"):
        target = args.output / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            parser.error(f"Refusing non-regular output: {target}")
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=True)
    # Compose single quotes preserve spaces and literal apostrophes in paths.
    quoted_config = "'" + config_path.replace("'", "\\'") + "'"
    write_private(args.output / "hub.env",
        f"HUB_LAN_IP={args.hub_ip}\nHA_IP={args.ha_ip}\nINFRA_IF={args.interface}\n"
        f"THREAD_SERIAL_DEVICE={args.thread_device}\nZIGBEE_SERIAL_DEVICE={args.zigbee_device}\n"
        f"SER2NET_CONFIG={quoted_config}\n",
    )
    # One connection, no banner, transparent TCP and explicit source allow-list.
    write_private(args.output / "ser2net.yaml",
        "%YAML 1.1\n---\nconnection: &zigbee\n"
        f"  accepter: tcp,{args.hub_ip},6638\n"
        "  enable: on\n  timeout: 0\n"
        f"  connector: serialdev,/dev/zigbee,{args.zigbee_baud}n81,local,rtscts\n"
        f'  options:\n    remaddr: "{args.ha_ip},0"\n'
        "    max-connections: 1\n    kickolduser: false\n",
    )
    write_private(args.output / "60-ha-radio-hub.conf",
        "# Apply on the dedicated Linux hub, not the HA server or workstation.\n"
        "net.ipv6.conf.all.forwarding = 1\nnet.ipv4.ip_forward = 1\n"
        f"net.ipv6.conf.{args.interface}.accept_ra = 2\n"
        f"net.ipv6.conf.{args.interface}.accept_ra_rt_info_max_plen = 64\n",
    )
    print(f"Wrote local files to {args.output}. No services started.")


if __name__ == "__main__":
    main()
