#!/usr/bin/env python3
"""Independent read-only audit of the Nano MC1 native KiCad board.

Does not import the CAD generator, its ledger, or its assertions. The endpoint
groups below come from the selected firmware contract and manufacturer header
pin maps. Native DRC still owns routed continuity; this audit owns assignment,
module hole geometry, supply boundaries and evidence-file consistency.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "nano": "https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf",
    "h2": "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html",
    "xiao": "https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip",
    "wiz": "https://docs.wiznet.io/Product/Modules/Ethernet-Modules/WIZ850io",
}


def sexpr(text):
    root, stack = None, []
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            node = []
            if stack:
                stack[-1].append(node)
            elif root is not None:
                raise ValueError("Multiple S-expression roots")
            else:
                root = node
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ValueError("Unmatched closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise ValueError("Atom outside S-expression")
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack or root is None:
        raise ValueError("Incomplete S-expression")
    return root


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def one(node, key, default=None):
    items = children(node, key)
    if len(items) > 1:
        raise ValueError(f"Expected one {key}, got {len(items)}")
    return items[0][1:] if items else default


def read_board(path):
    root = sexpr(path.read_text())
    if root[0] != "kicad_pcb":
        raise ValueError("Not a KiCad PCB")
    parts = {}
    for fp in children(root, "footprint"):
        ref = next((x[2] for x in children(fp, "property") if x[1] == "Reference"), None)
        if not ref or ref in parts:
            raise ValueError(f"Missing or duplicated reference {ref}")
        pos = one(fp, "at")
        pads = {}
        for p in children(fp, "pad"):
            number = p[1]
            if number in pads:
                raise ValueError(f"Duplicate {ref}.{number}")
            pads[number] = {
                "kind": p[2], "at": list(map(float, one(p, "at")[:2])),
                "size": list(map(float, one(p, "size"))),
                "drill": float(one(p, "drill")[0]),
                "net": (one(p, "net") or [""])[-1],
                "type": (one(p, "pintype") or [""])[0],
            }
        courtyard = []
        for key in ("fp_rect", "fp_line", "fp_poly"):
            for shape in children(fp, key):
                if one(shape, "layer") != ["F.CrtYd"]:
                    continue
                points = (one(shape, "pts") if key == "fp_poly" else
                          [["xy", *one(shape, "start")], ["xy", *one(shape, "end")]])
                courtyard.extend([list(map(float, p[1:])) for p in points if p[0] == "xy"])
        parts[ref] = {"name": fp[1], "layer": one(fp, "layer")[0],
                      "at": list(map(float, pos)), "pads": pads,
                      "courtyard_local_points": courtyard}
    return parts


def board_bounds(path):
    root = sexpr(path.read_text())
    points = []
    for key in ("gr_rect", "gr_line"):
        for shape in children(root, key):
            if one(shape, "layer") == ["Edge.Cuts"]:
                for endpoint in ("start", "end"):
                    points.append(list(map(float, one(shape, endpoint))))
    if not points:
        raise ValueError("No rectangular/linear native board edge")
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def audit_pad_containment(parts, bounds):
    errors = []
    for ref in PIN_SETS:
        fp = parts.get(ref)
        if fp is None:
            continue
        x, y, *angles = fp["at"]
        angle = math.radians(angles[0] if angles else 0)
        for number, p in fp["pads"].items():
            px, py = p["at"]
            gx = x + px * math.cos(angle) + py * math.sin(angle)
            gy = y - px * math.sin(angle) + py * math.cos(angle)
            # All current PTH copper pads fit inside a square of this half-width.
            radius = max(p["size"]) / 2
            if min(gx-radius-bounds[0], gy-radius-bounds[1],
                   bounds[2]-gx-radius, bounds[3]-gy-radius) < -0.001:
                errors.append(f"{ref}:{number} copper pad extends beyond board edge")
    return errors


def audit_courtyards(parts):
    boxes, errors = {}, []
    for ref, fp in parts.items():
        points = fp["courtyard_local_points"]
        if not points:
            continue
        x, y, *angles = fp["at"]
        angle = math.radians(angles[0] if angles else 0)
        transformed = [(x + px*math.cos(angle) + py*math.sin(angle),
                        y - px*math.sin(angle) + py*math.cos(angle)) for px, py in points]
        boxes[ref] = [min(p[0] for p in transformed), min(p[1] for p in transformed),
                      max(p[0] for p in transformed), max(p[1] for p in transformed)]
    for ref, a in boxes.items():
        for ref2, b in boxes.items():
            if ref >= ref2:
                continue
            if (min(a[2], b[2]) > max(a[0], b[0]) + 0.001 and
                    min(a[3], b[3]) > max(a[1], b[1]) + 0.001):
                errors.append(f"Native assembly courtyards overlap: {ref}/{ref2}")
    return errors


def endpoints(text):
    return [tuple(x.split(":", 1)) for x in text.split()]


# Signal labels are descriptive only: equality is checked by native net, not by
# comparing the generator's chosen net names. RX/TX below name the peripheral.
GROUPS = {k: endpoints(v) for k, v in {
    "input_5v": "J1:1 J2:1 J6:1 D1:2 D2:2 D3:2",
    "nano_vin": "D1:1 U1:JP1.15",
    "h2_5v": "D2:1 U2:J1.14",
    "xiao_vin": "D3:1 U3:14",
    "peripheral_3v3": "J2:3 J3:1 J4:1 J5:1 J7:2 U4:J2.2 U4:J2.3 R1:1 R2:1",
    "ground": "J1:2 J2:2 J2:4 J3:2 J4:2 J4:3 J5:2 J6:2 J7:1 J8:2 J9:2 U1:JP1.14 U1:JP2.4 U2:J1.13 U2:J1.15 U2:J3.1 U2:J3.10 U2:J3.12 U2:J3.15 U3:13 U4:J1.1 U4:J1.2 U4:J2.1",
    "spi_clock": "U1:JP1.10 U4:J1.4 J5:3",
    "spi_mosi": "U1:JP1.8 U4:J1.3 J5:4",
    "spi_miso": "U1:JP1.9 U4:J2.6 J5:5",
    "ethernet_cs": "U1:JP1.11 U4:J1.5",
    "ethernet_irq": "U1:JP2.10 U4:J1.6",
    "ethernet_reset": "U1:JP2.9 U4:J2.5",
    "rf_cs": "U1:JP2.6 J5:6 R2:2",
    "rf_tx_gdo0": "U1:JP1.7 J5:7 R1:2",
    "rf_rx_gdo2": "U1:JP2.5 J5:8",
    "thread_rx_gpio4": "U1:JP2.1 U2:J1.9",
    "thread_tx_gpio5": "U1:JP2.2 U2:J1.10",
    "thread_enable": "U1:JP2.15 U2:J1.2",
    "thread_boot_gpio9": "U1:JP1.1 U2:J3.11",
    "zigbee_rx_pc07": "U1:JP2.11 U3:8",
    "zigbee_tx_pc06": "U1:JP2.12 U3:7",
    "zigbee_cts_pc04": "U1:JP2.7 U3:5",
    "zigbee_rts_pc05": "U1:JP2.13 U3:6",
    "zigbee_boot_pc00": "J8:1 U3:1",
    "nano_boot_gpio0": "J9:1 U1:JP1.13",
    "i2c_sda": "U1:JP1.4 J3:3 J7:3",
    "i2c_scl": "U1:JP1.5 J3:4 J7:4",
    "radar_rx": "U1:JP2.8 J6:3",
    "radar_tx": "U1:JP2.14 J6:4",
    "zwave_rx": "J3:5 J4:4",
    "zwave_tx": "J3:6 J4:5",
}.items()}

PIN_SETS = {
    "U1": {f"{r}.{i}" for r in ("JP1", "JP2") for i in range(1, 16)},
    "U2": {f"{r}.{i}" for r in ("J1", "J3") for i in range(1, 16)},
    "U3": {str(i) for i in range(1, 15)},
    "U4": {f"{r}.{i}" for r in ("J1", "J2") for i in range(1, 7)},
    **{f"J{i}": {str(n) for n in range(1, count + 1)}
       for i, count in enumerate((2, 4, 6, 5, 8, 4, 4, 2, 2), 1)},
    **{ref: {"1", "2"} for ref in ("D1", "D2", "D3", "R1", "R2")},
}


def expected_xy(ref, number):
    if ref == "U1":
        row, n = number.split("."); n = int(n)
        return [0.0, (n - 1) * 2.54] if row == "JP1" else [15.24, (15 - n) * 2.54]
    if ref == "U2":
        row, n = number.split(".")
        return [0.0 if row == "J1" else 22.86, (int(n) - 1) * 2.54]
    if ref == "U3":
        n = int(number)
        return [0.0, (n - 1) * 2.54] if n <= 7 else [15.24, (14 - n) * 2.54]
    if ref == "U4":
        row, n = number.split(".")
        return [0.0 if row == "J1" else 20.32, (int(n) - 1) * 2.54]
    return None


def audit(parts):
    errors, assigned, nets = [], {}, {}
    for ref, expected in PIN_SETS.items():
        if ref not in parts:
            errors.append(f"Missing {ref}"); continue
        fp = parts[ref]
        if fp["layer"] != "F.Cu":
            errors.append(f"{ref} is not mounted on top")
        if set(fp["pads"]) != expected:
            errors.append(f"{ref} header pin set differs")
        for number, p in fp["pads"].items():
            if p["kind"] != "thru_hole":
                errors.append(f"{ref}:{number} is not a plated through-hole")
            xy = expected_xy(ref, number)
            if xy is not None and math.dist(xy, p["at"]) > 0.001:
                errors.append(f"{ref}:{number} manufacturer hole position differs")
            if xy is not None and (abs(p["drill"] - 1.1) > 0.001 or min(p["size"]) < 1.8):
                errors.append(f"{ref}:{number} module pin hole/pad allowance differs")
    for ref, fp in parts.items():
        if ref not in PIN_SETS and any(p["kind"] != "np_thru_hole" or p["net"] for p in fp["pads"].values()):
            errors.append(f"Unexpected electronic footprint {ref}")
    for group, members in GROUPS.items():
        group_nets = set()
        for ref, number in members:
            if (ref, number) in assigned:
                raise ValueError(f"Audit definition duplicates {ref}:{number}")
            assigned[(ref, number)] = group
            p = parts.get(ref, {}).get("pads", {}).get(number)
            if p is None:
                errors.append(f"Missing {ref}:{number} for {group}"); continue
            if not p["net"] or p["net"].startswith("unconnected-") or "no_connect" in p["type"]:
                errors.append(f"{ref}:{number} is unconnected but required for {group}")
            group_nets.add(p["net"])
        if len(group_nets) != 1:
            errors.append(f"{group} endpoints are split across nets")
        elif group_nets:
            net = next(iter(group_nets))
            if net in nets:
                errors.append(f"{group} is shorted to {nets[net]}")
            nets[net] = group
    all_net_counts = Counter(p["net"] for fp in parts.values() for p in fp["pads"].values() if p["net"])
    for ref in PIN_SETS:
        for number, p in parts.get(ref, {}).get("pads", {}).items():
            if (ref, number) not in assigned:
                if p["net"] and (not p["net"].startswith("unconnected-") or all_net_counts[p["net"]] != 1):
                    errors.append(f"Reserved {ref}:{number} is connected")
    return errors


def evidence(cad):
    manifest = json.loads((cad / "verification.json").read_text())
    errors = []
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((cad / name).read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"Verification hash mismatch: {name}")
    checks = manifest["checks"]
    for key in ("erc_violations", "drc_violations", "unconnected_items", "schematic_parity_issues"):
        if checks[key] != 0:
            errors.append(f"Native check {key}={checks[key]}")
    drc = json.loads((cad / "checks/drc.json").read_text())
    erc = json.loads((cad / "checks/erc.json").read_text())
    actual = {
        "erc_violations": sum(len(s["violations"]) for s in erc["sheets"]),
        "drc_violations": len(drc["violations"]),
        "unconnected_items": len(drc["unconnected_items"]),
        "schematic_parity_issues": len(drc["schematic_parity"]),
    }
    for key, value in actual.items():
        if value != checks[key]:
            errors.append(f"Native report/manifest mismatch: {key}")
    report_hashes = {name: hashlib.sha256((cad / name).read_bytes()).hexdigest()
                     for name in ("checks/drc.json", "checks/erc.json")}
    return errors, len(manifest["sha256"]), checks, report_hashes


def mutations(parts, bounds):
    """Prove the independent audit catches plausible assembly/netlist mistakes."""
    cases = {
        "thread_tx_rx_swap": lambda p: swap_net(p, ("U2", "J1.9"), ("U2", "J1.10")),
        "zigbee_flow_control_swap": lambda p: swap_net(p, ("U3", "5"), ("U3", "6")),
        "shared_spi_split": lambda p: p["J5"]["pads"]["5"].update(net="/BROKEN_MISO"),
        "nano_vbus_connected": lambda p: p["U1"]["pads"]["JP1.12"].update(net=p["J1"]["pads"]["1"]["net"]),
        "regulator_outputs_joined": lambda p: p["U3"]["pads"]["12"].update(net=p["J2"]["pads"]["3"]["net"]),
        "supply_diode_short": lambda p: p["D1"]["pads"]["1"].update(net=p["D1"]["pads"]["2"]["net"]),
        "missing_manual_boot": lambda p: p.pop("J9"),
        "nano_reversed_row": lambda p: p["U1"]["pads"]["JP2.1"].update(at=[15.24, 0.0]),
        "underside_component": lambda p: p["R1"].update(layer="B.Cu"),
        "header_outside_board": lambda p: p["J5"].update(at=[-10.0, -10.0, 0.0]),
        "overlapping_diodes": lambda p: p["D2"].update(at=list(p["D1"]["at"])),
    }
    result = {}
    for name, change in cases.items():
        mutated = copy.deepcopy(parts)
        change(mutated)
        result[name] = bool(audit(mutated) + audit_pad_containment(mutated, bounds) + audit_courtyards(mutated))
    return result


def swap_net(parts, a, b):
    ap, bp = parts[a[0]]["pads"][a[1]], parts[b[0]]["pads"][b[1]]
    ap["net"], bp["net"] = bp["net"], ap["net"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=HERE / "cad/mc1.kicad_pcb")
    parser.add_argument("--skip-evidence", action="store_true", help="For a preliminary board before final exports")
    parser.add_argument("--self-test", action="store_true", help="Inject eleven plausible errors in memory")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    parts = read_board(args.board)
    bounds = board_bounds(args.board)
    errors = audit(parts) + audit_pad_containment(parts, bounds) + audit_courtyards(parts)
    hashes, checks, report_hashes = None, None, None
    if not args.skip_evidence:
        evidence_errors, hashes, checks, report_hashes = evidence(args.board.parent)
        errors.extend(evidence_errors)
    mutation_results = mutations(parts, bounds) if args.self_test and not errors else {}
    errors.extend(f"Mutation not detected: {k}" for k, detected in mutation_results.items() if not detected)
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": args.board.name,
        "board_sha256": hashlib.sha256(args.board.read_bytes()).hexdigest(),
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "manufacturer_sources": SOURCES,
        "electronic_references": len(PIN_SETS),
        "expected_pads": sum(map(len, PIN_SETS.values())),
        "native_board_bounds_mm": bounds,
        "connected_endpoint_groups": len(GROUPS),
        "connected_pads": sum(map(len, GROUPS.values())),
        "native_checks": checks,
        "native_report_sha256": report_hashes,
        "manifest_hashes_checked": hashes,
        "mutations_detected": mutation_results,
        "errors": errors,
        "passed": not errors,
        "limits": "Read-only net-assignment and module-hole audit. DRC supplies route continuity. No physical fit, power, RF, USB or runtime test.",
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
