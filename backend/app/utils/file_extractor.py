"""
TaskPulse - File Text Extraction Utility
Extracts text content from PDF, DOCX, and plain text files.
"""

import io
import os
import logging

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """
    Extract text from file content based on filename extension.

    Args:
        content: Raw file bytes
        filename: Original filename (used to determine type)

    Returns:
        Extracted text string

    Raises:
        ValueError: If file type is unsupported or extraction fails
    """
    ext = _get_extension(filename)

    if ext == ".pdf":
        return _extract_from_pdf(content)
    elif ext == ".docx":
        return _extract_from_docx(content)
    elif ext in (".txt", ".md"):
        return content.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def is_supported_file(filename: str) -> bool:
    """Check if a filename has a supported extension."""
    return _get_extension(filename) in SUPPORTED_EXTENSIONS


def _get_extension(filename: str) -> str:
    """Get lowercase file extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext


def _extract_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_from_docx(content: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
    return "\n\n".join(paragraphs)
