#!/usr/bin/env python3
"""Lifetime electricity model and explicitly bounded wall-energy measurements."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "hardware/low-power/energy-comparison.json"


def number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'} and finite")
    return value


def read_json(path):
    def invalid(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(Path(path).read_text(), parse_constant=invalid)


def lifetime(watts, years, hours=8760):
    return number(watts, "watts") * number(years, "years") * number(hours, "hours", positive=True) / 1000


def planning(model, years=10, extra_ac_w=0):
    number(years, "years")
    number(extra_ac_w, "extra_ac_w")
    hours = number(model["hours_per_year"], "hours_per_year", positive=True)
    eta = [number(model["efficiency"][k], f"efficiency.{k}", positive=True)
           for k in ("low", "reference", "high")]
    if not eta[0] <= eta[1] <= eta[2] <= 1:
        raise ValueError("Efficiency must be ordered low <= reference <= high <= 1")
    parts = model["parts"]
    for key, part in parts.items():
        w = part["w"]
        if len(w) != 3:
            raise ValueError(f"{key}: expected low/reference/high watts")
        for value in w:
            number(value, key)
        if not w[0] <= w[1] <= w[2]:
            raise ValueError(f"{key}: unordered power envelope")
    results = []
    seen = set()
    for variant in model["variants"]:
        ident = variant["id"]
        if ident in seen:
            raise ValueError(f"Duplicate variant: {ident}")
        seen.add(ident)
        members = variant["parts"]
        if not members or len(members) != len(set(members)):
            raise ValueError(f"{ident}: empty or duplicate parts")
        dc = [sum(parts[p]["w"][i] for p in members) for i in range(3)]
        # Best-case power uses best efficiency; worst case uses worst efficiency.
        ac = [dc[i] / eta[2-i] + extra_ac_w for i in range(3)]
        results.append({"id": ident, "title": variant["title"], "kind": "engineering_estimate",
                        "dc_w": dc, "ac_w": ac,
                        "annual_kwh": [lifetime(w, 1, hours) for w in ac],
                        "lifetime_kwh": [lifetime(w, years, hours) for w in ac]})
    target = number(model["target"]["ac_w"], "target.ac_w", positive=True)
    return {"years": years, "boundary": model["boundary"], "extra_ac_w": extra_ac_w,
            "envelope_order": ["low", "reference", "high"], "variants": results,
            "target": {"kind": "design_target_not_measurement", "ac_w": target,
                       "lifetime_kwh": lifetime(target, years, hours)}}


def measurement(data, years=10, target_w=3):
    """AC-only: DC readings cannot establish a wall-power target."""
    number(years, "years")
    number(target_w, "target_w", positive=True)
    boundary = data["boundary"]
    if boundary not in ("ac_dedicated", "ac_incremental"):
        raise ValueError("Use ac_dedicated or ac_incremental; DC readings do not establish wall energy")
    hours = number(data["duration_hours"], "duration_hours", positive=True)
    energy = number(data["energy_wh"], "energy_wh")
    uncertainty = number(data["uncertainty_wh"], "uncertainty_wh")
    baseline_wh = data.get("baseline_energy_wh")
    baseline_hours = data.get("baseline_duration_hours")
    baseline_uncertainty = data.get("baseline_uncertainty_wh")
    if boundary == "ac_incremental":
        number(baseline_wh, "baseline_energy_wh")
        number(baseline_hours, "baseline_duration_hours", positive=True)
        number(baseline_uncertainty, "baseline_uncertainty_wh")
        # Normalize a separate, otherwise identical PSE baseline by its duration.
        baseline_rate = baseline_wh / baseline_hours
        baseline_error = baseline_uncertainty / baseline_hours
    else:
        if any(v is not None for v in (baseline_wh, baseline_hours, baseline_uncertainty)):
            raise ValueError("Dedicated AC measurements must not subtract a baseline")
        baseline_rate = baseline_error = 0
    mean = energy / hours - baseline_rate
    if mean < 0:
        raise ValueError("Negative incremental power; baseline is not comparable")
    error = uncertainty / hours + baseline_error
    envelope = [max(0, mean-error), mean, mean+error]
    functions = data["all_functions_passed"]
    if functions is not None and type(functions) is not bool:
        raise ValueError("all_functions_passed must be true, false, or null")
    if hours < 24 or functions is not True:
        verdict = "not_assessable"
    elif envelope[2] <= target_w:
        verdict = "met"
    elif envelope[0] > target_w:
        verdict = "not_met"
    else:
        verdict = "inconclusive"
    return {"kind": "user_supplied_ac_measurement", "boundary": boundary, "years": years,
            "duration_hours": hours, "ac_w": envelope,
            "envelope_order": ["low", "reference", "high"],
            "lifetime_kwh": [lifetime(w, years) for w in envelope],
            "design_target_w": target_w, "target_status": verdict,
            "qualification": "Requires >=24 hours, all functions passing, and uncertainty bounds. Not a hardware certification."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Compare unmeasured engineering scenarios")
    plan.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    plan.add_argument("--years", type=float, default=10)
    plan.add_argument("--extra-ac-w", type=float, default=0,
                      help="New PSE base load only; do not count losses already included in efficiency")
    measure = sub.add_parser("measure", help="Calculate from a completed measurement record")
    measure.add_argument("record", type=Path)
    measure.add_argument("--years", type=float, default=10)
    measure.add_argument("--target-w", type=float, default=3)
    args = parser.parse_args()
    try:
        result = (planning(read_json(args.model), args.years, args.extra_ac_w)
                  if args.command == "plan" else
                  measurement(read_json(args.record), args.years, args.target_w))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
