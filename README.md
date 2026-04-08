# 🛠️ AI Tool Hub

> A modular AI-powered productivity platform that executes tasks — it doesn't just talk about them.
## What is AI Tool Hub?

Most AI tools are chatbots — you describe a problem, they describe a solution. AI Tool Hub **actually executes the task**.

| You ask | A chatbot does | AI Tool Hub does |
|---|---|---|
| Analyze my CSV | Describes how to analyze it | Runs Pandas, returns real stats + charts |
| Fix my grammar | Suggests corrections | Corrects the text using an LLM |
| Generate Java code | Shows example code | Detects the language, generates working code |
| Test this API | Explains how to use curl | Sends the real HTTP request, shows the response |
| Summarize this document | Paraphrases it | Extracts key points with keywords via AI |

---

## Features

- **10 integrated tools** across 4 categories
- **AI-powered** — Groq (Llama 3.1) as primary LLM, Google Gemini as fallback
- **Intent Router** — automatically detects which tool to use from your query
- **Workflow Engine** — chain multiple tools together in a pipeline
- **Secure authentication** — bcrypt-hashed passwords, cookie-based sessions
- **Query logging** — every tool call logged to SQLite with timestamps
- **Analytics dashboard** — usage charts and query history
- **Modular plugin architecture** — add new tools without touching core code

---

## Tools

### 🔧 Utility Tools
| Tool | Description |
|---|---|
| 🌤️ Weather | Real-time weather for any city via OpenWeatherMap API |
| 🧮 Math Solver | Evaluates expressions — `sqrt(144)`, `sin(pi/2)`, `2**10` |
| 🔐 Hash Generator | SHA256, SHA512, MD5 and more |
| 🔒 Password Checker | Strength scoring with detailed feedback |
| ✏️ Grammar Fixer | AI-powered grammar and spelling correction |
| 📝 Resume Bullets | Generates 5 STAR-format resume bullet points via AI |

### 💻 Developer Tools
| Tool | Description |
|---|---|
| 💻 Code Generator | Generates code in **any language** using AI — Python, Java, JS, C++, SQL and more |
| 🌐 API Tester | Sends real HTTP requests and displays status, headers, response body |

### 📊 Data Tools
| Tool | Description |
|---|---|
| 📊 CSV Analyzer | Pandas-powered statistics — shape, column types, missing values, distributions |

### 🤖 AI Tools
| Tool | Description |
|---|---|
| 📄 Doc Summarizer | AI-powered summarization with overview, key bullets, and keywords |

---

## Architecture

```
User
 │
 ▼
Streamlit UI (app.py)
 │
 ├─► Intent Router  ──► auto-detects tool from natural language query
 │
 ▼
MCP Server (FastAPI — mcp/mcp_server.py)
 │
 ▼
Tool Registry  ──► @register_tool decorator — new tools plug in automatically
 │
 ├── Utility Tools    (weather, math, hash, password, grammar, resume)
 ├── Developer Tools  (code gen, API tester)
 ├── Data Tools       (CSV analyzer, chart generator)
 └── AI Tools         (document summarizer)
 │
 ▼
Workflow Engine  ──► chains tools sequentially, pipes output between steps
 │
 ▼
LLM Service  ──► Groq → Gemini → Together AI → Ollama (auto-fallback chain)
 │
 ▼
Result returned to UI + logged to SQLite
```

### Project Structure

```
AI_Tool_Hub/
│
├── app.py                          # Streamlit frontend
├── config.yaml                     # Auth credentials (never commit)
├── hash_gen.py                     # Password hash generator utility
├── requirements.txt
├── .env                            # API keys (never commit)
│
├── core/
│   ├── tool_registry.py            # @register_tool decorator + BaseTool
│   ├── intent_router.py            # Natural language → tool name
│   └── workflow_engine.py          # Multi-step pipeline execution
│
├── mcp/
│   └── mcp_server.py               # FastAPI orchestration layer
│
├── tools/
│   ├── utility_tools/
│   │   └── weather_tool.py         # Weather, Math, Hash, Password, Grammar, Resume
│   ├── developer_tools/
│   │   └── code_generator.py       # Code Gen + API Tester
│   ├── data_tools/
│   │   └── csv_analyzer.py         # CSV + Chart Generator
│   └── ai_tools/
│       └── document_summarizer.py  # Doc Summarizer
│
├── services/
│   ├── llm_service.py              # Groq / Gemini / Together / Ollama
│   └── api_service.py              # Shared HTTP client
│
├── utils/
│   ├── text_processing.py          # City extraction, math cleaning, etc.
│   └── file_handler.py             # File reading utilities
│
└── dashboards/
    └── analytics.py                # Usage analytics dashboard
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-tool-hub.git
cd ai-tool-hub
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install groq   # free LLM — get key at groq.com
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
# LLM — get free key at groq.com (no card needed)
GROQ_API_KEY=gsk_your_key_here

# Weather — get free key at openweathermap.org
OPENWEATHER_API_KEY=your_key_here

# Optional fallback LLMs
# GEMINI_API_KEY=your_key_here
# TOGETHER_API_KEY=your_key_here
```

### 5. Set up authentication

Generate a bcrypt hash for your password:

```bash
python hash_gen.py
```

Edit `config.yaml`:

```yaml
credentials:
  usernames:
    your_username:
      name: Your Name
      password: "$2b$12$..."   # paste hash here

cookie:
  name: ai_tool_hub_session
  key: "your_long_random_secret_key"
  expiry_days: 30
```

### 6. Run the application

**Terminal 1 — Start the MCP server** (from project root):

```bash
uvicorn mcp.mcp_server:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Start Streamlit** (from project root):

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## LLM Provider Setup

The platform uses a **free LLM fallback chain** — no paid API required.

| Provider | Free Tier | Speed | Setup |
|---|---|---|---|
| **Groq** ⭐ | 14,400 req/day | Extremely fast | [groq.com](https://groq.com) |
| Google Gemini | 1,500 req/day | Fast | [aistudio.google.com](https://aistudio.google.com) |
| Together AI | $5 free credit | Fast | [together.ai](https://together.ai) |
| Ollama | Unlimited (local) | Depends on hardware | [ollama.com](https://ollama.com) |

Add the key for whichever provider you want to `.env` — the platform auto-detects and uses the first available one.

---

## Adding a New Tool

New tools register themselves with a single decorator — no changes needed to any other file:

```python
# tools/my_category/my_tool.py

from core.tool_registry import BaseTool, register_tool

@register_tool(
    name="my_tool",
    display_name="🔧 My Tool",
    category="utility_tools",
    description="Does something useful",
    keywords=["keyword1", "keyword2"],
    input_type="chat",   # "chat" | "form" | "file"
)
class MyTool(BaseTool):
    def run(self, text: str = "", **kwargs) -> dict:
        result = f"Processed: {text}"
        return {"success": True, "result": result}
```

Then import it in `mcp/mcp_server.py`:

```python
import tools.my_category.my_tool  # registers on import
```

That's it — the tool appears in the UI, Intent Router, and Workflow Engine automatically.

---

## Workflow Engine

Chain tools together for multi-step pipelines:

```python
# Example: Grammar fix → Resume bullets
steps = [
    {"tool": "grammar",  "params": {}},
    {"tool": "resume",   "params": {}},
]
POST /workflow  {"steps": steps, "initial_params": {"text": "built a fastapi service"}}
```

Built-in workflow templates available in the UI:
- **Summarize text** — Grammar fix → Summarize
- **Code + Hash** — Generate code → Hash the output
- **Grammar + Resume** — Fix grammar → Generate bullets

---

## API Reference

The MCP server exposes a REST API at `http://127.0.0.1:8000`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check + tool list |
| `GET` | `/tools` | Full tool registry with metadata |
| `POST` | `/route` | Intent-route a query → best tool name |
| `POST` | `/run/{tool_name}` | Execute a tool with params |
| `POST` | `/run/csv/upload` | Upload and analyze a CSV file |
| `POST` | `/workflow` | Execute a multi-step workflow |
| `GET` | `/logs` | Recent query log |

### Example: Run a tool

```bash
curl -X POST http://127.0.0.1:8000/run/grammar \
  -H "Content-Type: application/json" \
  -d '{"params": {"text": "i dont know if its correct"}}'
```

### Example: Auto-route a query

```bash
curl -X POST http://127.0.0.1:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "what is the weather in Tokyo"}'
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| LLM Integration | Groq (Llama 3.1), Google Gemini |
| Data Processing | Pandas, Plotly |
| Authentication | streamlit-authenticator, bcrypt |
| Database | SQLite (query logging) |
| HTTP Client | httpx |
| Config | python-dotenv, PyYAML |

---

## Roadmap

- [ ] PDF Analyzer — upload PDF, get structured insights via LLM
- [ ] AI Code Reviewer — paste code, get bugs + improved version with diff
- [ ] Web Scraper + Summarizer — paste URL, get AI summary
- [ ] SQL Query Generator — natural language → SQL + execute on uploaded DB
- [ ] Image Analyzer — upload image, get description + extracted text (vision API)
- [ ] Unit tests (`tests/` folder with pytest)
- [ ] Docker deployment
- [ ] Live deployment on Railway / Render

---

## Security Notes

- Passwords are stored as **bcrypt hashes** — never plain text
- `.env` and `config.yaml` are in `.gitignore` — never commit these
- The MCP server runs locally — not exposed to the internet by default
- Math solver uses a sandboxed `eval()` with no builtins

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-tool`
3. Add your tool following the pattern in [Adding a New Tool](#adding-a-new-tool)
4. Commit: `git commit -m "Add: MyTool — does X"`
5. Push and open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with Python · FastAPI · Streamlit · Groq
</div>
