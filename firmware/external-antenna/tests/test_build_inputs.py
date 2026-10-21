"""Evidence must describe the prepared recipe and actual compiled local sources."""
from pathlib import Path
import subprocess
import sys
import unittest


class BuildInputTests(unittest.TestCase):
    def test_prepared_and_compiled_sources_cannot_drift(self):
        script = r'''
import shutil
import tempfile
from pathlib import Path
import validate

source = Path(validate.__file__).parent
with tempfile.TemporaryDirectory() as temporary:
    prepared = Path(temporary) / "firmware/external-antenna"
    built = prepared / ".esphome/build/test"
    for name in validate.RECIPE_INPUTS:
        target = prepared / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    copies = {
        "../include/rf_radio_handoff.h": "rf_radio_handoff.h",
        "../components/rf_tx_startup/rf_tx_startup.cpp": "esphome/components/rf_tx_startup/rf_tx_startup.cpp",
    }
    for name in ("transport.h", "wk2132_uart.h", "wk2132_uart.cpp"):
        copies["../module-carrier/components/wk2132_uart/" + name] = "esphome/components/wk2132_uart/" + name
    for name, destination in copies.items():
        target = built / "src" / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(prepared / name, target)
    assert set(validate.verify_recipe_inputs(prepared, built)) == set(validate.RECIPE_INPUTS)
    recipe = prepared / "../packages/rf-airbridge.yaml"
    original = recipe.read_bytes()
    recipe.write_bytes(original + b"\n# stale prepared input\n")
    try:
        validate.verify_recipe_inputs(prepared, built)
    except RuntimeError as error:
        assert "Prepared recipe differs" in str(error)
    else:
        raise AssertionError("Stale prepared recipe was accepted")
    recipe.write_bytes(original)
    runtime = built / "src/esphome/components/wk2132_uart/wk2132_uart.cpp"
    runtime.write_bytes(runtime.read_bytes() + b"\n// stale compiled input\n")
    try:
        validate.verify_recipe_inputs(prepared, built)
    except RuntimeError as error:
        assert "Compiled local source differs" in str(error)
    else:
        raise AssertionError("Stale compiled source was accepted")
'''
        subprocess.run([sys.executable, "-c", script],
                       cwd=Path(__file__).resolve().parents[1], check=True)
