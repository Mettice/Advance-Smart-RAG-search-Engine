"""
Vector store module.
Handles text embeddings and ChromaDB operations (indexing, upserting, and vector retrieval).
"""

import os
from typing import List, Tuple, Dict, Any, Optional
from config import openai_async_client, collection, EMBED_MODEL, TOP_K
from document_loader import load
from text_chunker import chunk_text


async def embed(texts: List[str]) -> List[List[float]]:
    """Generate vector embeddings asynchronously using OpenAI."""
    if not texts:
        return []
    response = await openai_async_client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [item.embedding for item in response.data]


async def index_file(path: str, source_name: Optional[str] = None) -> int:
    """
    Load a document, chunk it, embed it, and store into ChromaDB with upsert.
    Returns the number of indexed chunks.
    """
    source = source_name or os.path.basename(path)
    text = load(path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = await embed(chunks)
    ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(
        embeddings=vectors,
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    return len(chunks)


async def retrieve(question: str, k: int = TOP_K) -> List[Tuple[float, str, Dict[str, Any]]]:
    """Retrieve top-k chunks from ChromaDB closest to the question embedding."""
    q_vecs = await embed([question])
    results = collection.query(
        query_embeddings=q_vecs,
        n_results=k
    )

    scored = []
    if results and results.get("documents") and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            dist = results["distances"][0][i] if results.get("distances") else 0.0
            chunk = results["documents"][0][i]
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            scored.append((dist, chunk, meta))
    return scored
