from typing import Optional
from utils.helpers import get_llm


class QueryRouter:

    def __init__(self, model: Optional[str] = None):
        self.llm = get_llm(model=model, temperature=0.0)

    def route(self, question: str) -> str:
        prompt = f"""You are an intelligent query router for a GitHub Repository Analysis Multi-Agent System.

Classify the user's question into EXACTLY ONE of the following categories:

1. CODE_SEARCH
Questions looking for where code, functions, classes, imports, variables, endpoints, or exact implementations are located in the repository.
Examples: "Where is the Pinecone vector store initialized?", "Show me the authentication middleware function", "Find the database connection logic."

2. DOCUMENTATION
Questions about README files, setup guides, installation instructions, usage examples, configuration files (.env, pyproject.toml, package.json), or dependencies.
Examples: "How do I install this project?", "What environment variables are required?", "How to run the tests?"

3. DEBUGGING
Questions regarding errors, bugs, exceptions, why something is failing, stack traces, missing parameters, or how to fix a runtime/compile issue.
Examples: "Why does the client fail to connect?", "What happens if the API key is missing?", "How to fix the IndexError in the chunker?"

4. ARCHITECTURE
Questions asking about overall system design, project structure, component interactions, data flow, pipelines, design patterns, or technical tech stack overviews.
Examples: "Explain the architecture of this project", "How does the RAG pipeline flow end-to-end?", "What is the folder structure?"

5. GENERAL
Questions that do not strictly fit the above, or general comparisons.

Return ONLY the single category name in uppercase (e.g. CODE_SEARCH, DOCUMENTATION, DEBUGGING, ARCHITECTURE, GENERAL).

QUESTION:
{question}
"""
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            if isinstance(content, list):
                content = " ".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)

            category = content.strip().upper()

            valid_categories = {
                "CODE_SEARCH",
                "DOCUMENTATION",
                "DEBUGGING",
                "ARCHITECTURE",
                "GENERAL"
            }

            for valid in valid_categories:
                if valid in category:
                    return valid

            return "GENERAL"
        except Exception:
            return "GENERAL"