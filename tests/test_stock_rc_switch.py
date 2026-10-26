"""Behavioral integration with ESPHome's installed, pinned waveform decoder.

The full rc_switch.cpp/.h are copied unmodified into a temporary build. Exact
RemoteReceiveData/RemoteTransmitData declarations and receive-method definitions
are extracted from installed remote_base files to exclude unrelated runtime
dependencies; no decoding/tolerance implementation is replaced. Only automation
base classes, hardware clock/entropy, log and MQTT sinks are host seams.
No upstream code is redistributed in this repository by this test.
"""

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/rf_contract.json").read_text())

BASE_STUB = r'''
template<typename T> struct HostValue {
  T stored{};
  template<typename... Ts> T value(Ts...) const { return stored; }
};
#define TEMPLATABLE_VALUE(type,name) protected: HostValue<type> name##_; public:
template<typename... Ts> class RemoteTransmitterActionBase {
 public: virtual void encode(RemoteTransmitData *, Ts...) = 0;
};
class RemoteReceiverBinarySensorBase {
 protected: virtual bool matches(RemoteReceiveData) = 0;
};
class RemoteReceiverDumperBase {
 public: virtual bool dump(RemoteReceiveData) = 0;
};
template<typename T> class RemoteReceiverTrigger {};
'''


class StockRCSwitchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.metadata.version("esphome") != "2026.10.0":
            raise RuntimeError("Run with the pinned firmware/requirements.txt environment")
        spec = importlib.util.find_spec("esphome")
        installed = Path(next(iter(spec.submodule_search_locations))) / "components/remote_base"
        cls.temp = tempfile.TemporaryDirectory(prefix="rf-stock-decoder-")
        cls.addClassCleanup(cls.temp.cleanup)
        temporary = Path(cls.temp.name)
        remote = temporary / "esphome/components/remote_base"
        remote.mkdir(parents=True)
        for name in ("rc_switch_protocol.h", "rc_switch_protocol.cpp"):
            shutil.copyfile(installed / name, remote / name)
        original_header = (installed / "remote_base.h").read_text()
        start = original_header.index("enum ToleranceMode")
        end = original_header.index("class RemoteComponentBase")
        declarations = original_header[start:end]
        original_source = (installed / "remote_base.cpp").read_text()
        start = original_source.index("/* RemoteReceiveData */")
        end = original_source.index("/* RemoteReceiverBinarySensorBase */")
        methods = original_source[start:end]
        prelude = "#pragma once\n#include <cstdint>\n#include <string>\n#include <vector>\n#include <optional>\n"
        prelude += '#include "esphome/core/hal.h"\n'
        prelude += "namespace esphome { using std::optional; }\nnamespace esphome::remote_base {\n"
        (remote / "remote_base.h").write_text(prelude + declarations + BASE_STUB + "\n}\n")
        (remote / "receive_methods.cpp").write_text(
            '#include "remote_base.h"\nnamespace esphome::remote_base {\n' + methods + "\n}\n")
        core = temporary / "esphome/core"
        core.mkdir(parents=True)
        (core / "component.h").write_text("#pragma once\n")
        (core / "log.h").write_text("#define ESP_LOGI(...)\n")
        for name in ("hal.h", "helpers.h"):
            shutil.copyfile(ROOT / "tests/native/esphome/core" / name, core / name)
        # ESP32/host flash memory is directly addressable. Keep the installed
        # non-ESP8266 copy implementation verbatim alongside the clock seam.
        hal = (installed.parents[1] / "core/hal.h").read_text()
        copy_helper, = [line for line in hal.splitlines() if line.startswith("inline void progmem_memcpy(")]
        with (core / "hal.h").open("a") as stream:
            stream.write("\n#include <cstring>\n#define PROGMEM\nnamespace esphome {\n" + copy_helper + "\n}\n")
        cls.binary = temporary / "stock-decoder"
        harness = temporary / "stock_decoder_harness.cpp"
        shutil.copyfile(ROOT / "tests/native/stock_decoder_harness.cpp", harness)
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++20 compiler required")
        flags = ["-std=c++20", "-Wall", "-Wextra", "-Wno-unused-variable"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g", "-O1"]
        build = subprocess.run([
            compiler, *flags, "-I", str(temporary), "-I", str(ROOT / "firmware/include"),
            str(harness),
            str(remote / "rc_switch_protocol.cpp"), str(remote / "receive_methods.cpp"),
            "-o", str(cls.binary)
        ], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)

    def decode(self, timings):
        run = subprocess.run([str(self.binary)], input=" ".join(map(str, timings)),
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return [json.loads(line) for line in run.stdout.splitlines()]

    def test_literal_protocol_one_waveform_preserves_leading_zeroes(self):
        # Independent fixture: protocol-1 nominal 350/1050us, value5 in24bits.
        timings = [350, -1050] * 21 + [1050, -350, 350, -1050, 1050, -350] + [350, -10850]
        message, = self.decode(timings)
        self.assertEqual((message["format"], message["protocol"], message["bits"], message["code"], message["value"]),
                         ("rc_switch", 1, 24, "000000000000000000000101", "5"))

    def test_protocol_eight_maximum_64_bit_value_remains_a_string(self):
        message, = self.decode([250, -250] * 64 + [250, -2500])
        self.assertEqual((message["protocol"], message["bits"], message["code"], message["value"]),
                         (8, 64, "1" * 64, "18446744073709551615"))

    def test_too_short_capture_is_not_a_decoded_event(self):
        self.assertEqual(self.decode([350, -1050] * 7 + [350, -10850]), [])

    def test_stock_decoder_prefix_acceptance_is_not_misrepresented_as_full_frame_validation(self):
        # Stock decoder accepts a valid >=8-bit prefix before an unknown pulse.
        # The transport preserves this behavior; only RM433 requires all24bits.
        message, = self.decode([350, -1050] * 8 + [100, -9999])
        self.assertEqual((message["protocol"], message["bits"], message["code"]), (1, 8, "00000000"))

    def test_rm433_short_pulse_fixture_wins_before_stock_protocols(self):
        example = FIXTURE["rm433_example"]
        message, = self.decode(example["timings"])
        self.assertEqual((message["format"], message["bits"], message["code"], message["value"]),
                         ("rm433", 24, example["code"], example["value"]))


if __name__ == "__main__":
    unittest.main()
