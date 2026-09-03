"""
FastAPI application module.
Exposes RESTful endpoints for document ingestion (/index) and RAG querying (/query).
"""

import os
import tempfile
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import TOP_K
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


# ===========================================================================
# Endpoints
# ===========================================================================

@app.get("/")
def root():
    return {
        "service": "Smart Document Search API",
        "status": "online",
        "docs_url": "/docs"
    }


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
