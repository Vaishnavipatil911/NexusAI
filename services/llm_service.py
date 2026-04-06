"""
services/llm_service.py

Priority order (uses whichever key is set in .env):
  1. Groq          — fastest, 14,400 req/day free, no card needed
  2. Google Gemini — 1,500 req/day free, no card needed
  3. Together AI   — $5 free credit on signup
  4. Ollama        — runs locally, 100% free, no internet needed
  5. Stub          — returns a placeholder so the app never crashes

Add to your .env:
  GROQ_API_KEY=gsk_...          ← get free at groq.com
  GEMINI_API_KEY=AIza...        ← get free at aistudio.google.com
  TOGETHER_API_KEY=...          ← get free at together.ai
  OLLAMA_MODEL=llama3           ← if running Ollama locally
"""

from __future__ import annotations
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self):
        self._groq_key     = os.getenv("GROQ_API_KEY", "")
        self._gemini_key   = os.getenv("GEMINI_API_KEY", "")
        self._together_key = os.getenv("TOGETHER_API_KEY", "")
        self._ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self._ollama_url   = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        """
        Returns a text completion. Tries providers in order until one succeeds.
        """
        if self._groq_key:
            result = self._groq(prompt, system, max_tokens)
            if not result.startswith("❌"):
                return result

        if self._gemini_key:
            result = self._gemini(prompt, system, max_tokens)
            if not result.startswith("❌"):
                return result

        if self._together_key:
            result = self._together(prompt, system, max_tokens)
            if not result.startswith("❌"):
                return result

        # Try Ollama (local) — works even without any API key
        result = self._ollama(prompt, system, max_tokens)
        if not result.startswith("❌"):
            return result

        logger.warning("No LLM provider available — returning stub.")
        return (
            "⚠️ No LLM API key configured.\n\n"
            "Add one of these to your .env file:\n"
            "• GROQ_API_KEY — free at groq.com\n"
            "• GEMINI_API_KEY — free at aistudio.google.com\n"
            "• OLLAMA_MODEL=llama3 — run Ollama locally"
        )

    def which_provider(self) -> str:
        """Returns which provider will be used — useful for the UI status bar."""
        if self._groq_key:     return "Groq (Llama 3.1)"
        if self._gemini_key:   return "Google Gemini"
        if self._together_key: return "Together AI"
        return "Ollama (local)" if self._ollama_available() else "None configured"

    # ── Groq ──────────────────────────────────────────────────────────────────
    def _groq(self, prompt: str, system: str, max_tokens: int) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self._groq_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",   # fast + free
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"❌ Groq: {e}"

    # ── Google Gemini ──────────────────────────────────────────────────────────
    # def _gemini(self, prompt: str, system: str, max_tokens: int) -> str:
    #     try:
    #         import google.generativeai as genai
    #         genai.configure(api_key=self._gemini_key)
    #         model = genai.GenerativeModel(
    #             model_name="gemini-1.5-flash",
    #             system_instruction=system if system else None,
    #         )
    #         resp = model.generate_content(
    #             prompt,
    #             generation_config={"max_output_tokens": max_tokens},
    #         )
    #         return resp.text
    #     except Exception as e:
    #         logger.error(f"Gemini error: {e}")
    #         return f"❌ Gemini: {e}"

    # ── Together AI ────────────────────────────────────────────────────────────
    def _together(self, prompt: str, system: str, max_tokens: int) -> str:
        try:
            import httpx
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = httpx.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._together_key}"},
                json={
                    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                    "messages": messages,
                    "max_tokens": max_tokens,
                },
                timeout=30,
            )
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Together AI error: {e}")
            return f"❌ Together: {e}"

    # ── Ollama (local) ─────────────────────────────────────────────────────────
    def _ollama(self, prompt: str, system: str, max_tokens: int) -> str:
        try:
            import httpx
            payload = {
                "model": self._ollama_model,
                "prompt": f"{system}\n\n{prompt}" if system else prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
            resp = httpx.post(
                f"{self._ollama_url}/api/generate",
                json=payload,
                timeout=60,
            )
            return resp.json().get("response", "❌ Empty response from Ollama")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"❌ Ollama: {e}"

    def _ollama_available(self) -> bool:
        try:
            import httpx
            httpx.get(f"{self._ollama_url}/api/tags", timeout=2)
            return True
        except Exception:
            return False


# ── Module-level singleton ─────────────────────────────────────────────────────
_llm = LLMService()

def get_llm() -> LLMService:
    return _llm