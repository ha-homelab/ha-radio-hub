#!/usr/bin/env python3
"""Export the checked MC2-C prototype, or reject a stale published package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAD = ROOT / "hardware/external-antenna/cad"
ARCHIVE = "MC2-C-prototype-gerbers.zip"
EXPECTED = {
    "mc2-F_Cu.gtl", "mc2-B_Cu.gbl",
    "mc2-F_Mask.gts", "mc2-B_Mask.gbs",
    "mc2-F_Silkscreen.gto", "mc2-B_Silkscreen.gbo",
    "mc2-Edge_Cuts.gm1", "mc2-PTH.drl", "mc2-NPTH.drl", "mc2-job.gbrjob",
}
EVIDENCE = [
    "hardware/external-antenna/cad/verification.json",
    "hardware/external-antenna/cad/checks/reproduction.json",
    "firmware/external-antenna/c6-build-evidence.json",
    "firmware/external-antenna/build-evidence.json",
    "firmware/external-antenna/prepare_c6.py",
    "firmware/external-antenna/tinyc6d_antenna.c",
    "firmware/external-antenna/tinyc6d_antenna.h",
    "firmware/external-antenna/c6_identity.py",
    "mechanical/full-hub/verification.json",
    "mechanical/full-hub/print-manifest.json",
    "hardware/external-antenna/rf-bom.json",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_sources() -> dict[str, str]:
    evidence = json.loads((CAD / "verification.json").read_text())
    if evidence["kicad_version"] != "10.0.6":
        raise ValueError("Expected pinned KiCad 10.0.6")
    if evidence["checks"] != dict(erc=0, drc=0, unconnected=0, schematic_parity=0):
        raise ValueError("Native checks must all pass without waivers")
    design = json.loads((CAD / "design.json").read_text())
    if design["revision"] != "MC2-C":
        raise ValueError("Only the MC2-C assembly is eligible")
    u2 = next(p for p in design["parts"] if p["ref"] == "U2")
    if "TinyC6[D]" not in u2["model"]:
        raise ValueError("U2 must be the TinyC6[D] assembly")
    sources = {}
    for name, expected in evidence["source_sha256"].items():
        path = CAD / name
        actual = sha(path.read_bytes())
        if actual != expected:
            raise ValueError(f"Stale native evidence: {name}")
        sources[path.relative_to(ROOT).as_posix()] = actual
    for name in EVIDENCE:
        sources[name] = sha((ROOT / name).read_bytes())
    firmware = ROOT / "firmware/external-antenna"
    c6 = json.loads((firmware / "c6-build-evidence.json").read_text())
    host = json.loads((firmware / "build-evidence.json").read_text())
    if (not c6["compiled"] or c6["board_sku"] != "TC6D-01"
            or c6["hardware_revision"] != "MC2-C"
            or c6["antenna"]["mode"] != "external"
            or not c6["antenna"]["initialized_before_radio"]):
        raise ValueError("Missing compiled MC2-C external-antenna C6 evidence")
    if not host["compiled"] or not host["profile"].startswith("MC2-C"):
        raise ValueError("Missing compiled MC2-C host evidence")
    if (firmware / "pin-plan.json").read_bytes() != (CAD / "pin-plan.json").read_bytes():
        raise ValueError("Firmware pin plan differs from the native carrier")
    for report in (c6, host):
        for name, expected in report["recipe_sha256"].items():
            path = firmware / name
            actual = sha(path.read_bytes())
            if actual != expected:
                raise ValueError(f"Stale firmware evidence: {name}")
            sources[path.relative_to(ROOT).as_posix()] = actual
    mechanical = ROOT / "mechanical/full-hub"
    report = json.loads((mechanical / "verification.json").read_text())
    prints = json.loads((mechanical / "print-manifest.json").read_text())
    if (report["native_pcb_revision"] != "MC2-C"
            or prints["native_pcb_revision"] != "MC2-C"
            or prints["source_report_sha256"] != sha((mechanical / "verification.json").read_bytes())):
        raise ValueError("Enclosure evidence must match the MC2-C carrier")
    for name, expected in report["source_sha256"].items():
        path = (CAD if name in {"mc2.kicad_pcb", "design.json"} else mechanical) / name
        actual = sha(path.read_bytes())
        if actual != expected:
            raise ValueError(f"Stale mechanical evidence: {name}")
        sources[path.relative_to(ROOT).as_posix()] = actual
    for name, expected in report["generated_sha256"].items():
        path = mechanical / name
        actual = sha(path.read_bytes())
        if actual != expected:
            raise ValueError(f"Changed mechanical artifact: {name}")
        sources[path.relative_to(ROOT).as_posix()] = actual
    reproduction = json.loads((CAD / "checks/reproduction.json").read_text())
    if reproduction["status"] != "pass" or reproduction["topology_sha256"] != evidence["topology_sha256"]:
        raise ValueError("Missing clean reproduction of this carrier")
    return dict(sorted(sources.items()))


def inspect_files(files: dict[str, bytes]) -> None:
    if set(files) != EXPECTED:
        raise ValueError("Archive must contain exactly seven Gerbers, two drills and one job")
    job = json.loads(files["mc2-job.gbrjob"])
    specs = job["GeneralSpecs"]
    if specs["LayerNumber"] != 2 or specs["BoardThickness"] != 1.6:
        raise ValueError("Incorrect exported stackup")
    if specs["ProjectId"]["Revision"] != "MC2-C":
        raise ValueError("Exported job has the wrong revision")
    for name in ("mc2-F_Cu.gtl", "mc2-B_Cu.gbl"):
        text = files[name].decode()
        if "%MOMM*%" not in text or ",MC2-C*%" not in text:
            raise ValueError(f"Wrong unit or revision in {name}")
    if "NonPlated" not in files["mc2-NPTH.drl"].decode():
        raise ValueError("Missing non-plated drill classification")
    if "Plated,1,2,PTH" not in files["mc2-PTH.drl"].decode():
        raise ValueError("Missing plated drill classification")


def check() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    if manifest["source_sha256"] != current_sources():
        raise ValueError("Fabrication package is stale; regenerate after the design/evidence changes")
    data = (HERE / ARCHIVE).read_bytes()
    if sha(data) != manifest["archive_sha256"]:
        raise ValueError("Archive hash mismatch")
    with zipfile.ZipFile(HERE / ARCHIVE) as archive:
        if len(archive.namelist()) != len(EXPECTED):
            raise ValueError("Unexpected or duplicate archive members")
        files = {n: archive.read(n) for n in archive.namelist()}
    inspect_files(files)
    if {n: sha(b) for n, b in sorted(files.items())} != manifest["files_sha256"]:
        raise ValueError("Fabrication file hash mismatch")
    print("MC2-C fabrication package: sources, evidence and all 10 files match")


def export(cli: str) -> None:
    sources = current_sources()
    version = subprocess.check_output([cli, "version"], text=True).strip()
    if version != "10.0.6":
        raise ValueError(f"Use KiCad 10.0.6, not {version}")
    with tempfile.TemporaryDirectory(prefix="mc2c-fab-") as temp:
        dest = Path(temp)
        def run(*args: str) -> None:
            subprocess.run([cli, *args], check=True, stdout=subprocess.PIPE, text=True)
        run("sch", "erc", "--exit-code-violations", "--severity-all", "--format", "json",
            "--output", str(dest / "erc.json"), str(CAD / "mc2.kicad_sch"))
        run("pcb", "drc", "--exit-code-violations", "--severity-all", "--schematic-parity",
            "--format", "json", "--output", str(dest / "drc.json"), str(CAD / "mc2.kicad_pcb"))
        erc, drc = [json.loads((dest / f"{name}.json").read_text()) for name in ("erc", "drc")]
        if any(s["violations"] for s in erc["sheets"]) or any(drc[k] for k in ("violations", "unconnected_items", "schematic_parity")):
            raise ValueError("Fresh native checks failed")
        gerbers = dest / "gerbers"
        run("pcb", "export", "gerbers", "--layers",
            "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts",
            "--subtract-soldermask", "--output", str(gerbers) + "/", str(CAD / "mc2.kicad_pcb"))
        run("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute",
            "--excellon-units", "mm", "--excellon-zeros-format", "decimal", "--excellon-separate-th",
            "--output", str(gerbers) + "/", str(CAD / "mc2.kicad_pcb"))
        files = {p.name: p.read_bytes() for p in gerbers.iterdir() if p.is_file()}
        inspect_files(files)
        # Fixed ZIP member times; native export timestamps remain honest evidence.
        with zipfile.ZipFile(HERE / ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, (2026, 10, 19, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
    manifest = {
        "schema_version": 1, "revision": "MC2-C",
        "status": "digital_checks_passed_small_prototype_batch",
        "physical_qualification": "not_run",
        "kicad_version": version, "archive": ARCHIVE,
        "archive_sha256": sha((HERE / ARCHIVE).read_bytes()),
        "files_sha256": {n: sha(b) for n, b in sorted(files.items())},
        "source_sha256": sources,
        "fabrication": {
            "width_mm": 100, "height_mm": 100, "layers": 2, "thickness_mm": 1.6,
            "copper_oz": 1, "material": "FR-4", "finish": "Lead-free HASL",
            "mask": "green", "silkscreen": "white", "tented_vias": True,
            "mounting_holes": "4 x 2.7 mm NPTH", "assembly_service": False,
            "recommended_prototype_quantity": 5,
        },
        "note": "Native KiCad exports, no CAM geometry edits. Job bounds can include half the outline stroke; the routed outline centerline is 100 x 100 mm. Not an order, supplier DFM acceptance or physical qualification.",
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    check()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--cli", help="Pinned KiCad 10.0.6 CLI; required for fresh export")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.cli:
        export(args.cli)
    else:
        parser.error("Choose --check or --cli PATH")
