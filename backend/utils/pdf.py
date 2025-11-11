from pypdf import PdfReader
from io import BytesIO

def extract_text_from_pdf_bytes(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        parts = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
        return "\n".join(parts)
    except Exception:
        return ""  # fallback, caller may use heuristics or AI directly
