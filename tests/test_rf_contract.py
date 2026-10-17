"""Regression tests against the public RF Airbridge contract, not a new codec.

Production Receiver/RM433/validation headers run in a host C++ process. The
RCSwitch decode seam is controlled explicitly: tests cover exact serialization,
protocol precedence and delivery policy, not ESPHome's waveform implementation.
RM433 uses literal synthetic pulse fixtures and its real production decoder.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/rf_contract.json").read_text())


def receive(*, now=0, connected=True, success=True, learn=False, suppress=False,
            native=True, bits=0, value=0, protocols=(), timings=()):
    fields = (now, int(connected), int(success), int(learn), int(suppress),
              int(native), bits, value, sum(1 << p for p in protocols), *timings)
    return "receive " + " ".join(map(str, fields))


class RFContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required; compatibility tests must not silently skip")
        cls.temporary = tempfile.TemporaryDirectory(prefix="rf-contract-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.binary = Path(cls.temporary.name) / "receiver"
        include = Path(os.environ.get("RF_TEST_INCLUDE", ROOT / "firmware/include"))
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                      "-fno-omit-frame-pointer", "-g", "-O1"]
        build = subprocess.run(
            [compiler, *flags, "-I", str(ROOT / "tests/native"), "-I", str(include),
             str(ROOT / "tests/native/receiver_harness.cpp"), "-o", str(cls.binary)],
            capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)

    def run_commands(self, *commands):
        result = subprocess.run([str(self.binary)], input="\n".join(commands) + "\n",
                                text=True, capture_output=True, check=True)
        records = []
        for line in result.stdout.splitlines():
            kind, _, data = line.partition(" ")
            if kind == "MQTT":
                qos, retained, topic, payload = data.split(" ", 3)
                self.assertEqual((qos, retained), ("0", "0"))
                records.append((kind, topic, json.loads(payload)))
            else:
                records.append((kind, data))
        return records

    def expected_receive(self, *, now=0, sequence=1, **fields):
        return dict(FIXTURE["receiver_prefix"], sequence=sequence,
                    event_id=f"rf:0123456789abcdef:{sequence}", uptime_ms=now, **fields)

    def test_rc_switch_golden_payload_exact_width_and_first_matching_protocol(self):
        for example in FIXTURE["rc_switch_examples"]:
            with self.subTest(example=example):
                records = self.run_commands(receive(
                    now=123456, bits=example["bits"], value=example["value"],
                    protocols=example["matching_protocols"]))
                expected = self.expected_receive(now=123456, format="rc_switch", **{
                    key: example[key] for key in ("protocol", "bits", "code", "value")})
                self.assertEqual(records, [
                    ("MQTT", FIXTURE["topics"]["decoded"], expected),
                    ("RESULT", "DECODED_PUBLISHED")])

    def test_rm433_golden_payload_and_native_event_order(self):
        fixture = FIXTURE["rm433_example"]
        fields = {key: value for key, value in fixture.items() if key != "timings"}
        self.assertEqual(self.run_commands(receive(now=123456, timings=fixture["timings"])), [
            ("NATIVE", "1193041 button_1"),
            ("MQTT", FIXTURE["topics"]["decoded"], self.expected_receive(now=123456, **fields)),
            ("RESULT", "DECODED_PUBLISHED")])

    def test_rc_switch_repeats_are_not_rm433_debounced(self):
        command = receive(bits=24, value=5, protocols=(1,))
        records = self.run_commands(command, command)
        messages = [r[2] for r in records if r[0] == "MQTT"]
        self.assertEqual([m["sequence"] for m in messages], [1, 2])
        self.assertEqual([m["code"] for m in messages], ["000000000000000000000101"] * 2)

    def test_rm433_hold_refreshes_quiet_interval_and_other_code_is_immediate(self):
        first = FIXTURE["rm433_example"]["timings"]
        other = first.copy()
        other[46:48] = [240, -720]  # Different complete code, not a known native button.
        records = self.run_commands(
            receive(now=0, timings=first), receive(now=349, timings=first),
            receive(now=698, timings=first), receive(now=1047, timings=first),
            receive(now=1397, timings=first), receive(now=1398, timings=other))
        self.assertEqual([r[1] for r in records if r[0] == "RESULT"], [
            "DECODED_PUBLISHED", "REPEAT_SUPPRESSED", "REPEAT_SUPPRESSED",
            "REPEAT_SUPPRESSED", "DECODED_PUBLISHED", "DECODED_PUBLISHED"])
        self.assertEqual([r[1] for r in records if r[0] == "NATIVE"], [
            "1193041 button_1", "1193041 button_1", "1193040 unmapped"])

    def test_native_offline_and_failed_publish_are_not_replayed_on_reconnect(self):
        timings = FIXTURE["rm433_example"]["timings"]
        for connected, success, outcome in [(False, True, "OFFLINE"), (True, False, "PUBLISH_FAILED")]:
            with self.subTest(outcome=outcome):
                records = self.run_commands(
                    receive(now=1, connected=connected, success=success, timings=timings),
                    receive(now=2, timings=timings),
                    receive(now=352, timings=timings))
                self.assertEqual([r[1] for r in records if r[0] == "RESULT"], [
                    outcome, "REPEAT_SUPPRESSED", "DECODED_PUBLISHED"])
                self.assertEqual(sum(r[0] == "NATIVE" for r in records), 2)
                messages = [r[2] for r in records if r[0] == "MQTT"]
                self.assertEqual([m["sequence"] for m in messages], [1] if not connected else [1, 2])

    def test_suppression_does_not_consume_native_press_or_publish_sequence(self):
        timings = FIXTURE["rm433_example"]["timings"]
        records = self.run_commands(receive(suppress=True, learn=True, timings=timings),
                                    receive(timings=timings))
        self.assertEqual(records[0], ("RESULT", "SUPPRESSED"))
        self.assertEqual(sum(r[0] == "NATIVE" for r in records), 1)
        self.assertEqual([r[2]["sequence"] for r in records if r[0] == "MQTT"], [1])

    def test_rm433_dedup_clock_rollover(self):
        timings = FIXTURE["rm433_example"]["timings"]
        records = self.run_commands(
            receive(now=4294967195, timings=timings),
            receive(now=100, timings=timings), receive(now=449, timings=timings),
            receive(now=799, timings=timings))
        self.assertEqual([r[1] for r in records if r[0] == "RESULT"], [
            "DECODED_PUBLISHED", "REPEAT_SUPPRESSED", "REPEAT_SUPPRESSED", "DECODED_PUBLISHED"])

    def test_unknown_raw_requires_opt_in_and_has_exact_signed_payload(self):
        timings = [500, -1500, 1500, -4000]
        records = self.run_commands(receive(timings=timings), receive(learn=True, timings=timings))
        self.assertEqual(records, [
            ("RESULT", "UNDECODED"),
            ("MQTT", FIXTURE["topics"]["raw"], self.expected_receive(
                format="raw", pulse_count=4, durations_us=timings)),
            ("RESULT", "RAW_PUBLISHED")])

    def test_raw_rate_limit_counts_failed_attempts_and_handles_rollover(self):
        timings = [10, -10]
        records = self.run_commands(
            receive(now=4294967195, learn=True, success=False, timings=timings),
            receive(now=398, learn=True, timings=timings),
            receive(now=399, learn=True, timings=timings))
        self.assertEqual([r[1] for r in records if r[0] == "RESULT"], [
            "PUBLISH_FAILED", "RAW_RATE_LIMITED", "RAW_PUBLISHED"])
        self.assertEqual([r[2]["sequence"] for r in records if r[0] == "MQTT"], [1, 2])

    def test_raw_bounds_reject_whole_capture_without_consuming_rate_window(self):
        malformed = [[], [0], [120001], [-120001], [-2147483648], [2147483647], [1] * 257]
        for timings in malformed:
            with self.subTest(timings=timings[:3], count=len(timings)):
                records = self.run_commands(receive(learn=True, timings=timings),
                                            receive(learn=True, timings=[120000, -120000] * 128))
                self.assertEqual(records[0], ("RESULT", "RAW_OUT_OF_BOUNDS"))
                self.assertEqual(records[-1], ("RESULT", "RAW_PUBLISHED"))
                self.assertEqual(records[1][2]["pulse_count"], 256)
                self.assertEqual(len(records[1][2]["durations_us"]), 256)
                self.assertEqual(records[1][2]["sequence"], 1)

    def test_rm433_decoder_rejects_partial_extra_and_each_corrupt_pulse(self):
        fixture = FIXTURE["rm433_example"]["timings"]
        malformed = [fixture[:-1], fixture[:-2], fixture + [240, -720], [240, -720] + fixture]
        for offset in range(50):
            for invalid in (0, -2147483648, 2147483647):
                copy = fixture.copy()
                copy[offset] = invalid
                malformed.append(copy)
        results = self.run_commands(*("decode " + " ".join(map(str, t)) for t in malformed))
        self.assertEqual(results, [("DECODE", "0 3735928559 123")] * len(malformed))

    def test_tx_signed_narrowing_and_binary_string_boundaries(self):
        commands, expected = [], []
        def rc(code, protocol=1, repeats=1, valid=True):
            commands.append(f"rc {protocol} {repeats} {code.hex() or '-'}")
            expected.append(("VALID", str(int(valid))))
        for size in (8, 24, 64):
            for protocol in (1, 8):
                for repeats in (1, 10):
                    rc(b"0" * (size - 1) + b"1", protocol, repeats)
        for size in (0, 1, 7, 65, 1024):
            rc(b"1" * size, valid=False)
        for byte in range(256):
            rc(b"0" * 7 + bytes([byte]), valid=byte in (48, 49))
        for bad in (-2147483648, -1, 0, 9, 2147483647):
            rc(b"01010101", protocol=bad, valid=False)
        for bad in (-2147483648, -1, 0, 11, 2147483647):
            rc(b"01010101", repeats=bad, valid=False)
        boundaries = [(0, 16777215), (0, 255), (0, 15), (0, 15), (1, 10)]
        for index, (low, high) in enumerate(boundaries):
            for value, valid in ((low, True), (high, True), (low - 1, False),
                                 (high + 1, False), (-2147483648, False), (2147483647, False)):
                args = [1193046, 1, 1, 2, 3]
                args[index] = value
                commands.append("dooya " + " ".join(map(str, args)))
                expected.append(("VALID", str(int(valid))))
        self.assertEqual(self.run_commands(*commands), expected)


if __name__ == "__main__":
    unittest.main()
