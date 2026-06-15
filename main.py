import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from ocr import load_file_for_claude
from llm import extract_invoice_data, summarize_and_validate
from duplicate import check_duplicate, register_invoice
from export import export_json, export_csv

app = FastAPI(title="AI Invoice Processor")

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


@app.get("/")
def root():
    return {"status": "running", "message": "AI Invoice Processor is live"}


@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile):
    # Validate file type
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    # Save to temp
    temp_path = TEMP_DIR / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Step 1: Load file and prepare for Claude
        image_blocks = load_file_for_claude(str(temp_path))

        # Step 2: Extract structured data
        invoice_data = extract_invoice_data(image_blocks)

        # Step 3: Check for duplicate
        is_duplicate, fp = check_duplicate(invoice_data)
        if is_duplicate:
            return JSONResponse(status_code=409, content={
                "error": "Duplicate invoice detected",
                "fingerprint": fp,
                "data": invoice_data
            })

        # Step 4: Validate and summarize
        validation = summarize_and_validate(invoice_data)

        # Step 5: Merge and export
        full_record = {**invoice_data, **validation}
        json_path = export_json(full_record)
        csv_path  = export_csv(full_record)

        # Step 6: Register as seen
        register_invoice(invoice_data, fp)

        return {
            "status": "success",
            "data": invoice_data,
            "validation": validation,
            "exports": {
                "json": json_path,
                "csv": csv_path
            }
        }

    finally:
        # Always clean up temp file
        temp_path.unlink(missing_ok=True)


@app.post("/upload-batch")
async def upload_batch(files: list[UploadFile]):
    """Process multiple invoices in one request."""
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 files per batch")

    results = []
    for file in files:
        # Reuse the single upload logic by calling it directly
        result = await upload_invoice(file)
        results.append({
            "filename": file.filename,
            "result": result.body if hasattr(result, "body") else result
        })

    return {"status": "batch_complete", "processed": len(results), "results": results}
