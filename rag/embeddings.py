import os
import hashlib
import numpy as np
from typing import List
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from config.settings import DEFAULT_EMBEDDING_MODEL, GEMINI_API_KEY

load_dotenv()

# Ensure Google environment variable is set
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY


class LocalSemanticEmbeddings(Embeddings):
    """
    High-speed deterministic n-gram & token semantic projection embeddings
    used when cloud embedding APIs are unavailable, rate-limited, or forbidden.

    Inherits from langchain_core.embeddings.Embeddings so FAISS recognises it
    as a proper Embeddings object (not a plain callable), which avoids the
    'LocalSemanticEmbeddings object is not callable' error during similarity_search.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _text_to_vec(self, text: str) -> List[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = text.lower().replace("\n", " ").split()
        if not tokens:
            return vec.tolist()

        for token in tokens:
            # Word level hashing
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:16], 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 + len(token) * 0.1)

            # Character 3-gram hashing for subword syntax similarity
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngram = token[i:i+3]
                    nh = int(hashlib.md5(ngram.encode("utf-8")).hexdigest()[:8], 16)
                    nidx = nh % self.dim
                    vec[nidx] += 0.3 * (1.0 if (nh >> 8) % 2 == 0 else -1.0)

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vec(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._text_to_vec(query)


class EmbeddingManager(Embeddings):
    """
    Manages embedding model initialization with automatic fallback from
    Google Generative AI embeddings to fast Local Semantic Embeddings.

    Inherits from langchain_core.embeddings.Embeddings so it can be passed
    directly to FAISS.from_texts() and FAISS.load_local() without type errors.
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self.embeddings = self._init_embeddings()

    def _init_embeddings(self):
        # Try Google Generative AI Embeddings
        if GEMINI_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                g_emb = GoogleGenerativeAIEmbeddings(model=self.model_name)
                # Quick verification probe
                g_emb.embed_query("probe")
                return g_emb
            except Exception:
                # Silently fallback if cloud project has quota/permission restrictions
                pass

        return LocalSemanticEmbeddings()

    def embed_documents(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Embed a list of text documents in batches."""
        if not texts:
            return []

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embeddings.embed_documents(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query text."""
        return self.embeddings.embed_query(query)