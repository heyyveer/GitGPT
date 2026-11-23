from typing import Dict, Any, Optional, List
from rag.retriever import RepositoryRetriever
from rag.generator import AnswerGenerator
from agents.verification_agent import VerificationAgent


class DocumentationAgent:

    def __init__(self, vector_store, model: Optional[str] = None):
        self.retriever = RepositoryRetriever(vector_store)
        self.generator = AnswerGenerator(model=model)
        self.verifier = VerificationAgent()

    def run(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute documentation query: retrieves README, configuration files,
        setup guides, requirements, and generates a structured walkthrough.
        """
        documents = self.retriever.retrieve(question, k=5)

        if not documents:
            return {
                "agent": "DocumentationAgent",
                "answer": "No documentation or configuration files found matching this question.",
                "documents": [],
                "sources": [],
                "verification": {"verified": True, "confidence": 1.0, "reason": "No documentation found."}
            }

        generation = self.generator.generate(
            question=question,
            documents=documents,
            custom_instructions="Structure the response clearly with step-by-step installation/usage guides, prerequisites, environment variables, dependencies, and shell commands as documented in the repository.",
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

            doc = documents[evidence_id]
            metadata = doc.metadata
            file_path = metadata.get("file_path", "")
            start_line = metadata.get("start_line", 1)
            end_line = metadata.get("end_line", 1)
            symbol = metadata.get("symbol", "")

            source_item = {
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "symbol": symbol,
                "symbol_type": metadata.get("symbol_type", "doc")
            }

            if not any(s["file_path"] == file_path and s["start_line"] == start_line for s in sources):
                sources.append(source_item)

        if sources and "Verified Documentation Sources" not in answer:
            answer += "\n\n### 📖 Verified Documentation Sources\n"
            for s in sources:
                loc = f"`{s['file_path']}` (Lines {s['start_line']}-{s['end_line']})"
                sym = f" — *Section*: **{s['symbol']}**" if s.get("symbol") else ""
                answer += f"- {loc}{sym}\n"

        verification = self.verifier.verify(answer=answer, documents=documents)

        return {
            "agent": "DocumentationAgent",
            "answer": answer,
            "documents": documents,
            "sources": sources,
            "verification": verification
        }