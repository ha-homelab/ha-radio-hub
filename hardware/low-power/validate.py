#!/usr/bin/env python3
"""Validate LP-P0 contracts; this is not ERC, signal-integrity or a hardware test."""
import csv
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate():
    pins = json.loads((HERE / 'pinmap.json').read_text())
    power = json.loads((HERE / 'power-budget.json').read_text())
    bom = json.loads((HERE / 'bom.json').read_text())
    assigned = pins['exclusive_pins']
    gpio = [p['gpio'] for p in assigned]
    allowed = {1, 2, *range(4, 19), 21, *range(38, 45), 47, 48}
    require(len(gpio) == len(set(gpio)) == 26, 'S3 assignments must be26 unique GPIO')
    require(set(gpio) <= allowed, 'Use of inaccessible, strap, USB or PSRAM GPIO')
    require(set(gpio).isdisjoint(sum(pins['reserved'].values(), [])), 'Reserved GPIO assigned')
    require(all(p['logic_voltage'] == 3.3 for p in assigned), 'Wrong S3 logic voltage')
    require({x['port'] for x in pins['uart_owners']} == {0, 1, 2}, 'UART ownership collision')
    require([x['flow_control'] for x in pins['uart_owners']] == [False, True, False], 'MG24 flow control required')
    require(pins['sc16']['crystal_hz'] / (16 * pins['sc16']['prescaler'] * pins['sc16']['divisor']) == pins['sc16']['baud'], 'SC16 baud divisor invalid')
    require(pins['sc16']['irq_pullup_ohms'] == 1000, 'NXP IRQ pull-up must match selected3V3 circuit')
    require(pins['sc16']['fixed_pins']['9'].startswith('GND') and pins['sc16']['fixed_pins']['14'].startswith('GND'), 'SPI straps wrong')
    roles = {p['role']: p['gpio'] for p in assigned}
    for bus in pins['spi_buses']:
        for device in bus['devices']:
            if device['id'] == 'sc16is752':
                require(device['mode'] == 0 and device['clock_hz'] <= 4_000_000, 'SC16IS752 SPI electrical limit')
    require(all(m['supply_voltage'] == (5.0 if m['id'] == 'ld2450' else 3.3) for m in pins['external_modules']), 'Module supply rail mismatch')
    with (HERE / 'wiring.csv').open() as f:
        rows = list(csv.DictReader(f))
    require({int(r['S3_GPIO']): r['role'] for r in rows} == {r['gpio']: r['role'] for r in assigned}, 'CSV stale')
    require(len({x['ref'] for x in bom['items']}) == len(bom['items']), 'Duplicate BOM ref')
    require(all(x['qty'] > 0 for x in bom['items']), 'Invalid BOM quantity')
    require(power['hardware_measured'] is False and power['target_kind'].startswith('acceptance_hypothesis'), 'Unproven measurement/3W claim')
    eta = power['efficiency_scenarios']
    for scenario, eff in [('low', 'high'), ('reference', 'reference'), ('high', 'low')]:
        result = power['results'][scenario]
        p33 = sum(x['average_ma'][scenario]*3.3/1000 for x in power['loads'] if x['voltage_v'] == 3.3)
        p5 = sum(x['average_ma'][scenario]*5/1000 for x in power['loads'] if x['voltage_v'] == 5)
        secondary = p33 / eta['buck'][eff] + p5 + result['secondary_wiring_loss_w']
        ac = secondary / eta['pd'][eff] / eta['cable'][eff] / eta['pse'][eff]
        require(math.isclose(ac, result['ac_incremental_w'], abs_tol=1e-6), 'AC/DC boundary arithmetic mismatch')
        require(math.isclose(ac*8760*15/1000, result['kwh_15y'], abs_tol=.001), 'Lifetime conversion mismatch')
    peak = power['peak']
    require(peak['rail_3v3_a'] < peak['buck_required_test_a'], 'Buck current reserve insufficient')
    require(peak['pd_output_w_at_buck_eta_0_85'] < peak['pd_nominal_capacity_w'], 'PD reserve insufficient')
    require(eta['pd']['high'] <= .815, 'Wrong Ag97005-FL peak efficiency')
    # Independent comparison to the actual YAML, without executing custom YAML tags.
    proof = (ROOT / 'firmware/low-power/proof.yaml').read_text()
    integrated = (ROOT / 'firmware/low-power/hub.yaml').read_text()
    def block(text, key):
        match = re.search(r'^' + re.escape(key) + r':\n(.*?)(?=^\S|\Z)', text, re.M | re.S)
        require(match is not None, 'Missing firmware block ' + key)
        return match.group(1)
    checks = [
        (block(proof, 'ethernet'), {'clk_pin':'w5500_sclk','mosi_pin':'w5500_mosi','miso_pin':'w5500_miso','cs_pin':'w5500_cs','interrupt_pin':'w5500_irq','reset_pin':'w5500_reset'}),
        (block(proof, 'low_power_otbr'), {'tx_pin':'h2_tx','rx_pin':'h2_rx','reset_pin':'h2_reset','boot_pin':'h2_boot'}),
        (block(proof, 'uart'), {'tx_pin':'ld2450_tx','rx_pin':'ld2450_rx'}),
        (block(proof, 'i2c'), {'sda':'bme680_sda','scl':'bme680_scl'}),
        (block(integrated, 'sc16is752_uart'), {'cs_pin':'sc16_cs','interrupt_pin':'sc16_irq'}),
        (block(integrated, 'zigbee_tcp'), {'tx_pin':'mg24_tx','rx_pin':'mg24_rx','rts_pin':'mg24_rts','cts_pin':'mg24_cts'}),
    ]
    for text, mapping in checks:
        for field, role in mapping.items():
            require(re.search(r'\b'+field+r':\s*GPIO'+str(roles[role])+r'\b', text) is not None, 'Firmware pin mismatch: '+role)
    require(re.search(r'crystal_frequency:\s*'+str(pins['sc16']['crystal_hz'])+r'\b', integrated) is not None, 'Firmware crystal mismatches populated BOM')
    print('PASS:26 unique GPIO; UART/SPI/voltage/IRQ contracts; BOM/CSV; firmware pins; AC/DC and lifetime arithmetic.')
    print('NOT TESTED: assembly, flashed radio operation, power peaks, thermal behavior, isolation, EMC, coexistence.')


if __name__ == '__main__':
    validate()
