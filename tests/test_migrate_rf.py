"""Offline migration regression tests use synthetic, deliberately distinct secrets."""

import importlib.util
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("migrate_rf", ROOT / "tools/migrate_rf.py")
MIGRATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATE)

SOURCE = """substitutions:
  rf_source: house_rf
  rf_received_topic: house/rf/received
  rm433_button_1_code: "0x123451"
esphome:
  name: rf
  friendly_name: Living RF
esp8266:
  board: nodemcuv2
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
api:
  encryption:
    key: !secret old_api
ota:
  - platform: esphome
    password: !secret old_ota
mqtt:
  broker: !secret old_broker
  username: !secret old_user
  password: !secret old_password
  client_id: retained-client-identity
  discovery_prefix: homeassistant
packages:
  rf_airbridge: !include packages/rf-airbridge.yaml
binary_sensor:
  - platform: remote_receiver
    id: hall_motion
    name: Hall Motion
    rc_switch_raw:
      code: '000000010010001101000101'
      protocol: 1
    filters:
      - delayed_off: 30s
    on_press:
      - logger.log: "Motion observed"
"""
SECRETS = """old_api: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
old_ota: synthetic-ota-secret
old_broker: broker.example.invalid
old_user: synthetic-rf-user
old_password: synthetic-mqtt-secret
wifi_ssid: unused-private-wifi
wifi_password: unused-private-password
"""


class TaggedLoader(yaml.SafeLoader):
    pass


TaggedLoader.add_multi_constructor("!", lambda loader, tag, node: (tag, loader.construct_scalar(node)))


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rf-import-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "old.yaml"
        self.secrets = self.directory / "old-secrets.yaml"
        self.output = self.directory / "new-private"
        self.source.write_text(SOURCE)
        self.secrets.write_text(SECRETS)

    def migrate(self):
        return MIGRATE.migrate(self.source, self.secrets, self.output)

    def assert_rejected_without_output(self, text):
        self.source.write_text(text)
        with self.assertRaises(MIGRATE.MigrationError):
            self.migrate()
        self.assertFalse(self.output.exists())

    def test_preserves_identity_entities_callbacks_and_exact_binary_width(self):
        before = yaml.load(SOURCE, Loader=TaggedLoader)
        report = self.migrate()
        after = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
        self.assertEqual(after["binary_sensor"], before["binary_sensor"])
        self.assertEqual(after["binary_sensor"][0]["rc_switch_raw"]["code"], "000000010010001101000101")
        self.assertEqual(after["substitutions"]["rf_node_name"], "rf")
        self.assertEqual(after["substitutions"]["rf_friendly_name"], "Living RF")
        for key, value in before["substitutions"].items():
            self.assertEqual(after["substitutions"][key], value)
        self.assertEqual(after["mqtt"]["client_id"], "retained-client-identity")
        self.assertNotIn("wifi", after)
        self.assertNotIn("esp8266", after)
        tag, include = after["packages"]["rf_ethernet"]
        self.assertEqual(tag, "include")
        self.assertEqual((self.output / include).resolve(),
                         ROOT / "firmware/packages/rf-ethernet-base.yaml")
        self.assertEqual(report["binary_sensor_count"], 1)
        self.assertFalse(report["live_systems_modified"])
        self.assertFalse(report["ha_registry_identity_preserved"])

    def test_migration_base_keeps_secret_lookups_in_private_wrapper(self):
        # ESPHome resolves !secret relative to the included file. An included
        # public board package must not look for credentials beside itself.
        for name in ("rf-ethernet-base.yaml", "rf-airbridge.yaml"):
            text = (ROOT / "firmware/packages" / name).read_text()
            node = yaml.compose(text)
            def tags(value):
                yield value.tag
                if isinstance(value, yaml.MappingNode):
                    for key, child in value.value:
                        yield from tags(key)
                        yield from tags(child)
                elif isinstance(value, yaml.SequenceNode):
                    for child in value.value:
                        yield from tags(child)
            self.assertNotIn("!secret", set(tags(node)))

    def test_only_referenced_secrets_exported_to_private_files(self):
        self.migrate()
        output = yaml.safe_load((self.output / "secrets.yaml").read_text())
        self.assertEqual(output, {
            "api_encryption_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            "ota_password": "synthetic-ota-secret", "mqtt_broker": "broker.example.invalid",
            "mqtt_username": "synthetic-rf-user", "mqtt_password": "synthetic-mqtt-secret"})
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        for name in ("device.yaml", "secrets.yaml", "report.json"):
            self.assertEqual(stat.S_IMODE((self.output / name).stat().st_mode), 0o600)
        public_candidate = (self.output / "device.yaml").read_text() + (self.output / "report.json").read_text()
        for secret in output.values():
            self.assertNotIn(secret, public_candidate)
        self.assertNotIn("unused-private-password", (self.output / "secrets.yaml").read_text())

    def test_referenced_rf_code_remains_secret_in_device_file(self):
        self.source.write_text(SOURCE.replace("'000000010010001101000101'", "!secret motion_code"))
        self.secrets.write_text(SECRETS + "motion_code: '000000010010001101000101'\n")
        self.migrate()
        device = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
        secret = yaml.safe_load((self.output / "secrets.yaml").read_text())
        self.assertEqual(device["binary_sensor"][0]["rc_switch_raw"]["code"], ("secret", "motion_code"))
        self.assertEqual(secret["motion_code"], "000000010010001101000101")

    def test_existing_output_is_not_modified(self):
        self.output.mkdir()
        sentinel = self.output / "keep"
        sentinel.write_bytes(b"untouched\x00")
        with self.assertRaises(MIGRATE.MigrationError):
            self.migrate()
        self.assertEqual(list(self.output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"untouched\x00")

    def test_missing_secret_and_conflicting_ids_fail_before_writing(self):
        self.secrets.write_text(SECRETS.replace("old_ota: synthetic-ota-secret\n", ""))
        with self.assertRaises(MIGRATE.MigrationError):
            self.migrate()
        self.assertFalse(self.output.exists())
        self.secrets.write_text(SECRETS)
        self.assert_rejected_without_output(SOURCE.replace("id: hall_motion", "id: rf_transmitter"))

    def test_unsupported_sources_do_not_silently_drop_behavior(self):
        cases = [
            SOURCE + "script:\n  - id: old_custom_worker\n    then: []\n",
            SOURCE.replace("api:\n", "api:\n  actions: []\n"),
            SOURCE + "remote_receiver:\n  on_raw:\n    then: []\n",
            SOURCE.replace("binary_sensor:\n", "binary_sensor: !include old-sensors.yaml\nignored:\n"),
            SOURCE.replace("name: rf\n", "name: rf\n  name: collision\n"),
            SOURCE + "unknown: !!python/object/apply:os.system ['echo never-run']\n",
            SOURCE.replace("substitutions:\n", "substitutions: &cycle\n  recursive: *cycle\n"),
        ]
        for text in cases:
            with self.subTest(source=text[-60:]):
                self.assert_rejected_without_output(text)

    def test_repo_output_is_restricted_to_private_tree(self):
        fake_repo = self.directory / "repo"
        fake_repo.mkdir()
        with self.assertRaises(MIGRATE.MigrationError):
            MIGRATE.migrate(self.source, self.secrets, fake_repo / "firmware" / "device", fake_repo)
        self.assertFalse((fake_repo / "firmware").exists())

    def test_rejects_unreviewed_package_replacement(self):
        for replacement in ("{script: []}", "!include another-radio.yaml", "github://example/unreviewed.yaml"):
            with self.subTest(package=replacement):
                self.assert_rejected_without_output(SOURCE.replace(
                    "!include packages/rf-airbridge.yaml", replacement))

    def test_normalizes_filter_that_would_remove_rm433_short_pulses(self):
        for old, expected in (("250us", "150us"), ("100us", "100us"), ("170us", "170us")):
            with self.subTest(filter=old):
                self.output = self.directory / ("new-filter-" + old)
                self.source.write_text(SOURCE + f"remote_receiver:\n  filter: {old}\n")
                self.migrate()
                device = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
                self.assertEqual(device["remote_receiver"]["filter"], expected)

    def test_resolves_original_identity_substitutions_without_self_reference(self):
        self.source.write_text(SOURCE.replace("  rf_source: house_rf", "  rf_source: house_rf\n  rf_node_name: rf\n  old_friendly: Living RF")
                               .replace("\n  name: rf\n", "\n  name: ${rf_node_name}\n")
                               .replace("friendly_name: Living RF", "friendly_name: ${old_friendly}"))
        self.migrate()
        device = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
        self.assertEqual(device["substitutions"]["rf_node_name"], "rf")
        self.assertEqual(device["substitutions"]["rf_friendly_name"], "Living RF")

    def test_rejects_lifecycle_in_discarded_blocks_and_reserved_fault_id(self):
        for text in (SOURCE.replace("wifi:\n", "wifi:\n  on_connect:\n    - logger.log: important\n"),
                     SOURCE + "logger:\n  on_message:\n    then: []\n",
                     SOURCE.replace("id: hall_motion", "id: rf_tx_fault")):
            with self.subTest(text=text[-60:]):
                self.assert_rejected_without_output(text)

    def test_plaintext_legacy_api_and_passwordless_ota_are_not_invented(self):
        legacy = SOURCE.replace("api:\n  encryption:\n    key: !secret old_api\n", "api:\n")
        legacy = legacy.replace("    password: !secret old_ota\n", "")
        legacy += """web_server:
  port: 8080
cc1101:
  cs_pin: GPIO15
  frequency: 433.92MHz
  max_dvga_gain: 6
remote_receiver:
  pin:
    number: GPIO4
    allow_other_uses: true
  filter: 250us
"""
        self.source.write_text(legacy)
        report = self.migrate()
        after = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
        credentials = yaml.safe_load((self.output / "secrets.yaml").read_text())
        self.assertEqual(after["api"], {})
        self.assertEqual(after["ota"], [{"platform": "esphome"}])
        self.assertEqual(set(credentials), {"mqtt_broker", "mqtt_username", "mqtt_password"})
        self.assertEqual(after["web_server"], {"port": 8080})
        self.assertEqual(after["cc1101"], {"frequency": "433.92MHz", "max_dvga_gain": 6})
        self.assertEqual(after["remote_receiver"], {"filter": "150us"})
        self.assertFalse(report["api_encryption_preserved"])
        self.assertFalse(report["ota_password_preserved"])
        self.assertTrue(report["web_server_preserved"])
        self.assertIn("remote_receiver.pin", report["replaced_hardware_blocks"])
        self.assertIn("cc1101.cs_pin", report["replaced_hardware_blocks"])

    def test_unknown_radio_profile_and_pin_callbacks_require_review(self):
        for suffix in ("cc1101:\n  frequency: 868MHz\n",
                       "cc1101:\n  cs_pin: !lambda return private_pin();\n",
                       "remote_receiver:\n  pin: !lambda return private_pin();\n",
                       "web_server:\n  on_request: []\n"):
            with self.subTest(case=suffix.splitlines()[0]):
                self.assert_rejected_without_output(SOURCE + suffix)

    def test_missing_api_block_is_not_implicitly_enabled(self):
        self.assert_rejected_without_output(SOURCE.replace("api:\n  encryption:\n    key: !secret old_api\n", ""))

    def test_rejects_canonical_secret_collision_in_preserved_fields(self):
        cases = [SOURCE + "web_server:\n  auth:\n    username: test\n    password: !secret mqtt_password\n",
                 SOURCE.replace("'000000010010001101000101'", "!secret mqtt_password")]
        for source in cases:
            with self.subTest(field="web" if "web_server:" in source else "rf"):
                self.secrets.write_text(SECRETS + "mqtt_password: '000000010010001101000101'\n")
                self.assert_rejected_without_output(source)

    def test_equal_canonical_secret_alias_is_preserved(self):
        self.source.write_text(SOURCE + "web_server:\n  auth:\n    username: test\n    password: !secret mqtt_password\n")
        self.secrets.write_text(SECRETS + "mqtt_password: synthetic-mqtt-secret\n")
        self.migrate()
        after = yaml.load((self.output / "device.yaml").read_text(), Loader=TaggedLoader)
        values = yaml.safe_load((self.output / "secrets.yaml").read_text())
        self.assertEqual(after["web_server"]["auth"]["password"], ("secret", "mqtt_password"))
        self.assertEqual(values["mqtt_password"], "synthetic-mqtt-secret")

    def test_unused_canonical_secret_does_not_block_remapping(self):
        self.secrets.write_text(SECRETS + "mqtt_password: unused-distinct-secret\n")
        self.migrate()
        values = yaml.safe_load((self.output / "secrets.yaml").read_text())
        self.assertEqual(values["mqtt_password"], "synthetic-mqtt-secret")

    def test_cli_output_never_contains_values_on_success_or_parse_error(self):
        args = [sys.executable, str(ROOT / "tools/migrate_rf.py"), "--source", str(self.source),
                "--secrets", str(self.secrets), "--output", str(self.output)]
        success = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.source.write_text("private: [synthetic-parse-secret\n")
        args[-1] = str(self.directory / "failed-private")
        failure = subprocess.run(args, capture_output=True, text=True)
        self.assertNotEqual(failure.returncode, 0)
        combined = success.stdout + success.stderr + failure.stdout + failure.stderr
        for value in ("synthetic-parse-secret", "synthetic-mqtt-secret", "synthetic-ota-secret",
                      "unused-private-password"):
            self.assertNotIn(value, combined)
        self.assertFalse((self.directory / "failed-private").exists())


if __name__ == "__main__":
    unittest.main()
