import re
from typing import List, Dict, Any, Optional
from utils.helpers import get_llm


class AnswerGenerator:

    def __init__(self, model: Optional[str] = None):
        self.llm = get_llm(model=model, temperature=0.0)

    def generate(
        self,
        question: str,
        documents: List[Any],
        custom_instructions: str = "",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate grounded answers strictly from the provided repository evidence documents.
        """
        if not documents:
            return {
                "answer": "No relevant repository context or code chunks were retrieved.",
                "evidence_ids": []
            }

        context_parts = []
        for index, document in enumerate(documents):
            file_path = document.metadata.get("file_path", "unknown")
            start_line = document.metadata.get("start_line", 1)
            end_line = document.metadata.get("end_line", 1)
            symbol = document.metadata.get("symbol", "")

            context_parts.append(
                f"--- EVIDENCE_ID: {index} | FILE: {file_path} (Lines {start_line}-{end_line}) {f'[{symbol}]' if symbol else ''} ---\n"
                f"{document.page_content}\n"
            )

        context = "\n".join(context_parts)

        history_section = ""
        if history:
            h_lines = []
            for m in history[-6:]:
                role = m.get("role", "user").capitalize()
                cnt = m.get("content", "").split("### 📍")[0].strip()
                if cnt:
                    h_lines.append(f"{role}: {cnt[:300]}")
            if h_lines:
                history_section = f"\nCONVERSATION CONTEXT:\n" + "\n".join(h_lines) + "\n"

        extra_instruction = f"\nADDITIONAL AGENT INSTRUCTION:\n{custom_instructions}\n" if custom_instructions else ""

        prompt = f"""You are an expert GitHub Repository Analyst.
Answer the user's question accurately, concisely, and strictly based on the provided repository code and documentation evidence.
{history_section}
RULES:
1. Ground your answer ONLY on the provided code/docs evidence below.
2. If the evidence does not contain sufficient details to answer the question, state: "The repository evidence does not contain sufficient information to answer this question."
3. When referencing code, functions, classes, or configuration parameters, mention the exact names as they appear in the evidence.
4. List the zero-indexed EVIDENCE_IDs that directly supported your answer.
{extra_instruction}
USER QUESTION:
{question}

REPOSITORY EVIDENCE:
{context}

Format your output strictly as:
ANSWER: <your comprehensive, well-structured explanation in markdown>
EVIDENCE_IDS: <comma-separated list of evidence IDs used, e.g. 0, 1>
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return self._parse_response(content)
        except Exception as e:
            return {
                "answer": f"Error during answer generation: {str(e)}",
                "evidence_ids": []
            }

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        if isinstance(response, list):
            text_parts = []
            for item in response:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    text_parts.append(item.get("text", ""))
            response = "\n".join(text_parts)

        response = str(response).strip()

        answer = ""
        evidence_ids = []

        lines = response.splitlines()
        collecting_answer = False

        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("ANSWER:"):
                answer = trimmed.replace("ANSWER:", "", 1).strip()
                collecting_answer = True
            elif trimmed.startswith("EVIDENCE_IDS:"):
                collecting_answer = False
                raw_ids = trimmed.replace("EVIDENCE_IDS:", "", 1).strip()
                if raw_ids and raw_ids.lower() != "none":
                    # Extract integers
                    found_ids = re.findall(r"\b\d+\b", raw_ids)
                    evidence_ids = [int(x) for x in found_ids]
            elif collecting_answer:
                answer += "\n" + line

        # Fallback if parser didn't match strict format
        if not answer.strip():
            answer = response

        return {
            "answer": answer.strip(),
            "evidence_ids": evidence_ids
        }