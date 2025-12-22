"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

from . import storage
from . import config
from .council import run_full_council, generate_conversation_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings
from .export import export_to_markdown, export_to_json, export_to_html
from .pricing import estimate_query_cost, format_cost

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


class ConfigUpdateRequest(BaseModel):
    """Request to update council configuration."""
    council_models: List[str]
    chairman_model: str


class CostEstimateRequest(BaseModel):
    """Request to estimate cost of a query."""
    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/config")
async def get_config():
    """Get current council configuration."""
    return {
        "council_models": config.COUNCIL_MODELS,
        "chairman_model": config.CHAIRMAN_MODEL
    }


@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """Update council configuration."""
    # Update the runtime configuration
    config.COUNCIL_MODELS = request.council_models
    config.CHAIRMAN_MODEL = request.chairman_model

    return {
        "status": "success",
        "council_models": config.COUNCIL_MODELS,
        "chairman_model": config.CHAIRMAN_MODEL
    }


@app.post("/api/estimate-cost")
async def estimate_cost(request: CostEstimateRequest):
    """
    Estimate the cost of running a query through the council.

    Args:
        request: Request with message content

    Returns:
        Cost estimate breakdown
    """
    # Get current council models - Stage 1 + Stage 2 + Stage 3
    all_models = config.COUNCIL_MODELS + config.COUNCIL_MODELS + [config.CHAIRMAN_MODEL]

    estimate = estimate_query_cost(
        all_models,
        request.content,
        estimated_response_tokens=500  # Conservative estimate
    )

    return {
        "estimated_cost": estimate["total"],
        "formatted_cost": format_cost(estimate["total"]),
        "prompt_tokens": estimate["prompt_tokens"],
        "estimated_response_tokens": estimate["estimated_response_tokens"],
        "breakdown": {
            "stage1_cost": sum(estimate["models"].get(m, 0) for m in config.COUNCIL_MODELS),
            "stage2_cost": sum(estimate["models"].get(m, 0) for m in config.COUNCIL_MODELS),
            "stage3_cost": estimate["models"].get(config.CHAIRMAN_MODEL, 0)
        }
    }


@app.get("/api/models")
async def get_available_models():
    """
    Get list of popular OpenRouter models.
    In a production app, this would query OpenRouter's API.
    For now, we return a curated list of popular models.
    """
    models = [
        {
            "id": "openai/gpt-5.2",
            "name": "GPT-5.2",
            "provider": "OpenAI",
            "description": "Most capable GPT model"
        },
        {
            "id": "anthropic/claude-sonnet-4.5",
            "name": "Claude Sonnet 4.5",
            "provider": "Anthropic",
            "description": "Balanced performance and speed"
        },
        {
            "id": "anthropic/claude-opus-4.5",
            "name": "Claude Opus 4.5",
            "provider": "Anthropic",
            "description": "Most capable Claude model"
        },
        {
            "id": "google/gemini-3-pro-preview",
            "name": "Gemini 3 Pro",
            "provider": "Google",
            "description": "Advanced multimodal model"
        },
        {
            "id": "google/gemini-3-flash-preview",
            "name": "Gemini 3 Flash",
            "provider": "Google",
            "description": "Fast and efficient preview model"
        },
        {
            "id": "x-ai/grok-4.1-fast",
            "name": "Grok 4.1 Fast",
            "provider": "xAI",
            "description": "Fast Grok model"
        },
        {
            "id": "x-ai/grok-4",
            "name": "Grok 4",
            "provider": "xAI",
            "description": "Standard Grok model"
        },
        {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1",
            "provider": "DeepSeek",
            "description": "Reasoning model with thinking process"
        },
        {
            "id": "nex-agi/deepseek-v3.1-nex-n1:free",
            "name": "DeepSeek V3.1 Nex-N1 (Free)",
            "provider": "Nex-AGI",
            "description": "Free enhanced DeepSeek model"
        }
    ]

    return {"models": models}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.get("/api/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = "markdown"):
    """
    Export a conversation in various formats.

    Args:
        conversation_id: The conversation ID
        format: Export format (markdown, json, html)

    Returns:
        File download with appropriate content type
    """
    from fastapi.responses import Response

    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Sanitize title for filename
    title = conversation.get('title', 'conversation')
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    safe_title = safe_title.replace(' ', '_')[:50]  # Limit length

    if format == "markdown" or format == "md":
        content = export_to_markdown(conversation)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.md"'
            }
        )

    elif format == "json":
        content = export_to_json(conversation, pretty=True)
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.json"'
            }
        )

    elif format == "html":
        content = export_to_html(conversation)
        return Response(
            content=content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.html"'
            }
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'markdown', 'json', or 'html'.")


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result,
        metadata
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            metadata = {
                "label_to_model": label_to_model,
                "aggregate_rankings": aggregate_rankings
            }

            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result,
                metadata
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
