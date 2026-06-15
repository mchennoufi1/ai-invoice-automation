import json
import csv
from pathlib import Path
from datetime import datetime

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


def export_json(data: dict, filename: str = None) -> str:
    """Save extracted invoice data as JSON. Returns the file path."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_{timestamp}.json"

    path = EXPORTS_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return str(path)


def export_csv(data: dict, filename: str = "invoices.csv") -> str:
    """
    Append invoice summary row to a master CSV file.
    Line items are excluded — this is the ledger view businesses actually use.
    """
    path = EXPORTS_DIR / filename
    file_exists = path.exists()

    row = {
        "invoice_number": data.get("invoice_number"),
        "vendor_name":    data.get("vendor_name"),
        "invoice_date":   data.get("invoice_date"),
        "due_date":       data.get("due_date"),
        "currency":       data.get("currency"),
        "subtotal":       data.get("subtotal"),
        "vat_rate":       data.get("vat_rate"),
        "vat_amount":     data.get("vat_amount"),
        "total_amount":   data.get("total_amount"),
        "payment_method": data.get("payment_method"),
        "is_valid":       data.get("is_valid"),
        "flags":          "; ".join(data.get("flags") or []),
        "summary":        data.get("summary"),
        "processed_at":   datetime.now().isoformat(),
    }

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return str(path)