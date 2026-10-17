#!/usr/bin/env python3
"""Prepare a disposable, pinned single-Ethernet hub build. Never flash anything."""
from __future__ import annotations
import argparse
import base64
import io
from pathlib import Path
import secrets
import shutil
import subprocess
import tarfile

BR_COMMIT = "29a2345e3f0c61bba9307f3daea5ed0c94388ed3"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Pinned upstream context changed: {path.name}")
    path.write_text(text.replace(old, new))


def prepare(output: Path, upstream: Path | None = None) -> Path:
    output = output.resolve()
    firmware = Path(__file__).resolve().parent.parent
    if output.is_relative_to(firmware):
        raise ValueError("Build output must be outside the source firmware tree")
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    destination = output / "firmware"
    shutil.copytree(firmware, destination, ignore=shutil.ignore_patterns(
        "__pycache__", ".esphome", "secrets.yaml", "*.pyc"))
    if upstream is None:
        upstream = output / "upstream-git"
        subprocess.run(["git", "init", "--quiet", str(upstream)], check=True)
        subprocess.run(["git", "-C", str(upstream), "fetch", "--quiet", "--depth=1",
                        "https://github.com/espressif/esp-thread-br.git", BR_COMMIT], check=True)
    archive = subprocess.check_output(["git", "-C", str(upstream), "archive", BR_COMMIT,
                                       "LICENSE", "components/esp_ot_br_server"])
    unpacked = output / "upstream-source"
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(unpacked, filter="data")
    server = unpacked / "components/esp_ot_br_server"
    shutil.copytree(server, output / "upstream-original")
    # REST-only integration: no second Ethernet driver, Wi-Fi provisioning, or
    # filesystem image that ESPHome's OTA would not automatically update.
    (server / "CMakeLists.txt").write_text('''idf_component_register(
    SRCS "src/esp_br_web.c" "src/esp_br_web_api.c" "src/esp_br_web_base.c"
    INCLUDE_DIRS include
    PRIV_INCLUDE_DIRS private_include
    PRIV_REQUIRES mdns spiffs esp_eth nvs_flash freertos openthread esp_http_server
                  esp_wifi esp_app_format esp_timer json
    EMBED_FILES "favicon.ico")
''')
    web = server / "src/esp_br_web.c"
    replace_once(web, '#include "protocol_examples_common.h"\n', "")
    replace_once(web, "config.max_uri_handlers =", "config.server_port = LOW_POWER_OTBR_REST_PORT;\n    config.max_uri_handlers =")
    # Exact fix validated against python-otbr-api in the separate Thread proof.
    replace_once(web, '    cJSON *response = resource_status("404", "404 Not Found");',
                 '    httpd_resp_set_status(req, HTTPD_404);\n    cJSON *response = resource_status("404", "404 Not Found");')
    with web.open("a") as handle:
        handle.write('''\n/* ESPHome starts the REST server after its Ethernet netif and OT instance exist. */
void esp_br_web_start_immediate(char *base_path) { start_web_server(base_path); }
''')
    target_server = destination / "low-power/generated/esp_ot_br_server"
    target_server.parent.mkdir()
    shutil.copytree(server, target_server)
    shutil.copyfile(unpacked / "LICENSE", target_server / "LICENSE")
    secret_file = destination / "low-power/secrets.yaml"
    secret_file.write_text(
        f'api_encryption_key: "{base64.b64encode(secrets.token_bytes(32)).decode()}"\n'
        f'ota_password: "{secrets.token_hex(24)}"\n'
        'mqtt_broker: "192.0.2.1"\nmqtt_username: "build-only"\n'
        f'mqtt_password: "{secrets.token_hex(24)}"\n')
    secret_file.chmod(0o600)
    return destination / "low-power/hub.yaml"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--upstream", type=Path, help="Existing git clone containing the exact pinned commit")
    args = parser.parse_args()
    print(prepare(args.output.resolve(), args.upstream))
