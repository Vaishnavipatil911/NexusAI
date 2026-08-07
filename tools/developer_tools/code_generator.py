"""Code Generator Tool - Using Groq API"""

from __future__ import annotations
import os
import re
from groq import Groq

from core.tool_registry import BaseTool, register_tool


@register_tool(
    name="code",
    display_name="💻 Code Generator",
    category="developer_tools",
    description="Generate code using Groq",
    keywords=["code", "generate", "java", "python", "javascript"],
    input_type="chat",
)
class CodeGeneratorTool(BaseTool):

    def run(self, prompt: str = "", **kwargs) -> dict:
        print(f"[CODE_GEN] Tool called with prompt: {prompt[:100]}...")

        api_key = os.getenv("GROQ_API_KEY")
        print(f"[CODE_GEN] GROQ_API_KEY found: {'YES' if api_key else 'NO'}")

        if not api_key:
            return {
                "success": False,
                "result": "❌ Error: GROQ_API_KEY not found in environment variables",
                "error": "Missing API key"
            }

        try:
            client = Groq(api_key=api_key)

            system_prompt = """You are a code generation expert. Generate a complete Python function named EXACTLY "solution" that solves the user's request.

CRITICAL RULES (FOLLOW EXACTLY):
1. Function signature: def solution(): (NO parameters)
2. Put ALL imports at the TOP of the code
3. Implement COMPLETE working solution inside solution()
4. Use real APIs/services if needed
5. Print results or return dict/json
6. NO explanations, markdown, comments, or text outside the function

Request: {prompt}

Return ONLY: imports + def solution(): + code inside"""

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt.format(prompt=prompt)},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_completion_tokens=3000,
            )

            generated_code = chat_completion.choices[0].message.content.strip()
            language = self._detect_language(prompt, generated_code)
            cleaned_code = self._clean_code_response(generated_code)

            return {
                "success": True,
                "result": f"💻 **Generated {language.upper()} Code**\n\n```{language}\n{cleaned_code}\n```\n\n✅ Ready to copy-paste into your AI Tool Hub!",
                "code": cleaned_code,
                "language": language,
                "model": "llama-3.3-70b-versatile"
            }

        except Exception as e:
            print(f"[CODE_GEN] Error: {str(e)}")
            return {
                "success": False,
                "result": f"❌ Error: {str(e)}\n\nDebug: Check GROQ_API_KEY, quotas, internet",
                "error": str(e)
            }

    def _detect_language(self, prompt: str, code: str) -> str:
        """Detect programming language"""
        prompt_lower = prompt.lower()

        lang_map = {
            "java": "java",
            "python": "python",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "c++": "cpp",
            "cpp": "cpp",
            "c#": "csharp",
            "csharp": "csharp",
            "go": "go",
            "golang": "go",
            "rust": "rust",
            "ruby": "ruby",
            "php": "php",
            "html": "html",
            "css": "css",
        }

        for keyword, lang in lang_map.items():
            if keyword in prompt_lower:
                return lang

        if "public class" in code or "System.out" in code:
            return "java"
        elif "def " in code:
            return "python"
        elif "function " in code or "const " in code:
            return "javascript"

        return "python"

    def _clean_code_response(self, response: str) -> str:
        """Extract clean code from response"""
        response = re.sub(r'^```python\s*\n?', '', response, flags=re.MULTILINE)
        response = re.sub(r'```.*$', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*\n?', '', response, flags=re.MULTILINE)

        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches.strip()

        return response.strip()