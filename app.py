import os
import sys
from pathlib import Path
import streamlit as st

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


# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TalkToGitHub — Autonomous Multi-Agent Code Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Title Styling */
    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }

    /* Glassmorphic Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.22rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }

    .badge-primary { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-amber   { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-cyan    { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
    .badge-rose    { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }

    /* Agent Badge in Chat */
    .agent-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        background: #1e1b4b;
        color: #c7d2fe;
        border: 1px solid #4338ca;
        margin-bottom: 0.5rem;
    }

    /* Verification Box */
    .verified-box {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin-top: 0.6rem;
        font-size: 0.85rem;
        color: #a7f3d0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "active_repo" not in st.session_state:
    st.session_state["active_repo"] = None  # {name, url, path, stats, chunks_count}

if "vector_store" not in st.session_state:
    st.session_state["vector_store"] = None

if "coordinator" not in st.session_state:
    st.session_state["coordinator"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = DEFAULT_GROQ_MODEL


# -----------------------------------------------------------------------------
# 3. Helper Ingestion Pipeline Function
# -----------------------------------------------------------------------------
def ingest_repository(repo_url: str, force_reclone: bool = False) -> bool:
    """Clone, load, chunk, embed, and initialize agents for a repository."""
    owner, repo_name, clean_url = parse_github_url(repo_url)

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Clone
        status_text.info(f"⏳ Step 1/4: Cloning `{repo_name}` (shallow depth=1)...")
        progress_bar.progress(20)
        repo_manager = RepositoryManager()
        repo_path = repo_manager.clone_repository(clean_url, force_reclone=force_reclone)

        # Step 2: Load
        status_text.info(f"⏳ Step 2/4: Discovering and filtering codebase files...")
        progress_bar.progress(40)
        loader = RepositoryLoader()
        documents = loader.load_files(repo_path)
        stats = repo_manager.get_repository_stats(repo_path)

        if not documents:
            status_text.error("No supported source files found in this repository.")
            return False

        # Step 3: AST & Semantic Chunking
        status_text.info(f"⏳ Step 3/4: AST chunking across {len(documents)} files ({stats['total_lines']:,} lines of code)...")
        progress_bar.progress(65)
        chunker = CodeChunker()
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        # Step 4: Vector Store (FAISS)
        status_text.info(f"⏳ Step 4/4: Generating embeddings for {len(all_chunks)} semantic chunks...")
        progress_bar.progress(85)
        vec_manager = VectorStoreManager()

        # Check cache if not forcing re-clone
        if not force_reclone and vec_manager.exists(repo_name):
            vector_store = vec_manager.load_repo(repo_name)
        else:
            vector_store = vec_manager.create_vector_store(all_chunks)
            vec_manager.save_repo(repo_name, vector_store)

        progress_bar.progress(100)

        # Step 5: Multi-Agent Coordinator
        coordinator = MultiAgentCoordinator(
            vector_store=vector_store,
            repository_path=repo_path,
            model=st.session_state["selected_model"]
        )

        st.session_state["active_repo"] = {
            "name": repo_name,
            "owner": owner,
            "url": clean_url,
            "path": repo_path,
            "stats": stats,
            "chunks_count": len(all_chunks),
            "files_count": len(documents)
        }
        st.session_state["vector_store"] = vector_store
        st.session_state["coordinator"] = coordinator
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": f"👋 Repository **[{repo_name}]({clean_url})** has been fully indexed!\n\n"
                           f"- 📦 **{len(documents)}** Code Files | **{stats['total_lines']:,}** Lines of Code\n"
                           f"- 🧩 **{len(all_chunks)}** AST & Semantic Chunks indexed in Vector Memory\n"
                           f"- 🤖 **Multi-Agent Swarm Ready**: Code Search, Documentation, Debugging, Architecture & Verifier.\n\n"
                           f"Ask any question below or try the quick prompts!",
                "agent": "SystemCoordinator",
                "route": "GENERAL",
                "latency": 0.0,
                "verification": {"verified": True, "confidence": 1.0, "reason": "Repository indexed successfully."}
            }
        ]

        status_text.success(f"🎉 Successfully indexed `{repo_name}`! Ready for multi-agent reasoning.")
        return True

    except Exception as e:
        status_text.error(f"❌ Ingestion failed: {str(e)}")
        return False


# -----------------------------------------------------------------------------
# 4. Sidebar: Active Repository & Global Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **TalkToGitHub**")
    st.caption("Autonomous Multi-Agent Repository Intelligence")

    st.markdown("---")

    # Active Repo Card
    if st.session_state["active_repo"]:
        repo = st.session_state["active_repo"]
        st.markdown(f"#### 📦 **Active Repository**")
        st.markdown(f"**[{repo['name']}]({repo['url']})**")

        st.markdown(f"""
        <div style="background: rgba(99, 102, 241, 0.1); border-left: 3px solid #6366f1; padding: 0.5rem; border-radius: 4px; font-size: 0.85rem; margin-bottom: 0.5rem;">
            📁 <b>{repo['files_count']}</b> files &nbsp;|&nbsp; 📝 <b>{repo['stats']['total_lines']:,}</b> lines<br>
            🧩 <b>{repo['chunks_count']}</b> vector chunks indexed
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Unload / Switch Repository", use_container_width=True):
            st.session_state["active_repo"] = None
            st.session_state["vector_store"] = None
            st.session_state["coordinator"] = None
            st.session_state["messages"] = []
            st.rerun()
    else:
        st.info("ℹ️ No repository loaded. Search or ingest a repo to begin chatting.")

    st.markdown("---")

    # LLM & Model Selection
    st.markdown("#### 🧠 **Model & Reasoning Engine**")
    available_models = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "gemini-3.8-flash"
    ]
    selected = st.selectbox(
        "Inference Model",
        options=available_models,
        index=0,
        help="Select LLM model for routing, generation, and multi-agent reasoning."
    )
    if selected != st.session_state["selected_model"]:
        st.session_state["selected_model"] = selected
        if st.session_state["vector_store"] and st.session_state["active_repo"]:
            st.session_state["coordinator"] = MultiAgentCoordinator(
                vector_store=st.session_state["vector_store"],
                repository_path=st.session_state["active_repo"]["path"],
                model=selected
            )

    # API Status Indicators
    st.markdown("#### 🔌 **Service Status**")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        if GROQ_API_KEY:
            st.markdown("🟢 **Groq LLM**: Ready")
        else:
            st.markdown("🔴 **Groq LLM**: Missing")
    with col_k2:
        if GEMINI_API_KEY:
            st.markdown("🟢 **Gemini**: Ready")
        else:
            st.markdown("🔴 **Gemini**: Missing")

    if GITHUB_TOKEN:
        st.markdown("🟢 **GitHub API**: Authenticated")
    else:
        st.markdown("🟡 **GitHub API**: Public rate limit")

    st.markdown("---")
    st.caption("TalkToGitHub Multi-Agent Architecture v1.0")


# -----------------------------------------------------------------------------
# 5. Main Hero Banner
# -----------------------------------------------------------------------------
st.markdown('<div class="hero-title">🤖 TalkToGitHub</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Discover, ingest, AST-chunk, and converse with any GitHub codebase using specialized Multi-Agent reasoning.</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. Tab Navigation
# -----------------------------------------------------------------------------
tab_search, tab_ingest, tab_chat, tab_explorer, tab_diagnostics = st.tabs([
    "🔍 1. Discover Repositories",
    "📥 2. Ingest Codebase",
    "💬 3. Multi-Agent Chat Studio",
    "📂 4. Code Explorer & AST",
    "⚙️ 5. Diagnostics & Cache"
])


# -----------------------------------------------------------------------------
# TAB 1: DISCOVER REPOSITORIES
# -----------------------------------------------------------------------------
with tab_search:
    st.markdown("### 🔍 Find the Ideal Repository for Your Project")
    st.write("Describe your goal in natural language. Our semantic searcher ranks repositories by keyword match, popularity, stars, and language.")

    # Search Box
    col_input, col_lang, col_stars = st.columns([3, 1, 1])
    with col_input:
        search_prompt = st.text_input(
            "What do you want to build or explore?",
            placeholder="e.g., Simple RAG Chatbot using LangChain and Pinecone"
        )
    with col_lang:
        lang_choice = st.selectbox(
            "Language",
            ["All", "Python", "TypeScript", "JavaScript", "Go", "Rust", "C++", "Java"]
        )
    with col_stars:
        min_stars_val = st.number_input("Min Stars", min_value=0, value=0, step=50)

    # Quick Prompts Chips
    st.markdown("**Quick Topics:**")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    if q_col1.button("🤖 RAG LangChain Chatbot", use_container_width=True):
        search_prompt = "RAG chatbot LangChain vector database"
    if q_col2.button("⚡ FastAPI Microservice", use_container_width=True):
        search_prompt = "FastAPI backend async microservice"
    if q_col3.button("🧠 Agentic AI Swarm", use_container_width=True):
        search_prompt = "Multi-Agent AI reasoning workflow"
    if q_col4.button("👁️ Vision AI PyTorch", use_container_width=True):
        search_prompt = "PyTorch computer vision segmentation"

    if st.button("🚀 Search GitHub Repositories", type="primary", use_container_width=True) or search_prompt:
        if not search_prompt.strip():
            st.warning("Please enter a search description or select a quick topic.")
        else:
            with st.spinner("Searching and ranking GitHub repositories..."):
                try:
                    searcher = RepositorySearcher()
                    results = searcher.search(
                        task=search_prompt,
                        limit=30,
                        language=lang_choice if lang_choice != "All" else None,
                        min_stars=min_stars_val,
                        top_k=8
                    )
                    st.session_state["search_results"] = results
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")

    # Display Search Results
    if st.session_state["search_results"]:
        st.markdown(f"#### 🏆 Top {len(st.session_state['search_results'])} Ranked Repositories")

        for idx, repo in enumerate(st.session_state["search_results"], 1):
            with st.container(border=True):
                col_title, col_action = st.columns([3, 1])

                with col_title:
                    st.markdown(f"### #{idx} [{repo['name']}]({repo['url']})")
                    st.write(repo["description"])

                    # Badges row
                    st.markdown(f"""
                    <span class="badge badge-primary">★ {format_number(repo['stars'])} Stars</span>
                    <span class="badge badge-cyan">🍴 {format_number(repo['forks'])} Forks</span>
                    <span class="badge badge-amber">💻 {repo['language']}</span>
                    <span class="badge badge-success">🎯 Score: {repo['relevance_score']}</span>
                    """, unsafe_allow_html=True)

                    if repo["topics"]:
                        st.caption("🏷️ " + ", ".join(f"`{t}`" for t in repo["topics"][:6]))

                with col_action:
                    st.write("")
                    st.write("")
                    if st.button(f"⚡ Ingest & Chat", key=f"ingest_search_{idx}", type="primary", use_container_width=True):
                        with st.spinner(f"Ingesting {repo['name']}..."):
                            success = ingest_repository(repo["url"])
                            if success:
                                st.success("Repository loaded! Switch to Tab 3 to chat.")
                                st.rerun()


# -----------------------------------------------------------------------------
# TAB 2: INGEST ANY REPOSITORY
# -----------------------------------------------------------------------------
with tab_ingest:
    st.markdown("### 📥 Ingest Any GitHub Repository")
    st.write("Enter any public repository URL (or `owner/repo`) to clone, parse AST symbols, generate embeddings, and build the vector index.")

    col_url, col_force = st.columns([4, 1])
    with col_url:
        custom_url = st.text_input(
            "GitHub Repository URL",
            value="https://github.com/Faridghr/Simple-RAG-Chatbot",
            placeholder="https://github.com/owner/repo"
        )
    with col_force:
        st.write("")
        st.write("")
        force_reindex = st.checkbox("Force Re-index", value=False)

    if st.button("⚡ Start Ingestion Pipeline", type="primary", use_container_width=True):
        if not custom_url.strip():
            st.warning("Please provide a valid GitHub URL.")
        else:
            success = ingest_repository(custom_url.strip(), force_reclone=force_reindex)
            if success:
                st.rerun()

    # If repo loaded, show rich analytics card
    if st.session_state["active_repo"]:
        repo = st.session_state["active_repo"]
        st.markdown("---")
        st.markdown(f"### 📊 Active Repository Ingestion Breakdown: **{repo['name']}**")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📁 Code Files", f"{repo['files_count']}")
        m2.metric("📝 Lines of Code", f"{repo['stats']['total_lines']:,}")
        m3.metric("🧩 Semantic Chunks", f"{repo['chunks_count']}")
        m4.metric("💾 Disk Size", format_bytes(repo['stats']['total_size_bytes']))

        st.markdown("#### 💻 Language Breakdown")
        lang_cols = st.columns(min(len(repo['stats']['languages']), 5) or 1)
        for i, (ext, count) in enumerate(sorted(repo['stats']['languages'].items(), key=lambda x: x[1], reverse=True)[:5]):
            with lang_cols[i % len(lang_cols)]:
                st.info(f"**{ext or 'other'}**: {count} files")


# -----------------------------------------------------------------------------
# TAB 3: MULTI-AGENT CHAT STUDIO
# -----------------------------------------------------------------------------
with tab_chat:
    st.markdown("### 💬 Multi-Agent Conversation Studio")

    if not st.session_state["active_repo"]:
        st.warning("⚠️ No repository currently loaded. Please search for a repository in Tab 1 or ingest a URL in Tab 2 first!")
    else:
        repo = st.session_state["active_repo"]
        coordinator: MultiAgentCoordinator = st.session_state["coordinator"]

        # Control Bar
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
        with col_ctrl1:
            st.markdown(f"**Active Codebase:** `[{repo['name']}]`")
        with col_ctrl2:
            agent_override = st.selectbox(
                "Routing Mode",
                ["AUTO (Query Router)", "CODE_SEARCH", "DOCUMENTATION", "DEBUGGING", "ARCHITECTURE"],
                index=0
            )
        with col_ctrl3:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()

        # Prompt Starters
        st.markdown("**Suggested Questions:**")
        s1, s2, s3, s4 = st.columns(4)
        preset_q = None
        if s1.button("📖 How to install & run?", use_container_width=True):
            preset_q = "How do I install and run this project?"
        if s2.button("🔍 Find Vector Store Setup", use_container_width=True):
            preset_q = "Where is the vector store or database initialized in the code?"
        if s3.button("🏛️ Explain System Architecture", use_container_width=True):
            preset_q = "Explain the overall architecture, data flow, and key components."
        if s4.button("🐛 Find Potential Bugs/Errors", use_container_width=True):
            preset_q = "What errors or exceptions might occur in the main execution flow and how to fix them?"

        st.markdown("---")

        # Render Chat Messages
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
                if msg.get("agent"):
                    agent_name = msg["agent"]
                    route_name = msg.get("route", "")
                    latency = msg.get("latency", 0)
                    ver = msg.get("verification", {})
                    is_verified = ver.get("verified", True)

                    ver_pill = "✓ Grounded" if is_verified else "⚠ Notice"
                    ver_class = "badge-success" if is_verified else "badge-rose"

                    st.markdown(f"""
                    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.4rem;">
                        <span class="badge badge-primary">🤖 {agent_name}</span>
                        <span class="badge badge-cyan">🎯 Route: {route_name}</span>
                        <span class="badge {ver_class}">{ver_pill}</span>
                        <span class="badge badge-amber">⚡ {latency}s</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(msg["content"])

                # Expandable Verified Sources
                if msg.get("sources"):
                    with st.expander(f"📍 Verified Code References ({len(msg['sources'])} sources)"):
                        for s in msg["sources"]:
                            st.markdown(f"**`{s['file_path']}`** (Lines {s.get('start_line', 1)}-{s.get('end_line', 1)})")
                            if s.get("symbol"):
                                st.caption(f"Symbol: `{s['symbol']}` ({s.get('symbol_type', 'code')})")
                            if s.get("full_chunk"):
                                st.code(s["full_chunk"][:400] + "...", language="python")

                # Expandable Raw Evidence Chunks
                if msg.get("documents"):
                    with st.expander(f"🔍 Technical Inspection: Retrieved Context Chunks ({len(msg['documents'])})"):
                        for i, doc in enumerate(msg["documents"]):
                            st.markdown(f"**Chunk #{i} — `{doc.metadata.get('file_path')}`**")
                            st.code(doc.page_content, language="python")

        # Chat Input
        user_input = st.chat_input("Ask anything about this repository...") or preset_q

        if user_input:
            # Append User Message
            st.session_state["messages"].append({
                "role": "user",
                "content": user_input
            })

            # Assistant Execution
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("🤖 Coordinating specialized agents & verifying answer..."):
                    route_mode = agent_override.split()[0] if " " in agent_override else agent_override
                    result = coordinator.answer(
                        question=user_input,
                        manual_route=None if route_mode == "AUTO" else route_mode
                    )

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": result["answer"],
                        "agent": result["agent"],
                        "route": result["route"],
                        "latency": result["latency_seconds"],
                        "sources": result.get("sources", []),
                        "documents": result.get("documents", []),
                        "verification": result.get("verification", {})
                    })

            st.rerun()


# -----------------------------------------------------------------------------
# TAB 4: CODEBASE EXPLORER & AST
# -----------------------------------------------------------------------------
with tab_explorer:
    st.markdown("### 📂 Codebase File Explorer & AST Symbols")

    if not st.session_state["active_repo"]:
        st.info("Ingest a repository to browse its files and inspect AST symbols.")
    else:
        repo = st.session_state["active_repo"]
        repo_mgr = RepositoryManager()
        files = repo_mgr.get_repository_files(repo["path"])

        col_f1, col_f2 = st.columns([1, 2])

        with col_f1:
            st.markdown(f"**Total Files ({len(files)}):**")
            selected_file = st.selectbox("Select File to View", files)

        if selected_file:
            full_path = Path(repo["path"]) / selected_file
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                with col_f2:
                    st.markdown(f"#### 📄 `{selected_file}` ({len(lines)} lines)")

                # AST inspection if python file
                if selected_file.endswith(".py"):
                    chunker = CodeChunker()
                    doc_dict = {
                        "content": content,
                        "file_path": selected_file,
                        "extension": ".py"
                    }
                    chunks = chunker.chunk_document(doc_dict)

                    with st.expander(f"🧩 AST Symbols Detected ({len(chunks)})"):
                        ast_data = []
                        for c in chunks:
                            ast_data.append({
                                "Symbol": c.get("symbol") or "module",
                                "Type": c.get("symbol_type") or "code",
                                "Start Line": c.get("start_line"),
                                "End Line": c.get("end_line")
                            })
                        st.dataframe(ast_data, use_container_width=True)

                st.code(content, language="python" if selected_file.endswith(".py") else "markdown")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")


# -----------------------------------------------------------------------------
# TAB 5: DIAGNOSTICS & SYSTEM CACHE
# -----------------------------------------------------------------------------
with tab_diagnostics:
    st.markdown("### ⚙️ System Health, Diagnostics & Vector Cache")

    st.markdown("#### 🗄️ Storage & Cache Directories")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"**Repositories Folder**: `{REPOSITORIES_DIR}`")
        cloned = list(REPOSITORIES_DIR.glob("*"))
        st.write(f"Cloned Repositories on Disk: **{len(cloned)}**")
        for c in cloned:
            st.caption(f"- `{c.name}`")

    with col_d2:
        st.markdown(f"**Vector Store Folder**: `{VECTOR_STORE_DIR}`")
        indices = list(VECTOR_STORE_DIR.glob("*"))
        st.write(f"Cached Vector Stores: **{len(indices)}**")
        for idx_dir in indices:
            st.caption(f"- `{idx_dir.name}`")

    st.markdown("---")
    st.markdown("#### 🧹 Cache Management")
    if st.button("🗑️ Clear All Cloned Repositories and Vector Stores", type="secondary"):
        for c in REPOSITORIES_DIR.glob("*"):
            safe_remove_directory(c)
        for i in VECTOR_STORE_DIR.glob("*"):
            safe_remove_directory(i)
        st.session_state["active_repo"] = None
        st.session_state["vector_store"] = None
        st.session_state["coordinator"] = None
        st.session_state["messages"] = []
        st.success("All local storage and vector caches cleared successfully.")
        st.rerun()