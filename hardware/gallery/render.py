#!/usr/bin/env python3
"""Render the actual native PCB sources; record provenance, not invented assemblies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BOARDS = {
    "carrier-c0": ("hardware/low-power/carrier/carrier.kicad_pcb", 1600, 1050, "top"),
    "mg24-m0": ("hardware/low-power/carrier/mg24-adapter/mg24-adapter.kicad_pcb", 1300, 950, "top"),
    "integrated-i0": ("hardware/low-power/integrated/integrated.kicad_pcb", 1600, 1300, "top"),
    "diy-d0": ("hardware/low-power/diy/diy.kicad_pcb", 1600, 1250, "bottom"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"Invalid PNG: {path}"
    return struct.unpack(">II", data[16:24])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", default="kicad-cli")
    parser.add_argument("--check", action="store_true", help="Verify source/image hashes without rendering")
    args = parser.parse_args()
    manifest_path = HERE / "provenance.json"
    if args.check:
        manifest = json.loads(manifest_path.read_text())
        assert set(manifest["boards"]) == set(BOARDS), "Board inventory changed"
        for name, (source, width, height, side) in BOARDS.items():
            item = manifest["boards"][name]
            assert item["source"] == source
            assert item["options"][item["options"].index("--side") + 1] == side
            assert item["source_sha256"] == digest(ROOT / source), f"Stale source: {name}"
            png = HERE / (name + ".png")
            assert item["image_sha256"] == digest(png), f"Image changed: {name}"
            actual = dimensions(png)
            assert list(actual) == item["image_dimensions_px"]
            # KiCad's viewport can round the requested pixel size down.
            assert 0.95 * width <= actual[0] <= width
            assert 0.95 * height <= actual[1] <= height
        print(f"Gallery provenance and dimensions verified for all {len(BOARDS)} native PCB renders.")
        return

    version = subprocess.check_output([args.kicad_cli, "version"], text=True).strip()
    manifest = {
        "generator": "KiCad pcb render",
        "kicad_version": version,
        "representation": "Unpopulated native PCB, not a photo or assembled-product model",
        "appearance": "Renderer default soldermask/finish; not a fabrication specification",
        "boards": {},
    }
    for name, (source, width, height, side) in BOARDS.items():
        png = HERE / (name + ".png")
        options = ["--width", str(width), "--height", str(height), "--side", side,
                   "--background", "transparent", "--quality", "high", "--perspective",
                   "--rotate", "335,0,15", "--zoom", "0.85"]
        subprocess.run([args.kicad_cli, "pcb", "render", str(ROOT / source),
                        "-o", str(png), *options], check=True, cwd=ROOT)
        manifest["boards"][name] = {
            "source": source, "source_sha256": digest(ROOT / source),
            "image_sha256": digest(png), "options": options,
            "image_dimensions_px": list(dimensions(png)),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
