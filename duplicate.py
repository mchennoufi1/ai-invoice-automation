import hashlib
import json
from pathlib import Path

SEEN_FILE = "seen_invoices.json"


def _load_seen() -> dict:
    """Load the registry of previously seen invoice hashes."""
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_seen(seen: dict):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def fingerprint(data: dict) -> str:
    """
    Create a hash from the fields most likely to uniquely identify an invoice.
    Robust to minor formatting differences.
    """
    key = "|".join([
        str(data.get("invoice_number") or ""),
        str(data.get("vendor_name") or "").lower().strip(),
        str(data.get("invoice_date") or ""),
        str(data.get("total_amount") or ""),
    ])
    return hashlib.sha256(key.encode()).hexdigest()


def check_duplicate(data: dict) -> tuple[bool, str]:
    """
    Returns (is_duplicate, hash).
    If duplicate, the hash matches a previously seen invoice.
    """
    seen = _load_seen()
    fp = fingerprint(data)

    if fp in seen:
        return True, fp
    return False, fp


def register_invoice(data: dict, fp: str):
    """Mark an invoice hash as seen."""
    seen = _load_seen()
    seen[fp] = {
        "invoice_number": data.get("invoice_number"),
        "vendor_name": data.get("vendor_name"),
        "total_amount": data.get("total_amount"),
        "invoice_date": data.get("invoice_date"),
    }
    _save_seen(seen)