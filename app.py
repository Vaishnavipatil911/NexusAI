import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import httpx
import re

st.set_page_config(
    page_title="AI Tool Hub",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .tool-badge {
        display: inline-block;
        background: #1e3a5f;
        color: #7eb8f7;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .stChatMessage { border-radius: 12px; }
    div[data-testid="stSidebarContent"] { background: #0f1923; }
    section[data-testid="stSidebar"] .stSelectbox label { color: #aab4c0; }
</style>
""", unsafe_allow_html=True)

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

if not st.session_state.get("authentication_status"):
    with st.sidebar:
        tab1, tab2 = st.tabs(["Login", "Create Account"])

        with tab1:
            try:
                authenticator.login(location="main")
            except Exception as e:
                st.error(f"Auth setup error: {e}")

        with tab2:
            try:
                if authenticator.register_user(location='main'):
                    st.success('User registered successfully! You can now login.')
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
            except Exception as e:
                st.error(e)

if st.session_state.get("authentication_status") is not True:
    if st.session_state.get("authentication_status") is False:
        st.error("❌ Incorrect username or password.")
    elif st.session_state.get("authentication_status") is None:
        st.title("🛠️ AI Tool Hub")
        st.warning("⚠️ Please log in or create an account in the sidebar to continue.")
    st.stop()

MCP_SERVER_URL = "http://127.0.0.1:8000"

TOOLS = {
    "🌤️ Weather": {"key": "weather", "desc": "Real-time weather for any city"},
    "💻 Code Generator": {"key": "code", "desc": "Generate Python code snippets"},
    "🧮 Math Solver": {"key": "math", "desc": "Evaluate math expressions"},
    "🔐 Hash Generator": {"key": "hash", "desc": "Generate cryptographic hashes"},
    "✏️ Grammar Fixer": {"key": "grammar", "desc": "Fix grammar & punctuation"},
    "📄 Doc Summarizer": {"key": "summarizer", "desc": "Summarize long text to key points"},
    "📊 CSV Analyzer": {"key": "csv", "desc": "Analyze CSV files & show stats"},
    "🔒 Password Checker": {"key": "password", "desc": "Check password strength"},
    "🌐 API Tester": {"key": "api", "desc": "Test REST API endpoints"},
    "📝 Resume Bullets": {"key": "resume", "desc": "Generate resume bullet points"},
}

TOOL_HINTS = {
    "weather": "💡 Try: *What's the weather in Tokyo?* or just type a city name.",
    "code": "💡 Try: *Generate quicksort in Python* or *write a linked list class*.",
    "math": "💡 Try: `sqrt(144)`, `2**10`, `sin(pi/2)`, or `25 * 48`.",
    "hash": "💡 Enter text below. Choose your algorithm and click Generate Hash.",
    "grammar": "💡 Paste any text and it will be corrected automatically.",
    "summarizer": "💡 Paste a long article or document. Key points will be extracted.",
    "csv": "💡 Upload a CSV file to get statistics and column analysis.",
    "password": "💡 Enter a password below to check its strength.",
    "api": "💡 Enter a URL, choose a method, and optionally add headers/body.",
    "resume": "💡 Describe your project or role and get 5 professional bullet points.",
}

def _call_tool(tool_key: str, prompt: str) -> str:
    """Route a chat prompt to the correct MCP endpoint."""
    try:
        if tool_key == "weather":
            city_match = re.search(r'(?:in|for|at)\s+([A-Za-z\s]+?)(?:\?|!|\.|$)', prompt, re.IGNORECASE)
            city = city_match.group(1).strip() if city_match else prompt.strip()
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/get_weather", json={"city": city}, timeout=10)
            return resp.json().get("result", "Error")

        elif tool_key == "code":
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/code_gen", json={"prompt": prompt}, timeout=30)
            return resp.json().get("result", "Error")

        elif tool_key == "math":
            expr = re.sub(r'(what is|calculate|solve|compute|evaluate|=\?)', '', prompt, flags=re.IGNORECASE).strip()
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/math_solver", json={"expression": expr}, timeout=10)
            return resp.json().get("result", "Error")

        elif tool_key == "grammar":
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/grammar_fix", json={"text": prompt}, timeout=10)
            return resp.json().get("result", "Error")

        elif tool_key == "summarizer":
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/summarizer", json={"text": prompt}, timeout=15)
            return resp.json().get("result", "Error")

        elif tool_key == "resume":
            resp = httpx.post(f"{MCP_SERVER_URL}/tools/resume_bullets", json={"description": prompt}, timeout=10)
            return resp.json().get("result", "Error")

        else:
            return f"ℹ️ Use the dedicated input panel above for the **{tool_key}** tool."
    except Exception as e:
        return f"❌ Tool call failed: {str(e)}"

if st.session_state.get("authentication_status"):
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state['name']}")
        if st.button("Logout", use_container_width=True):
            authenticator.logout(location="sidebar")
            st.rerun()

        st.divider()
        st.markdown("### 🧰 Select Tool")
        selected_label = st.selectbox("Tool", list(TOOLS.keys()), label_visibility="collapsed")
        tool_key = TOOLS[selected_label]["key"]
        tool_desc = TOOLS[selected_label]["desc"]

        st.caption(tool_desc)
        st.divider()

        if tool_key == "hash":
            hash_algo = st.selectbox("Algorithm", ["SHA256", "SHA512", "MD5", "SHA1", "SHA224", "SHA384"])
        if tool_key == "api":
            api_method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
            api_headers = st.text_area("Headers (JSON)", height=80, placeholder='{"Authorization": "Bearer token"}')
            api_body = st.text_area("Request Body", height=80, placeholder='{"key": "value"}')

        st.divider()
        if st.button("📋 View Query Log", use_container_width=True):
            st.session_state.show_log = not st.session_state.get("show_log", False)

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    col_title, col_status = st.columns([4, 1])
    with col_title:
        st.title("🛠️ AI Tool Hub")
        st.markdown(f'<span class="tool-badge">{selected_label}</span>', unsafe_allow_html=True)
    with col_status:
        try:
            httpx.get(f"{MCP_SERVER_URL}/", timeout=2)
            st.success("MCP Online ✅")
        except Exception:
            st.error("MCP Offline ❌")

    if st.session_state.get("show_log", False):
        with st.expander("📋 Recent Query Log", expanded=True):
            try:
                log_resp = httpx.get(f"{MCP_SERVER_URL}/logs?limit=20", timeout=5)
                logs = log_resp.json()
                if logs:
                    st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
                else:
                    st.info("No queries logged yet.")
            except Exception:
                st.warning("Could not fetch logs — is the MCP server running?")

    st.divider()
    st.info(TOOL_HINTS.get(tool_key, "Ask anything!"))

    if tool_key == "hash":
        hash_input = st.text_area("Text to hash", height=100, placeholder="Enter any text…")
        if st.button("🔐 Generate Hash", type="primary"):
            if hash_input.strip():
                with st.spinner("Hashing…"):
                    resp = httpx.post(
                        f"{MCP_SERVER_URL}/tools/hash_gen",
                        json={"text": hash_input, "algorithm": hash_algo.lower()},
                        timeout=10,
                    )
                st.markdown(resp.json().get("result", "Error"))

    elif tool_key == "password":
        pwd_input = st.text_input("Password to check", type="password")
        if st.button("🔒 Analyze Password", type="primary"):
            if pwd_input:
                with st.spinner("Analyzing…"):
                    resp = httpx.post(
                        f"{MCP_SERVER_URL}/tools/password_check",
                        json={"password": pwd_input},
                        timeout=10,
                    )
                result_data = resp.json()
                st.markdown(result_data.get("result", "Error"))
                st.progress(result_data.get("score", 0) / 100)

    elif tool_key == "api":
        api_url = st.text_input("API URL", placeholder="https://api.example.com/data")
        if st.button("🌐 Send Request", type="primary"):
            if api_url.strip():
                import json as json_lib
                headers_dict = {}
                try:
                    headers_dict = json_lib.loads(api_headers) if api_headers.strip() else {}
                except Exception:
                    st.warning("Invalid JSON in headers — sending without headers.")
                with st.spinner(f"Sending {api_method}…"):
                    resp = httpx.post(
                        f"{MCP_SERVER_URL}/tools/api_tester",
                        json={"url": api_url, "method": api_method, "headers": headers_dict, "body": api_body or ""},
                        timeout=20,
                    )
                st.markdown(resp.json().get("result", "Error"))

    elif tool_key == "csv":
        uploaded = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded and st.button("📊 Analyze CSV", type="primary"):
            with st.spinner("Analyzing CSV…"):
                resp = httpx.post(
                    f"{MCP_SERVER_URL}/tools/csv_analyze",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    timeout=30,
                )
            result_data = resp.json()
            st.markdown(result_data.get("result", "Error"))

            uploaded.seek(0)
            df_preview = pd.read_csv(uploaded)
            with st.expander("📋 Data Preview (first 20 rows)"):
                st.dataframe(df_preview.head(20), use_container_width=True)

            numeric_cols = df_preview.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                with st.expander("📈 Numeric Column Distribution"):
                    chart_col = st.selectbox("Select column to chart", numeric_cols)
                    st.bar_chart(df_preview[chart_col].dropna())

    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input(f"Ask the {selected_label} tool…"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🔄 Processing…"):
                    try:
                        response_text = _call_tool(tool_key, prompt)
                    except httpx.ConnectError:
                        response_text = (
                            "❌ **MCP Server not running!**\n\n"
                            "Start it in a terminal:\n"
                            "```powershell\n"
                            "uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8000\n"
                            "```"
                        )
                    except Exception as e:
                        response_text = f"❌ Error: {str(e)}"
                st.markdown(response_text)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

        if st.session_state.get("messages"):
            _, col2 = st.columns([5, 1])
            with col2:
                df_export = pd.DataFrame(st.session_state.messages)
                st.download_button(
                    "📥 Export Chat",
                    data=df_export.to_csv(index=False).encode("utf-8"),
                    file_name="ai_tool_hub_chat.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

elif st.session_state.get("authentication_status") is False:
    st.error("❌ Incorrect username or password.")
    if st.button("🔄 Clear & Retry"):
        st.cache_data.clear()
        st.rerun()

else:
    st.title("🛠️ AI Tool Hub")
    st.warning("⚠️ Please log in using the sidebar to continue.")