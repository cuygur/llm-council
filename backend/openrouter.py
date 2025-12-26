"""OpenRouter API client for making LLM requests."""

import json
import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODELS_URL
from .reasoning import get_model_timeout, parse_reasoning_response, is_reasoning_model


async def fetch_available_models() -> List[Dict[str, str]]:
    """
    Fetch list of available models from OpenRouter.

    Returns:
        List of model dicts with id, name, provider, description
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPENROUTER_MODELS_URL)
            response.raise_for_status()
            
            data = response.json()
            models_data = data.get('data', [])
            
            formatted_models = []
            for model in models_data:
                # Derive provider from ID (e.g. "anthropic/claude" -> "Anthropic")
                model_id = model.get('id', '')
                provider = model_id.split('/')[0].capitalize() if '/' in model_id else 'Unknown'
                
                formatted_models.append({
                    "id": model_id,
                    "name": model.get('name', model_id),
                    "provider": provider,
                    "description": model.get('description', '')
                })
                
            # Sort by name
            formatted_models.sort(key=lambda x: x['name'])
            
            return formatted_models

    except httpx.HTTPError as e:
        print(f"HTTP error fetching models: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error fetching models: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching models: {e}")
        return []


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    # Use model-specific timeout if not provided
    if timeout is None:
        timeout = get_model_timeout(model)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            # Extract token usage
            usage = data.get('usage', {})

            # Get content
            content = message.get('content', '')

            # Parse reasoning if it's a reasoning model
            thinking = ""
            answer = content

            if is_reasoning_model(model):
                parsed = parse_reasoning_response(content)
                thinking = parsed['thinking']
                answer = parsed['answer']

            return {
                'content': answer,  # Final answer without thinking tags
                'thinking': thinking,  # Extracted thinking process
                'reasoning_details': message.get('reasoning_details'),
                'is_reasoning_model': is_reasoning_model(model),
                'usage': {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
            }

    except httpx.HTTPError as e:
        print(f"HTTP error querying model {model}: {e}")
        return {
            'error': f"HTTP Error: {str(e)}",
            'content': f"Error: {str(e)}",
            'thinking': "",
            'is_reasoning_model': is_reasoning_model(model),
            'usage': {}
        }
    except Exception as e:
        print(f"Unexpected error querying model {model}: {e}")
        return {
            'error': str(e),
            'content': f"Error: {str(e)}",
            'thinking': "",
            'is_reasoning_model': is_reasoning_model(model),
            'usage': {}
        }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
