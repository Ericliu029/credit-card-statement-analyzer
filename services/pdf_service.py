from __future__ import annotations

from io import BytesIO

import pdfplumber


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    chunks: list[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)
