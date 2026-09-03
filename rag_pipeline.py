"""
RAG Pipeline module.
Handles reranking, context prompt construction, and LLM generation with Claude & OpenAI fallback.
"""

from typing import List, Tuple, Dict, Any
import anthropic
import openai
from config import (
    anthropic_client,
    openai_async_client,
    ANTHROPIC_MODEL,
    OPENAI_CHAT_MODEL,
    LLM_PROVIDER,
    TOP_K
)
from vector_store import retrieve


def rerank(question: str, found: List[Tuple[float, str, Dict[str, Any]]]) -> List[Tuple[float, str, Dict[str, Any]]]:
    """Sort retrieved chunks by ascending distance (highest similarity first)."""
    return sorted(found, key=lambda item: item[0])


def build_prompt(question: str, found: List[Tuple[float, str, Dict[str, Any]]]) -> str:
    """Construct a grounded prompt incorporating retrieved document chunks and sources."""
    if not found:
        return (
            "You are a helpful assistant. No contextual notes were found in the database.\n"
            f"Question: {question}\n\n"
            "State that you do not have documents in your notes to answer this question."
        )

    context_parts = []
    sources = set()
    for idx, (_, chunk, meta) in enumerate(found, 1):
        src = meta.get("source", "Unknown")
        sources.add(src)
        context_parts.append(f"[Excerpt {idx} | Source: {src}]\n{chunk}")

    context = "\n\n".join(context_parts)
    source_str = ", ".join(sources)

    return (
        "Answer the question using ONLY the context below.\n"
        "If the context does not contain the answer, say "
        "\"I don't have that in my notes.\"\n"
        f"Cite the source file(s) [{source_str}] in your answer.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


async def generate_completion(prompt: str) -> str:
    """Generate LLM response with Anthropic Claude and automatic model/provider fallback."""
    if LLM_PROVIDER == "openai":
        response = await openai_async_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    # Anthropic models to try in sequence if a specific version is not enabled on the API key
    candidate_models = [
        ANTHROPIC_MODEL,
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-3-haiku-20240307",
        "claude-3-7-sonnet-20250219"
    ]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    last_error = None
    for model_name in models_to_try:
        try:
            reply = await anthropic_client.messages.create(
                model=model_name,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return reply.content[0].text
        except anthropic.NotFoundError as e:
            last_error = e
            continue
        except Exception:
            raise

    # Graceful fallback to OpenAI (using the existing valid OpenAI key)
    try:
        response = await openai_async_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
    except Exception:
        raise last_error or RuntimeError("Failed to generate completion from LLM.")


async def answer(question: str, k: int = TOP_K) -> Tuple[str, List[str]]:
    """Execute end-to-end RAG query: retrieve, rerank, build prompt, and query the LLM."""
    found = await retrieve(question, k=k)
    found = rerank(question, found)
    prompt = build_prompt(question, found)

    ans = await generate_completion(prompt)
    sources = list({meta.get("source", "Unknown") for _, _, meta in found})
    return ans, sources
