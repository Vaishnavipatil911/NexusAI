import tools.utility_tools.weather_tool
import tools.developer_tools.code_generator
import tools.data_tools.csv_analyzer
import tools.ai_tools.document_summarizer
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, re, math, hashlib, sqlite3, datetime, io, httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="AI Tool Hub MCP Server v3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SQLite logging ──────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("query_log.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tool      TEXT,
            query     TEXT,
            result    TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_query(tool: str, query: str, result: str):
    conn = sqlite3.connect("query_log.db")
    conn.execute(
        "INSERT INTO query_log (tool, query, result, timestamp) VALUES (?, ?, ?, ?)",
        (tool, query, result[:500], datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

init_db()

# ── Request models ──────────────────────────────────────────────────────────
class WeatherRequest(BaseModel):
    city: str

class CodeRequest(BaseModel):
    prompt: str

class MathRequest(BaseModel):
    expression: str

class HashRequest(BaseModel):
    text: str
    algorithm: str = "sha256"

class GrammarRequest(BaseModel):
    text: str

class SummarizerRequest(BaseModel):
    text: str

class PasswordRequest(BaseModel):
    password: str

class APITestRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: dict = {}
    body: str = ""

class ResumeRequest(BaseModel):
    description: str

# ── Root ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "✅ MCP Server v3.0",
        "tools": [
            "get_weather", "code_gen", "math_solver", "hash_gen",
            "grammar_fix", "summarizer", "csv_analyze",
            "password_check", "api_tester", "resume_bullets"
        ]
    }

@app.get("/logs")
def get_logs(limit: int = 50):
    conn = sqlite3.connect("query_log.db")
    rows = conn.execute(
        "SELECT tool, query, result, timestamp FROM query_log ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"tool": r[0], "query": r[1], "result": r[2], "timestamp": r[3]} for r in rows]

# ── 1. Weather ───────────────────────────────────────────────────────────────
@app.post("/tools/get_weather")
def get_weather(request: WeatherRequest):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"result": "❌ OPENWEATHER_API_KEY not set in .env"}
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={request.city}&appid={api_key}&units=metric"
    )
    try:
        r = httpx.get(url, timeout=10)
        d = r.json()
        if r.status_code == 200:
            desc   = d["weather"][0]["description"].capitalize()
            temp   = d["main"]["temp"]
            feels  = d["main"]["feels_like"]
            humid  = d["main"]["humidity"]
            wind   = d["wind"]["speed"]
            result = (
                f"🌤️ **{request.city.title()} Weather**\n\n"
                f"**Condition:** {desc}\n"
                f"**Temperature:** {temp}°C (feels like {feels}°C)\n"
                f"**Humidity:** {humid}%\n"
                f"**Wind:** {wind} m/s"
            )
        else:
            result = f"❌ City '{request.city}' not found. Check spelling."
    except Exception as e:
        result = f"❌ Weather error: {str(e)}"
    log_query("Weather", request.city, result)
    return {"result": result}

# ── 2. Code Generator ────────────────────────────────────────────────────────
@app.post("/tools/code_gen")
def code_gen(request: CodeRequest):
    p = request.prompt.lower()
    templates = {
        ("quick", "sort"):       ("QuickSort", "def quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left   = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right  = [x for x in arr if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)"),
        ("merge", "sort"):       ("MergeSort",  "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left  = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(l, r):\n    result = []\n    i = j = 0\n    while i < len(l) and j < len(r):\n        if l[i] < r[j]: result.append(l[i]); i += 1\n        else:           result.append(r[j]); j += 1\n    return result + l[i:] + r[j:]"),
        ("binary", "search"):    ("Binary Search", "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:   return mid\n        elif arr[mid] < target:  left = mid + 1\n        else:                    right = mid - 1\n    return -1"),
        ("linked", "list"):      ("Linked List", "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n\n    def append(self, data):\n        new_node = Node(data)\n        if not self.head:\n            self.head = new_node; return\n        cur = self.head\n        while cur.next:\n            cur = cur.next\n        cur.next = new_node\n\n    def display(self):\n        cur, values = self.head, []\n        while cur:\n            values.append(str(cur.data))\n            cur = cur.next\n        print(' -> '.join(values))"),
        ("fibonacci",):          ("Fibonacci", "def fibonacci(n):\n    if n <= 0: return []\n    if n == 1: return [0]\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq"),
        ("factorial",):          ("Factorial", "def factorial(n):\n    if n < 0:  raise ValueError('Negative input')\n    if n == 0: return 1\n    return n * factorial(n - 1)"),
        ("calculator",):         ("Calculator", "def calculator(a, b, op):\n    ops = {'+': a+b, '-': a-b, '*': a*b, '/': a/b if b else 'Div/0'}\n    return ops.get(op, 'Unknown op')"),
        ("palindrome",):         ("Palindrome Check", "def is_palindrome(s):\n    s = ''.join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]"),
        ("stack",):              ("Stack", "class Stack:\n    def __init__(self):\n        self._data = []\n    def push(self, item): self._data.append(item)\n    def pop(self):        return self._data.pop() if self._data else None\n    def peek(self):       return self._data[-1] if self._data else None\n    def is_empty(self):   return len(self._data) == 0\n    def size(self):       return len(self._data)"),
        ("api", "request"):      ("API Request", "import requests\n\ndef fetch_data(url, params=None, headers=None):\n    try:\n        response = requests.get(url, params=params, headers=headers, timeout=10)\n        response.raise_for_status()\n        return response.json()\n    except requests.exceptions.RequestException as e:\n        return {'error': str(e)}"),
        ("read", "file"):        ("File Reader", "def read_file(filepath, encoding='utf-8'):\n    try:\n        with open(filepath, 'r', encoding=encoding) as f:\n            return f.read()\n    except FileNotFoundError:\n        return f'File not found: {filepath}'\n    except Exception as e:\n        return f'Error: {e}'"),
    }
    chosen_name, chosen_code = "Custom Function", f"def solution():\n    '''{request.prompt}'''\n    # TODO: Implement\n    pass"
    for keys, (name, code) in templates.items():
        if all(k in p for k in keys):
            chosen_name, chosen_code = name, code
            break
    result = f"💻 **{chosen_name}**\n\n```python\n{chosen_code}\n```\n\n✅ Ready to use!"
    log_query("Code Gen", request.prompt, result)
    return {"result": result}

# ── 3. Math Solver ───────────────────────────────────────────────────────────
@app.post("/tools/math_solver")
def math_solver(request: MathRequest):
    expr = request.expression.strip()
    safe_globals = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    safe_globals["abs"] = abs
    try:
        result_val = eval(expr, {"__builtins__": {}}, safe_globals)
        if isinstance(result_val, float):
            result_val = round(result_val, 10)
        result = f"🧮 `{expr}` = **{result_val}**"
    except ZeroDivisionError:
        result = "❌ Division by zero"
    except Exception:
        result = f"❌ Could not evaluate `{expr}`. Try: `2+2`, `sqrt(16)`, `sin(pi/2)`, `2**10`"
    log_query("Math Solver", expr, result)
    return {"result": result}

# ── 4. Hash Generator ────────────────────────────────────────────────────────
@app.post("/tools/hash_gen")
def hash_gen(request: HashRequest):
    algo = request.algorithm.lower().replace("-", "")
    supported = {"md5", "sha1", "sha256", "sha512", "sha224", "sha384"}
    if algo not in supported:
        return {"result": f"❌ Unsupported algorithm. Choose: {', '.join(sorted(supported))}"}
    h = hashlib.new(algo, request.text.encode()).hexdigest()
    result = (
        f"🔐 **{algo.upper()} Hash**\n\n"
        f"**Input:** `{request.text[:60]}{'...' if len(request.text) > 60 else ''}`\n"
        f"**Hash:** `{h}`"
    )
    log_query("Hash Gen", f"{algo}:{request.text[:30]}", result)
    return {"result": result}

# ── 5. Grammar Fixer ─────────────────────────────────────────────────────────
@app.post("/tools/grammar_fix")
def grammar_fix(request: GrammarRequest):
    text = request.text.strip()
    fixes = []
    corrected = text

    # Common rule-based corrections
    rules = [
        (r'\bi\b',            'I',          "Capitalize pronoun 'I'"),
        (r'\s{2,}',           ' ',          "Remove extra spaces"),
        (r'([.!?])\s*([a-z])',lambda m: m.group(1) + ' ' + m.group(2).upper(), "Capitalize after sentence end"),
        (r'\b(its)\s+(a|an|the)\b', r"it's \2", "its → it's (contraction)"),
        (r'\b(dont)\b',       "don't",      "dont → don't"),
        (r'\b(cant)\b',       "can't",      "cant → can't"),
        (r'\b(wont)\b',       "won't",      "wont → won't"),
        (r'\b(shouldnt)\b',   "shouldn't",  "shouldnt → shouldn't"),
        (r'\b(couldnt)\b',    "couldn't",   "couldnt → couldn't"),
        (r'\b(wouldnt)\b',    "wouldn't",   "wouldnt → wouldn't"),
        (r'\b(doesnt)\b',     "doesn't",    "doesnt → doesn't"),
        (r'\b(didnt)\b',      "didn't",     "didnt → didn't"),
        (r'\b(isnt)\b',       "isn't",      "isnt → isn't"),
        (r'\b(arent)\b',      "aren't",     "arent → aren't"),
    ]

    for pattern, replacement, desc in rules:
        new_text = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE if isinstance(replacement, str) else 0)
        if new_text != corrected:
            fixes.append(f"• {desc}")
            corrected = new_text

    # Ensure ends with punctuation
    if corrected and corrected[-1] not in ".!?":
        corrected += "."
        fixes.append("• Added missing end punctuation")

    # Capitalize first letter
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]

    if not fixes:
        result = f"✅ **No grammar issues found!**\n\n> {text}"
    else:
        result = (
            f"✏️ **Grammar Corrected**\n\n"
            f"**Original:** {text}\n\n"
            f"**Corrected:** {corrected}\n\n"
            f"**Changes made:**\n" + "\n".join(fixes)
        )
    log_query("Grammar Fix", text[:80], result)
    return {"result": result}

# ── 6. Document Summarizer ───────────────────────────────────────────────────
@app.post("/tools/summarizer")
def summarizer(request: SummarizerRequest):
    text = request.text.strip()
    if len(text) < 50:
        return {"result": "❌ Text too short to summarize (min 50 chars)."}
    sentences = re.split(r'(?<=[.!?])\s+', text)
    word_count = len(text.split())
    char_count = len(text)

    # Score sentences by keyword frequency
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {"the","a","an","is","it","in","on","at","to","for","of","and","or","but","with","this","that","was","are","were","be","been","have","has","had","do","did","not","from","by","as","its","their","they","we","you","he","she","my","our","your","his","her"}
    freq = {}
    for w in words:
        if w not in stop_words and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1

    scored = []
    for s in sentences:
        score = sum(freq.get(w.lower(), 0) for w in re.findall(r'\b\w+\b', s))
        scored.append((score, s))

    scored.sort(reverse=True)
    num_bullets = min(5, max(3, len(sentences) // 4))
    key_points = [s for _, s in scored[:num_bullets] if s.strip()]
    key_points_md = "\n".join(f"• {s.strip()}" for s in key_points)

    result = (
        f"📄 **Document Summary**\n\n"
        f"**Stats:** {word_count} words · {len(sentences)} sentences · {char_count} chars\n\n"
        f"**Key Points:**\n{key_points_md}"
    )
    log_query("Summarizer", text[:80] + "...", result)
    return {"result": result}

# ── 7. CSV Analyzer ──────────────────────────────────────────────────────────
@app.post("/tools/csv_analyze")
async def csv_analyze(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        rows, cols = df.shape
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        text_cols    = df.select_dtypes(include="object").columns.tolist()
        missing      = df.isnull().sum().sum()

        lines = [
            f"📊 **CSV Analysis: `{file.filename}`**\n",
            f"**Shape:** {rows} rows × {cols} columns",
            f"**Numeric columns ({len(numeric_cols)}):** {', '.join(numeric_cols) or 'None'}",
            f"**Text columns ({len(text_cols)}):** {', '.join(text_cols) or 'None'}",
            f"**Missing values:** {missing}",
            "",
            "**Numeric Statistics:**"
        ]
        if numeric_cols:
            desc = df[numeric_cols].describe().round(2)
            for col in numeric_cols:
                lines.append(
                    f"• **{col}**: min={desc[col]['min']}, max={desc[col]['max']}, "
                    f"mean={desc[col]['mean']:.2f}, std={desc[col]['std']:.2f}"
                )
        else:
            lines.append("• No numeric columns found")

        result = "\n".join(lines)
        log_query("CSV Analyzer", file.filename, result)
        return {"result": result, "columns": list(df.columns), "shape": [rows, cols]}
    except Exception as e:
        return {"result": f"❌ CSV Error: {str(e)}"}

# ── 8. Password Strength Checker ─────────────────────────────────────────────
@app.post("/tools/password_check")
def password_check(request: PasswordRequest):
    pwd = request.password
    score = 0
    feedback = []

    checks = [
        (len(pwd) >= 8,  1, "✅ 8+ characters",           "❌ Too short (min 8 chars)"),
        (len(pwd) >= 12, 1, "✅ 12+ characters",          None),
        (len(pwd) >= 16, 1, "✅ 16+ characters (great!)", None),
        (bool(re.search(r'[A-Z]', pwd)), 1, "✅ Has uppercase letters", "❌ Add uppercase letters (A-Z)"),
        (bool(re.search(r'[a-z]', pwd)), 1, "✅ Has lowercase letters", "❌ Add lowercase letters (a-z)"),
        (bool(re.search(r'\d',    pwd)), 1, "✅ Has numbers",           "❌ Add numbers (0-9)"),
        (bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-\[\]\\]', pwd)), 2,
         "✅ Has special characters", "❌ Add special chars (!@#$...)"),
        (not re.search(r'(.)\1{2,}', pwd), 1, "✅ No repeated chars",    "⚠️ Avoid repeating characters"),
        (pwd.lower() not in {"password","123456","qwerty","abc123","letmein","admin","welcome"},
         1, "✅ Not a common password", "❌ This is a very common password!"),
    ]
    for passed, pts, good_msg, bad_msg in checks:
        if passed:
            score += pts
            feedback.append(good_msg)
        elif bad_msg:
            feedback.append(bad_msg)

    max_score = sum(pts for _, pts, _, _ in checks)
    pct = int((score / max_score) * 100)
    if pct >= 80:   label, bar = "💪 Strong",    "🟩🟩🟩🟩🟩"
    elif pct >= 60: label, bar = "😐 Moderate",  "🟨🟨🟨⬜⬜"
    elif pct >= 40: label, bar = "⚠️ Weak",      "🟧🟧⬜⬜⬜"
    else:           label, bar = "🔴 Very Weak", "🟥⬜⬜⬜⬜"

    result = (
        f"🔒 **Password Strength: {label}**\n\n"
        f"**Score:** {pct}% {bar}\n\n"
        f"**Analysis:**\n" + "\n".join(feedback)
    )
    log_query("Password Check", f"[password hidden]", result)
    return {"result": result, "score": pct}

# ── 9. API Tester ────────────────────────────────────────────────────────────
@app.post("/tools/api_tester")
async def api_tester(request: APITestRequest):
    import time
    start = time.time()
    try:
        method = request.method.upper()
        headers = request.headers or {}
        body_data = request.body or None

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(method, request.url, headers=headers, content=body_data)

        elapsed = round((time.time() - start) * 1000)
        try:
            body = resp.json()
            body_preview = str(body)[:600]
            content_type = "JSON"
        except Exception:
            body_preview = resp.text[:600]
            content_type = resp.headers.get("content-type", "text/plain")

        status_emoji = "✅" if resp.status_code < 400 else "❌"
        result = (
            f"🌐 **API Test Result**\n\n"
            f"**URL:** `{request.url}`\n"
            f"**Method:** {method}\n"
            f"**Status:** {status_emoji} {resp.status_code} ({resp.reason_phrase})\n"
            f"**Time:** {elapsed}ms\n"
            f"**Content-Type:** {content_type}\n\n"
            f"**Response Preview:**\n```\n{body_preview}\n```"
        )
    except httpx.ConnectError:
        result = f"❌ Could not connect to `{request.url}`. Check the URL."
    except httpx.TimeoutException:
        result = f"❌ Request timed out after 15s."
    except Exception as e:
        result = f"❌ Error: {str(e)}"
    log_query("API Tester", f"{request.method} {request.url}", result)
    return {"result": result}

# ── 10. Resume Bullet Generator ──────────────────────────────────────────────
@app.post("/tools/resume_bullets")
def resume_bullets(request: ResumeRequest):
    desc = request.description.strip()
    action_verbs = [
        "Developed", "Built", "Designed", "Implemented", "Optimized",
        "Deployed", "Automated", "Integrated", "Led", "Delivered",
        "Architected", "Reduced", "Improved", "Increased", "Managed"
    ]
    import random
    random.seed(len(desc))
    verbs = random.sample(action_verbs, min(5, len(action_verbs)))

    # Extract tech keywords
    tech_pattern = r'\b(Python|Java|React|Node|FastAPI|SQL|AWS|Docker|Kubernetes|ML|AI|API|REST|GraphQL|TensorFlow|Streamlit|Pandas)\b'
    techs = list(set(re.findall(tech_pattern, desc, re.IGNORECASE)))
    tech_str = f" using {', '.join(techs[:3])}" if techs else ""

    words = desc.split()
    short = ' '.join(words[:6]) if len(words) > 6 else desc

    bullets = [
        f"• {verbs[0]} {short.lower()}{tech_str}, improving team productivity by 30%",
        f"• {verbs[1]} scalable solution for {short.lower()}, reducing manual effort by 40%",
        f"• {verbs[2]} and deployed end-to-end {short.lower()}{tech_str} serving 500+ users",
        f"• {verbs[3]} automated pipeline for {short.lower()}, cutting processing time by 50%",
        f"• {verbs[4]} cross-functional collaboration to deliver {short.lower()} on schedule",
    ]

    result = f"📝 **Resume Bullets**\n\n" + "\n".join(bullets) + "\n\n💡 *Customize the metrics to match your actual impact.*"
    log_query("Resume Bullets", desc[:80], result)
    return {"result": result}