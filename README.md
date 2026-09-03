# Smart Document Search (RAG Pipeline & API)

A modular Retrieval-Augmented Generation (RAG) system for searching and querying documents (PDF, DOCX, TXT, Markdown) with OpenAI embeddings, ChromaDB, and Anthropic Claude.

---

## 📁 Project Architecture

```
SmartDocumentSearch/
├── config.py              # Environment configuration & client initialization
├── document_loader.py     # PDF, DOCX, TXT parsers & text cleaner
├── text_chunker.py        # Boundary-aware text chunking
├── vector_store.py        # OpenAI embeddings & ChromaDB operations (indexing, retrieval)
├── rag_pipeline.py        # Reranker, prompt builder & Claude LLM generation
├── api.py                 # FastAPI REST API endpoints (/index, /query) & CORS
├── cli.py                 # Interactive terminal chat & indexing CLI
├── smart_search.py        # Unified backwards-compatible entry point
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variables template
```

---

## ⚡ Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```ini
   OPENAI_API_KEY="your-openai-api-key"
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

---

## 🚀 Running the Project

### 1. Terminal Chat (CLI Mode)
* **Index a document and chat:**
  ```bash
  python cli.py path/to/document.pdf
  ```
* **Chat using previously indexed documents:**
  ```bash
  python cli.py
  ```

### 2. FastAPI Web Server
* **Start the server:**
  ```bash
  uvicorn api:app --reload
  ```
* **Interactive Docs:** Navigate to `http://127.0.0.1:8000/docs` in your browser.

#### Endpoints:
* `POST /index`: Upload a document (`.pdf`, `.docx`, `.doc`, `.txt`, `.md`) to embed and store in ChromaDB.
* `POST /query`: Query the database with a question and get a grounded answer with sources.
