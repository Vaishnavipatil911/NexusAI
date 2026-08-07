from fastapi import FastAPI, UploadFile, File, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import re
import hashlib
import requests
import pandas as pd
from io import BytesIO, StringIO

from groq import Groq

from core.tool_registry import get_registered_tools

app = FastAPI(title="AI Tool Hub MCP Server")

tools = get_registered_tools()

class WeatherRequest(BaseModel):
    city: str

class CodeRequest(BaseModel):
    prompt: str

class MathRequest(BaseModel):
    expression: str

class GrammarRequest(BaseModel):
    text: str

class SummarizerRequest(BaseModel):
    text: str

class ResumeRequest(BaseModel):
    description: str

@app.get("/")
def root():
    return {"status": "ok", "message": "MCP Server running"}

@app.get("/logs")
def logs(limit: int = 20):
    return []

@app.post("/tools/code_gen")
def code_gen(payload: CodeRequest):
    tool = tools.get("code")
    if not tool:
        return {"success": False, "result": "❌ Code tool not registered", "error": "tool_missing"}

    return tool.run(prompt=payload.prompt)

@app.post("/tools/get_weather")
def get_weather(payload: WeatherRequest):
    return {"success": False, "result": "Weather tool not implemented in this file"}

@app.post("/tools/math_solver")
def math_solver(payload: MathRequest):
    try:
        result = eval(payload.expression, {"__builtins__": {}}, {})
        return {"success": True, "result": f"✅ Result: {result}"}
    except Exception as e:
        return {"success": False, "result": f"❌ Error: {str(e)}", "error": str(e)}

@app.post("/tools/grammar_fix")
def grammar_fix(payload: GrammarRequest):
    return {"success": True, "result": payload.text}

@app.post("/tools/summarizer")
def summarizer(payload: SummarizerRequest):
    return {"success": True, "result": payload.text[:500]}

@app.post("/tools/resume_bullets")
def resume_bullets(payload: ResumeRequest):
    return {"success": True, "result": f"• {payload.description}"}

@app.post("/tools/hash_gen")
def hash_gen(text: str = Body(...), algorithm: str = Body("sha256")):
    algo = algorithm.lower()
    data = text.encode("utf-8")

    if algo == "sha256":
        digest = hashlib.sha256(data).hexdigest()
    elif algo == "sha512":
        digest = hashlib.sha512(data).hexdigest()
    elif algo == "md5":
        digest = hashlib.md5(data).hexdigest()
    elif algo == "sha1":
        digest = hashlib.sha1(data).hexdigest()
    elif algo == "sha224":
        digest = hashlib.sha224(data).hexdigest()
    elif algo == "sha384":
        digest = hashlib.sha384(data).hexdigest()
    else:
        return {"success": False, "result": "❌ Unsupported algorithm", "error": "bad_algorithm"}

    return {"success": True, "result": f"🔐 `{digest}`"}

@app.post("/tools/password_check")
def password_check(payload: Dict[str, Any] = Body(...)):
    pwd = payload.get("password", "")
    score = min(len(pwd) * 10, 100)
    return {"success": True, "result": f"Password score: {score}/100", "score": score}

@app.post("/tools/api_tester")
def api_tester(payload: Dict[str, Any] = Body(...)):
    return {"success": True, "result": f"API tester received: {payload.get('url', '')}"}

@app.post("/tools/csv_analyze")
async def csv_analyze(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_csv(StringIO(content.decode("utf-8")))
    return {"success": True, "result": f"Rows: {len(df)}, Columns: {len(df.columns)}"}