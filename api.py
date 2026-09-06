"""
FastAPI application module.
Exposes RESTful endpoints for document ingestion (/index), RAG querying (/query),
and serves the modern ResearchMate web user interface.
"""

import os
import tempfile
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import (
    TOP_K,
    collection,
    LLM_PROVIDER,
    ANTHROPIC_MODEL,
    OPENAI_CHAT_MODEL,
    EMBED_MODEL
)
from vector_store import index_file
from rag_pipeline import answer

# Create FastAPI application
app = FastAPI(
    title="Smart Document Search API",
    description="High-performance RAG API powered by ChromaDB, OpenAI, and Anthropic Claude",
    version="1.0.0"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ===========================================================================
# Request & Response Schemas
# ===========================================================================

class QueryRequest(BaseModel):
    question: str
    top_k: int = TOP_K


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]


class IndexResponse(BaseModel):
    filename: str
    chunks_indexed: int


class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    model: str
    llm_provider: str
    embed_model: str


# ===========================================================================
# Web UI & Endpoints
# ===========================================================================

@app.get("/")
def serve_ui():
    """Serve the modern dark minimalist web UI."""
    index_file_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file_path):
        return FileResponse(index_file_path)
    return {
        "service": "Smart Document Search API",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """Return live ChromaDB and LLM pipeline statistics."""
    try:
        count = collection.count()
    except Exception:
        count = 0

    active_model = ANTHROPIC_MODEL if LLM_PROVIDER == "anthropic" else OPENAI_CHAT_MODEL

    return StatsResponse(
        collection_name=collection.name,
        total_chunks=count,
        model=active_model,
        llm_provider=LLM_PROVIDER,
        embed_model=EMBED_MODEL
    )


@app.post("/index", response_model=IndexResponse)
async def api_index_file(file: UploadFile = File(...)):
    """Upload and index a document (.pdf, .docx, .doc, .txt, .md) into ChromaDB."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file missing filename.")

    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Supported formats: .pdf, .docx, .txt, .md"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        n_chunks = await index_file(tmp_path, source_name=file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return IndexResponse(filename=file.filename, chunks_indexed=n_chunks)


@app.post("/query", response_model=QueryResponse)
async def api_query(request: QueryRequest):
    """Ask a question to the RAG pipeline."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        ans, sources = await answer(request.question, k=request.top_k)
        return QueryResponse(question=request.question, answer=ans, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
