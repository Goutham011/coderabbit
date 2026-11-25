"""Knowledge graph — persistent repository memory with multilingual support."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Set


class KnowledgeBase:
    """Stores repository structure for improved reviews with multilingual support."""

    # Map file extensions to languages
    EXTENSIONS: Dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".lua": "lua",
        ".r": "r",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".scss": "css",
        ".md": "markdown",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
    }

    # Language-specific symbol patterns
    SYMBOL_PATTERNS: Dict[str, str] = {
        "python": r"^(\s*)(def|class)\s+(\w+)",
        "javascript": r"^(\s*)(function\s+(\w+)|const\s+(\w+)\s*=|class\s+(\w+)|async\s+function\s+(\w+))",
        "typescript": r"^(\s*)(function\s+(\w+)|const\s+(\w+)\s*=|class\s+(\w+)|interface\s+(\w+)|type\s+(\w+)\s*=|async\s+function\s+(\w+))",
        "java": r"^(\s*)(public\s+)?(class|interface|enum|record|void)\s+(\w+)",
        "go": r"^(\s*)(func\s+func?\s*(\w+)|type\s+(\w+)\s+(struct|interface|func))",
        "rust": r"^(\s*)(fn\s+(\w+)|struct\s+(\w+)|enum\s+(\w+)|trait\s+(\w+)|impl\s+(\w+))",
        "cpp": r"^(\s*)(class\s+(\w+)|struct\s+(\w+)|namespace\s+(\w+)|void\s+(\w+)\s*\()",
    }

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".agentic" / "knowledge.db"
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                type TEXT NOT NULL,
                PRIMARY KEY (source, target, type)
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
        """)
        self._conn.commit()

    def index_repo(self, repo_path: Path, language: Optional[str] = None) -> dict:
        """Scan repository and populate knowledge graph. Detects language if not specified."""
        file_count = 0
        symbol_count = 0
        indexed_languages: Set[str] = set()

        for file_path in repo_path.rglob("*"):
            if ".git" in str(file_path) or file_path.is_dir():
                continue

            # Detect language from extension
            ext = file_path.suffix.lower()
            detected_lang = language or self.EXTENSIONS.get(ext, "unknown")

            if detected_lang == "unknown" and language is None:
                continue

            self._index_file(file_path, detected_lang)
            file_count += 1
            indexed_languages.add(detected_lang)
            if detected_lang != "unknown":
                symbol_count += self._count_symbols(file_path)

        return {"files_indexed": file_count, "symbols_indexed": symbol_count, "languages": list(indexed_languages)}

    def _count_symbols(self, file_path: Path) -> int:
        """Count symbols in a file using language-specific patterns."""
        lang = self.EXTENSIONS.get(file_path.suffix.lower(), "unknown")
        pattern = self.SYMBOL_PATTERNS.get(lang, r"^(\s*)(def|class|function|fn)\s+(\w+)")
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            return len(re.findall(pattern, content, re.MULTILINE))
        except Exception:
            return 0

    def _index_file(self, file_path: Path, language: str) -> None:
        """Index a single file and its symbols."""
        node_id = f"file:{file_path.resolve()}"
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return

        # Store file metadata (language stored in both content and metadata for flexible querying)
        self._upsert_node(node_id, "file", {
            "path": str(file_path),
            "language": language,
            "lines": len(content.splitlines()),
        }, metadata={"language": language})

        # Extract symbols based on language
        pattern = self.SYMBOL_PATTERNS.get(language, r"^(\s*)(def|class)\s+(\w+)")
        for match in re.finditer(pattern, content, re.MULTILINE):
            try:
                if language == "python":
                    indent = len(match.group(1))
                    kind = match.group(2)
                    name = match.group(3)
                elif language in ("javascript", "typescript"):
                    indent = len(match.group(1))
                    # Handle multiple capture groups for different patterns
                    kind = "function" if "function" in match.group(0) else "class"
                    name = match.group(3) or match.group(4) or match.group(5) or match.group(6) or match.group(7)
                elif language == "java":
                    indent = len(match.group(1))
                    kind = match.group(3)
                    name = match.group(4)
                elif language == "go":
                    indent = len(match.group(1))
                    kind = "function" if "func" in match.group(0) else "type"
                    name = match.group(3) or match.group(4) or match.group(5)
                elif language == "rust":
                    indent = len(match.group(1))
                    kind = "function" if "fn " in match.group(0) else "struct"
                    name = match.group(3) or match.group(4) or match.group(5) or match.group(6) or match.group(7)
                else:
                    # Default pattern
                    indent = len(match.group(1)) if match.group(1) else 0
                    kind = match.group(2) if match.group(2) else "symbol"
                    name = match.group(3) if match.group(3) else match.group(0).split()[-1]

                line_no = content.count('\n', 0, match.start()) + 1
                sym_id = f"{node_id}:sym:{kind}:{name}"
                self._upsert_node(sym_id, kind, {
                    "name": name,
                    "file": str(file_path),
                    "line": line_no,
                    "indent": indent,
                })
            except (IndexError, AttributeError):
                continue

    def _upsert_node(self, node_id: str, node_type: str, content: dict, metadata: Optional[dict] = None) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO nodes (id, type, content, metadata) VALUES (?, ?, ?, ?)",
            (node_id, node_type, json.dumps(content), json.dumps(metadata or {})),
        )
        self._conn.commit()

    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO edges (source, target, type) VALUES (?, ?, ?)",
            (source, target, edge_type),
        )
        self._conn.commit()

    def query(self, query_type: str, value: str) -> list[dict]:
        """Search knowledge graph by type and value."""
        cursor = self._conn.execute(
            "SELECT id, type, content, metadata FROM nodes WHERE type = ? AND content LIKE ?",
            (query_type, f"%{value}%"),
        )
        results = []
        for row in cursor:
            try:
                content = json.loads(row[2])
                metadata = json.loads(row[3]) if row[3] else {}
                result = {"id": row[0], "type": row[1], **content}
                if metadata:
                    result.update(metadata)
                results.append(result)
            except (json.JSONDecodeError, TypeError):
                pass
        return results

    def query_by_language(self, language: str, query_type: Optional[str] = None, value: Optional[str] = None) -> list[dict]:
        """Query nodes filtered by language (searched in content and metadata)."""
        # JSON format is: "language": "value" (with space after colon)
        lang_content_pattern = '%"language": "' + language + '"%'
        lang_metadata_pattern = '%"language": "' + language + '"%'

        # Build query - language can be in content or metadata
        # For backward compatibility, check both columns
        if query_type and value:
            cursor = self._conn.execute(
                "SELECT id, type, content, metadata FROM nodes WHERE type = ? AND content LIKE ? AND (content LIKE ? OR metadata LIKE ?)",
                (query_type, f"%{value}%", lang_content_pattern, lang_metadata_pattern),
            )
        elif query_type:
            cursor = self._conn.execute(
                "SELECT id, type, content, metadata FROM nodes WHERE type = ? AND (content LIKE ? OR metadata LIKE ?)",
                (query_type, lang_content_pattern, lang_metadata_pattern),
            )
        elif value:
            cursor = self._conn.execute(
                "SELECT id, type, content, metadata FROM nodes WHERE content LIKE ? AND (content LIKE ? OR metadata LIKE ?)",
                (f"%{value}%", lang_content_pattern, lang_metadata_pattern),
            )
        else:
            cursor = self._conn.execute(
                "SELECT id, type, content, metadata FROM nodes WHERE content LIKE ? OR metadata LIKE ?",
                (lang_content_pattern, lang_metadata_pattern),
            )

        results = []
        for row in cursor:
            try:
                content = json.loads(row[2])
                metadata = json.loads(row[3]) if row[3] else {}
                result = {"id": row[0], "type": row[1], **content}
                if metadata:
                    result.update(metadata)
                results.append(result)
            except (json.JSONDecodeError, TypeError):
                pass
        return results

    def find_related(self, node_id: str, edge_types: Optional[list[str]] = None) -> list[dict]:
        """Find all nodes connected to the given node."""
        if edge_types is None:
            edge_types = ["references", "imports", "extends", "related_to"]

        # SECURITY: Validate edge_types to prevent SQL injection
        # Only allow alphanumeric and underscore characters
        validated_types = []
        for et in edge_types:
            if isinstance(et, str) and all(c.isalnum() or c == '_' for c in et):
                validated_types.append(et)

        if not validated_types:
            return []

        placeholders = ",".join("?" for _ in validated_types)
        # SECURITY: Use parameterized query with validated placeholders
        # All values in edge_types are validated to contain only alphanumeric and underscore
        # This prevents SQL injection - bandit B608 is a false positive here
        cursor = self._conn.execute(  # nosec B608
            f"""SELECT e.target, n.type, n.content, n.metadata
                FROM edges e
                JOIN nodes n ON e.target = n.id
                WHERE e.source = ? AND e.type IN ({placeholders})""",
            [node_id, *validated_types],
        )
        results = []
        for row in cursor:
            try:
                content = json.loads(row[2])
                metadata = json.loads(row[3]) if row[3] else {}
                result = {"target": row[0], "type": row[1], **content}
                if metadata:
                    result.update(metadata)
                results.append(result)
            except json.JSONDecodeError:
                pass
        return results

    def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        cursor = self._conn.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type")
        type_counts = {row[0]: row[1] for row in cursor}

        cursor = self._conn.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]

        return {"nodes": sum(type_counts.values()), "edges": edge_count, "by_type": type_counts}

    def close(self) -> None:
        self._conn.close()