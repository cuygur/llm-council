"""Utilities for handling reasoning models (o1, o3, DeepSeek-R1, etc.)."""

import re
from typing import Dict, Tuple, Optional

# Models that use extended reasoning with <think> tags or similar
REASONING_MODELS = {
    "openai/o1",
    "openai/o1-preview",
    "openai/o1-mini",
    "openai/o3",
    "openai/o3-mini",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-reasoner",
    "nex-agi/deepseek-v3.1-nex-n1:free",
}

# Extended timeout for reasoning models (in seconds)
REASONING_TIMEOUT = 300.0  # 5 minutes
STANDARD_TIMEOUT = 120.0   # 2 minutes


def is_reasoning_model(model_id: str) -> bool:
    """
    Check if a model is a reasoning model.

    Args:
        model_id: OpenRouter model identifier

    Returns:
        True if the model uses extended reasoning
    """
    # Check exact match
    if model_id in REASONING_MODELS:
        return True

    # Check partial matches (for versioned models)
    model_lower = model_id.lower()
    reasoning_keywords = ['o1', 'o3', 'deepseek-r', 'reasoner', 'reasoning']

    return any(keyword in model_lower for keyword in reasoning_keywords)


def get_model_timeout(model_id: str) -> float:
    """
    Get appropriate timeout for a model.

    Args:
        model_id: OpenRouter model identifier

    Returns:
        Timeout in seconds
    """
    return REASONING_TIMEOUT if is_reasoning_model(model_id) else STANDARD_TIMEOUT


def parse_reasoning_response(content: str) -> Dict[str, str]:
    """
    Parse reasoning model response to extract thinking process and final answer.

    Reasoning models often output in formats like:
    - <think>reasoning here</think>answer
    - <reasoning>thinking</reasoning>answer
    - Or just extended thought process followed by answer

    Args:
        content: Raw response content

    Returns:
        Dict with 'thinking' and 'answer' keys
    """
    if not content:
        return {"thinking": "", "answer": ""}

    # Try to extract <think> tags (DeepSeek-R1 style)
    think_match = re.search(r'<think>(.*?)</think>(.*)', content, re.DOTALL)
    if think_match:
        return {
            "thinking": think_match.group(1).strip(),
            "answer": think_match.group(2).strip()
        }

    # Try to extract <reasoning> tags
    reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>(.*)', content, re.DOTALL)
    if reasoning_match:
        return {
            "thinking": reasoning_match.group(1).strip(),
            "answer": reasoning_match.group(2).strip()
        }

    # Try to extract <thought> tags
    thought_match = re.search(r'<thought>(.*?)</thought>(.*)', content, re.DOTALL)
    if thought_match:
        return {
            "thinking": thought_match.group(1).strip(),
            "answer": thought_match.group(2).strip()
        }

    # If no tags found, return full content as answer
    return {
        "thinking": "",
        "answer": content
    }


def format_prompt_for_reasoning_model(user_query: str) -> str:
    """
    Format a prompt appropriately for reasoning models.

    Reasoning models (especially OpenAI o1/o3) don't support system messages
    and work best with direct, clear user prompts.

    Args:
        user_query: The user's question

    Returns:
        Formatted prompt
    """
    # Reasoning models work best with direct prompts
    # No need to add extra instructions, they reason internally
    return user_query


def should_show_thinking(model_id: str, thinking: str) -> bool:
    """
    Determine if thinking process should be displayed in UI.

    Args:
        model_id: Model identifier
        thinking: Extracted thinking content

    Returns:
        True if thinking should be shown
    """
    # Show thinking if:
    # 1. Model is a reasoning model
    # 2. Thinking content exists and is substantial (>50 chars)
    return is_reasoning_model(model_id) and len(thinking) > 50


def format_thinking_for_display(thinking: str) -> str:
    """
    Format thinking content for better readability in UI.

    Args:
        thinking: Raw thinking content

    Returns:
        Formatted thinking
    """
    if not thinking:
        return ""

    # Clean up extra whitespace
    thinking = re.sub(r'\n\s*\n\s*\n+', '\n\n', thinking)

    # Add structure if it's a long block of text
    lines = thinking.split('\n')

    # If it's very long, add some structure
    if len(lines) > 10:
        # Try to identify step markers
        thinking = re.sub(
            r'(Step \d+|First|Second|Third|Finally|Therefore|Thus|In conclusion)',
            r'\n\n**\1**',
            thinking,
            flags=re.IGNORECASE
        )

    return thinking.strip()


def get_reasoning_model_config(model_id: str) -> Dict[str, any]:
    """
    Get special configuration for reasoning models.

    Args:
        model_id: Model identifier

    Returns:
        Dict with configuration options
    """
    if not is_reasoning_model(model_id):
        return {
            "timeout": STANDARD_TIMEOUT,
            "supports_system_message": True,
            "requires_thinking_extraction": False
        }

    return {
        "timeout": REASONING_TIMEOUT,
        "supports_system_message": False,  # o1/o3 don't support system messages
        "requires_thinking_extraction": True,
        "show_thinking_ui": True
    }
