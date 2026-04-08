"""developer_tools — code generator and API tester."""

from __future__ import annotations
import time
import json
import re

import httpx

from core.tool_registry import BaseTool, register_tool


# ── 1. Code Generator — Groq LLM + template fallback ─────────────────────────

@register_tool(
    name="code",
    display_name="💻 Code Generator",
    category="developer_tools",
    description="Generate code in any language using AI",
    keywords=["code", "generate", "function", "algorithm", "python", "java",
              "javascript", "snippet", "script", "program", "write"],
    input_type="chat",
)
class CodeGeneratorTool(BaseTool):

    _TEMPLATES = {
        ("quick", "sort"):    ("QuickSort (Python)",
            "def quick_sort(arr):\n"
            "    if len(arr) <= 1:\n        return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left   = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right  = [x for x in arr if x > pivot]\n"
            "    return quick_sort(left) + middle + quick_sort(right)", "python"),

        ("merge", "sort"):    ("MergeSort (Python)",
            "def merge_sort(arr):\n"
            "    if len(arr) <= 1:\n        return arr\n"
            "    mid   = len(arr) // 2\n"
            "    left  = merge_sort(arr[:mid])\n"
            "    right = merge_sort(arr[mid:])\n"
            "    return _merge(left, right)\n\n"
            "def _merge(l, r):\n"
            "    result, i, j = [], 0, 0\n"
            "    while i < len(l) and j < len(r):\n"
            "        if l[i] < r[j]: result.append(l[i]); i += 1\n"
            "        else:           result.append(r[j]); j += 1\n"
            "    return result + l[i:] + r[j:]", "python"),

        ("binary", "search"): ("Binary Search (Python)",
            "def binary_search(arr, target):\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:   return mid\n"
            "        elif arr[mid] < target:  left = mid + 1\n"
            "        else:                    right = mid - 1\n"
            "    return -1", "python"),

        ("fibonacci",):       ("Fibonacci (Python)",
            "def fibonacci(n):\n"
            "    if n <= 0: return []\n"
            "    if n == 1: return [0]\n"
            "    seq = [0, 1]\n"
            "    while len(seq) < n:\n"
            "        seq.append(seq[-1] + seq[-2])\n"
            "    return seq", "python"),

        ("factorial",):       ("Factorial (Python)",
            "def factorial(n):\n"
            "    if n < 0:  raise ValueError('Negative input')\n"
            "    if n == 0: return 1\n"
            "    return n * factorial(n - 1)", "python"),

        ("palindrome",):      ("Palindrome Check (Python)",
            "def is_palindrome(s):\n"
            "    s = ''.join(c.lower() for c in s if c.isalnum())\n"
            "    return s == s[::-1]", "python"),
    }

    def run(self, prompt: str = "", **kwargs) -> dict:
        # Try Groq LLM first — handles ANY language
        try:
            from services.llm_service import get_llm
            llm = get_llm()

            # Detect language from prompt
            lang = self._detect_language(prompt)

            response = llm.complete(
                prompt=f"Write code for the following request:\n\n{prompt}",
                system=(
                    f"You are an expert {lang} developer. "
                    f"Write clean, working, well-commented {lang} code. "
                    f"Return ONLY the code block with no extra explanation before or after it. "
                    f"Use markdown code fences with the language specified, like ```{lang.lower()}."
                ),
                max_tokens=1024,
            )

            if response and not response.startswith("❌") and not response.startswith("⚠️"):
                # Clean up response — ensure it has code fences
                if "```" not in response:
                    lang_lower = lang.lower()
                    response = f"```{lang_lower}\n{response}\n```"
                return {
                    "success": True,
                    "result": f"💻 **{lang} Code**\n\n{response}\n\n*Powered by AI*",
                    "language": lang,
                }
        except Exception:
            pass  # Fall through to templates

        # Fallback: Python template matching
        return self._template_match(prompt)

    def _detect_language(self, prompt: str) -> str:
        """Detect programming language from the prompt."""
        p = prompt.lower()
        langs = {
            "java":       ["java", "class ", "public static", "system.out"],
            "javascript": ["javascript", "js", "node", "nodejs", "react", "typescript", "ts"],
            "c++":        ["c++", "cpp", "#include", "cout", "cin"],
            "c":          [" c ", "c language", "printf", "scanf", "#include <stdio"],
            "rust":       ["rust", "fn main", "cargo"],
            "go":         ["golang", "go lang", " go ", "fmt.println"],
            "sql":        ["sql", "select ", "insert ", "create table"],
            "html":       ["html", "webpage", "web page", "<div", "css"],
            "bash":       ["bash", "shell script", "#!/bin/bash"],
            "r":          [" r ", "r language", "ggplot", "data.frame"],
        }
        for lang, keywords in langs.items():
            if any(kw in p for kw in keywords):
                return lang.title() if lang not in ("sql", "html", "r") else lang.upper()
        return "Python"  # default

    def _template_match(self, prompt: str) -> dict:
        p = prompt.lower()
        name, code, lang = "Custom Function", (
            f"def solution():\n    '''{prompt}'''\n    # TODO: implement\n    pass"
        ), "python"
        for keys, (tname, tcode, tlang) in self._TEMPLATES.items():
            if all(k in p for k in keys):
                name, code, lang = tname, tcode, tlang
                break
        return {
            "success": True,
            "result": (
                f"💻 **{name}**\n\n```{lang}\n{code}\n```\n\n"
                f"✅ Ready to use!\n\n"
                f"💡 *Add GROQ_API_KEY to .env for AI-powered code generation in any language*"
            ),
            "code": code,
        }


# ── 2. API Tester ─────────────────────────────────────────────────────────────

@register_tool(
    name="api",
    display_name="🌐 API Tester",
    category="developer_tools",
    description="Test REST API endpoints and inspect responses",
    keywords=["api", "http", "get", "post", "endpoint", "request", "url", "rest"],
    input_type="form",
)
class APITesterTool(BaseTool):

    def run(
        self,
        url: str = "",
        method: str = "GET",
        headers: dict = None,
        body: str = "",
        **kwargs,
    ) -> dict:
        if not url:
            return {"success": False, "result": "❌ URL is required."}
        start = time.time()
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.request(
                    method.upper(),
                    url,
                    headers=headers or {},
                    content=body.encode() if body else None,
                )
            elapsed = int((time.time() - start) * 1000)
            try:
                body_preview = json.dumps(resp.json(), indent=2)[:800]
                ct = "JSON"
            except Exception:
                body_preview = resp.text[:800]
                ct = resp.headers.get("content-type", "text/plain")

            emoji = "✅" if resp.status_code < 400 else "❌"
            result = (
                f"🌐 **API Test — {method.upper()} {url}**\n\n"
                f"**Status:** {emoji} {resp.status_code}\n"
                f"**Time:** {elapsed}ms\n"
                f"**Content-Type:** {ct}\n\n"
                f"**Response:**\n```json\n{body_preview}\n```"
            )
            return {"success": resp.status_code < 400, "result": result,
                    "status_code": resp.status_code, "elapsed_ms": elapsed}
        except httpx.ConnectError:
            return {"success": False, "result": f"❌ Cannot connect to `{url}`"}
        except httpx.TimeoutException:
            return {"success": False, "result": "❌ Request timed out (15s)"}
        except Exception as e:
            return {"success": False, "result": f"❌ Error: {str(e)}"}