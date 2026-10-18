#!/usr/bin/env python3
"""Plan by default; --execute explicitly programs an MC1 radio over its wired host."""
import argparse
import asyncio
import contextlib
import hashlib
import importlib.metadata
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import sys

HERE = Path(__file__).resolve().parent


def normalized_mac(value):
    value = value.replace(":", "").replace("-", "").lower()
    if not re.fullmatch(r"[0-9a-f]{12}", value):
        raise ValueError("Expected six-byte ESPHome device/base MAC")
    return value


def checked_image(kind, image, report):
    """Require the matching local build report; reject initial/bootloader images."""
    data = image.read_bytes()
    metadata = json.loads(report.read_text())
    if kind == "h2":
        config = metadata.get("sdkconfig_verified", {})
        if metadata.get("rom_uart_connected") is not True or config.get("CONFIG_IDF_TARGET") != '"esp32h2"' or (
                config.get("CONFIG_OPENTHREAD_UART_RX_PIN"), config.get("CONFIG_OPENTHREAD_UART_TX_PIN")) != ("23", "24"):
            raise ValueError("H2 requires a freshly verified ROM-UART23/24 MC1 build")
        if metadata.get("application_flash_offset") != 65536:
            raise ValueError("Only the fixed H2 application partition at0x10000 is supported")
        expected = metadata["artifacts"]["esp_ot_rcp.bin"]
        if not data or data[0] != 0xE9 or len(data) > 1024 * 1024:
            raise ValueError("Invalid/oversized H2 application image")
    else:
        if metadata.get("target") != "EFR32MG24B220F1536IM48" or metadata.get("board_sku") != "102010690":
            raise ValueError("Only the MC1 XIAO MG24 build report is accepted")
        pins = metadata.get("board_configuration", {})
        if any(pins.get(key) != value for key, value in {
            "SL_IOSTREAM_USART_VCOM_TX_PIN": "6", "SL_IOSTREAM_USART_VCOM_RX_PIN": "7",
            "SL_IOSTREAM_USART_VCOM_CTS_PIN": "4", "SL_IOSTREAM_USART_VCOM_RTS_PIN": "5",
            "SL_IOSTREAM_USART_VCOM_BAUDRATE": "115200",
            "SL_IOSTREAM_USART_VCOM_FLOW_CONTROL_TYPE": "usartHwFlowControlCtsAndRts"}.items()):
            raise ValueError("Wrong MG24 UART configuration")
        expected = metadata["files"]["artifacts/mc1-xiao-mg24-ncp.gbl"]
        if data[:4] != bytes.fromhex("eb17a603"):
            raise ValueError("Expected application GBL, not initial HEX or S37")
    digest = hashlib.sha256(data).hexdigest()
    if expected != {"bytes": len(data), "sha256": digest}:
        raise ValueError("Image size/hash does not match the supplied build report")
    return {"bytes": len(data), "sha256": digest}


def check_versions(kind):
    packages = {"aioesphomeapi": "46.3.0", "esptool": "5.3.1"} if kind == "h2" else {
        "universal-silabs-flasher": "1.1.0", "bellows": "1.1.0", "zigpy": "2.3.0"}
    for name, expected in packages.items():
        if importlib.metadata.version(name) != expected:
            raise ValueError(f"Use updates/requirements.txt: expected {name}=={expected}")


def flash_command(kind, host, image, executable=None):
    if kind == "h2":
        return [sys.executable, "-m", "esptool", "--chip", "esp32h2", "--port", host,
                "--baud", "115200", "--before", "no-reset", "--after", "no-reset", "write-flash",
                "--flash-size", "keep", "0x10000", str(image)]
    return [executable or "universal-silabs-flasher", "--device", f"socket://{host}:6638",
            "--probe-methods", "bootloader:115200,ezsp:115200", "flash", "--firmware", str(image)]


async def relay(reader, writer):
    """Backpressure both sides; never accumulate an entire firmware image in RAM."""
    while data := await reader.read(4096):
        writer.write(data)
        await writer.drain()


async def tunnel_session(local_reader, local_writer, host, token, remote_port=6639):
    remote_writer = None
    tasks = []
    try:
        remote_reader, remote_writer = await asyncio.wait_for(asyncio.open_connection(host, remote_port), 10)
        remote_writer.write(token.encode("ascii") + b"\n")
        await remote_writer.drain()
        if await asyncio.wait_for(remote_reader.readexactly(6), 6) != b"READY\n":
            raise ValueError("H2 updater did not authenticate")
        tasks = [asyncio.create_task(relay(local_reader, remote_writer)), asyncio.create_task(relay(remote_reader, local_writer))]
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for writer in (remote_writer, local_writer):
            if writer:
                writer.close()
                with contextlib.suppress(Exception):
                    await writer.wait_closed()


class HubAPI:
    def __init__(self, host, psk, expected_mac):
        from aioesphomeapi import APIClient
        self.client = APIClient(host, 6053, noise_psk=psk, expected_name="module-carrier-hub", expected_mac=normalized_mac(expected_mac))
        self.services, self.states = {}, {}

    async def connect(self):
        await asyncio.wait_for(self.client.connect(login=True), 15)
        entities, services = await self.client.list_entities_services()
        self.services = {s.name: s for s in services}
        names = {e.key: e.name for e in entities}
        self.client.subscribe_states(lambda state: self.states.update({names.get(state.key): getattr(state, "state", None)}))

    async def call(self, name, **kwargs):
        await self.client.execute_service(self.services[name], kwargs)

    async def wait(self, predicate, timeout=20):
        async with asyncio.timeout(timeout):
            while not predicate(self.states):
                await asyncio.sleep(0.2)

    async def disconnect(self):
        with contextlib.suppress(Exception):
            await self.client.disconnect()


async def connect_hub(host, psk, mac, attempts=1):
    for attempt in range(attempts):
        api = HubAPI(host, psk, mac)
        try:
            await api.connect()
            return api
        except Exception:
            await api.disconnect()
            if attempt + 1 == attempts:
                raise
            await asyncio.sleep(2)
    raise ValueError("attempts must be at least 1")


async def execute_h2(args):
    psk = os.environ.get("MC1_API_KEY")
    if not psk:
        raise ValueError("Set MC1_API_KEY to the existing ESPHome encryption key; never put it in a command line")
    api = await connect_hub(args.host, psk, args.mac)
    try:
        await api.wait(lambda s: "Thread State" in s and "Thread Guard Durable" in s)
        if api.states["Thread State"] != "maintenance" or not api.states["Thread Guard Durable"]:
            print("Persisting Thread maintenance and restarting the complete hub once...", flush=True)
            await api.call("pause_thread_for_h2_service")
            await api.disconnect()
            await asyncio.sleep(3)
            api = await connect_hub(args.host, psk, args.mac, attempts=20)
        await api.wait(lambda s: s.get("Thread State") == "maintenance" and s.get("Thread Guard Durable") is True)
        token = secrets.token_hex(16)
        await api.call("arm_h2_uart_update", token=token)
        await api.wait(lambda s: s.get("H2 UART Update State") == "waiting_authenticated_client")
        claimed = False
        session_task = None
        async def accept(reader, writer):
            nonlocal claimed, session_task
            if claimed:
                writer.close()
                await writer.wait_closed()
                return
            claimed = True
            session_task = asyncio.current_task()
            await tunnel_session(reader, writer, args.host, token)
        server = await asyncio.start_server(accept, "127.0.0.1", 0)
        process = None
        try:
            port = server.sockets[0].getsockname()[1]
            command = flash_command("h2", f"socket://127.0.0.1:{port}", args.image)
            process = await asyncio.create_subprocess_exec(*command)
            result = await asyncio.wait_for(process.wait(), 590)
            if result:
                raise RuntimeError(f"esptool failed({result}); Thread remains in maintenance")
        finally:
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            server.close()
            await server.wait_closed()
            if session_task:
                session_task.cancel()
                await asyncio.gather(session_task, return_exceptions=True)
            await api.call("cancel_h2_uart_update")
        await api.wait(lambda s: s.get("H2 UART Update State") == "closed")
        print("esptool verified application bytes. Resuming Thread with one explicit hub restart.", flush=True)
        await api.call("retry_quarantined_thread")
        await api.disconnect()
        await asyncio.sleep(3)
        api = await connect_hub(args.host, psk, args.mac, attempts=20)
        await api.wait(lambda s: s.get("Thread State") in ("ready_uncommissioned_or_disabled", "ready_detached", "routing", "quarantined"), 45)
        if api.states["Thread State"] == "quarantined":
            raise RuntimeError("New RCP failed Thread preflight/startup; inspect Thread Last Fault, re-enter maintenance and restore a known-good build")
        print("RCP passed host startup: " + api.states["Thread State"])
    finally:
        await api.disconnect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("h2", "mg24"))
    parser.add_argument("--host", required=True, help="MC1 IPv4 address or DNS name")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path, help="Matching verify_h2 output or MC1 MG24 build-report.json")
    parser.add_argument("--mac", help="Expected ESPHome device/base MAC (may differ from Ethernet MAC); required when executing H2")
    parser.add_argument("--execute", action="store_true", help="Actually program the selected radio; default is offline plan")
    parser.add_argument("--coordinator-stopped", action="store_true", help="Affirm ZHA/Zigbee2MQTT is stopped before MG24 execution")
    args = parser.parse_args()
    if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-" for c in args.host):
        parser.error("Use an IPv4 address or DNS name, not a URL/port")
    args.image = args.image.resolve()
    verified = checked_image(args.kind, args.image, args.report)
    print(json.dumps({"radio": args.kind, "host": args.host, "image": str(args.image), "verified": verified,
                      "execute": args.execute, "scope": "application only; no bootloader, partition table, full-chip erase, or eFuse write"}, indent=2))
    if not args.execute:
        return
    check_versions(args.kind)
    if args.kind == "h2":
        if not args.mac:
            parser.error("--mac is required for H2 execution to bind the encrypted API to this hub")
        asyncio.run(execute_h2(args))
    else:
        if not args.coordinator_stopped:
            parser.error("Stop ZHA/Zigbee2MQTT, then affirm --coordinator-stopped")
        executable = shutil.which("universal-silabs-flasher")
        if not executable:
            parser.error("Run inside the updates requirements virtual environment")
        import subprocess
        subprocess.run(flash_command("mg24", args.host, args.image, executable), check=True, timeout=600)
        print("GBL upload completed; restart the coordinator owner and verify its network/devices.")


if __name__ == "__main__":
    main()
