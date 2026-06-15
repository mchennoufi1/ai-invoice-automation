import shutil
import csv
import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse

from ocr import load_file_for_claude
from llm import extract_invoice_data, summarize_and_validate
from duplicate import check_duplicate, fingerprint
from database import init_db, insert_invoice, get_all_invoices, get_stats
from export import export_json, export_csv
from auth import require_api_key

app = FastAPI(title="AI Invoice Processor")

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "running", "message": "AI Invoice Processor is live"}


@app.get("/invoices")
def list_invoices():
    return {"invoices": get_all_invoices()}


@app.get("/stats")
def stats():
    return get_stats()


@app.get("/export-csv")
def export_all_csv():
    invoices = get_all_invoices()
    if not invoices:
        raise HTTPException(status_code=404, detail="No invoices found")

    path = f"exports/all_invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "invoice_number", "vendor_name", "invoice_date",
            "due_date", "currency", "subtotal", "vat_rate", "vat_amount",
            "total_amount", "payment_method", "summary", "is_valid",
            "flags", "processed_at"
        ])
        writer.writeheader()
        for inv in invoices:
            inv["flags"] = "; ".join(inv["flags"]) if inv["flags"] else ""
            inv.pop("line_items", None)
            inv.pop("fingerprint", None)
            writer.writerow({k: inv.get(k) for k in writer.fieldnames})

    return FileResponse(path, media_type="text/csv", filename="invoices_export.csv")


@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile, _=Depends(require_api_key)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    temp_path = TEMP_DIR / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        image_blocks = load_file_for_claude(str(temp_path))
        invoice_data = extract_invoice_data(image_blocks)

        is_duplicate, fp = check_duplicate(invoice_data)
        if is_duplicate:
            return JSONResponse(status_code=409, content={
                "error": "Duplicate invoice detected",
                "fingerprint": fp,
                "data": invoice_data
            })

        validation = summarize_and_validate(invoice_data)
        insert_invoice(invoice_data, validation, fp)
        json_path = export_json({**invoice_data, **validation})
        csv_path = export_csv({**invoice_data, **validation})

        return {
            "status": "success",
            "data": invoice_data,
            "validation": validation,
            "exports": {"json": json_path, "csv": csv_path}
        }

    finally:
        temp_path.unlink(missing_ok=True)


@app.post("/upload-batch")
async def upload_batch(files: list[UploadFile], _=Depends(require_api_key)):
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 files per batch")

    results = []
    for file in files:
        result = await upload_invoice(file)
        results.append({
            "filename": file.filename,
            "result": result.body if hasattr(result, "body") else result
        })

    return {"status": "batch_complete", "processed": len(results), "results": results}


@app.get("/app")
def frontend():
    return FileResponse("static/index.html")