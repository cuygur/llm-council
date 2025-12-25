import asyncio
import os
from dotenv import load_dotenv
from backend.openrouter import query_model

async def test():
    load_dotenv()
    model = "google/gemini-3-flash-preview"
    print(f"Testing model: {model}")
    response = await query_model(model, [{"role": "user", "content": "Hello"}])
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test())