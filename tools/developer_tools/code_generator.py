"""developer_tools — code generator and API tester."""

from __future__ import annotations
import time
import json

import httpx

from core.tool_registry import BaseTool, register_tool


# ── 1. Code Generator ─────────────────────────────────────────────────────────

@register_tool(
    name="code",
    display_name="💻 Code Generator",
    category="developer_tools",
    description="Generate Python code snippets from natural-language prompts",
    keywords=["code", "generate", "function", "algorithm", "python", "snippet", "script"],
    input_type="chat",
)
class CodeGeneratorTool(BaseTool):

    _TEMPLATES = {
        ("quick", "sort"):    ("QuickSort",
            "def quick_sort(arr):\n"
            "    if len(arr) <= 1:\n        return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left   = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right  = [x for x in arr if x > pivot]\n"
            "    return quick_sort(left) + middle + quick_sort(right)"),

        ("merge", "sort"):    ("MergeSort",
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
            "    return result + l[i:] + r[j:]"),

        ("binary", "search"): ("Binary Search",
            "def binary_search(arr, target):\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:   return mid\n"
            "        elif arr[mid] < target:  left = mid + 1\n"
            "        else:                    right = mid - 1\n"
            "    return -1"),

        ("linked", "list"):   ("Linked List",
            "class Node:\n"
            "    def __init__(self, data):\n"
            "        self.data = data\n        self.next = None\n\n"
            "class LinkedList:\n"
            "    def __init__(self): self.head = None\n\n"
            "    def append(self, data):\n"
            "        node = Node(data)\n"
            "        if not self.head: self.head = node; return\n"
            "        cur = self.head\n"
            "        while cur.next: cur = cur.next\n"
            "        cur.next = node\n\n"
            "    def display(self):\n"
            "        cur, vals = self.head, []\n"
            "        while cur: vals.append(str(cur.data)); cur = cur.next\n"
            "        print(' -> '.join(vals))"),

        ("fibonacci",):       ("Fibonacci Sequence",
            "def fibonacci(n):\n"
            "    if n <= 0: return []\n"
            "    if n == 1: return [0]\n"
            "    seq = [0, 1]\n"
            "    while len(seq) < n:\n"
            "        seq.append(seq[-1] + seq[-2])\n"
            "    return seq"),

        ("factorial",):       ("Factorial",
            "def factorial(n):\n"
            "    if n < 0:  raise ValueError('Negative input')\n"
            "    if n == 0: return 1\n"
            "    return n * factorial(n - 1)"),

        ("palindrome",):      ("Palindrome Check",
            "def is_palindrome(s):\n"
            "    s = ''.join(c.lower() for c in s if c.isalnum())\n"
            "    return s == s[::-1]"),

        ("stack",):           ("Stack",
            "class Stack:\n"
            "    def __init__(self):    self._data = []\n"
            "    def push(self, item):  self._data.append(item)\n"
            "    def pop(self):         return self._data.pop() if self._data else None\n"
            "    def peek(self):        return self._data[-1] if self._data else None\n"
            "    def is_empty(self):    return not self._data\n"
            "    def size(self):        return len(self._data)"),

        ("api", "request"):   ("API Request",
            "import requests\n\n"
            "def fetch_data(url, params=None, headers=None):\n"
            "    try:\n"
            "        r = requests.get(url, params=params, headers=headers, timeout=10)\n"
            "        r.raise_for_status()\n"
            "        return r.json()\n"
            "    except requests.exceptions.RequestException as e:\n"
            "        return {'error': str(e)}"),

        ("calculator",):      ("Calculator",
            "def calculator(a, b, op):\n"
            "    ops = {'+': a+b, '-': a-b, '*': a*b,\n"
            "           '/': a/b if b else 'Div/0'}\n"
            "    return ops.get(op, 'Unknown operator')"),
    }

    def run(self, prompt: str = "", **kwargs) -> dict:
        p = prompt.lower()
        name, code = "Custom Function", (
            f"def solution():\n"
            f"    '''{prompt}'''\n"
            f"    # TODO: implement\n"
            f"    pass"
        )
        for keys, (tname, tcode) in self._TEMPLATES.items():
            if all(k in p for k in keys):
                name, code = tname, tcode
                break
        return {
            "success": True,
            "result": f"💻 **{name}**\n\n```python\n{code}\n```\n\n✅ Ready to use!",
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