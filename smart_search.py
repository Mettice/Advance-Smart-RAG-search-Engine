"""
Smart Document Search — Unified Entry Point
==========================================
Re-exports modular components for backwards compatibility:
- Run CLI: `python smart_search.py` or `python smart_search.py path/to/doc.pdf`
- Run Server: `uvicorn smart_search:app --reload`
"""

import asyncio
from config import (
    ANTHROPIC_MODEL,
    EMBED_MODEL,
    TOP_K,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHROMA_PATH,
    anthropic_client,
    openai_async_client,
    chroma_client,
    collection,
)
from document_loader import read_pdf, read_word, read_text, clean, load
from text_chunker import chunk_text
from vector_store import embed, index_file, retrieve
from rag_pipeline import rerank, build_prompt, answer
from api import app
from cli import main

if __name__ == "__main__":
    asyncio.run(main())