import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from github.repository import RepositoryManager
from rag.loader import RepositoryLoader
from rag.chunker import CodeChunker
from rag.vector_store import VectorStoreManager
from rag.retriever import RepositoryRetriever
from rag.generator import AnswerGenerator
from agents.verification_agent import VerificationAgent


# ------------------------------------------------
# 1. Clone repository
# ------------------------------------------------
manager = RepositoryManager()
repo_path = manager.clone_repository(
    "https://github.com/Faridghr/Simple-RAG-Chatbot"
)
print("Repository:", repo_path)


# ------------------------------------------------
# 2. Load repository files
# ------------------------------------------------
loader = RepositoryLoader()
documents = loader.load_files(repo_path)
print("Documents:", len(documents))


# ------------------------------------------------
# 3. Create code-aware chunks
# ------------------------------------------------
chunker = CodeChunker()
all_chunks = []
for document in documents:
    chunks = chunker.chunk_document(document)
    all_chunks.extend(chunks)

print("Total chunks:", len(all_chunks))


# ------------------------------------------------
# 4. Create FAISS vector store
# ------------------------------------------------
print("\nCreating embeddings...")
vector_manager = VectorStoreManager()
vector_store = vector_manager.create_vector_store(all_chunks)
print("Vector store created successfully.")


# ------------------------------------------------
# 5. Save vector store
# ------------------------------------------------
vector_manager.save_repo("Simple-RAG-Chatbot", vector_store)
print("Vector store saved.")


# ------------------------------------------------
# 6. Create retriever
# ------------------------------------------------
retriever = RepositoryRetriever(vector_store)


# ------------------------------------------------
# 7. Test semantic retrieval
# ------------------------------------------------
query = "Where is the Pinecone vector store initialized?"
print("\nQuery:", query)

results = retriever.retrieve(query, k=3)


# ------------------------------------------------
# 8. Display retrieval results
# ------------------------------------------------
print("\n" + "=" * 70)
print("RETRIEVAL RESULTS")
print("=" * 70)

for i, result in enumerate(results, 1):
    print("\n" + "-" * 50)
    print(f"Result {i}")
    print("File:", result.metadata.get("file_path"))
    print("Lines:", result.metadata.get("start_line"), "-", result.metadata.get("end_line"))
    print("Symbol:", result.metadata.get("symbol"))
    print("Type:", result.metadata.get("symbol_type"))
    print("\nContent:")
    print(result.page_content)


# ------------------------------------------------
# 9. Generate answer
# ------------------------------------------------
generator = AnswerGenerator()
generation = generator.generate(
    question=query,
    documents=results
)

print("\n" + "=" * 70)
print("RAW GENERATED ANSWER")
print("=" * 70)
print(generation["answer"])


# ------------------------------------------------
# 10. Verify answer
# ------------------------------------------------
verifier = VerificationAgent()
verification = verifier.verify(
    answer=generation["answer"],
    documents=results
)

print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)
print("Verified:", verification["verified"])
print("Confidence:", verification["confidence"])
print("Reason:", verification["reason"])


# ------------------------------------------------
# 11. Final answer
# ------------------------------------------------
if verification["verified"]:
    print("\n" + "=" * 70)
    print("FINAL GROUNDED ANSWER")
    print("=" * 70)
    print(verification["answer"])
else:
    print("\n" + "=" * 70)
    print("ANSWER REJECTED / FLAGGED")
    print("=" * 70)
    print("The generated answer contains unverified claims.")