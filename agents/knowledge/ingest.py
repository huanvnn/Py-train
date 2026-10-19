"""Prewarm the RAG embedding cache. Run after adding/updating source documents."""
import json
import os
from pathlib import Path
from rag import RagEngine

if __name__ == "__main__":
    root = Path(__file__).parent
    engine = RagEngine(
        os.getenv("RAG_DATA_DIR", str(root / "data")),
        os.getenv("RAG_CACHE_PATH", str(root / ".rag-cache" / "vectors.sqlite3")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
        top_k=int(os.getenv("RAG_TOP_K", "4")),
        min_score=float(os.getenv("RAG_MIN_SCORE", "0.45")),
    )
    print(json.dumps(engine.index_documents()))