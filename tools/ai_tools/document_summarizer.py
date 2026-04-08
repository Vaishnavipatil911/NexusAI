"""ai_tools — document summarizer powered by Groq LLM."""

from __future__ import annotations
import re

from core.tool_registry import BaseTool, register_tool


@register_tool(
    name="summarizer",
    display_name="📄 Doc Summarizer",
    category="ai_tools",
    description="Summarize long text documents into key bullet points using AI",
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
            return {"success": False, "result": "❌ Text too short to summarize (minimum 50 characters)."}

        word_count = len(text.split())

        # Try Groq LLM first
        try:
            from services.llm_service import get_llm
            llm = get_llm()
            response = llm.complete(
                prompt=(
                    f"Summarize the following text. Return:\n"
                    f"1. A 2-sentence overview\n"
                    f"2. Exactly {num_points} key bullet points (start each with •)\n"
                    f"3. Top 5 keywords as a comma-separated list after 'Keywords:'\n\n"
                    f"Text ({word_count} words):\n{text[:4000]}"
                ),
                system=(
                    "You are an expert summarizer. Be concise and accurate. "
                    "Extract the most important information. "
                    "Always follow the exact format requested."
                ),
                max_tokens=768,
            )

            if response and not response.startswith("❌") and not response.startswith("⚠️"):
                return {
                    "success": True,
                    "result": (
                        f"📄 **Document Summary**\n\n"
                        f"**Stats:** {word_count:,} words\n\n"
                        f"{response}\n\n"
                        f"*Powered by AI*"
                    ),
                    "word_count": word_count,
                }
        except Exception:
            pass  # Fall through to rule-based

        # Fallback: TF-IDF sentence scoring
        return self._rule_based(text, word_count, num_points)

    def _rule_based(self, text: str, word_count: int, num_points: int) -> dict:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        words = re.findall(r"\b\w+\b", text.lower())
        freq: dict = {}
        for w in words:
            if w not in self._STOP_WORDS and len(w) > 2:
                freq[w] = freq.get(w, 0) + 1

        scored = []
        for idx, s in enumerate(sentences):
            s = s.strip()
            if len(s) < 10:
                continue
            score = sum(freq.get(w.lower(), 0) for w in re.findall(r"\b\w+\b", s))
            if idx == 0 or idx == len(sentences) - 1:
                score += 5
            scored.append((score, s))

        scored.sort(reverse=True)
        n = min(num_points, max(3, len(sentences) // 4), len(scored))
        key_points = [s for _, s in scored[:n]]
        top_keywords = sorted(freq, key=freq.get, reverse=True)[:8]

        bullets = "\n".join(f"• {s}" for s in key_points)
        return {
            "success": True,
            "result": (
                f"📄 **Document Summary**\n\n"
                f"**Stats:** {word_count:,} words · {len(sentences)} sentences\n\n"
                f"**Key Points:**\n{bullets}\n\n"
                f"**Top Keywords:** {', '.join(f'`{k}`' for k in top_keywords)}\n\n"
                f"💡 *Add GROQ_API_KEY to .env for AI-powered summaries*"
            ),
            "key_points": key_points,
            "keywords": top_keywords,
            "word_count": word_count,
        }