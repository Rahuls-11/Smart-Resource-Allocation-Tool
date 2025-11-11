from io import BytesIO

def extract_text_from_pdf_bytes(data: bytes) -> str:
    """
    Very safe, dependency-light extractor using PyPDF2.
    If PyPDF2 is not installed, return empty string.
    """
    try:
        import PyPDF2  # pip install PyPDF2
    except Exception:
        return ""
    try:
        reader = PyPDF2.PdfReader(BytesIO(data))
        text = []
        for page in reader.pages:
            try:
                text.append(page.extract_text() or "")
            except Exception:
                pass
        return "\n".join(text)
    except Exception:
        return ""
