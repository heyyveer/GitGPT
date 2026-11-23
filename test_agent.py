import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rag.github.repository import RepositoryManager
from rag.loader import RepositoryLoader
from rag.chunker import CodeChunker
from rag.vector_store import VectorStoreManager
from agents.coordinator import MultiAgentCoordinator


# ------------------------------------------------
# 1. Clone repository
# ------------------------------------------------
manager = RepositoryManager()
repo_path = manager.clone_repository(
    "https://github.com/Faridghr/Simple-RAG-Chatbot"
)
print("Repository Cloned:", repo_path)


# ------------------------------------------------
# 2. Load files & stats
# ------------------------------------------------
loader = RepositoryLoader()
documents = loader.load_files(repo_path)
stats = manager.get_repository_stats(repo_path)
print(f"Loaded {len(documents)} allowed files ({stats['total_lines']} lines of code)")


# ------------------------------------------------
# 3. Create code-aware chunks
# ------------------------------------------------
chunker = CodeChunker()
all_chunks = []
for document in documents:
    chunks = chunker.chunk_document(document)
    all_chunks.extend(chunks)

print(f"Generated {len(all_chunks)} semantic chunks")


# ------------------------------------------------
# 4. Create vector store & save
# ------------------------------------------------
print("\nCreating FAISS vector store...")
vector_manager = VectorStoreManager()
vector_store = vector_manager.create_vector_store(all_chunks)
vector_manager.save_repo("Simple-RAG-Chatbot", vector_store)
print("Vector store ready & cached on disk.")


# ------------------------------------------------
# 5. Initialize Multi-Agent Coordinator
# ------------------------------------------------
coordinator = MultiAgentCoordinator(
    vector_store=vector_store,
    repository_path=repo_path
)


# ------------------------------------------------
# 6. Test Multi-Agent Questions Across Routes
# ------------------------------------------------
test_queries = [
    "How do I install and run this project?",
    "Where is the Pinecone vector store initialized in the code?",
    "What error might occur if PINECONE_API_KEY is not set?",
    "Explain the overall architecture and data flow of this application."
]

for query in test_queries:
    print("\n" + "=" * 75)
    print(f"USER QUERY: {query}")
    print("=" * 75)

    result = coordinator.answer(query)

    print(f"[ROUTE]: {result['route']} | [AGENT]: {result['agent']} | [LATENCY]: {result['latency_seconds']}s")
    print("\n--- ANSWER ---")
    print(result["answer"])
    print("\n--- VERIFICATION STATUS ---")
    v = result.get("verification", {})
    print(f"Verified: {v.get('verified')} | Confidence: {v.get('confidence')} | Reason: {v.get('reason')}")