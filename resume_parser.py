from __future__ import annotations

import io
from pathlib import Path

import pdfplumber


class ResumeParseError(Exception):
    """Raised when a resume cannot be parsed into usable text."""


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from a PDF byte stream."""
    if not file_bytes:
        raise ResumeParseError("Uploaded PDF is empty.")

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [(page.extract_text() or "").strip() for page in pdf.pages]
    except Exception as exc:  # pragma: no cover - library-specific parsing failures
        raise ResumeParseError("Unable to read the PDF resume.") from exc

    text = "\n\n".join(page for page in pages if page).strip()
    if not text:
        raise ResumeParseError("The PDF did not contain extractable text.")
    return text


import docx

def extract_text_from_word_file(file_path: str | Path) -> str:
    """Extract text from a Word document."""
    try:
        doc = docx.Document(file_path)
        text = "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
        if not text:
            raise ResumeParseError("The Word document is empty or unreadable.")
        return text
    except Exception as exc:  # pragma: no cover
        raise ResumeParseError("Unable to read the Word (.docx) file.") from exc


def extract_text_from_file(file_path: str | Path) -> str:
    """Extract text from a supported file path."""
    path = Path(file_path)
    if not path.exists():
        raise ResumeParseError("Resume file was not found.")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf_bytes(path.read_bytes())
    if suffix == ".docx":
        return extract_text_from_word_file(path)

    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            raise ResumeParseError("The uploaded text file is empty.")
        return text

    raise ResumeParseError("Unsupported file type. Please upload a PDF, DOCX, or text file.")


def normalize_resume_text(raw_text: str) -> str:
    """Normalize pasted resume text."""
    text = raw_text.strip()
    if not text:
        raise ResumeParseError("Resume text is empty.")
    return text
