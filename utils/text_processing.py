"""utils/text_processing.py — shared text utilities used across tools."""
from __future__ import annotations
import re
from typing import List


def extract_city(text: str, fallback: str = "London") -> str:
    """Pull a city name out of a natural-language weather query."""
    # Find the LAST occurrence of in/for/at followed by 1-3 capitalised words
    matches = list(re.finditer(r"\b(?:in|for|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", text))
    if not matches:
        # Try case-insensitive fallback
        matches = list(re.finditer(r"\b(?:in|for|at)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,1})", text, re.IGNORECASE))
    if matches:
        city = matches[-1].group(1).strip()
        city = re.sub(r"\s+(today|now|currently|please|right\s+now)$", "", city, flags=re.IGNORECASE)
        return city.strip().title() or fallback
    # Last resort: treat the whole input as a city name
    cleaned = re.sub(r"\b(weather|temperature|forecast|what|is|the|show|me|tell)\b", "", text, flags=re.IGNORECASE)
    return cleaned.strip().title() or fallback


def clean_math_expr(text: str) -> str:
    """Strip natural-language preamble from a math query."""
    return re.sub(
        r"(what is|calculate|compute|solve|evaluate|find|=\?)",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def tokenize(text: str) -> List[str]:
    """Lowercase word tokens, punctuation removed."""
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def truncate(text: str, max_chars: int = 500, suffix: str = "…") -> str:
    return text[:max_chars] + suffix if len(text) > max_chars else text


def word_count(text: str) -> int:
    return len(text.split())