"""Offline update interlocks and real loopback tunnel; never connect to a hub."""
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mc2_update", ROOT / "updates/update.py")
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
                        str(ROOT.parent / "module-carrier/tests/update_session_test.cpp"), "-o", str(cls.binary)], check=True)

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
        data = bytearray(288)
        data[0] = 0xE9
        data[3] = 0x30
        struct.pack_into("<H", data, 12, 13)
        struct.pack_into("<I", data, 32, 0xABCD5432)
        version = update.APP_VERSION.encode()
        data[48:48 + len(version)] = version
        data[80:90] = b"esp_ot_rcp"
        self.image.write_bytes(data)
        self.metadata = {"board": update.BOARD, "board_sku": update.SKU,
                         "hardware_revision": "MC2-C", "antenna": dict(update.ANTENNA),
                         "application_header": update.verify_c6_image(data),
                         "rom_uart_connected": True, "application_flash_offset": 65536,
                         "required_download_strap": {"gpio": 8, "level": 1, "pullup_ohms": 10000,
                                                     "rail": "C6_LOCAL_3V3", "header_pin": "10"},
                         "sdkconfig_verified": {"CONFIG_IDF_TARGET": '"esp32c6"',
                          "CONFIG_OPENTHREAD_UART_RX_PIN": "17", "CONFIG_OPENTHREAD_UART_TX_PIN": "16", "CONFIG_ESPTOOLPY_FLASHSIZE_8MB": "y"},
                         "artifacts": {"esp_ot_rcp.bin": {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}}}
        self.save()
    def save(self): self.report.write_text(json.dumps(self.metadata))
    def test_matching_application(self):
        self.assertEqual(update.checked_image("c6", self.image, self.report)["bytes"], 288)
    def test_tampered_image(self):
        self.image.write_bytes(b"\xe9" + b"b" * 63)
        with self.assertRaises(ValueError): update.checked_image("c6", self.image, self.report)
    def test_h2_image_rejected_even_when_hash_matches(self):
        self.metadata["sdkconfig_verified"]["CONFIG_IDF_TARGET"] = '"esp32h2"'
        self.save()
        with self.assertRaisesRegex(ValueError, "C6 requires"):
            update.checked_image("c6", self.image, self.report)

    def test_missing_required_gpio8_strap_contract_is_rejected(self):
        del self.metadata["required_download_strap"]
        self.save()
        with self.assertRaisesRegex(ValueError, "GPIO8 pull-up"):
            update.checked_image("c6", self.image, self.report)

    def test_obsolete_board_and_unlabelled_reports_are_rejected(self):
        for sku in (None, "TC6-U-01"):
            self.metadata["board_sku"] = sku
            self.save()
            with self.assertRaisesRegex(ValueError, "TC6D-01"):
                update.checked_image("c6", self.image, self.report)

    def test_onboard_antenna_and_wrong_expander_are_rejected(self):
        for key, value in (("mode", "onboard"), ("i2c_address", 0x44),
                           ("sda", 7), ("select_pin", "GPIO0"),
                           ("initialized_before_radio", False)):
            self.metadata["antenna"] = dict(update.ANTENNA) | {key: value}
            self.save()
            with self.assertRaisesRegex(ValueError, "FXL6408"):
                update.checked_image("c6", self.image, self.report)

    def test_renamed_obsolete_image_is_rejected_even_with_matching_hash(self):
        data = bytearray(self.image.read_bytes())
        data[48:80] = b"1" + bytes(31)
        self.image.write_bytes(data)
        self.metadata["artifacts"]["esp_ot_rcp.bin"]["sha256"] = hashlib.sha256(data).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "identify the MC2-C"):
            update.checked_image("c6", self.image, self.report)

    def test_wrong_chip_header_is_rejected_even_with_matching_metadata(self):
        data = bytearray(self.image.read_bytes())
        struct.pack_into("<H", data, 12, 9)
        self.image.write_bytes(data)
        self.metadata["artifacts"]["esp_ot_rcp.bin"]["sha256"] = hashlib.sha256(data).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "target ESP32-C6"):
            update.checked_image("c6", self.image, self.report)

    def test_old_wrong_uart(self):
        self.metadata["sdkconfig_verified"]["CONFIG_OPENTHREAD_UART_RX_PIN"] = "4"
        self.save()
        with self.assertRaises(ValueError): update.checked_image("c6", self.image, self.report)
    def test_no_bootloader_write(self):
        self.metadata["application_flash_offset"] = 0
        self.save()
        with self.assertRaises(ValueError): update.checked_image("c6", self.image, self.report)
    def test_no_implicit_flash(self):
        result = subprocess.run(["python3", str(ROOT / "updates/update.py"), "c6", "--host", "invalid.example",
                                 "--image", str(self.image), "--report", str(self.report)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["execute"])
    def test_commands_are_application_only(self):
        command = update.flash_command("c6", "socket://127.0.0.1:12345", self.image)
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
    def test_external_mg24_label_and_gpio_must_agree(self):
        data = bytes.fromhex("eb17a603") + b"fixture"
        self.image.write_bytes(data)
        self.metadata = {"target": "EFR32MG24B220F1536IM48", "board_sku": "102010690",
            "board_configuration": {"SL_IOSTREAM_USART_VCOM_TX_PIN": "6", "SL_IOSTREAM_USART_VCOM_RX_PIN": "7",
                "SL_IOSTREAM_USART_VCOM_CTS_PIN": "4", "SL_IOSTREAM_USART_VCOM_RTS_PIN": "5",
                "SL_IOSTREAM_USART_VCOM_BAUDRATE": "115200",
                "SL_IOSTREAM_USART_VCOM_FLOW_CONTROL_TYPE": "usartHwFlowControlCtsAndRts"},
            "antenna": {"mode": "external", "rf_path": "RF2/U.FL", "select_gpio": "PB04", "select_level": 1,
                        "enable_gpio": "PB05", "enable_level": 1},
            "files": {"artifacts/mc1-xiao-mg24-external-ncp.gbl": {
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}}}
        self.save()
        self.assertEqual(update.checked_image("mg24", self.image, self.report)["bytes"], len(data))
        self.metadata["antenna"]["mode"] = "onboard"
        self.save()
        with self.assertRaisesRegex(ValueError, "external-antenna"):
            update.checked_image("mg24", self.image, self.report)
        self.metadata["antenna"]["mode"] = "external"
        self.metadata["antenna"]["select_level"] = 0
        self.save()
        with self.assertRaisesRegex(ValueError, "antenna selection"):
            update.checked_image("mg24", self.image, self.report)

    def test_real_mg24_report_and_image(self):
        image = ROOT.parent / "module-carrier/zigbee/artifacts/mc1-xiao-mg24-external-ncp.gbl"
        if not image.is_file(): self.skipTest("Locally generated ignored GBL unavailable")
        self.assertEqual(update.checked_image("mg24", image, ROOT.parent / "module-carrier/zigbee/build-evidence-external.json")["bytes"], image.stat().st_size)

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


class HubConnectionTests(unittest.IsolatedAsyncioTestCase):
    def test_client_binds_to_classic_host_identity_and_expected_mac(self):
        client = Mock()
        with patch.dict(sys.modules, {"aioesphomeapi": SimpleNamespace(APIClient=client)}):
            update.HubAPI("hub.invalid", "test-key", "AA:BB:CC:DD:EE:FF")
        client.assert_called_once_with("hub.invalid", 6053, noise_psk="test-key",
                                      expected_name="mc2-classic-hub", expected_mac="aabbccddeeff")
        self.assertIn("name: mc2-classic-hub", (ROOT / "hub.yaml").read_text())

    async def test_nonpositive_attempts_are_rejected_without_connecting(self):
        with patch.object(update, "HubAPI") as factory:
            for attempts in (0, -1):
                with self.subTest(attempts=attempts), self.assertRaisesRegex(ValueError, "attempts"):
                    await update.connect_hub("test.invalid", "test-key", "00" * 6, attempts)
            factory.assert_not_called()

    async def test_success_returns_the_connected_instance(self):
        api = AsyncMock()
        with patch.object(update, "HubAPI", return_value=api) as factory:
            self.assertIs(await update.connect_hub("test.invalid", "test-key", "00" * 6), api)
        factory.assert_called_once()
        api.connect.assert_awaited_once()
        api.disconnect.assert_not_awaited()

    async def test_retry_closes_failed_client_before_returning_success(self):
        first, second = AsyncMock(), AsyncMock()
        first.connect.side_effect = ConnectionError("not ready")
        with patch.object(update, "HubAPI", side_effect=[first, second]), \
                patch.object(update.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            self.assertIs(await update.connect_hub("test.invalid", "test-key", "00" * 6, 2), second)
        first.disconnect.assert_awaited_once()
        second.disconnect.assert_not_awaited()
        sleep.assert_awaited_once_with(2)

    async def test_exhaustion_preserves_last_error_and_closes_clients(self):
        first, second = AsyncMock(), AsyncMock()
        first.connect.side_effect = ConnectionError("not ready")
        failure = ConnectionError("last attempt failed")
        second.connect.side_effect = failure
        with patch.object(update, "HubAPI", side_effect=[first, second]) as factory, \
                patch.object(update.asyncio, "sleep", new_callable=AsyncMock):
            with self.assertRaises(ConnectionError) as caught:
                await update.connect_hub("test.invalid", "test-key", "00" * 6, 2)
        self.assertIs(caught.exception, failure)
        self.assertEqual(factory.call_count, 2)
        first.disconnect.assert_awaited_once()
        second.disconnect.assert_awaited_once()
