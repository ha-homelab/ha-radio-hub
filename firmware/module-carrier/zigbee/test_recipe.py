"""Offline safety checks for generation and image verification (no vendor SDK)."""
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess
import json

from antenna import configuration, header, artifact_prefix

from build import macro, srecords, verify_images, check_configuration
from generate import check_python_pack, configure_headers, inspect_sdk, configure_board


def record(address, payload):
    raw = bytes([5+len(payload)])+address.to_bytes(4,'big')+payload
    return 'S3'+(raw+bytes([255-(sum(raw)&255)])).hex().upper()+'\n'


class RecipeTests(unittest.TestCase):
    def test_mismatched_antenna_header_cannot_be_built_or_relabelled(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d/'application/autogen').mkdir(parents=True)
            (d/'application/autogen/sl_event_handler.c').write_text('  sl_gpio_init();\n')
            configure_board(d/'application', 'external')
            cfg = {'antenna': configuration('external'),
                   'application': {'configuration': {}}, 'bootloader': {'configuration': {}}}
            (d/'input-config.json').write_text(json.dumps(cfg))
            check_configuration(d, cfg)
            (d/'application/autogen/mc1_antenna_config.h').write_text(header('onboard'))
            with self.assertRaisesRegex(ValueError, 'antenna selection'):
                check_configuration(d, cfg)

    def test_unknown_antenna_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown XIAO'):
            configuration('auto')

    def test_compiled_board_initialization_selects_each_physical_path(self):
        """Execute the real board init with a GPIO stub, rather than matching text."""
        compiler = shutil.which('cc')
        self.assertIsNotNone(compiler, 'Host C compiler required for board-init regression')
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            shutil.copyfile(Path(__file__).with_name('mc1_board_init.h'), d/'mc1_board_init.h')
            (d/'em_gpio.h').write_text('enum {gpioPortA, gpioPortB, gpioModePushPull};\n'
                'void GPIO_PinModeSet(int port, int pin, int mode, int level);\n')
            (d/'test.c').write_text('#include <assert.h>\n#include "mc1_board_init.h"\n'
                'static int n;\n'
                'void GPIO_PinModeSet(int port, int pin, int mode, int level) {\n'
                'assert(mode == gpioModePushPull);\n'
                'if(n==0) { assert(port==gpioPortB && pin==4 && level==EXPECTED_SELECT); }\n'
                'if(n==1) { assert(port==gpioPortB && pin==5 && level==1); }\n'
                'if(n==2) { assert(port==gpioPortA && pin==6 && level==1); }\n'
                'if(n==3) { assert(port==gpioPortA && pin==7 && level==1); }\n'
                '++n; }\nint main(void) { mc1_xiao_board_init(); assert(n==4); }\n')
            for mode, expected in [('onboard', 0), ('external', 1)]:
                (d/'mc1_antenna_config.h').write_text(header(mode))
                subprocess.run([compiler, '-Wall', '-Wextra', '-Werror', '-DEXPECTED_SELECT='+str(expected),
                                str(d/'test.c'), '-o', str(d/'test')], check=True)
                subprocess.run([str(d/'test')], check=True)
                self.assertEqual(configuration(mode)['select_level'], expected)
                self.assertTrue(artifact_prefix(mode).endswith('-'+mode))
            (d/'mc1_antenna_config.h').write_text('#define MC1_ANTENNA_EXTERNAL 2\n')
            result = subprocess.run([compiler, '-DEXPECTED_SELECT=2', str(d/'test.c'), '-o', str(d/'test')],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_board_initialization_is_inserted_in_driver_phase(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d/'autogen').mkdir()
            source = d/'autogen/sl_event_handler.c'
            source.write_text('void sl_driver_init(void) {\n  sl_gpio_init();\n}\n')
            configure_board(d)
            self.assertIn('  sl_gpio_init();\n  mc1_xiao_board_init();', source.read_text())
            self.assertTrue((d/'autogen/mc1_board_init.h').is_file())
            self.assertEqual((d/'autogen/mc1_antenna_config.h').read_text(), header('onboard'))

    def test_external_selection_is_generated_without_modifying_shared_source(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d/'autogen').mkdir()
            (d/'autogen/sl_event_handler.c').write_text('  sl_gpio_init();\n')
            configure_board(d, 'external')
            self.assertEqual((d/'autogen/mc1_antenna_config.h').read_text(), header('external'))
            self.assertEqual((d/'autogen/mc1_board_init.h').read_bytes(),
                             Path(__file__).with_name('mc1_board_init.h').read_bytes())

    def test_changed_generator_template_cannot_silently_omit_radio_switch(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d/'autogen').mkdir()
            (d/'autogen/sl_event_handler.c').write_text('void changed_template(void) {}')
            with self.assertRaisesRegex(RuntimeError, 'Expected one GPIO'):
                configure_board(d)

    def test_python_runtime_is_an_explicit_native_adapter_pack(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root)
            with self.assertRaisesRegex(RuntimeError,'Missing Silicon Labs'):
                check_python_pack(d,'Linux')
            (d/'apack.json').write_text('{"id":"other","app_version":"3.10.5"}')
            with self.assertRaisesRegex(RuntimeError,'Expected Silicon Labs'):
                check_python_pack(d,'Linux')
            (d/'apack.json').write_text('{"id":"python","app_version":"3.10.5"}')
            with self.assertRaisesRegex(RuntimeError,'Missing native JEP'):
                check_python_pack(d,'Linux')
            (d/'jep').mkdir();(d/'jep/jep.so').write_bytes(b'fixture')
            self.assertEqual(check_python_pack(d,'Linux')['native_library'],'jep.so')
            with self.assertRaisesRegex(RuntimeError,'Missing native JEP'):
                check_python_pack(d,'Darwin')

    def test_sdk_inspection_checks_version_and_protocol_without_claiming_commit(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root); header=d/'protocol/zigbee/app/util/ezsp/ezsp-protocol.h'
            header.parent.mkdir(parents=True)
            (d/'simplicity_sdk.slcs').write_text('sdk_version: "2025.6.3"\n')
            header.write_text('#define EZSP_PROTOCOL_VERSION 0x12\n')
            cfg={'sdk_tag':'v2025.6.3','sdk_commit':'expected-only'}
            result=inspect_sdk(d,cfg)
            self.assertEqual(result['verified_ezsp_protocol_version'],18)
            self.assertFalse(result['source_commit_verified'])
            header.write_text('#define EZSP_PROTOCOL_VERSION 0x11\n')
            with self.assertRaisesRegex(RuntimeError,'protocol18'):
                inspect_sdk(d,cfg)
            header.write_text('#define EZSP_PROTOCOL_VERSION 0x12\n')
            (d/'simplicity_sdk.slcs').write_text('sdk_version: "2025.6.2"\n')
            with self.assertRaisesRegex(RuntimeError,'version differs'):
                inspect_sdk(d,cfg)

    def test_known_record_and_bad_checksum(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'sample.s37'
            p.write_text('S3090800000001020304E4\n')
            self.assertEqual(srecords(p),dict(zip(range(0x8000000,0x8000004),(1,2,3,4))))
            p.write_text('S3090800000001020304E5\n')
            with self.assertRaisesRegex(ValueError,'checksum'):
                srecords(p)

    def test_conflicting_records_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'sample.s37'
            p.write_text(record(0x8000000,b'abc')+record(0x8000001,b'x'))
            with self.assertRaisesRegex(ValueError,'Conflicting'):
                srecords(p)

    def test_commented_pins_become_active(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root);(d/'config').mkdir()
            p=d/'config/pin.h';p.write_text('// #define PIN 11\n#warning "not configured"\n')
            configure_headers(d,{'configuration':{'PIN':'6'},'configured_pin_headers':{'pin.h':'not configured'}})
            self.assertEqual(macro(d,'PIN'),'6')
            self.assertNotIn('#warning',p.read_text())

    def test_missing_and_duplicate_pin_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root);(d/'config').mkdir()
            for text in ('// unrelated\n','#define PIN 1\n#define PIN 2\n'):
                (d/'config/pin.h').write_text(text)
                with self.assertRaisesRegex(RuntimeError,'Expected one'):
                    configure_headers(d,{'configuration':{'PIN':'6'},'configured_pin_headers':{}})

    def test_images_and_unsafe_substitution(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root)
            app,boot,merged,rt=[d/x for x in ('app','boot','merged','rt')]
            # Cortex-M stack at RAM end, thumb reset vector inside each flash region.
            av=(0x20040000).to_bytes(4,'little')+(0x08006009).to_bytes(4,'little')+b'\x00\xbf'
            bv=(0x20040000).to_bytes(4,'little')+(0x08000009).to_bytes(4,'little')+b'\x00\xbf'
            app.write_text(record(0x08006000,av));boot.write_text(record(0x08000000,bv))
            merged.write_text(boot.read_text()+app.read_text());rt.write_text(app.read_text())
            self.assertEqual(verify_images(app,boot,merged,rt)['application']['first_address'],'0x8006000')
            rt.write_text(record(0x08006000,av[:-1]+b'\xaa'))
            with self.assertRaisesRegex(ValueError,'roundtrip'):
                verify_images(app,boot,merged,rt)
            rt.write_text(app.read_text());boot.write_text(record(0x08006000,bv))
            with self.assertRaisesRegex(ValueError,'reserved'):
                verify_images(app,boot,merged,rt)


if __name__=='__main__':
    unittest.main()
