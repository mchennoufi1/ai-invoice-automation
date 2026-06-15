import fitz  # pymupdf
import base64
from pathlib import Path


SUPPORTED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def load_file_for_claude(file_path: str) -> list[dict]:
    """
    Takes a file path (PDF or image) and returns a list of
    Claude-ready image content blocks — one per page for PDFs,
    one for images.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _pdf_to_image_blocks(file_path)
    elif suffix in SUPPORTED_IMAGE_TYPES:
        return _image_to_block(file_path, SUPPORTED_IMAGE_TYPES[suffix])
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _pdf_to_image_blocks(file_path: str) -> list[dict]:
    """Convert each PDF page to a base64 PNG image block."""
    doc = fitz.open(file_path)
    blocks = []

    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)  # 2x resolution for better accuracy
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.standard_b64encode(img_bytes).decode("utf-8")

        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64,
            }
        })

    doc.close()
    return blocks


def _image_to_block(file_path: str, media_type: str) -> list[dict]:
    """Convert an image file to a base64 content block."""
    with open(file_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    return [{
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": b64,
        }
    }]