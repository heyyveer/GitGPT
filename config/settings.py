import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPOSITORIES_DIR = DATA_DIR / "repositories"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Ensure directories exist
REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Ensure Google environment variable is consistently set for libraries
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Model Configurations
# Supported Groq models: openai/gpt-oss-20b, openai/gpt-oss-120b, qwen/qwen3.8-27b
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"

# Vector Store and RAG Configurations
DEFAULT_CHUNK_SIZE = 1500
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_RETRIEVAL_K = 5
MAX_SEARCH_REPOSITORIES = 30
