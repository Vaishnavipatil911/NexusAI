"""utility_tools — weather, math, hash, password, grammar, resume bullets."""

from __future__ import annotations
import hashlib
import math
import os
import re

import httpx
from dotenv import load_dotenv

from core.tool_registry import BaseTool, register_tool

load_dotenv()


# ── 1. Weather ────────────────────────────────────────────────────────────────

@register_tool(
    name="weather",
    display_name="🌤️ Weather",
    category="utility_tools",
    description="Real-time weather for any city",
    keywords=["weather", "temperature", "forecast", "city", "humidity"],
    input_type="chat",
)
class WeatherTool(BaseTool):
    def run(self, city: str = "London", **kwargs) -> dict:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {"success": False, "result": "❌ OPENWEATHER_API_KEY not set in .env"}
        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric"
        )
        r = httpx.get(url, timeout=10)
        d = r.json()
        if r.status_code == 200:
            desc  = d["weather"][0]["description"].capitalize()
            temp  = d["main"]["temp"]
            feels = d["main"]["feels_like"]
            humid = d["main"]["humidity"]
            wind  = d["wind"]["speed"]
            result = (
                f"🌤️ **{city.title()} Weather**\n\n"
                f"**Condition:** {desc}\n"
                f"**Temperature:** {temp}°C (feels like {feels}°C)\n"
                f"**Humidity:** {humid}%\n"
                f"**Wind:** {wind} m/s"
            )
            return {"success": True, "result": result}
        return {"success": False, "result": f"❌ City '{city}' not found."}


# ── 2. Math Solver ────────────────────────────────────────────────────────────

@register_tool(
    name="math",
    display_name="🧮 Math Solver",
    category="utility_tools",
    description="Evaluate mathematical expressions safely",
    keywords=["math", "calculate", "compute", "expression", "formula"],
    input_type="chat",
)
class MathSolverTool(BaseTool):
    _safe_globals = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    _safe_globals["abs"] = abs

    def run(self, expression: str = "", **kwargs) -> dict:
        expr = expression.strip()
        if not expr:
            return {"success": False, "result": "❌ No expression provided."}
        try:
            val = eval(expr, {"__builtins__": {}}, self._safe_globals)
            if isinstance(val, float):
                val = round(val, 10)
            return {"success": True, "result": f"🧮 `{expr}` = **{val}**"}
        except ZeroDivisionError:
            return {"success": False, "result": "❌ Division by zero."}
        except Exception:
            return {"success": False, "result": f"❌ Cannot evaluate `{expr}`. Try: `sqrt(16)`, `2**10`, `sin(pi/2)`"}


# ── 3. Hash Generator ─────────────────────────────────────────────────────────

@register_tool(
    name="hash",
    display_name="🔐 Hash Generator",
    category="utility_tools",
    description="Generate cryptographic hashes (SHA256, MD5, etc.)",
    keywords=["hash", "sha256", "md5", "sha512", "checksum", "crypto"],
    input_type="form",
)
class HashGeneratorTool(BaseTool):
    SUPPORTED = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512"}

    def run(self, text: str = "", algorithm: str = "sha256", **kwargs) -> dict:
        algo = algorithm.lower().replace("-", "")
        if algo not in self.SUPPORTED:
            return {"success": False, "result": f"❌ Unsupported. Choose: {', '.join(sorted(self.SUPPORTED))}"}
        h = hashlib.new(algo, text.encode()).hexdigest()
        preview = text[:60] + ("..." if len(text) > 60 else "")
        return {
            "success": True,
            "result": (
                f"🔐 **{algo.upper()} Hash**\n\n"
                f"**Input:** `{preview}`\n"
                f"**Hash:** `{h}`"
            ),
            "hash": h,
            "algorithm": algo,
        }


# ── 4. Password Checker ───────────────────────────────────────────────────────

@register_tool(
    name="password",
    display_name="🔒 Password Checker",
    category="utility_tools",
    description="Evaluate password strength with detailed feedback",
    keywords=["password", "strength", "secure", "security", "weak", "strong"],
    input_type="form",
)
class PasswordCheckerTool(BaseTool):
    _COMMON = {"password", "123456", "qwerty", "abc123", "letmein", "admin", "welcome", "iloveyou"}

    def run(self, password: str = "", **kwargs) -> dict:
        pwd = password
        score, feedback = 0, []
        checks = [
            (len(pwd) >= 8,   1, "✅ 8+ characters",          "❌ Too short (min 8 chars)"),
            (len(pwd) >= 12,  1, "✅ 12+ characters",         None),
            (len(pwd) >= 16,  1, "✅ 16+ characters",         None),
            (bool(re.search(r"[A-Z]", pwd)), 1, "✅ Uppercase letters",   "❌ Add uppercase (A-Z)"),
            (bool(re.search(r"[a-z]", pwd)), 1, "✅ Lowercase letters",   "❌ Add lowercase (a-z)"),
            (bool(re.search(r"\d",    pwd)), 1, "✅ Numbers",             "❌ Add numbers (0-9)"),
            (bool(re.search(r'[!@#$%^&*(),.?":{}|<>\-_\[\]\\]', pwd)), 2,
             "✅ Special characters", "❌ Add special chars (!@#$...)"),
            (not re.search(r"(.)\1{2,}", pwd), 1, "✅ No repeated chars",   "⚠️ Avoid repeating chars"),
            (pwd.lower() not in self._COMMON,  1, "✅ Not a common password", "❌ Very common password!"),
        ]
        max_score = sum(pts for _, pts, _, _ in checks)
        for passed, pts, good, bad in checks:
            if passed:
                score += pts
                feedback.append(good)
            elif bad:
                feedback.append(bad)

        pct = int(score / max_score * 100)
        if pct >= 80:   label, bar = "💪 Strong",    "🟩🟩🟩🟩🟩"
        elif pct >= 60: label, bar = "😐 Moderate",  "🟨🟨🟨⬜⬜"
        elif pct >= 40: label, bar = "⚠️ Weak",      "🟧🟧⬜⬜⬜"
        else:           label, bar = "🔴 Very Weak", "🟥⬜⬜⬜⬜"

        return {
            "success": True,
            "score": pct,
            "result": (
                f"🔒 **Password Strength: {label}**\n\n"
                f"**Score:** {pct}% {bar}\n\n"
                f"**Analysis:**\n" + "\n".join(feedback)
            ),
        }


# ── 5. Grammar Fixer ──────────────────────────────────────────────────────────

@register_tool(
    name="grammar",
    display_name="✏️ Grammar Fixer",
    category="utility_tools",
    description="Fix grammar mistakes and improve sentence structure",
    keywords=["grammar", "correct", "proofread", "spelling", "fix", "typo"],
    input_type="chat",
)
class GrammarFixerTool(BaseTool):
    _RULES = [
        (r"\bi\b",            "I",          "Capitalize pronoun 'I'"),
        (r"\s{2,}",           " ",          "Remove extra spaces"),
        (r"\b(dont)\b",       "don't",      "dont → don't"),
        (r"\b(cant)\b",       "can't",      "cant → can't"),
        (r"\b(wont)\b",       "won't",      "wont → won't"),
        (r"\b(shouldnt)\b",   "shouldn't",  "shouldnt → shouldn't"),
        (r"\b(couldnt)\b",    "couldn't",   "couldnt → couldn't"),
        (r"\b(wouldnt)\b",    "wouldn't",   "wouldnt → wouldn't"),
        (r"\b(doesnt)\b",     "doesn't",    "doesnt → doesn't"),
        (r"\b(didnt)\b",      "didn't",     "didnt → didn't"),
        (r"\b(isnt)\b",       "isn't",      "isnt → isn't"),
        (r"\b(arent)\b",      "aren't",     "arent → aren't"),
    ]

    def run(self, text: str = "", **kwargs) -> dict:
        text = text.strip()
        corrected = text
        fixes = []
        for pattern, replacement, desc in self._RULES:
            new = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
            if new != corrected:
                fixes.append(f"• {desc}")
                corrected = new
        if corrected and corrected[-1] not in ".!?":
            corrected += "."
            fixes.append("• Added end punctuation")
        if corrected:
            corrected = corrected[0].upper() + corrected[1:]
        if not fixes:
            result = f"✅ **No issues found!**\n\n> {text}"
        else:
            result = (
                f"✏️ **Grammar Corrected**\n\n"
                f"**Original:** {text}\n\n"
                f"**Corrected:** {corrected}\n\n"
                f"**Changes:**\n" + "\n".join(fixes)
            )
        return {"success": True, "result": result, "corrected": corrected}


# ── 6. Resume Bullet Generator ────────────────────────────────────────────────

@register_tool(
    name="resume",
    display_name="📝 Resume Bullets",
    category="utility_tools",
    description="Generate professional resume bullet points from a description",
    keywords=["resume", "cv", "bullet", "job", "career", "professional"],
    input_type="chat",
)
class ResumeBulletTool(BaseTool):
    _VERBS = [
        "Developed", "Built", "Designed", "Implemented", "Optimized",
        "Deployed", "Automated", "Integrated", "Led", "Delivered",
        "Architected", "Reduced", "Improved", "Increased", "Managed",
    ]
    _TECH_RE = re.compile(
        r"\b(Python|Java|React|Node|FastAPI|SQL|AWS|Docker|Kubernetes|"
        r"ML|AI|API|REST|GraphQL|TensorFlow|Streamlit|Pandas)\b",
        re.IGNORECASE,
    )

    def run(self, description: str = "", **kwargs) -> dict:
        import random
        random.seed(len(description))
        verbs = random.sample(self._VERBS, 5)
        techs = list(set(self._TECH_RE.findall(description)))
        tech_str = f" using {', '.join(techs[:3])}" if techs else ""
        words = description.split()
        short = " ".join(words[:6]) if len(words) > 6 else description
        bullets = [
            f"• {verbs[0]} {short.lower()}{tech_str}, improving productivity by 30%",
            f"• {verbs[1]} scalable solution for {short.lower()}, cutting effort by 40%",
            f"• {verbs[2]} and deployed {short.lower()}{tech_str} serving 500+ users",
            f"• {verbs[3]} automated pipeline for {short.lower()}, saving 50% processing time",
            f"• {verbs[4]} cross-functional team to deliver {short.lower()} on schedule",
        ]
        return {
            "success": True,
            "result": "📝 **Resume Bullets**\n\n" + "\n".join(bullets)
                      + "\n\n💡 *Adjust metrics to match your actual impact.*",
        }