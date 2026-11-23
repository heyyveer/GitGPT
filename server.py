import os
import sys
import time
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Reconfigure stdout for utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.settings import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    GROQ_API_KEY,
    GEMINI_API_KEY,
    GITHUB_TOKEN,
    REPOSITORIES_DIR,
    VECTOR_STORE_DIR,
)
from github.client import GitHubClient
from github.search import RepositorySearcher
from github.repository import RepositoryManager
from rag.loader import RepositoryLoader
from rag.chunker import CodeChunker
from rag.vector_store import VectorStoreManager
from agents.coordinator import MultiAgentCoordinator
from utils.helpers import format_number, format_bytes, parse_github_url, safe_remove_directory

app = FastAPI(
    title="TalkToGitHub API",
    description="Autonomous Multi-Agent Repository Intelligence Platform API",
    version="1.0.0"
)

# Enable CORS for React Vite frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Application State
class AppState:
    active_repo: Optional[Dict[str, Any]] = None
    vector_store: Optional[Any] = None
    coordinator: Optional[MultiAgentCoordinator] = None
    selected_model: str = DEFAULT_GROQ_MODEL
    
    # Ingestion status tracking
    ingesting: bool = False
    ingest_progress: int = 0
    ingest_step: str = ""
    ingest_error: Optional[str] = None
    ingest_repo_name: Optional[str] = None

state = AppState()

# Pydantic Request Models
class SearchRequest(BaseModel):
    query: str
    language: Optional[str] = None
    min_stars: int = 0
    sort: Optional[str] = "best-match"
    top_k: int = 12

class IngestRequest(BaseModel):
    url: str
    force_reclone: bool = False

class ChatRequest(BaseModel):
    message: str
    manual_route: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

class ModelSelectRequest(BaseModel):
    model: str


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/status")
def get_system_status():
    """Returns system status, API readiness, loaded repository and available models."""
    available_models = [
        {"id": "openai/gpt-oss-20b", "name": "OpenAI GPT-OSS 20B (Fast)", "provider": "Groq"},
        {"id": "openai/gpt-oss-120b", "name": "OpenAI GPT-OSS 120B (Deep)", "provider": "Groq"},
        {"id": "qwen/qwen3.8-27b", "name": "Qwen 3.8 27B (Code Expert)", "provider": "Groq"},
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Multimodal)", "provider": "Google"},
    ]
    
    cloned_repos = [p.name for p in REPOSITORIES_DIR.glob("*") if p.is_dir()]
    cached_indices = [p.name for p in VECTOR_STORE_DIR.glob("*") if p.is_dir()]

    return {
        "services": {
            "groq": bool(GROQ_API_KEY),
            "gemini": bool(GEMINI_API_KEY),
            "github": bool(GITHUB_TOKEN)
        },
        "selected_model": state.selected_model,
        "available_models": available_models,
        "active_repo": state.active_repo,
        "is_loaded": state.active_repo is not None,
        "cache_stats": {
            "cloned_count": len(cloned_repos),
            "indices_count": len(cached_indices)
        }
    }


@app.post("/api/settings/model")
def set_model(req: ModelSelectRequest):
    """Change the active reasoning model."""
    state.selected_model = req.model
    if state.vector_store and state.active_repo:
        state.coordinator = MultiAgentCoordinator(
            vector_store=state.vector_store,
            repository_path=state.active_repo["path"],
            model=req.model
        )
    return {"status": "success", "selected_model": state.selected_model}


@app.post("/api/search")
def search_repositories(req: SearchRequest):
    """Search and semantically rank GitHub repositories."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    
    try:
        searcher = RepositorySearcher()
        results = searcher.search(
            task=req.query,
            limit=max(30, req.top_k),
            language=req.language if req.language and req.language != "All" else None,
            min_stars=req.min_stars,
            sort=req.sort or "best-match",
            top_k=req.top_k
        )
        return {"query": req.query, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def run_ingestion_pipeline(url: str, force_reclone: bool = False):
    """Core synchronous pipeline to clone, parse, AST chunk, and embed a repository."""
    owner, repo_name, clean_url = parse_github_url(url)
    state.ingesting = True
    state.ingest_repo_name = repo_name
    state.ingest_error = None

    try:
        # Step 1: Git Clone
        state.ingest_step = f"Cloning {repo_name} (shallow depth=1)..."
        state.ingest_progress = 25
        repo_manager = RepositoryManager()
        repo_path = repo_manager.clone_repository(clean_url, force_reclone=force_reclone)

        # Step 2: Discover files & stats
        state.ingest_step = "Discovering and filtering codebase files..."
        state.ingest_progress = 50
        loader = RepositoryLoader()
        documents = loader.load_files(repo_path)
        stats = repo_manager.get_repository_stats(repo_path)

        if not documents:
            raise ValueError("No supported source files found in this repository.")

        # Step 3: AST & Semantic Chunking
        state.ingest_step = f"AST symbol chunking across {len(documents)} source files..."
        state.ingest_progress = 75
        chunker = CodeChunker()
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        # Step 4: Vector Store (FAISS)
        state.ingest_step = f"Generating vector embeddings for {len(all_chunks)} semantic chunks..."
        state.ingest_progress = 90
        vec_manager = VectorStoreManager()

        if not force_reclone and vec_manager.exists(repo_name):
            vector_store = vec_manager.load_repo(repo_name)
        else:
            vector_store = vec_manager.create_vector_store(all_chunks)
            vec_manager.save_repo(repo_name, vector_store)

        # Step 5: Multi-Agent Coordinator Setup
        state.ingest_step = "Initializing Multi-Agent reasoning swarm..."
        state.ingest_progress = 100
        coordinator = MultiAgentCoordinator(
            vector_store=vector_store,
            repository_path=repo_path,
            model=state.selected_model
        )

        state.active_repo = {
            "name": repo_name,
            "owner": owner,
            "url": clean_url,
            "path": repo_path,
            "stats": stats,
            "chunks_count": len(all_chunks),
            "files_count": len(documents)
        }
        state.vector_store = vector_store
        state.coordinator = coordinator
        state.ingesting = False
        return True, "Success"

    except Exception as e:
        state.ingesting = False
        state.ingest_error = str(e)
        return False, str(e)


@app.post("/api/ingest")
def ingest_repository(req: IngestRequest):
    """Trigger the ingestion pipeline for a given repository URL."""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="Repository URL is required.")
    
    success, msg = run_ingestion_pipeline(req.url.strip(), force_reclone=req.force_reclone)
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    
    return {
        "status": "success",
        "message": f"Successfully ingested {state.active_repo['name']}",
        "repo": state.active_repo
    }


@app.get("/api/ingest/status")
def get_ingestion_status():
    """Poll the real-time progress of an ongoing ingestion."""
    return {
        "ingesting": state.ingesting,
        "progress": state.ingest_progress,
        "step": state.ingest_step,
        "repo_name": state.ingest_repo_name,
        "error": state.ingest_error,
        "active_repo": state.active_repo
    }


@app.get("/api/repo/active")
def get_active_repo():
    """Get active loaded repository information."""
    if not state.active_repo:
        return {"loaded": False, "repo": None}
    return {"loaded": True, "repo": state.active_repo}


@app.post("/api/repo/unload")
def unload_repo():
    """Unload active repository from memory."""
    state.active_repo = None
    state.vector_store = None
    state.coordinator = None
    return {"status": "success", "message": "Repository unloaded"}


@app.post("/api/chat")
def chat_with_agents(req: ChatRequest):
    """Query the MultiAgentCoordinator with question and get verified multi-agent response."""
    if not state.coordinator or not state.active_repo:
        raise HTTPException(
            status_code=400,
            detail="No repository is currently loaded. Ingest a repository first."
        )
    
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        route_mode = req.manual_route if req.manual_route and req.manual_route.upper() != "AUTO" else None
        result = state.coordinator.answer(
            question=req.message.strip(),
            manual_route=route_mode,
            history=req.history
        )
        
        # Serialize documents for JSON response
        serialized_docs = []
        for doc in result.get("documents", []):
            serialized_docs.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "answer": result.get("answer", ""),
            "agent": result.get("agent", "MultiAgentCoordinator"),
            "route": result.get("route", "GENERAL"),
            "latency_seconds": result.get("latency_seconds", 0.0),
            "sources": result.get("sources", []),
            "documents": serialized_docs,
            "verification": result.get("verification", {"verified": True, "confidence": 1.0})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent reasoning failed: {str(e)}")


@app.get("/api/files")
def list_repository_files():
    """List all supported codebase files in the active repository."""
    if not state.active_repo:
        raise HTTPException(status_code=400, detail="No active repository loaded.")
    
    try:
        repo_mgr = RepositoryManager()
        files = repo_mgr.get_repository_files(state.active_repo["path"])
        return {
            "repo": state.active_repo["name"],
            "count": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file")
def get_file_content(path: str = Query(..., description="Relative file path")):
    """Read a specific file from the active repository and extract AST symbols if applicable."""
    if not state.active_repo:
        raise HTTPException(status_code=400, detail="No active repository loaded.")
    
    repo_path = Path(state.active_repo["path"])
    full_path = (repo_path / path).resolve()
    
    # Security check: Ensure file is inside repo_path
    if not str(full_path).startswith(str(repo_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied: Path outside repository.")
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        ast_symbols = []
        if path.endswith(".py"):
            chunker = CodeChunker()
            doc_dict = {
                "content": content,
                "file_path": path,
                "extension": ".py"
            }
            chunks = chunker.chunk_document(doc_dict)
            for c in chunks:
                ast_symbols.append({
                    "symbol": c.get("symbol") or "module",
                    "symbol_type": c.get("symbol_type") or "code",
                    "start_line": c.get("start_line", 1),
                    "end_line": c.get("end_line", 1),
                })
        
        return {
            "file_path": path,
            "content": content,
            "line_count": len(lines),
            "size_bytes": len(content.encode("utf-8")),
            "extension": Path(path).suffix,
            "ast_symbols": ast_symbols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@app.get("/api/cache")
def get_cache_info():
    """List local storage and vector caches on disk."""
    cloned = []
    for c in REPOSITORIES_DIR.glob("*"):
        if c.is_dir():
            size = sum(f.stat().st_size for f in c.rglob("*") if f.is_file())
            cloned.append({"name": c.name, "path": str(c), "size_bytes": size, "formatted_size": format_bytes(size)})
    
    indices = []
    for idx_dir in VECTOR_STORE_DIR.glob("*"):
        if idx_dir.is_dir():
            size = sum(f.stat().st_size for f in idx_dir.rglob("*") if f.is_file())
            indices.append({"name": idx_dir.name, "path": str(idx_dir), "size_bytes": size, "formatted_size": format_bytes(size)})
    
    return {
        "repositories_dir": str(REPOSITORIES_DIR),
        "vector_store_dir": str(VECTOR_STORE_DIR),
        "cloned_repositories": cloned,
        "vector_indices": indices
    }


@app.delete("/api/cache")
def clear_cache():
    """Clear all cloned repositories and FAISS vector index caches."""
    cleared_repos = 0
    cleared_indices = 0
    
    for c in REPOSITORIES_DIR.glob("*"):
        if c.is_dir():
            safe_remove_directory(c)
            cleared_repos += 1
            
    for idx_dir in VECTOR_STORE_DIR.glob("*"):
        if idx_dir.is_dir():
            safe_remove_directory(idx_dir)
            cleared_indices += 1
            
    state.active_repo = None
    state.vector_store = None
    state.coordinator = None
    
    return {
        "status": "success",
        "message": f"Cleared {cleared_repos} repositories and {cleared_indices} vector caches."
    }


# -----------------------------------------------------------------------------
# Static Files & SPA Fallback
# -----------------------------------------------------------------------------
dist_path = Path(__file__).resolve().parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_candidate = dist_path / full_path
        if full_path and file_candidate.exists() and file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(dist_path / "index.html")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TalkToGitHub API server on http://localhost:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
