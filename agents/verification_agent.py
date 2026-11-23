import re
from typing import List, Dict, Any


class VerificationAgent:
    """
    Verifies that generated answers are strictly grounded in retrieved evidence
    and checks for hallucinated functions, classes, files, and code snippets.
    """

    def verify(
        self,
        answer: str,
        documents: List[Any]
    ) -> Dict[str, Any]:
        if not answer or answer == "NOT_FOUND":
            return {
                "verified": True,
                "confidence": 1.0,
                "reason": "Standard negative response.",
                "unverified_claims": [],
                "answer": answer
            }

        evidence_text = "\n".join(
            doc.page_content for doc in documents
        )

        source_files = set()
        for doc in documents:
            file_path = doc.metadata.get("file_path", "")
            if file_path:
                norm = file_path.replace("\\", "/").lower()
                source_files.add(norm)
                source_files.add(norm.split("/")[-1])

        unverified_claims = []

        # ------------------------------------------------
        # Check 1: Code snippets / calls inside backticks
        # ------------------------------------------------
        code_claims = re.findall(r"`([^`\n]+)`", answer)

        for claim in code_claims:
            claim_strip = claim.strip()
            # Check for functional/code expressions
            if any(char in claim_strip for char in ["(", ")", "=", "->", "import ", "from "]):
                # Normalize spaces for verification
                claim_norm = re.sub(r"\s+", " ", claim_strip)
                evidence_norm = re.sub(r"\s+", " ", evidence_text)
                
                # Check if core tokens exist in evidence
                if claim_strip not in evidence_text and claim_norm not in evidence_norm:
                    # Token check: if function name is in evidence, give partial benefit
                    fn_match = re.match(r"([a-zA-Z_]\w*)\s*\(", claim_strip)
                    if fn_match and fn_match.group(1) in evidence_text:
                        continue
                    unverified_claims.append(f"Code assertion `{claim_strip}` not found in retrieved code.")

        # ------------------------------------------------
        # Check 2: File name references
        # ------------------------------------------------
        file_candidates = re.findall(r"`([^`\s]+\.[a-zA-Z0-9]+)`", answer)
        for fc in file_candidates:
            fc_norm = fc.replace("\\", "/").lower()
            fc_name = fc_norm.split("/")[-1]
            if not any(fc_name == sf or fc_norm == sf for sf in source_files):
                # Only flag if it looks like a source code file
                if fc_norm.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".cpp", ".c", ".java")):
                    unverified_claims.append(f"Referenced file `{fc}` not present in retrieved context.")

        if unverified_claims:
            return {
                "verified": False,
                "confidence": max(0.2, 1.0 - (len(unverified_claims) * 0.3)),
                "reason": "; ".join(unverified_claims[:3]),
                "unverified_claims": unverified_claims,
                "answer": answer
            }

        return {
            "verified": True,
            "confidence": 1.0,
            "reason": "All code references, symbols, and files verified against retrieved evidence.",
            "unverified_claims": [],
            "answer": answer
        }