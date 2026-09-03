"""
Text chunking module.
Splits text into overlapping windows respecting natural document boundaries.
"""

from typing import List
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping windows respecting paragraph, sentence, and word boundaries.
    """
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Find the best split point within the overlap window
            split_at = text.rfind("\n\n", start + overlap, end)
            if split_at == -1:
                split_at = text.rfind("\n", start + overlap, end)
            if split_at == -1:
                split_at = text.rfind(". ", start + overlap, end)
            if split_at == -1:
                split_at = text.rfind(" ", start + overlap, end)

            if split_at != -1 and split_at > start:
                end = split_at + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = max(end - overlap, start + 1)

    return chunks
