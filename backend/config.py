"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-4o",
    "google/gemini-flash-1.5",
    "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3.1-70b-instruct",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "openai/gpt-4o"

# Default council mode
DEFAULT_MODE = "standard"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
