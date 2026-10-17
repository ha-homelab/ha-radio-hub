"""Check energy boundaries, uncertainty and lifetime arithmetic."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("energy", ROOT / "tools/energy.py")
energy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(energy)


class EnergyTests(unittest.TestCase):
    def setUp(self):
        self.record = dict(boundary="ac_dedicated", duration_hours=24, energy_wh=60,
                           uncertainty_wh=1, all_functions_passed=True)

    def test_one_continuous_watt_ten_years(self):
        self.assertAlmostEqual(energy.lifetime(1, 10), 87.6)

    def test_reference_model_is_ordered_and_does_not_count_target_as_measurement(self):
        result = energy.planning(energy.read_json(energy.DEFAULT_MODEL))
        self.assertEqual(len(result["variants"]), 6)
        self.assertEqual(result["target"]["kind"], "design_target_not_measurement")
        self.assertAlmostEqual(result["target"]["lifetime_kwh"], 262.8)
        for row in result["variants"]:
            self.assertEqual(row["ac_w"], sorted(row["ac_w"]))

    def test_incremental_baseline_uses_its_own_duration_and_sums_uncertainty(self):
        self.record.update(boundary="ac_incremental", energy_wh=120, baseline_energy_wh=30,
                           baseline_duration_hours=12, baseline_uncertainty_wh=0.5)
        result = energy.measurement(self.record)
        self.assertAlmostEqual(result["ac_w"][1], 2.5)
        self.assertAlmostEqual(result["ac_w"][2], 2.5+1/12)
        self.assertEqual(result["target_status"], "met")

    def test_uncertain_target_is_not_passed(self):
        self.record["energy_wh"] = 72
        self.assertEqual(energy.measurement(self.record)["target_status"], "inconclusive")

    def test_short_or_broken_run_cannot_pass(self):
        for key, value in [("duration_hours", 1), ("all_functions_passed", False),
                           ("all_functions_passed", None)]:
            record = dict(self.record, **{key: value})
            self.assertEqual(energy.measurement(record)["target_status"], "not_assessable")

    def test_reject_dc_invalid_numbers_and_double_subtraction(self):
        for key, value in [("boundary", "dc_5v"), ("energy_wh", float("nan")),
                           ("duration_hours", 0), ("uncertainty_wh", -1),
                           ("all_functions_passed", "yes"), ("energy_wh", True),
                           ("baseline_energy_wh", 1)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                energy.measurement(dict(self.record, **{key: value}))

    def test_invalid_scenarios(self):
        source = energy.read_json(energy.DEFAULT_MODEL)
        broken = copy.deepcopy(source)
        broken["efficiency"]["low"] = 0.9
        with self.assertRaises(ValueError):
            energy.planning(broken)
        broken = copy.deepcopy(source)
        broken["variants"][0]["parts"].append(broken["variants"][0]["parts"][0])
        with self.assertRaises(ValueError):
            energy.planning(broken)


if __name__ == "__main__":
    unittest.main()
