"""Offline update interlocks and real loopback tunnel; never connect to a hub."""
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mc1_update", ROOT / "updates/update.py")
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)

class UpdatePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="update-policy-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / "policy"
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
        subprocess.run([shutil.which("c++"), *flags, "-I", str(ROOT.parent / "low-power/components/low_power_otbr"),
                        str(ROOT / "tests/update_session_test.cpp"), "-o", str(cls.binary)], check=True)

for case in ("token_validation", "token_comparison", "maintenance_interlock", "deadline_wrap"):
    def test(self, case=case):
        subprocess.run([str(self.binary), case], check=True)
    setattr(UpdatePolicyTests, "test_" + case, test)

class UpdateImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.image = Path(self.tmp.name) / "app.bin"
        self.report = Path(self.tmp.name) / "report.json"
        data = b"\xe9" + b"a" * 63
        self.image.write_bytes(data)
        self.metadata = {"rom_uart_connected": True, "application_flash_offset": 65536,
                         "sdkconfig_verified": {"CONFIG_IDF_TARGET": '"esp32h2"',
                          "CONFIG_OPENTHREAD_UART_RX_PIN": "23", "CONFIG_OPENTHREAD_UART_TX_PIN": "24"},
                         "artifacts": {"esp_ot_rcp.bin": {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}}}
        self.save()
    def save(self): self.report.write_text(json.dumps(self.metadata))
    def test_matching_application(self):
        self.assertEqual(update.checked_image("h2", self.image, self.report)["bytes"], 64)
    def test_tampered_image(self):
        self.image.write_bytes(b"\xe9" + b"b" * 63)
        with self.assertRaises(ValueError): update.checked_image("h2", self.image, self.report)
    def test_old_wrong_uart(self):
        self.metadata["sdkconfig_verified"]["CONFIG_OPENTHREAD_UART_RX_PIN"] = "4"
        self.save()
        with self.assertRaises(ValueError): update.checked_image("h2", self.image, self.report)
    def test_no_bootloader_write(self):
        self.metadata["application_flash_offset"] = 0
        self.save()
        with self.assertRaises(ValueError): update.checked_image("h2", self.image, self.report)
    def test_no_implicit_flash(self):
        result = subprocess.run(["python3", str(ROOT / "updates/update.py"), "h2", "--host", "invalid.example",
                                 "--image", str(self.image), "--report", str(self.report)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["execute"])
    def test_commands_are_application_only(self):
        command = update.flash_command("h2", "socket://127.0.0.1:12345", self.image)
        self.assertIn("0x10000", command)
        self.assertEqual(command.count("no-reset"), 2)
        self.assertNotIn("erase-flash", command)
        command = update.flash_command("mg24", "hub.example", self.image)
        self.assertIn("bootloader:115200,ezsp:115200", command)
        self.assertNotIn("--bootloader-reset", command)
        self.assertNotIn("--profile", command)
    def test_api_mac_normalization(self):
        self.assertEqual(update.normalized_mac("AA:BB:CC:DD:EE:FF"), "aabbccddeeff")
        self.assertEqual(update.normalized_mac("AA-BB-CC-DD-EE-FF"), "aabbccddeeff")
        for value in ("", "aa:bb:cc:dd:ee", "aa:bb:cc:dd:ee:gg"):
            with self.assertRaises(ValueError): update.normalized_mac(value)
    def test_real_mg24_report_and_image(self):
        image = ROOT / "zigbee/artifacts/mc1-xiao-mg24-ncp.gbl"
        if not image.is_file(): self.skipTest("Locally generated ignored GBL unavailable")
        self.assertEqual(update.checked_image("mg24", image, ROOT / "zigbee/build-evidence.json")["bytes"], image.stat().st_size)

class UpdateTunnelTests(unittest.IsolatedAsyncioTestCase):
    async def test_binary_roundtrip_with_fragmented_ready(self):
        token = "0123456789abcdef" * 2
        payload = bytes(range(256)) * 257
        remote_done = asyncio.Event()
        async def remote(reader, writer):
            self.assertEqual(await reader.readexactly(33), token.encode() + b"\n")
            writer.write(b"RE"); await writer.drain(); await asyncio.sleep(0.001)
            writer.write(b"ADY\n"); await writer.drain()
            while data := await reader.read(773):
                writer.write(data); await writer.drain()
            writer.close(); await writer.wait_closed(); remote_done.set()
        remote_server = await asyncio.start_server(remote, "127.0.0.1", 0)
        port = remote_server.sockets[0].getsockname()[1]
        async def local(reader, writer):
            await update.tunnel_session(reader, writer, "127.0.0.1", token, port)
        local_server = await asyncio.start_server(local, "127.0.0.1", 0)
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", local_server.sockets[0].getsockname()[1])
            writer.write(payload); await writer.drain()
            self.assertEqual(await asyncio.wait_for(reader.readexactly(len(payload)), 5), payload)
            writer.close(); await writer.wait_closed()
            await asyncio.wait_for(remote_done.wait(), 3)
        finally:
            local_server.close(); remote_server.close()
            await local_server.wait_closed(); await remote_server.wait_closed()
    async def test_bad_handshake_stops_before_binary_transfer(self):
        token = "a" * 32
        failed = asyncio.Future()
        async def remote(reader, writer):
            await reader.readexactly(33)
            writer.write(b"DENIED"); await writer.drain()
            self.assertEqual(await reader.read(), b"")
            writer.close(); await writer.wait_closed()
        remote_server = await asyncio.start_server(remote, "127.0.0.1", 0)
        async def local(reader, writer):
            try:
                await update.tunnel_session(reader, writer, "127.0.0.1", token, remote_server.sockets[0].getsockname()[1])
            except ValueError:
                failed.set_result(True)
        local_server = await asyncio.start_server(local, "127.0.0.1", 0)
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", local_server.sockets[0].getsockname()[1])
            writer.write(b"DO-NOT-FLASH"); await writer.drain()
            self.assertTrue(await asyncio.wait_for(failed, 3))
            self.assertEqual(await reader.read(), b"")
            writer.close(); await writer.wait_closed()
        finally:
            local_server.close(); remote_server.close()
            await local_server.wait_closed(); await remote_server.wait_closed()
