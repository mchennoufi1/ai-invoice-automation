import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "invoices.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Create tables if they don't exist. Called once on startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint     TEXT UNIQUE NOT NULL,
            invoice_number  TEXT,
            vendor_name     TEXT,
            invoice_date    TEXT,
            due_date        TEXT,
            currency        TEXT,
            subtotal        REAL,
            vat_rate        REAL,
            vat_amount      REAL,
            total_amount    REAL,
            payment_method  TEXT,
            notes           TEXT,
            line_items      TEXT,  -- stored as JSON string
            summary         TEXT,
            is_valid        INTEGER,
            flags           TEXT,  -- stored as JSON string
            processed_at    TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_invoice(data: dict, validation: dict, fingerprint: str):
    """Insert a processed invoice into the database."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO invoices (
            fingerprint, invoice_number, vendor_name, invoice_date,
            due_date, currency, subtotal, vat_rate, vat_amount,
            total_amount, payment_method, notes, line_items,
            summary, is_valid, flags, processed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fingerprint,
        data.get("invoice_number"),
        data.get("vendor_name"),
        data.get("invoice_date"),
        data.get("due_date"),
        data.get("currency"),
        data.get("subtotal"),
        data.get("vat_rate"),
        data.get("vat_amount"),
        data.get("total_amount"),
        data.get("payment_method"),
        data.get("notes"),
        json.dumps(data.get("line_items", [])),
        validation.get("summary"),
        1 if validation.get("is_valid") else 0,
        json.dumps(validation.get("flags", [])),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def fingerprint_exists(fingerprint: str) -> bool:
    """Check if an invoice fingerprint already exists."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM invoices WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    conn.close()
    return row is not None


def get_all_invoices() -> list[dict]:
    """Return all invoices as a list of dicts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM invoices ORDER BY processed_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["line_items"] = json.loads(d["line_items"] or "[]")
        d["flags"] = json.loads(d["flags"] or "[]")
        d["is_valid"] = bool(d["is_valid"])
        result.append(d)
    return result


def get_stats() -> dict:
    """Return summary statistics for the dashboard."""
    conn = get_connection()
    stats = conn.execute("""
        SELECT
            COUNT(*)                        as total_invoices,
            SUM(total_amount)               as total_value,
            AVG(total_amount)               as avg_value,
            SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as flagged_count
        FROM invoices
    """).fetchone()
    conn.close()
    return dict(stats)