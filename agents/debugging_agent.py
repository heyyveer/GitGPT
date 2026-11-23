from typing import Dict, Any, Optional, List
from rag.retriever import RepositoryRetriever
from rag.generator import AnswerGenerator
from agents.verification_agent import VerificationAgent


class DebuggingAgent:
    """
    Agent specialized in diagnosing runtime errors, unhandled exceptions,
    configuration mismatches, missing dependencies/env keys, and suggesting code fixes.
    """

    def __init__(self, vector_store, repository_path: Optional[str] = None, model: Optional[str] = None):
        self.retriever = RepositoryRetriever(vector_store)
        self.generator = AnswerGenerator(model=model)
        self.repository_path = repository_path
        self.verifier = VerificationAgent()

    def run(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Diagnose the problem from repository code and generate root cause analysis + fix.
        """
        documents = self.retriever.retrieve(question, k=6, prefer_code=True)

        if not documents:
            return {
                "agent": "DebuggingAgent",
                "answer": "No relevant code or error handling routines found for this issue.",
                "documents": [],
                "sources": [],
                "verification": {"verified": True, "confidence": 1.0, "reason": "No code found."}
            }

        custom_instructions = """You are a senior debugging and code triage expert.
Analyze the user's issue strictly against the provided repository code.
Structure your response as follows:
1. 🔍 Root Cause Analysis: Exactly why the issue occurs based on the code logic or missing parameters.
2. ⚠️ Problematic Code Location: Mention the exact file and lines responsible.
3. 🛠️ Step-by-Step Solution & Fix: Show the corrected code snippet or required configuration change.
4. 💡 Prevention Tips: How to prevent similar regressions."""

        generation = self.generator.generate(
            question=question,
            documents=documents,
            custom_instructions=custom_instructions,
            history=history
        )

        answer = generation["answer"]
        evidence_ids = generation["evidence_ids"] or list(range(len(documents)))

        sources = []
        for evidence_id in evidence_ids:
            if evidence_id < 0 or evidence_id >= len(documents):
                continue
            doc = documents[evidence_id]
            meta = doc.metadata
            file_path = meta.get("file_path", "")
            start_line = meta.get("start_line", 1)
            end_line = meta.get("end_line", 1)

            source_item = {
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "symbol": meta.get("symbol", ""),
                "symbol_type": meta.get("symbol_type", "code")
            }
            if not any(s["file_path"] == file_path and s["start_line"] == start_line for s in sources):
                sources.append(source_item)

        if sources and "Investigated Files" not in answer:
            answer += "\n\n### 🔍 Investigated Files & Context\n"
            for s in sources:
                loc = f"`{s['file_path']}` (Lines {s['start_line']}-{s['end_line']})"
                sym = f" — *Symbol*: `{s['symbol']}`" if s.get("symbol") else ""
                answer += f"- {loc}{sym}\n"

        verification = self.verifier.verify(answer=answer, documents=documents)

        return {
            "agent": "DebuggingAgent",
            "answer": answer,
            "documents": documents,
            "sources": sources,
            "verification": verification
        }
