"""Shared helpers for the historical compact S3 study; no preparation imports."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require_historical_baseline():
    profile = ROOT / "firmware/module-carrier/hub.yaml"
    if hashlib.sha256(profile.read_bytes()).hexdigest() != "5d65e7d74cc29dfd806e94d72e4e37922d53fcaae4702ae2341186c3031d4ff6":
        raise SystemExit("Historical study helper: reproduce from revision 177a547c70bba11d5f48dee0bdc8595670a4fafb. "
                         "For the current Nano board, use firmware/module-carrier/validate.py.")


def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one original fragment in {path}: {old!r}")
    path.write_text(text.replace(old, new))


