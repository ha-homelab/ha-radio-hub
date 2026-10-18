"""Cross-file MC1 interface checks; these do not substitute for bench tests."""
from pathlib import Path
import json
import re
import runpy
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DESIGN = runpy.run_path(str(HERE / 'cad/design.py'))
PARTS = {p['ref']: p for p in DESIGN['parts']}
PROFILE = (ROOT / 'firmware/module-carrier/hub.yaml').read_text()
ZIGBEE = json.loads((ROOT / 'firmware/module-carrier/zigbee/config.json').read_text())


def section(name):
    match = re.search(r'^' + re.escape(name) + r':\n(.*?)(?=^\S|\Z)', PROFILE, re.M | re.S)
    if not match:
        raise AssertionError('Missing configuration section: ' + name)
    return match.group(1)


def pin(name, field):
    match = re.search(r'^\s+' + field + r': GPIO(\d+)\s*$', section(name), re.M)
    if not match:
        raise AssertionError('Missing GPIO: ' + name + '.' + field)
    return match.group(1)


class Contract(unittest.TestCase):
    def test_single_current_design(self):
        registry = json.loads((ROOT / 'hardware/designs.json').read_text())
        self.assertEqual(registry['active_design'], 'MC1')
        self.assertEqual(registry['active_custom_pcb_count'], 1)
        self.assertEqual(registry['active_directory'], 'hardware/module-carrier')

    def test_s3_interfaces_reach_named_cad_nets(self):
        checks = {
            'substitutions': {'rf_cs_pin':'RF_CS'},
            'ethernet': {'cs_pin':'ETH_CS', 'interrupt_pin':'ETH_INT', 'reset_pin':'ETH_RESET'},
            'low_power_otbr': {'tx_pin':'THREAD_RX', 'rx_pin':'THREAD_TX',
                              'reset_pin':'THREAD_EN', 'boot_pin':'THREAD_BOOT'},
            'zigbee_tcp': {'tx_pin':'ZB_RX', 'rx_pin':'ZB_TX', 'rts_pin':'ZB_CTS', 'cts_pin':'ZB_RTS'},
            'uart': {'tx_pin':'RADAR_RX', 'rx_pin':'RADAR_TX'},
            'i2c': {'sda':'I2C_SDA', 'scl':'I2C_SCL'},
            'spi': {'clk_pin':'SPI_SCK', 'mosi_pin':'SPI_MOSI', 'miso_pin':'SPI_MISO'},
        }
        for component, fields in checks.items():
            for field, net in fields.items():
                with self.subTest(component=component, field=field):
                    self.assertEqual(DESIGN['s3nets'].get(pin(component, field)), net)

    def test_xiao_ncp_pins_reach_crossed_host_signals(self):
        config = ZIGBEE['application']['configuration']
        # Manufacturer header D0..D7 corresponds to PC00..PC07, physical pads1..8.
        for function, net in [('TX','ZB_TX'), ('RX','ZB_RX'), ('CTS','ZB_CTS'), ('RTS','ZB_RTS')]:
            prefix = 'SL_IOSTREAM_USART_VCOM_' + function
            self.assertEqual(config[prefix + '_PORT'], 'gpioPortC')
            pad = str(int(config[prefix + '_PIN']) + 1)
            self.assertEqual(PARTS['U3']['pins'][pad], net)
        self.assertEqual(config['SL_IOSTREAM_USART_VCOM_FLOW_CONTROL_TYPE'], 'usartHwFlowControlCtsAndRts')
        self.assertEqual(config['SL_IOSTREAM_USART_VCOM_BAUDRATE'], '115200')

    def test_xiao_boot_service_is_separate(self):
        config = ZIGBEE['bootloader']['configuration']
        self.assertEqual(config['SL_BTL_BUTTON_PORT'], 'gpioPortC')
        pad = str(int(config['SL_BTL_BUTTON_PIN']) + 1)
        self.assertEqual(PARTS['U3']['pins'][pad], 'ZB_BOOT_SERVICE')
        self.assertEqual(PARTS['J8']['pins'], {'1':'ZB_BOOT_SERVICE','2':'GND'})

    def test_factory_regulator_outputs_are_not_paralleled(self):
        for ref, pads in {'U1':['JP1.2','JP1.12'], 'U2':['J1.1','J1.12'], 'U3':['12']}.items():
            for pad in pads:
                self.assertIsNone(PARTS[ref]['pins'][pad], (ref, pad))
        self.assertEqual(PARTS['U4']['pins']['J2.2'], '+3V3')
        self.assertEqual(PARTS['J2']['pins']['3'], '+3V3')

    def test_native_usb_and_unused_straps_are_free(self):
        for names, part, reserved in [(DESIGN['s3names'], PARTS['U1'], ['19','20','3','46']),
                                      (DESIGN['h2names'], PARTS['U2'], ['4','5','26','27'])]:
            for row, labels in names.items():
                for i, label in enumerate(labels, 1):
                    if label in reserved:
                        self.assertIsNone(part['pins'][f'{row}.{i}'])

    def test_shared_spi_reaches_both_modules_with_distinct_selects(self):
        bus_id = re.search(r'^\s+-?\s*id: (\w+)', section('spi'), re.M).group(1)
        self.assertRegex(section('ethernet'), r'spi_id: ' + re.escape(bus_id) + r'\b')
        self.assertNotIn('clk_pin:', section('ethernet'))
        for net, wiz, rf in [('SPI_SCK','J1.4','3'), ('SPI_MOSI','J1.3','4'), ('SPI_MISO','J2.6','5')]:
            self.assertEqual(PARTS['U4']['pins'][wiz], net)
            self.assertEqual(PARTS['J5']['pins'][rf], net)
        self.assertNotEqual(PARTS['U4']['pins']['J1.5'], PARTS['J5']['pins']['6'])

    def test_nano_input_and_manual_recovery(self):
        self.assertEqual(PARTS['U1']['pins']['JP1.15'], '+5V_S3')
        self.assertEqual(PARTS['D1']['pins'], {'1': '+5V_S3', '2': '+5V'})
        boot_net = DESIGN['s3nets']['0']
        self.assertEqual(PARTS['U1']['pins']['JP1.13'], boot_net)
        services = [p for p in PARTS.values() if p['ref'].startswith('J') and p['pins'] == {'1': boot_net, '2': 'GND'}]
        self.assertEqual(len(services), 1)
        self.assertEqual(DESIGN['s3nets']['43'], 'THREAD_RX')
        self.assertEqual(DESIGN['s3nets']['44'], 'THREAD_TX')

    def test_h2_rom_uart_matches_the_carrier(self):
        self.assertEqual(PARTS['U2']['pins']['J3.3'], 'THREAD_RX')
        self.assertEqual(PARTS['U2']['pins']['J3.2'], 'THREAD_TX')
        self.assertIsNone(PARTS['U2']['pins']['J1.9'])
        self.assertIsNone(PARTS['U2']['pins']['J1.10'])

    def test_compact_assembly_has_no_usb_cable_corridors(self):
        self.assertEqual(DESIGN['USB_ENVELOPES'], {})
        self.assertLess(DESIGN['BOARD_W'] * DESIGN['BOARD_H'], 80 * 90)
        self.assertFalse(PARTS['J8']['fitted'])
        self.assertFalse(PARTS['J9']['fitted'])
        self.assertEqual(sum(p.get('fitted', True) for p in PARTS.values()), 16)

    def test_external_uart_matches_zac93_direction(self):
        self.assertEqual(PARTS['J3']['pins']['5'], PARTS['J4']['pins']['4'])
        self.assertEqual(PARTS['J3']['pins']['6'], PARTS['J4']['pins']['5'])
        self.assertNotEqual(PARTS['J3']['pins']['5'], PARTS['J3']['pins']['6'])
        self.assertIn('address: 0x70', section('wk2132_uart'))

    def test_mounted_modules_use_through_holes_without_sockets(self):
        for ref in ('U1','U2','U3','U4'):
            fp = PARTS[ref]['footprint'].split(':')[1]
            source = (HERE / 'cad/MC1.pretty' / (fp + '.kicad_mod')).read_text()
            self.assertNotRegex(source, r'\(pad\s+\S+\s+smd\b')
            self.assertIn('thru_hole', source)
            self.assertNotIn('Socket', PARTS[ref]['footprint'])

    def test_radio_and_service_contracts_remain_enabled(self):
        for required in ['low_power_otbr','bluetooth_proxy','zigbee_tcp','zwave_proxy','ld2450','api','ota','mqtt']:
            section(required)
        self.assertIn('active: true', section('bluetooth_proxy'))
        self.assertIn('connection_slots: 3', section('bluetooth_proxy'))
        self.assertIn('flash_size: 16MB', section('esp32'))
        self.assertIn('mode: octal', section('psram'))
        self.assertIn('enable_ipv6: true', section('network'))
        self.assertIn('encryption:', section('api'))
        for package in ('rf-airbridge.yaml','ld2450.yaml','bme680.yaml'):
            self.assertIn(package, section('packages'))


if __name__ == '__main__':
    unittest.main()
