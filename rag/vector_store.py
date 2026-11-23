import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from rag.embeddings import EmbeddingManager, LocalSemanticEmbeddings
from config.settings import VECTOR_STORE_DIR


class VectorStoreManager:

    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.base_dir = Path(VECTOR_STORE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, repo_identifier: str) -> str:
        # e.g., 'owner/repo' or url to 'owner_repo'
        clean = repo_identifier.replace("https://github.com/", "").replace(".git", "").strip("/")
        return re.sub(r"[^\w\-]", "_", clean)

    def _get_embedding_type(self) -> str:
        """Return a string identifying which embedding backend is active."""
        if isinstance(self.embedding_manager.embeddings, LocalSemanticEmbeddings):
            return "local"
        return "gemini"

    def _save_meta(self, path: Path, embedding_type: str) -> None:
        """Persist embedding type metadata so load can reconstruct the same embedder."""
        meta = {"embedding_type": embedding_type}
        (path / "meta.json").write_text(json.dumps(meta))

    def _load_matching_embedding(self, path: Path):
        """
        Return an embedding object whose dimension matches the saved index.
        Reads meta.json; if embedding_type == 'local' or no meta found, uses
        LocalSemanticEmbeddings to avoid dimension-mismatch AssertionErrors.
        """
        meta_file = path / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            embedding_type = meta.get("embedding_type", "local")
        else:
            # Legacy index with no metadata — assume Gemini, but if current
            # embedder is local we have a dimension mismatch. Safest: use
            # whatever the current manager chose.
            embedding_type = self._get_embedding_type()

        if embedding_type == "local":
            return LocalSemanticEmbeddings()
        else:
            # Gemini — use the full manager (which falls back to local if Gemini fails)
            return self.embedding_manager

    def create_vector_store(self, chunks: List[Dict[str, Any]]) -> FAISS:
        if not chunks:
            raise ValueError("No chunks provided to create vector store.")

        texts = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "file_path": chunk["file_path"],
                "chunk_id": chunk["chunk_id"],
                "extension": chunk["extension"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "symbol": chunk.get("symbol") or "",
                "symbol_type": chunk.get("symbol_type") or "code",
            }
            for chunk in chunks
        ]

        # Pass the EmbeddingManager itself (which IS an Embeddings subclass)
        vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embedding_manager,
            metadatas=metadatas
        )

        return vector_store

    def save(self, vector_store: FAISS, path: Optional[Path | str] = None) -> None:
        save_path = Path(path) if path else self.base_dir / "default"
        save_path.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(save_path))
        self._save_meta(save_path, self._get_embedding_type())

    def load(self, path: Optional[Path | str] = None) -> FAISS:
        load_path = Path(path) if path else self.base_dir / "default"
        embeddings = self._load_matching_embedding(load_path)
        return FAISS.load_local(
            str(load_path),
            embeddings,
            allow_dangerous_deserialization=True
        )

    def save_repo(self, repo_identifier: str, vector_store: FAISS) -> Path:
        sanitized = self._sanitize_name(repo_identifier)
        repo_store_path = self.base_dir / sanitized
        repo_store_path.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(repo_store_path))
        self._save_meta(repo_store_path, self._get_embedding_type())
        return repo_store_path

    def load_repo(self, repo_identifier: str) -> FAISS:
        sanitized = self._sanitize_name(repo_identifier)
        repo_store_path = self.base_dir / sanitized
        if not (repo_store_path / "index.faiss").exists():
            raise FileNotFoundError(f"No indexed vector store found for {repo_identifier} at {repo_store_path}")
        embeddings = self._load_matching_embedding(repo_store_path)
        return FAISS.load_local(
            str(repo_store_path),
            embeddings,
            allow_dangerous_deserialization=True
        )

    def exists(self, repo_identifier: str) -> bool:
        sanitized = self._sanitize_name(repo_identifier)
        repo_store_path = self.base_dir / sanitized
        return (repo_store_path / "index.faiss").exists()