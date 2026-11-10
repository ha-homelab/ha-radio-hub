"""Exercise the pinned upstream json2 formatter shape and legacy raw reports."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "memory_report", ROOT / "firmware/low-power/memory_report.py")
MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEMORY)
FIXTURE = json.loads((ROOT / "tests/fixtures/esp-idf-size-json2.json").read_text())


class LinkedMemoryTests(unittest.TestCase):
    def read(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "esp_idf_size.json"
            path.write_text(json.dumps(data))
            return MEMORY.read_memory_report(path, **kwargs)

    def test_classic_esp32_keeps_dram_and_iram_separate(self):
        result = self.read(FIXTURE, require_iram=True)
        self.assertEqual(result["ram"], {"used": 100432, "size": 124580})
        self.assertEqual(result["iram"], {"used": 110000, "size": 131072})

    def test_json2_12_image_size_does_not_change_memory_measurements(self):
        # Upstream v1.8.0 / esp_idf_size/ng/format_json.py adds only
        # total_size and version 1.2 to the 1.1 summary layout.
        data = copy.deepcopy(FIXTURE)
        data.update(version="1.2", total_size=1494196)
        self.assertEqual(self.read(data, require_iram=True),
                         self.read(FIXTURE, require_iram=True))
        data["layout"][1]["name"] = "DIRAM"
        data["layout"].pop()
        self.assertEqual(self.read(data)["ram"],
                         {"used": 100432, "size": 124580})
        with self.assertRaisesRegex(ValueError, "Missing.*IRAM"):
            self.read(data, require_iram=True)

    def test_unknown_json2_versions_fail_with_valid_layout(self):
        for version in (None, "1.0", "1.3", "2.0", 1.2, ["1.2"]):
            data = copy.deepcopy(FIXTURE)
            data["version"] = version
            with self.subTest(version=version), self.assertRaisesRegex(
                    ValueError, "Unknown esp-idf-size json2 schema"):
                self.read(data, require_iram=True)

    def test_old_raw_report_retains_same_measurements(self):
        raw = {"memory_types": {region["name"]: {
            "used": region["used"], "size": region["total"]}
            for region in FIXTURE["layout"]}}
        self.assertEqual(self.read(raw, require_iram=True),
                         self.read(FIXTURE, require_iram=True))
        del raw["memory_types"]["DRAM"]["size"]
        with self.assertRaises(ValueError):
            self.read(raw)

    def test_s3_unified_diram_does_not_require_separate_iram(self):
        data = copy.deepcopy(FIXTURE)
        data["layout"][1]["name"] = "DIRAM"
        data["layout"].pop()
        self.assertEqual(self.read(data)["ram"]["used"], 100432)
        with self.assertRaisesRegex(ValueError, "Missing.*IRAM"):
            self.read(data, require_iram=True)

    def test_missing_duplicate_or_unknown_regions_fail(self):
        for data in ({"memory_types": {}}, {"layout": [None], "version": "1.1"},
                     {"layout": [], "version": "2.0"},
                     {"layout": [FIXTURE["layout"][0]], "version": "1.1"},
                     {"layout": [FIXTURE["layout"][1]] * 2, "version": "1.1"},
                     {"layout": [], "memory_types": {}, "version": "1.1"}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.read(data)

    def test_invalid_or_inconsistent_totals_fail(self):
        for version in ("1.1", "1.2"):
            for key, value in (("used", -1), ("used", 124581), ("used", True),
                               ("used", float("inf")), ("used", float("nan")),
                               ("total", 0), ("total", "124580"), ("free", 24149)):
                data = copy.deepcopy(FIXTURE)
                data["version"] = version
                data["layout"][1][key] = value
                with self.subTest(version=version, key=key, value=value), self.assertRaises(
                        ValueError):
                    self.read(data)


if __name__ == "__main__":
    unittest.main()
