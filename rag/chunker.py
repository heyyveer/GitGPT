import ast
import re
from typing import List, Dict, Any


class CodeChunker:

    def __init__(
        self,
        chunk_size: int = 1500,
        overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = document["content"]
        file_path = document["file_path"]
        extension = document.get("extension", "").lower()

        if extension == ".py":
            chunks = self._python_chunks(content)
        elif extension in {".md", ".markdown", ".txt", ".rst"}:
            chunks = self._markdown_chunks(content)
        else:
            chunks = self._code_chunks(content)

        results = []
        for index, chunk in enumerate(chunks):
            results.append({
                "content": chunk["content"],
                "file_path": file_path,
                "chunk_id": index,
                "extension": extension,
                "start_line": chunk.get("start_line", 1),
                "end_line": chunk.get("end_line", 1),
                "symbol": chunk.get("symbol"),
                "symbol_type": chunk.get("symbol_type", "code"),
            })

        return results

    # ---------------------------------------------------------
    # Python AST Chunking
    # ---------------------------------------------------------
    def _python_chunks(self, code: str) -> List[Dict[str, Any]]:
        lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return self._code_chunks(code)

        chunks = []

        # Extract top-level imports
        import_nodes = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        if import_nodes:
            start_line = min(node.lineno for node in import_nodes)
            end_line = max(getattr(node, "end_lineno", node.lineno) for node in import_nodes)
            import_content = "\n".join(lines[start_line - 1:end_line])

            if import_content.strip():
                chunks.append({
                    "content": import_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "symbol": "__imports__",
                    "symbol_type": "imports"
                })

        # Extract functions, async functions, classes and methods
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            if not hasattr(node, "lineno"):
                continue

            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)

            chunk_lines = lines[start_line - 1:end_line]
            content = "\n".join(chunk_lines)

            if not content.strip():
                continue

            if isinstance(node, ast.ClassDef):
                symbol_type = "class"
            elif isinstance(node, ast.AsyncFunctionDef):
                symbol_type = "async_function"
            else:
                symbol_type = "function"

            # If class/function is too large, sub-chunk it
            if len(content) > self.chunk_size * 2:
                sub_chunks = self._split_large_block(content, start_line, node.name, symbol_type)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "content": content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "symbol": node.name,
                    "symbol_type": symbol_type
                })

        if not chunks:
            return self._code_chunks(code)

        chunks.sort(key=lambda x: x["start_line"])
        return chunks

    def _split_large_block(self, code: str, base_start_line: int, symbol: str, symbol_type: str) -> List[Dict[str, Any]]:
        lines = code.splitlines()
        chunks = []
        current_lines = []
        current_size = 0
        current_start = base_start_line

        for idx, line in enumerate(lines):
            line_size = len(line) + 1
            if current_size + line_size > self.chunk_size and current_lines:
                chunks.append({
                    "content": "\n".join(current_lines),
                    "start_line": current_start,
                    "end_line": base_start_line + idx - 1,
                    "symbol": symbol,
                    "symbol_type": symbol_type
                })
                # Overlap
                overlap_lines = current_lines[-5:] if len(current_lines) >= 5 else current_lines
                current_lines = list(overlap_lines)
                current_size = sum(len(l) + 1 for l in current_lines)
                current_start = base_start_line + idx - len(overlap_lines)

            current_lines.append(line)
            current_size += line_size

        if current_lines:
            chunks.append({
                "content": "\n".join(current_lines),
                "start_line": current_start,
                "end_line": base_start_line + len(lines) - 1,
                "symbol": symbol,
                "symbol_type": symbol_type
            })

        return chunks

    # ---------------------------------------------------------
    # Markdown & Documentation Chunking
    # ---------------------------------------------------------
    def _markdown_chunks(self, text: str) -> List[Dict[str, Any]]:
        lines = text.splitlines()
        chunks = []

        current_lines = []
        current_start = 1
        current_heading = "Overview"

        heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

        for idx, line in enumerate(lines, 1):
            match = heading_pattern.match(line)
            if match and current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    chunks.append({
                        "content": content,
                        "start_line": current_start,
                        "end_line": idx - 1,
                        "symbol": current_heading,
                        "symbol_type": "documentation"
                    })
                current_lines = []
                current_start = idx
                current_heading = match.group(2).strip()

            current_lines.append(line)

            # If section exceeds chunk size, flush
            section_len = sum(len(l) + 1 for l in current_lines)
            if section_len >= self.chunk_size:
                content = "\n".join(current_lines).strip()
                if content:
                    chunks.append({
                        "content": content,
                        "start_line": current_start,
                        "end_line": idx,
                        "symbol": current_heading,
                        "symbol_type": "documentation"
                    })
                current_lines = []
                current_start = idx + 1

        if current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                chunks.append({
                    "content": content,
                    "start_line": current_start,
                    "end_line": len(lines),
                    "symbol": current_heading,
                    "symbol_type": "documentation"
                })

        return chunks or self._code_chunks(text)

    # ---------------------------------------------------------
    # Generic Code Chunking
    # ---------------------------------------------------------
    def _code_chunks(self, code: str) -> List[Dict[str, Any]]:
        lines = code.splitlines()
        chunks = []

        current_lines = []
        current_size = 0
        current_start_line = 1

        for index, line in enumerate(lines):
            line_size = len(line) + 1

            if current_size + line_size > self.chunk_size and current_lines:
                chunks.append({
                    "content": "\n".join(current_lines),
                    "start_line": current_start_line,
                    "end_line": index,
                    "symbol": None,
                    "symbol_type": "code"
                })

                # Calculate overlap
                overlap_lines = []
                overlap_size = 0
                for prev_line in reversed(current_lines):
                    if overlap_size >= self.overlap:
                        break
                    overlap_lines.insert(0, prev_line)
                    overlap_size += len(prev_line) + 1

                current_lines = overlap_lines
                current_size = overlap_size
                current_start_line = max(1, index - len(overlap_lines) + 1)

            if not current_lines:
                current_start_line = index + 1

            current_lines.append(line)
            current_size += line_size

        if current_lines:
            chunks.append({
                "content": "\n".join(current_lines),
                "start_line": current_start_line,
                "end_line": len(lines),
                "symbol": None,
                "symbol_type": "code"
            })

        return chunks