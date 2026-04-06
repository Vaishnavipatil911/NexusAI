"""
Intent Router — maps a natural-language query to the best-matching tool.

Routing strategy (in order of priority):
  1. Exact keyword match against tool.keywords list
  2. Partial keyword overlap score
  3. Falls back to None (caller decides)
"""

from __future__ import annotations
import re
from typing import Optional, List, Tuple
from core.tool_registry import get_registry, ToolMeta


# ── Keyword expansion map ────────────────────────────────────────────────────
# Aliases not stored on individual tools; centralised here for easy extension.
_ALIAS_MAP = {
    "weather":    ["weather", "temperature", "forecast", "climate", "humid", "rain",
                   "sunny", "wind", "city", "degrees", "celsius", "fahrenheit"],
    "code":       ["code", "generate", "function", "class", "script", "python",
                   "javascript", "algorithm", "implement", "program", "snippet",
                   "sort", "search", "fibonacci", "factorial", "palindrome"],
    "math":       ["math", "calculate", "compute", "solve", "expression", "formula",
                   "equation", "arithmetic", "sqrt", "sin", "cos", "log", "sum",
                   "multiply", "divide", "plus", "minus", "power", "percent"],
    "hash":       ["hash", "sha", "md5", "sha256", "sha512", "encrypt", "checksum",
                   "digest", "hex", "crypto"],
    "grammar":    ["grammar", "correct", "proofread", "spelling", "punctuation",
                   "sentence", "fix", "typo", "rewrite", "improve writing"],
    "summarizer": ["summarize", "summary", "key points", "tldr", "shorten",
                   "abstract", "brief", "condense", "document", "article", "passage"],
    "csv":        ["csv", "spreadsheet", "data", "dataset", "analyze", "statistics",
                   "columns", "rows", "upload", "file", "excel"],
    "password":   ["password", "strength", "secure", "security", "passphrase",
                   "credentials", "weak", "strong", "checker"],
    "api":        ["api", "endpoint", "http", "get", "post", "request", "url",
                   "rest", "json", "response", "status", "curl", "test"],
    "resume":     ["resume", "cv", "bullet", "job", "experience", "career",
                   "professional", "achievement", "linkedin", "hire"],
}


class IntentRouter:
    """Scores each registered tool against a query and returns the best match."""

    def route(self, query: str) -> Optional[str]:
        """
        Returns the tool name with the highest match score, or None if
        no tool scores above the minimum threshold.
        """
        if not query or not query.strip():
            return None

        normalised = self._normalise(query)
        scores = self._score_all(normalised)

        if not scores:
            return None

        best_name, best_score = scores[0]
        return best_name if best_score > 0 else None

    def ranked(self, query: str, top_n: int = 3) -> List[Tuple[str, int]]:
        """Returns top-n (tool_name, score) pairs — useful for debugging."""
        normalised = self._normalise(query)
        return self._score_all(normalised)[:top_n]

    # ── Internal ─────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return text.split()

    def _score_all(self, tokens: List[str]) -> List[Tuple[str, int]]:
        registry = get_registry()
        scores: List[Tuple[str, int]] = []

        for meta in registry.all():
            score = self._score_tool(tokens, meta)
            scores.append((meta.name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _score_tool(self, tokens: List[str], meta: ToolMeta) -> int:
        score = 0
        token_set = set(tokens)

        # Score from tool's own keyword list
        for kw in meta.keywords:
            kw_tokens = set(kw.lower().split())
            if kw_tokens.issubset(token_set):
                score += 3 * len(kw_tokens)   # exact multi-word phrase = extra weight
            elif kw_tokens & token_set:
                score += len(kw_tokens & token_set)

        # Score from centralised alias map
        for alias in _ALIAS_MAP.get(meta.name, []):
            alias_tokens = set(alias.lower().split())
            if alias_tokens.issubset(token_set):
                score += 2 * len(alias_tokens)
            elif alias_tokens & token_set:
                score += len(alias_tokens & token_set)

        return score


# ── Module-level singleton ────────────────────────────────────────────────────
_router = IntentRouter()


def route_query(query: str) -> Optional[str]:
    """Convenience function — returns the best-matching tool name or None."""
    return _router.route(query)


def ranked_matches(query: str, top_n: int = 3) -> List[Tuple[str, int]]:
    """Returns top-n (tool_name, score) pairs."""
    return _router.ranked(query, top_n)