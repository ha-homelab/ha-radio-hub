"""Offline safety checks for generation and image verification (no vendor SDK)."""
from pathlib import Path
import tempfile
import unittest

from build import macro, srecords, verify_images
from generate import configure_headers, inspect_sdk


def record(address, payload):
    raw = bytes([5+len(payload)])+address.to_bytes(4,'big')+payload
    return 'S3'+(raw+bytes([255-(sum(raw)&255)])).hex().upper()+'\n'


class RecipeTests(unittest.TestCase):
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
