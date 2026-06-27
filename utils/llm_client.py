import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

PRIMARY_MODEL  = "llama-3.3-70b-versatile"
NARRATOR_MODEL = "llama-3.3-70b-versatile"

def chat(messages: list, tools: list = None,
         tool_choice: str = "auto", use_narrator: bool = False) -> object:

    model = NARRATOR_MODEL if use_narrator else PRIMARY_MODEL

    kwargs = {
        "model":       model,
        "messages":    messages,
        "temperature": 0,
        "max_tokens":  1024,
    }
    if tools:
        kwargs["tools"]       = tools
        kwargs["tool_choice"] = tool_choice

    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err.lower():
                wait = 60 if attempt == 0 else 90
                print(f"⏳ Rate limit hit. Waiting {wait}s (retry {attempt+1}/3)...")
                time.sleep(wait)
            else:
                raise

    return client.chat.completions.create(**kwargs)