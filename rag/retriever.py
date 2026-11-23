import re
from typing import List, Optional, Dict, Any


class RepositoryRetriever:

    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp",
        ".c", ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb",
        ".swift", ".kt", ".scala", ".sh", ".bash", ".sql"
    }

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        prefer_code: bool = False
    ) -> List[Any]:
        """
        Retrieve the top k most relevant documents/chunks for a query using
        hybrid vector similarity + code-aware keyword and structural reranking.
        """
        candidate_k = max(k * 4, 25)

        if filter_dict:
            candidates = self.vector_store.similarity_search(
                query,
                k=candidate_k,
                filter=filter_dict
            )
        else:
            candidates = self.vector_store.similarity_search(
                query,
                k=candidate_k
            )

        if not candidates:
            return []

        # Parse query keywords and line ranges
        query_words = set(w.lower() for w in re.findall(r"\w+", query) if len(w) >= 2)
        line_range_match = re.search(r"(?:between|lines?)\s+(\d+)\s*(?:to|-|and)\s*(\d+)", query, re.IGNORECASE)
        line_start = int(line_range_match.group(1)) if line_range_match else None
        line_end = int(line_range_match.group(2)) if line_range_match else None

        single_line_match = re.search(r"line\s+(\d+)", query, re.IGNORECASE)
        target_line = int(single_line_match.group(1)) if single_line_match and not line_range_match else None

        def score_candidate(doc) -> float:
            content_lower = doc.page_content.lower()
            file_path = doc.metadata.get("file_path", "").lower()
            symbol_type = doc.metadata.get("symbol_type", "code")
            start_line = doc.metadata.get("start_line", 0)
            end_line = doc.metadata.get("end_line", 0)

            score = 0.0

            # 1. Keyword overlap
            for w in query_words:
                if w in content_lower:
                    score += 2.0
                if w in file_path:
                    score += 3.0

            # 2. Code bonus
            is_code_file = any(file_path.endswith(ext) for ext in self.CODE_EXTENSIONS)
            if is_code_file:
                score += (4.0 if prefer_code else 1.5)

            if symbol_type in ("function", "class", "async_function", "imports", "code"):
                score += (3.0 if prefer_code else 1.0)
            elif symbol_type == "documentation" and prefer_code:
                score -= 1.0

            # 3. Line range matching
            if line_start is not None and line_end is not None:
                if start_line <= line_end and end_line >= line_start:
                    score += 6.0
            elif target_line is not None:
                if start_line <= target_line <= end_line:
                    score += 6.0

            return score

        reranked = sorted(candidates, key=score_candidate, reverse=True)
        return reranked[:k]

    def retrieve_with_scores(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple]:
        """
        Retrieve chunks with distance/relevance score.
        """
        return self.vector_store.similarity_search_with_score(
            query,
            k=k
        )