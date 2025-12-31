"""Configuration for the LLM Council."""

import os
import warnings
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Validate API key is present
if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY environment variable is required. "
        "Please set it in your .env file or environment."
    )

# Optional: Warn if API key format looks unusual
if not OPENROUTER_API_KEY.startswith("sk-"):
    warnings.warn(
        "OPENROUTER_API_KEY doesn't match expected format (should start with 'sk-'). "
        "Ensure you're using a valid OpenRouter API key.",
        UserWarning
    )

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.2",
    "anthropic/claude-sonnet-4.5",
    "google/gemini-3-pro-preview",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# Default council mode
DEFAULT_MODE = "auto"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
