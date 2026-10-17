#!/usr/bin/env python3
"""Validate in an isolated directory with disposable credentials; never flash."""
from __future__ import annotations

import argparse
import base64
import importlib.util
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile


def migration_fixture(snapshot: Path, repository: Path, key: str) -> Path:
    """Exercise the actual importer and build its private result with fake data."""
    spec = importlib.util.spec_from_file_location("rf_migration", repository / "tools/migrate_rf.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the RF migration tool")
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    original = snapshot / "upstream-fixture"
    original.mkdir()
    (original / "secrets.yaml").write_text(
        f'old_api_key: "{key}"\nold_ota: "{secrets.token_hex(24)}"\n'
        'old_broker: "192.0.2.1"\nold_user: "validation"\n'
        f'old_password: "{secrets.token_hex(24)}"\n', encoding="utf-8",
    )
    source = """substitutions:
  node_name: rf-migration-validation
  rf_source: validation_rf
  rf_received_topic: validation/rf/received
  rf_raw_topic: validation/rf/received/raw
  rf_transmit_result_topic: validation/rf/transmit/result
  rm433_button_1_code: "0x000001"
esphome:
  name: ${node_name}
  friendly_name: RF Migration Validation
  comment: Synthetic legacy RF fixture
  project:
    name: validation.rf_bridge
    version: "1.0.0"
  min_version: "2026.9.1"
  compile_process_limit: 2
esp8266:
  board: esp12e
packages:
  rf_airbridge: !include packages/rf-airbridge.yaml
api:
  encryption:
    key: !secret old_api_key
ota:
  - platform: esphome
    password: !secret old_ota
mqtt:
  broker: !secret old_broker
  username: !secret old_user
  password: !secret old_password
remote_receiver:
  filter: 250us
binary_sensor:
"""
    for index in range(1, 16):
        source += f'''  - platform: remote_receiver
    name: "Fixture RF sensor {index}"
    id: fixture_rf_sensor_{index}
    rc_switch_raw:
      code: "{index:024b}"
      protocol: 1
    filters:
      - delayed_off: 100ms
'''
    (original / "device.yaml").write_text(source, encoding="utf-8")
    output = snapshot / "private/regression"
    report = importer.migrate(original / "device.yaml", original / "secrets.yaml", output, repo_root=snapshot)
    if report["binary_sensor_count"] != 15 or not report["receiver_filter_normalized_to_150us"]:
        raise RuntimeError("Migration fixture failed to preserve its expected configuration")
    return output / "device.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true", help="also compile and discard the test binary")
    parser.add_argument("--esphome", default="esphome", help="ESPHome executable")
    parser.add_argument("--config", choices=("hub-s3-eth.yaml", "rf-ethernet.yaml"), default="hub-s3-eth.yaml")
    parser.add_argument("--migration-fixture", action="store_true", help="import and validate 15 synthetic legacy RF sensors")
    args = parser.parse_args()
    if args.migration_fixture and args.config != "rf-ethernet.yaml":
        parser.error("--migration-fixture requires --config rf-ethernet.yaml")
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="ha-radio-hub-validation-") as temporary:
        snapshot = Path(temporary)
        target = snapshot / "firmware"
        target.mkdir()
        shutil.copy(root / args.config, target)
        for directory in ("packages", "include", "components"):
            if (root / directory).exists():
                shutil.copytree(root / directory, target / directory)
        key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        (target / "secrets.yaml").write_text(
            f'api_encryption_key: "{key}"\nota_password: "{secrets.token_hex(24)}"\n'
            'mqtt_broker: "192.0.2.1"\nmqtt_username: "validation"\n'
            f'mqtt_password: "{secrets.token_hex(24)}"\n',
            encoding="utf-8",
        )
        config = (migration_fixture(snapshot, root.parent, key) if args.migration_fixture
                  else target / args.config)
        # `config` prints expanded secrets in some versions. Suppress stdout;
        # validation diagnostics remain on stderr and credentials are disposable.
        result = subprocess.run([args.esphome, "config", str(config)], text=True, stdout=subprocess.PIPE)
        if result.returncode:
            # Every value in this snapshot is generated and disposable.
            print(result.stdout)
            result.check_returncode()
        label = "migrated 15-sensor fixture" if args.migration_fixture else args.config
        print(f"ESPHome schema validation passed: {label} (isolated disposable secrets).", flush=True)
        if args.compile:
            subprocess.run(
                [args.esphome, "compile", str(config)], check=True,
            )
            print("ESPHome compile passed. Disposable test binary was not flashed and will be deleted.")


if __name__ == "__main__":
    main()
