"""Model pricing and cost calculation utilities."""

from typing import Dict, Optional

# OpenRouter pricing (per million tokens) as of 2025
# Updated pricing - check https://openrouter.ai/models for latest
MODEL_PRICING = {
    "openai/gpt-5.2": {
        "prompt": 10.00,  # $10 per 1M input tokens
        "completion": 30.00,  # $30 per 1M output tokens
    },
    "anthropic/claude-sonnet-4.5": {
        "prompt": 3.00,
        "completion": 15.00,
    },
    "anthropic/claude-opus-4.5": {
        "prompt": 15.00,
        "completion": 75.00,
    },
    "google/gemini-3-pro-preview": {
        "prompt": 3.50,
        "completion": 10.50,
    },
    "google/gemini-3-flash-preview": {
        "prompt": 0.15,
        "completion": 0.60,
    },
    "x-ai/grok-4.1-fast": {
        "prompt": 0.50,
        "completion": 1.50,
    },
    "x-ai/grok-4": {
        "prompt": 5.00,
        "completion": 15.00,
    },
    "deepseek/deepseek-r1": {
        "prompt": 0.55,
        "completion": 2.19,
    },
    "nex-agi/deepseek-v3.1-nex-n1:free": {
        "prompt": 0.00,  # Free model
        "completion": 0.00,
    },
}

# Default pricing for unknown models
DEFAULT_PRICING = {
    "prompt": 1.00,
    "completion": 3.00,
}


def get_model_pricing(model_id: str) -> Dict[str, float]:
    """
    Get pricing for a specific model.

    Args:
        model_id: OpenRouter model identifier

    Returns:
        Dict with 'prompt' and 'completion' prices per million tokens
    """
    return MODEL_PRICING.get(model_id, DEFAULT_PRICING)


def calculate_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int
) -> float:
    """
    Calculate the cost for a specific API call.

    Args:
        model_id: OpenRouter model identifier
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Cost in USD (rounded to 6 decimal places)
    """
    pricing = get_model_pricing(model_id)

    # Calculate cost (pricing is per million tokens)
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]

    total_cost = prompt_cost + completion_cost

    return round(total_cost, 6)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    Rule of thumb: ~4 characters per token for English text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Simple estimation: 1 token ≈ 4 characters
    # More accurate would use tiktoken, but this is fast
    return len(text) // 4


def estimate_query_cost(
    model_ids: list,
    prompt_text: str,
    estimated_response_tokens: int = 500
) -> Dict[str, float]:
    """
    Estimate the cost of a query before sending it.

    Args:
        model_ids: List of model identifiers
        prompt_text: The user's prompt
        estimated_response_tokens: Expected response length (default 500)

    Returns:
        Dict with 'total', 'per_model', and 'models' breakdown
    """
    prompt_tokens = estimate_tokens(prompt_text)

    total_cost = 0.0
    model_costs = {}

    for model_id in model_ids:
        cost = calculate_cost(model_id, prompt_tokens, estimated_response_tokens)
        model_costs[model_id] = cost
        total_cost += cost

    return {
        "total": round(total_cost, 4),
        "prompt_tokens": prompt_tokens,
        "estimated_response_tokens": estimated_response_tokens,
        "models": model_costs
    }


def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0234" or "$1.23")
    """
    if cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def get_cost_category(cost: float) -> str:
    """
    Categorize cost for color-coding in UI.

    Args:
        cost: Cost in USD

    Returns:
        Category string: 'low', 'medium', 'high', 'very-high'
    """
    if cost < 0.10:
        return "low"
    elif cost < 0.50:
        return "medium"
    elif cost < 2.00:
        return "high"
    else:
        return "very-high"
