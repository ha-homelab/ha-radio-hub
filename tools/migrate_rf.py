#!/usr/bin/env python3
"""Offline importer for an rf-airbridge device wrapper; never contacts HA or a node.

The importer intentionally rejects custom firmware pipelines rather than dropping
unknown behavior. YAML is handled as nodes: !secret/!lambda values and quoted RF
codes are never executed, interpolated or printed.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
from pathlib import Path
import sys

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

STR = 'tag:yaml.org,2002:str'
MAP = 'tag:yaml.org,2002:map'
SEQ = 'tag:yaml.org,2002:seq'
ALLOWED_TAGS = {STR, MAP, SEQ, 'tag:yaml.org,2002:int', 'tag:yaml.org,2002:float',
                'tag:yaml.org,2002:bool', 'tag:yaml.org,2002:null', '!secret', '!lambda', '!include'}
RESERVED_IDS = {'rf_mqtt', 'rm433_button', 'rf_radio', 'rf_receiver', 'rf_tx_active',
                'rf_raw_learning', 'rf_transmitter', 'rf_send_job', 'rf_tx_complete', 'rf_tx_error', 'rf_tx_fault'}


class MigrationError(ValueError):
    """A deliberately value-free explanation of an unsupported input."""


def scalar(value: str, tag: str = STR) -> ScalarNode:
    return ScalarNode(tag, value, style='"' if tag == STR else None)


def mapping(values: dict[str, object]) -> MappingNode:
    return MappingNode(MAP, [(scalar(k), v) for k, v in values.items()])


def fields(node, context='mapping') -> dict:
    if not isinstance(node, MappingNode):
        raise MigrationError(f'Expected {context}.')
    result = {}
    for key, value in node.value:
        if not isinstance(key, ScalarNode) or key.tag != STR or key.value in result:
            raise MigrationError('Mapping keys must be unique strings; YAML merge keys are unsupported.')
        result[key.value] = value
    return result


def validate_tree(node, ancestors=None):
    ancestors = set() if ancestors is None else ancestors
    if id(node) in ancestors or node.tag not in ALLOWED_TAGS:
        raise MigrationError('Cyclic YAML or an unsupported YAML tag requires manual migration.')
    ancestors = ancestors | {id(node)}
    if isinstance(node, MappingNode):
        for value in fields(node).values():
            validate_tree(value, ancestors)
    elif isinstance(node, SequenceNode):
        for value in node.value:
            validate_tree(value, ancestors)
    elif not isinstance(node, ScalarNode):
        raise MigrationError('Unsupported YAML node.')


def load(path: Path):
    try:
        node = yaml.compose(path.read_text(), Loader=yaml.SafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise MigrationError('Cannot read or parse an input YAML file; no contents are logged.') from exc
    if node is None:
        raise MigrationError('Input YAML must not be empty.')
    validate_tree(node)
    return node


def require_scalar(node, context):
    if not isinstance(node, ScalarNode):
        raise MigrationError(f'{context} must be a scalar.')
    return node


def secret_refs(node) -> set[str]:
    if node.tag == '!include':
        raise MigrationError('Nested includes require a reviewed standalone device wrapper before migration.')
    if isinstance(node, ScalarNode):
        return {node.value} if node.tag == '!secret' else set()
    children = fields(node).values() if isinstance(node, MappingNode) else node.value
    return set().union(*(secret_refs(child) for child in children))


def reject_keys(values, allowed, message):
    if set(values) - set(allowed):
        raise MigrationError(message)


def resolve_identity(node, substitutions, seen=None):
    """Resolve identity before overriding the port's substitution names."""
    seen = set() if seen is None else seen
    require_scalar(node, 'Identity')
    if node.tag != STR:
        raise MigrationError('Identity must be a literal or resolvable string substitution.')
    def replace(match):
        key = match.group(1)
        if key in seen or key not in substitutions:
            raise MigrationError('Identity contains a cyclic or missing substitution.')
        return resolve_identity(substitutions[key], substitutions, seen | {key})
    value = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', replace, node.value)
    if '$' in value:
        raise MigrationError('Identity contains an unsupported substitution syntax.')
    return value


def reject_discarded_hooks(node):
    """No lifecycle behavior may disappear with a replaced hardware block."""
    if node.tag in {'!lambda', '!include'}:
        raise MigrationError('Discarded hardware blocks contain custom behavior; migrate it manually.')
    if isinstance(node, MappingNode):
        values = fields(node)
        if any(key.startswith('on_') or key in {'lambda', 'then', 'action'} for key in values):
            raise MigrationError('Discarded hardware blocks contain lifecycle hooks; migrate them manually.')
        for value in values.values():
            reject_discarded_hooks(value)
    elif isinstance(node, SequenceNode):
        for value in node.value:
            reject_discarded_hooks(value)


def migrate(source: Path, secrets: Path, output: Path, repo_root: Path | None = None) -> dict:
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    output = output.resolve()
    if output.exists():
        raise MigrationError('Output already exists; choose a new private directory.')
    if output == root or (root in output.parents and root / 'private' not in output.parents):
        raise MigrationError('Output inside this repository must be below private/.')
    original = fields(load(source), 'a device wrapper mapping')
    secret_values = fields(load(secrets), 'a secrets mapping')
    reject_keys(original, {'substitutions', 'esphome', 'esp8266', 'wifi', 'logger', 'api', 'ota',
                           'mqtt', 'spi', 'packages', 'binary_sensor', 'remote_receiver'},
                'Custom top-level firmware blocks require manual review; no files were written.')
    discarded = [key for key in ('esp8266', 'wifi', 'spi', 'logger') if key in original]
    for key in discarded:
        reject_discarded_hooks(original[key])
    package_values = fields(original.get('packages', mapping({})))
    reject_keys(package_values, {'rf_airbridge'}, 'Additional packages require manual review.')
    if 'rf_airbridge' not in package_values:
        raise MigrationError('Expected the upstream packages.rf_airbridge device-wrapper contract.')
    package = package_values['rf_airbridge']
    if (not isinstance(package, ScalarNode) or package.tag != '!include'
            or Path(package.value).name != 'rf-airbridge.yaml'):
        raise MigrationError('Expected a local !include of rf-airbridge.yaml; custom packages require manual review.')
    esp = fields(original.get('esphome', mapping({})))
    reject_keys(esp, {'name', 'friendly_name', 'min_version', 'compile_process_limit', 'comment', 'project'},
                'Custom esphome lifecycle, includes or name suffix settings require manual review.')
    if 'name' not in esp:
        raise MigrationError('The original esphome.name is required.')
    require_scalar(esp['name'], 'Node name')
    subs = fields(copy.deepcopy(original.get('substitutions', mapping({}))))
    for value in subs.values():
        require_scalar(value, 'Substitution')
    node_name = resolve_identity(esp['name'], subs)
    friendly_name = resolve_identity(esp.get('friendly_name', esp['name']), subs)
    subs['rf_node_name'] = scalar(node_name)
    subs['rf_friendly_name'] = scalar(friendly_name)
    subs['rf_airbridge_path'] = scalar(os.path.relpath(root / 'firmware', output))
    api = fields(copy.deepcopy(original.get('api', mapping({}))))
    reject_keys(api, {'encryption', 'reboot_timeout', 'port', 'batch_delay', 'max_connections',
                      'listen_backlog', 'max_send_queue'},
                'Custom API actions or hooks require manual review; standard actions come from the new package.')
    encryption = fields(api.get('encryption', mapping({})))
    if set(encryption) != {'key'}:
        raise MigrationError('Expected api.encryption.key in the original wrapper.')
    mqtt = fields(copy.deepcopy(original.get('mqtt', mapping({}))))
    if 'id' in mqtt and require_scalar(mqtt['id'], 'MQTT id').value != 'rf_mqtt':
        raise MigrationError('A custom MQTT component id requires manual review.')
    if not {'broker', 'username', 'password'} <= set(mqtt):
        raise MigrationError('Expected MQTT broker, username and password in the original wrapper.')
    ota_node = copy.deepcopy(original.get('ota'))
    if not isinstance(ota_node, SequenceNode) or len(ota_node.value) != 1:
        raise MigrationError('Expected one ESPHome OTA platform in a list.')
    ota = fields(ota_node.value[0])
    if 'platform' not in ota or ota['platform'].value != 'esphome' or 'password' not in ota:
        raise MigrationError('Expected the password-protected ESPHome OTA platform.')

    # Preserve the effective credential values, without copying unused Wi-Fi secrets.
    exported_secrets = {}
    credentials = {'api_encryption_key': encryption['key'], 'ota_password': ota['password'],
                   'mqtt_broker': mqtt['broker'], 'mqtt_username': mqtt['username'], 'mqtt_password': mqtt['password']}
    for canonical, node in credentials.items():
        require_scalar(node, 'Credential')
        value = secret_values.get(node.value) if node.tag == '!secret' else node
        if value is None or not isinstance(value, ScalarNode) or value.tag != STR:
            raise MigrationError('A required credential is missing or is not a literal string.')
        # Firmware supplies the canonical !secret references; wrapper keeps them explicit.
        exported_secrets[canonical] = copy.deepcopy(value)
    encryption['key'] = scalar('api_encryption_key', '!secret')
    api['encryption'] = mapping(encryption)
    ota['password'] = scalar('ota_password', '!secret')
    ota_node.value[0] = mapping(ota)
    for key in ('broker', 'username', 'password'):
        mqtt[key] = scalar('mqtt_' + key, '!secret')

    result = {'substitutions': mapping(subs),
              'packages': mapping({'rf_ethernet': scalar(os.path.relpath(root / 'firmware/packages/rf-ethernet-base.yaml', output), '!include')}),
              'api': mapping(api), 'ota': ota_node, 'mqtt': mapping(mqtt)}
    rx = fields(copy.deepcopy(original.get('remote_receiver', mapping({}))))
    reject_keys(rx, {'filter', 'idle', 'tolerance', 'dump'},
                'Receiver wiring or callbacks require manual migration; only timing/dump overrides are imported.')
    normalized_filter = False
    if 'filter' in rx:
        filter_node = require_scalar(rx['filter'], 'Receiver filter')
        match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)(us|ms)', filter_node.value)
        if filter_node.tag != STR or match is None:
            raise MigrationError('Receiver filter must be a literal us/ms duration for migration.')
        micros = float(match.group(1)) * (1000 if match.group(2) == 'ms' else 1)
        if micros > 170:
            # RM433 short pulses are ~240 us; ESP32 software filtering differs
            # from the original ESP8266 path. Preserve a lower custom threshold.
            rx['filter'] = scalar('150us')
            normalized_filter = True
    if rx:
        result['remote_receiver'] = mapping(rx)
    sensors = copy.deepcopy(original.get('binary_sensor', SequenceNode(SEQ, [])))
    if not isinstance(sensors, SequenceNode):
        raise MigrationError('binary_sensor must be an inline list; includes require manual review.')
    sensor_ids = set()
    for sensor in sensors.value:
        values = fields(sensor, 'binary_sensor entry')
        if 'id' in values:
            sid = require_scalar(values['id'], 'Entity id').value
            if sid in RESERVED_IDS or sid in sensor_ids:
                raise MigrationError('A binary_sensor id conflicts with another or a reserved component.')
            sensor_ids.add(sid)
    if sensors.value:
        result['binary_sensor'] = sensors

    # Do not traverse the new package include; it is a known local source path.
    references = set()
    for key, node in result.items():
        if key != 'packages':
            references |= secret_refs(node)
    for reference in references:
        if reference not in exported_secrets:
            if reference not in secret_values:
                raise MigrationError('A referenced secret is missing; no files were written.')
            value = secret_values[reference]
            if not isinstance(value, ScalarNode) or value.tag == '!secret':
                raise MigrationError('Secrets must be literal scalar values.')
            exported_secrets[reference] = copy.deepcopy(value)

    report = {'status': 'offline_candidate_requires_compile_and_hardware_acceptance',
              'binary_sensor_count': len(sensors.value), 'secret_count': len(exported_secrets),
              'original_node_name_preserved': True,
              'upstream_package_contents_verified': False,
              'replaced_hardware_blocks': discarded, 'network_transport': 'ethernet',
              'receiver_filter_normalized_to_150us': normalized_filter,
              'ha_registry_identity_preserved': False,
              'live_systems_modified': False,
              'review_required': ['new MAC and HA device/entity registry mapping',
                                  'MQTT client_id/discovery topics with old node offline',
                                  'legacy binary_sensor callbacks against ESP32-S3',
                                  'physical receive/transmit/receive acceptance']}
    candidate = '# PRIVATE: migrated offline; compile and review before flashing.\n' + yaml.serialize(mapping(result))
    secret_text = '# PRIVATE: retained installation values; never commit.\n' + yaml.serialize(mapping(exported_secrets))
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    for filename, content in {'device.yaml': candidate, 'secrets.yaml': secret_text,
                               'report.json': json.dumps(report, indent=2) + '\n'}.items():
        fd = os.open(output / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as handle:
            handle.write(content)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--secrets', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = migrate(args.source, args.secrets, args.output)
    except (MigrationError, OSError) as exc:
        # OSError filenames may contain private installation identifiers.
        message = str(exc) if isinstance(exc, MigrationError) else 'Cannot write private output files.'
        print('Migration stopped: ' + message, file=sys.stderr)
        return 2
    print(f'Offline candidate written: {result["binary_sensor_count"]} binary sensors; no live systems changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
