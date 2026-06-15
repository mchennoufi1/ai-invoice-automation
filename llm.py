import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

EXTRACTION_PROMPT = """You are an invoice data extraction expert.

Extract the following fields from this invoice and return ONLY valid JSON — no markdown, no explanation:

{
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "currency": "EUR/USD/GBP etc or null",
  "subtotal": number or null,
  "vat_rate": number or null,
  "vat_amount": number or null,
  "total_amount": number or null,
  "line_items": [
    {"description": "string", "quantity": number, "unit_price": number, "total": number}
  ],
  "payment_method": "string or null",
  "notes": "string or null"
}

If a field is not found, use null. For amounts, return numbers only (no currency symbols).
"""


def extract_invoice_data(image_blocks: list[dict]) -> dict:
    """
    Send invoice image(s) to Claude Vision and get structured JSON back.
    """
    content = image_blocks + [{"type": "text", "text": EXTRACTION_PROMPT}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text
    return _parse_json_response(raw)


def summarize_and_validate(data: dict) -> dict:
    """
    Second Claude call: validate the extracted data and generate a summary.
    """
    prompt = f"""You are an accounting assistant reviewing an extracted invoice.

Invoice data:
{json.dumps(data, indent=2)}

Do the following and return ONLY valid JSON:
1. Write a one-sentence plain-language summary of this invoice
2. Check if subtotal + VAT approximates total (flag if not)
3. Flag any suspicious patterns (missing invoice number, far future due date, etc)

Return this structure:
{{
  "summary": "string",
  "is_valid": true/false,
  "flags": ["list of issues found, or empty list"]
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict:
    """Safely parse JSON, stripping markdown fences if present."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}", "raw": raw}