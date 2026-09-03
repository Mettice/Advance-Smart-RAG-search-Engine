"""
Document loader module.
Handles reading and cleaning of PDF, DOCX, TXT, and Markdown files.
"""

import os
import re
from pypdf import PdfReader
from docx import Document


def read_pdf(path: str) -> str:
    """Read a PDF page by page and extract text with clean page separation."""
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            pages.append(extracted)
    return "\n\n".join(pages)


def read_word(path: str) -> str:
    """Read a .docx file paragraph by paragraph."""
    doc = Document(path)
    parts = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(parts)


def read_text(path: str) -> str:
    """Read a UTF-8 text or markdown file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def clean(text: str) -> str:
    """Clean extracted text by resolving hyphenated line breaks and normalizing whitespace."""
    # Rejoin words broken across line breaks (e.g. docu-\nment -> document)
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # Standardize newline characters
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse excessive blank lines into standard paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple inline spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def load(path: str) -> str:
    """Identify the document reader by file extension, read and clean the text."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        raw = read_pdf(path)
    elif ext in [".docx", ".doc"]:
        raw = read_word(path)
    else:
        raw = read_text(path)
    return clean(raw)
