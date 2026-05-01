"""
Simple RAG retriever using sentence-transformers for embeddings and FAISS for index.
Usage:
  - Build index with build_index(folder_path)
  - Query with retrieve(query, top_k=3)

This implementation is intentionally minimal for a prototype/POC.
"""
from typing import List, Tuple, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid hard dependency at import time
_model = None
_faiss = None
_index = None
_doc_map = {}


def _ensure_dependencies():
    global _model, _faiss
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        except Exception as e:
            logger.error("sentence-transformers not available: %s", e)
            raise
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except Exception as e:
            logger.error("faiss not available: %s", e)
            raise


def build_index(doc_folder: str, index_path: str = "./.faiss_index", metadata_path: str = "./.faiss_metadata.json"):
    """Build FAISS index from plain text files in a folder.
    Each file is split into paragraphs by blank lines; each paragraph becomes a document.
    Saves index and metadata to disk.
    """
    _ensure_dependencies()

    docs = []
    for root, _, files in os.walk(doc_folder):
        for fname in files:
            if not fname.lower().endswith(('.txt', '.md')):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            # simple split into paragraphs
            for para in [p.strip() for p in text.split('\n\n') if p.strip()]:
                docs.append({
                    "source": path,
                    "text": para
                })

    if not docs:
        raise ValueError("No documents found to index in: %s" % doc_folder)

    texts = [d['text'] for d in docs]
    embeddings = _model.encode(texts, show_progress_bar=True)

    dim = embeddings.shape[1]
    index = _faiss.IndexFlatL2(dim)
    index.add(embeddings.astype('float32'))

    os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
    _faiss.write_index(index, index_path)

    # Save metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False)

    logger.info("Built FAISS index with %d documents", len(docs))


def load_index(index_path: str = "./.faiss_index", metadata_path: str = "./.faiss_metadata.json"):
    """Load FAISS index and metadata into memory."""
    global _index, _faiss, _doc_map
    _ensure_dependencies()
    if not os.path.exists(index_path):
        raise FileNotFoundError("FAISS index not found: %s" % index_path)
    if not os.path.exists(metadata_path):
        raise FileNotFoundError("FAISS metadata not found: %s" % metadata_path)

    import faiss as _faiss_local
    _index = _faiss_local.read_index(index_path)

    with open(metadata_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    _doc_map = {i: docs[i] for i in range(len(docs))}

    logger.info("Loaded FAISS index with %d docs", len(_doc_map))


def retrieve(query: str, top_k: int = 3) -> List[Tuple[float, str]]:
    """Return list of (score, text) for top_k relevant passages."""
    _ensure_dependencies()
    if _index is None:
        # try to load default
        try:
            load_index()
        except Exception as e:
            logger.error("Failed to load index: %s", e)
            return []

    query_emb = _model.encode([query])
    D, I = _index.search(query_emb.astype('float32'), top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        doc = _doc_map.get(int(idx), {})
        text = doc.get('text', '')
        results.append((float(score), text))
    return results
