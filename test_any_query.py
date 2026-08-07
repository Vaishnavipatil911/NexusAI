import os
from groq import Groq

def test_groq(query: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY is missing")
        return

    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=200,
        )

        content = resp.choices[0].message.content
        print("✅ Got response:")
        print(content)

        if content and content.strip():
            print("✅ Model returned non-empty text")
        else:
            print("⚠️ Model response was empty")

    except Exception as e:
        print("❌ Error from Groq:")
        print(type(e).__name__, str(e))

test_groq("Say only:Groq works")

