import time
from typing import Dict, Any, Optional, List
from agents.router import QueryRouter
from agents.code_search_agent import CodeSearchAgent
from agents.documentation_agent import DocumentationAgent
from agents.debugging_agent import DebuggingAgent
from agents.analysis_agent import AnalysisAgent


class MultiAgentCoordinator:
    """
    Central orchestrator that routes user questions to specialized agents,
    manages agent execution, aggregates context, and ensures verification.
    """

    def __init__(
        self,
        vector_store,
        repository_path: str,
        model: Optional[str] = None
    ):
        self.vector_store = vector_store
        self.repository_path = repository_path
        self.model = model

        self.router = QueryRouter(model=model)
        self.code_search_agent = CodeSearchAgent(vector_store, repository_path, model=model)
        self.doc_agent = DocumentationAgent(vector_store, model=model)
        self.debug_agent = DebuggingAgent(vector_store, repository_path, model=model)
        self.analysis_agent = AnalysisAgent(vector_store, repository_path, model=model)

    def contextualize_query(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        If prior conversation history exists, rewrite follow-up questions
        into self-contained standalone search queries.
        """
        if not history:
            return question

        # Extract last 4 turns, skipping long citations
        h_lines = []
        for msg in history[-4:]:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "").split("### 📍")[0].strip()
            if content:
                h_lines.append(f"{role}: {content[:250]}")

        if not h_lines:
            return question

        history_text = "\n".join(h_lines)
        prompt = f"""Given the conversation history and a follow-up user question, rewrite the follow-up question into a clear, standalone search query that preserves the specific code, file, component, or line references being asked about.
If the question is already standalone, return it unchanged.
Return ONLY the standalone rewritten question without any preamble.

CONVERSATION HISTORY:
{history_text}

FOLLOW-UP QUESTION:
{question}

STANDALONE QUESTION:"""

        try:
            response = self.router.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            if isinstance(content, list):
                content = " ".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
            rewritten = content.strip().strip('"').strip("'")
            if rewritten:
                return rewritten
        except Exception:
            pass

        return question

    def answer(
        self,
        question: str,
        manual_route: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Step 0: Conversational Query Rewriting / Contextualization
        effective_query = self.contextualize_query(question, history)

        # Step 1: Query Routing
        if manual_route and manual_route.upper() != "AUTO":
            route = manual_route.upper()
        else:
            route = self.router.route(effective_query)

        # Step 2: Agent Dispatch
        if route == "CODE_SEARCH":
            result = self.code_search_agent.run(effective_query, history=history)
        elif route == "DOCUMENTATION":
            result = self.doc_agent.run(effective_query, history=history)
        elif route == "DEBUGGING":
            result = self.debug_agent.run(effective_query, history=history)
        elif route == "ARCHITECTURE":
            result = self.analysis_agent.run(effective_query, history=history)
        else:  # GENERAL fallback
            result = self.code_search_agent.run(effective_query, history=history)

        elapsed = round(time.time() - start_time, 2)

        result["route"] = route
        result["latency_seconds"] = elapsed
        result["effective_query"] = effective_query

        return result
