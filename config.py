"""
Configuration module for Smart Document Search.
Loads environment variables and initializes shared API and database clients.
"""

import os
from dotenv import load_dotenv
import openai
from anthropic import AsyncAnthropic
import chromadb

# Load environment variables
load_dotenv()

# LLM Provider and Models
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()  # "anthropic" or "openai"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# RAG Pipeline Hyperparameters
TOP_K = int(os.getenv("TOP_K", "8"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# Global Clients
anthropic_client = AsyncAnthropic()
openai_async_client = openai.AsyncOpenAI()
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="documents")
