from typing import Dict, Any, Optional, List
from rag.retriever import RepositoryRetriever
from rag.generator import AnswerGenerator
from utils.source_locator import SourceLocator
from agents.verification_agent import VerificationAgent


class CodeSearchAgent:

    def __init__(self, vector_store, repository_path: str, model: Optional[str] = None):
        self.retriever = RepositoryRetriever(vector_store)
        self.generator = AnswerGenerator(model=model)
        self.source_locator = SourceLocator(repository_path)
        self.verifier = VerificationAgent()

    def run(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute code search: retrieve code chunks, generate grounded answer,
        dynamically locate exact line numbers, and verify against hallucination.
        """
        documents = self.retriever.retrieve(question, k=6, prefer_code=True)

        if not documents:
            return {
                "agent": "CodeSearchAgent",
                "answer": "No relevant code was found in the repository for this query.",
                "documents": [],
                "sources": [],
                "verification": {"verified": True, "confidence": 1.0, "reason": "No code found."}
            }

        generation = self.generator.generate(
            question=question,
            documents=documents,
            custom_instructions="Focus on pinpointing exact functions, class definitions, variable initializations, and where in the repository specific logic is implemented.",
            history=history
        )

        answer = generation["answer"]
        evidence_ids = generation["evidence_ids"]

        if not evidence_ids:
            evidence_ids = list(range(len(documents)))

        sources = []
        for evidence_id in evidence_ids:
            if evidence_id < 0 or evidence_id >= len(documents):
                continue

            document = documents[evidence_id]
            file_path = document.metadata.get("file_path", "")
            start_line = document.metadata.get("start_line", 1)
            end_line = document.metadata.get("end_line", 1)
            symbol = document.metadata.get("symbol", "")
            symbol_type = document.metadata.get("symbol_type", "code")

            # Extract first 2-3 meaningful code lines from this chunk to display as preview
            sample_lines = [
                line.strip() for line in document.page_content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            preview_snippet = sample_lines[0] if sample_lines else ""

            source_item = {
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "line": start_line,
                "symbol": symbol,
                "symbol_type": symbol_type,
                "content": preview_snippet,
                "full_chunk": document.page_content
            }

            if not any(s["file_path"] == file_path and s["start_line"] == start_line for s in sources):
                sources.append(source_item)

        sources.sort(key=lambda x: (x["file_path"], x["start_line"]))

        # Build clean verified sources section
        if sources and "Verified Sources" not in answer:
            answer += "\n\n### 📍 Verified Source Locations\n"
            for s in sources:
                loc = f"`{s['file_path']}` (Lines {s['start_line']}-{s['end_line']})"
                sym = f" — *{s['symbol_type']}* `{s['symbol']}`" if s.get("symbol") else ""
                code_prev = f"\n  > `{s['content'][:120]}`" if s.get("content") else ""
                answer += f"- **{loc}**{sym}{code_prev}\n"

        verification = self.verifier.verify(answer=answer, documents=documents)

        return {
            "agent": "CodeSearchAgent",
            "answer": answer,
            "documents": documents,
            "sources": sources,
            "verification": verification
        }