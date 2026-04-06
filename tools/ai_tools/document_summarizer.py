"""ai_tools — document summarizer."""

from __future__ import annotations
import re

from core.tool_registry import BaseTool, register_tool


@register_tool(
    name="summarizer",
    display_name="📄 Doc Summarizer",
    category="ai_tools",
    description="Summarize long text documents into key bullet points",
    keywords=["summarize", "summary", "key points", "tldr", "document", "article", "condense"],
    input_type="chat",
)
class DocumentSummarizerTool(BaseTool):

    _STOP_WORDS = frozenset({
        "the","a","an","is","it","in","on","at","to","for","of","and","or",
        "but","with","this","that","was","are","were","be","been","have","has",
        "had","do","did","not","from","by","as","its","their","they","we","you",
        "he","she","my","our","your","his","her","also","which","who","when",
        "where","what","how","if","then","so","than","more","very","just","can",
        "will","would","could","should","may","might","shall","does","about","any",
    })

    def run(self, text: str = "", num_points: int = 5, **kwargs) -> dict:
        text = text.strip()
        if len(text) < 50:
            return {"success": False, "result": "❌ Text is too short to summarize (minimum 50 characters)."}

        sentences = re.split(r"(?<=[.!?])\s+", text)
        word_count = len(text.split())

        # TF-IDF-style word frequency scoring
        words = re.findall(r"\b\w+\b", text.lower())
        freq: dict = {}
        for w in words:
            if w not in self._STOP_WORDS and len(w) > 2:
                freq[w] = freq.get(w, 0) + 1

        # Score each sentence
        scored = []
        for idx, s in enumerate(sentences):
            s = s.strip()
            if len(s) < 10:
                continue
            score = sum(freq.get(w.lower(), 0) for w in re.findall(r"\b\w+\b", s))
            # Position bonus: first and last sentences often carry the main idea
            if idx == 0 or idx == len(sentences) - 1:
                score += 5
            scored.append((score, s))

        scored.sort(reverse=True)
        n = min(num_points, max(3, len(sentences) // 4), len(scored))
        key_points = [s for _, s in scored[:n]]

        # Topic keywords (top-8 non-stop words)
        top_keywords = sorted(freq, key=freq.get, reverse=True)[:8]

        bullets = "\n".join(f"• {s}" for s in key_points)
        result = (
            f"📄 **Document Summary**\n\n"
            f"**Stats:** {word_count:,} words · {len(sentences)} sentences\n\n"
            f"**Key Points:**\n{bullets}\n\n"
            f"**Top Keywords:** {', '.join(f'`{k}`' for k in top_keywords)}"
        )
        return {
            "success": True,
            "result": result,
            "key_points": key_points,
            "keywords": top_keywords,
            "word_count": word_count,
        }