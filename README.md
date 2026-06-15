# AI Invoice Processor

An AI-powered invoice processing API that extracts structured data from PDF and image invoices, validates the results, detects duplicates, and exports to JSON and CSV.

Built with Claude Vision (Anthropic), FastAPI, and deployed on Railway.

## What it does

- **Extracts** structured data from any invoice (PDF or image) using Claude Vision — no traditional OCR needed
- **Validates** extracted data: checks VAT math, flags suspicious patterns, confirms totals
- **Detects duplicates** using SHA-256 fingerprinting before processing
- **Exports** results to JSON (per invoice) and CSV (master ledger)
- **Batch upload** support for processing multiple invoices in one request

## Tech stack

| Layer | Technology |
|---|---|
| AI / Vision | Anthropic Claude claude-sonnet-4-6 |
| Backend | FastAPI + Uvicorn |
| PDF handling | PyMuPDF (fitz) |
| Export | pandas + csv |
| Deployment | Railway |

## API endpoints

### `POST /upload-invoice`
Upload a single invoice (PDF, JPG, PNG, WEBP).

```bash
curl -X POST https://your-url.railway.app/upload-invoice \
  -F "file=@invoice.pdf"
```

Response:
```json
{
  "status": "success",
  "data": {
    "invoice_number": "INV-2024-0042",
    "vendor_name": "Acme Software BV",
    "invoice_date": "2024-06-01",
    "due_date": "2024-06-30",
    "currency": "EUR",
    "subtotal": 875.0,
    "vat_rate": 21.0,
    "vat_amount": 183.75,
    "total_amount": 1058.75,
    "line_items": [...],
    "payment_method": "Bank transfer"
  },
  "validation": {
    "summary": "Acme Software BV invoiced EUR 1,058.75...",
    "is_valid": true,
    "flags": []
  },
  "exports": {
    "json": "exports/invoice_20240601.json",
    "csv": "exports/invoices.csv"
  }
}
```

### `POST /upload-batch`
Upload up to 20 invoices in one request.

### `GET /`
Health check.

## Architecture
Upload → PyMuPDF (PDF→image) → Claude Vision API → Structured JSON

→ Duplicate check (SHA-256) → Validation (Claude) → Export (JSON + CSV)

## Local setup

```bash
git clone https://github.com/mchennoufi1/ai-invoice-automation
cd ai-invoice-automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your API key:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

Run:
```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API explorer.

## Why Claude Vision instead of Tesseract OCR

Traditional OCR (Tesseract) extracts raw text, then you need a second LLM call to parse it. Claude Vision does both in one step — it reads the image and returns structured data directly. This means fewer API calls, better accuracy on complex layouts, and no OCR preprocessing pipeline to maintain.

## Business use cases

- Accounting firms automating invoice intake
- Logistics companies processing supplier invoices at scale
- SMEs in NL/EU replacing manual data entry
