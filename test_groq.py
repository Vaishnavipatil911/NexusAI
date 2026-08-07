import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say only: Groq works"}],
)

print(resp.choices[0].message.content)