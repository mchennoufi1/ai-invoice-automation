import hashlib
from database import fingerprint_exists


def fingerprint(data: dict) -> str:
    """Create a SHA-256 hash from the fields that uniquely identify an invoice."""
    key = "|".join([
        str(data.get("invoice_number") or ""),
        str(data.get("vendor_name") or "").lower().strip(),
        str(data.get("invoice_date") or ""),
        str(data.get("total_amount") or ""),
    ])
    return hashlib.sha256(key.encode()).hexdigest()


def check_duplicate(data: dict) -> tuple[bool, str]:
    """Returns (is_duplicate, fingerprint)."""
    fp = fingerprint(data)
    return fingerprint_exists(fp), fp
