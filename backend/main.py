"""FastAPI backend for LLM Council."""

import logging
import re
import uuid
import json
import asyncio
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from . import storage
from . import config
from .openrouter import fetch_available_models
from .council import (
    run_full_council, 
    generate_conversation_title, 
    stage1_collect_responses, 
    stage2_collect_rankings, 
    stage2_5_rebuttal, 
    stage3_synthesize_final, 
    calculate_aggregate_rankings, 
    check_clarification_needs, 
    get_council_config
)
from .export import export_to_markdown, export_to_json, export_to_html
from .pricing import estimate_query_cost, format_cost

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def sanitize_attachment_name(name: str, max_length: int = 100) -> str:
    """
    Sanitize attachment filename to prevent injection attacks.
    
    Args:
        name: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    # Remove any markdown formatting characters that could break formatting
    sanitized = re.sub(r'[`*_\[\]()#]', '', name)
    # Remove newlines and control characters
    sanitized = re.sub(r'[\n\r\x00-\x1f]', '', sanitized)
    # Truncate to max length
    return sanitized[:max_length] if len(sanitized) > max_length else sanitized


def sanitize_attachment_content(content: str, max_length: int = 100000) -> str:
    """
    Sanitize attachment content to prevent injection attacks.
    
    Args:
        content: Original file content
        max_length: Maximum allowed length (default 100KB)
        
    Returns:
        Sanitized content
    """
    # Escape backticks to prevent breaking out of code blocks
    sanitized = content.replace('```', '\\`\\`\\`')
    # Truncate to prevent memory issues
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "\n[Content truncated due to size limit]"
    return sanitized


def process_attachments(content: str, attachments: Optional[List[Dict[str, str]]]) -> str:
    """
    Process and append attachment content to the message.
    
    Args:
        content: Original message content
        attachments: List of attachment dicts with 'name' and 'content'
        
    Returns:
        Content with sanitized attachments appended
    """
    if not attachments:
        return content
    
    full_content = content
    for attachment in attachments:
        name = sanitize_attachment_name(attachment.get("name", "Unknown File"))
        file_content = sanitize_attachment_content(attachment.get("content", ""))
        full_content += f"\n\n---\n**Attached File:** {name}\n\n```\n{file_content}\n```\n---"
    
    return full_content


def is_clarification_response(messages: List[Dict]) -> bool:
    """
    Determine if the latest user message is a response to a clarification request.
    
    The pattern we're looking for is:
    [..., user_msg, assistant_clarification, user_response]
    where the second-to-last message is an assistant message with 'clarification' key.
    
    Args:
        messages: Full conversation message list
        
    Returns:
        True if this appears to be a response to a clarification
    """
    if len(messages) < 2:
        return False
    
    # The second-to-last message should be the assistant's clarification
    # (the last message is the current user message)
    second_to_last = messages[-2]
    
    return (
        second_to_last is not None 
        and second_to_last.get('role') == 'assistant'
        and 'clarification' in second_to_last
    )


# ============================================================================
# Pydantic Schemas
# ============================================================================

from .schemas import (
    CreateConversationRequest, 
    SendMessageRequest, 
    ConfigUpdateRequest, 
    CostEstimateRequest, 
    ConversationMetadata, 
    Conversation
)

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler that sanitizes error responses."""
    # Log full details server-side for debugging
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=True
    )
    
    # Return sanitized message to client (never expose internal details)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later."
        },
    )




@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/config")
async def get_config():
    """Get current council configuration."""
    return {
        "council_models": config.COUNCIL_MODELS,
        "chairman_model": config.CHAIRMAN_MODEL,
        "mode": config.DEFAULT_MODE
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
    # Default to global config
    council_models = config.COUNCIL_MODELS
    chairman_model = config.CHAIRMAN_MODEL

    # Override if conversation_id is provided
    if request.conversation_id:
        conversation = storage.get_conversation(request.conversation_id)
        if conversation:
            council_models = conversation.get("council_models", council_models)
            chairman_model = conversation.get("chairman_model", chairman_model)

    # Get current council models - Stage 1 + Stage 2 + Stage 3
    # Note: Stage 2 and 3 actually have much larger prompts, but this provides a baseline
    all_models = council_models + council_models + [chairman_model]

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
            "stage1_cost": sum(estimate["models"].get(m, 0) for m in council_models),
            "stage2_cost": sum(estimate["models"].get(m, 0) for m in council_models),
            "stage3_cost": estimate["models"].get(chairman_model, 0)
        }
    }


@app.get("/api/models")
async def get_available_models():
    """
    Get list of available models.
    Fetches from OpenRouter API, falling back to curated list on error.
    """
    # Try fetching from OpenRouter
    models = await fetch_available_models()
    
    if models:
        return {"models": models}

    # Fallback list if API fails
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
            "id": "anthropic/claude-3-opus",
            "name": "Claude 3 Opus",
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
        },
        {
            "id": "google/gemini-2.0-flash-exp:free",
            "name": "Gemini 2.0 Flash Exp (Free)",
            "provider": "Google",
            "description": "Free experimental Gemini model"
        },
        {
            "id": "meta-llama/llama-3.3-70b-instruct:free",
            "name": "Llama 3.3 70B (Free)",
            "provider": "Meta",
            "description": "Free open source Llama model"
        },
        {
            "id": "qwen/qwen-2.5-72b-instruct:free",
            "name": "Qwen 2.5 72B (Free)",
            "provider": "Qwen",
            "description": "Free open source Qwen model"
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
    conversation = storage.create_conversation(
        conversation_id,
        council_models=request.council_models,
        chairman_model=request.chairman_model,
        model_personas=request.model_personas,
        mode=request.mode
    )
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": "Conversation deleted"}


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

    # Process attachments with sanitization (SEC-002)
    full_content = process_attachments(request.content, request.attachments)

    # Add user message
    storage.add_user_message(conversation_id, full_content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    # Re-fetch conversation to get full history including the new user message
    updated_conversation = storage.get_conversation(conversation_id)
    
    council_models, chairman_model, model_personas = await get_council_config(
        updated_conversation, 
        request.content
    )

    # Check for clarification needs using improved detection (BUG-002)
    is_clarification_answer = is_clarification_response(updated_conversation["messages"])
    
    if not is_clarification_answer:
        questions = await check_clarification_needs(request.content)
        if questions:
            # Add assistant message with clarification only
            storage.add_assistant_message(
                conversation_id,
                clarification=questions
            )
            return {
                "clarification": questions,
                "stage1": None,
                "stage2": None,
                "stage3": None,
                "metadata": {}
            }
    
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        updated_conversation["messages"],
        council_models,
        chairman_model,
        model_personas
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1=stage1_results,
        stage2=stage2_results,
        stage3=stage3_result,
        metadata=metadata
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
            # Process attachments with sanitization (SEC-002)
            full_content = process_attachments(request.content, request.attachments)

            # Add user message
            storage.add_user_message(conversation_id, full_content)
            
            # Re-fetch conversation to get full history
            updated_conversation = storage.get_conversation(conversation_id)
            messages = updated_conversation["messages"]
            
            from .council import get_council_config
            # Send persona resolution event if needed
            if updated_conversation.get("mode") != "standard" and not updated_conversation.get("model_personas"):
                yield f"data: {json.dumps({'type': 'resolving_personas'})}\n\n"

            council_models, chairman_model, model_personas = await get_council_config(
                updated_conversation, 
                request.content
            )

            # Check for clarification needs using improved detection (BUG-002)
            is_clarification_answer = is_clarification_response(messages)
            
            should_check_clarification = not is_clarification_answer and len(request.content) < 2000

            if should_check_clarification:
                questions = await check_clarification_needs(request.content)
                if questions:
                    print(f"Sending clarification_needed event with {len(questions)} questions")
                    # Send clarification needed event
                    yield f"data: {json.dumps({'type': 'clarification_needed', 'data': {'questions': questions}})}\n\n"
                    
                    # Save clarification message
                    storage.add_assistant_message(
                        conversation_id,
                        stage1=None, stage2=None, stage3=None, # Explicitly None
                        clarification=questions
                    )
                    
                    yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                    return

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses (now uses full history)
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(messages, council_models, model_personas)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings (still focuses on latest response evaluation)
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results, council_models, model_personas)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 2.5: Rebuttal Round
            yield f"data: {json.dumps({'type': 'stage2_5_start'})}\n\n"
            stage2_5_results = await stage2_5_rebuttal(
                request.content,
                stage1_results,
                stage2_results,
                label_to_model,
                model_personas
            )
            # Re-emit stage1_complete with updated results so UI updates
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage2_5_results})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage2_5_results, stage2_results, chairman_model, model_personas)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            from .pricing import calculate_total_stats
            stats = calculate_total_stats(stage2_5_results, stage2_results, stage3_result)

            metadata = {
                "label_to_model": label_to_model,
                "aggregate_rankings": aggregate_rankings,
                "total_cost": stats["total_cost"],
                "total_tokens": stats["total_tokens"]
            }

            storage.add_assistant_message(
                conversation_id,
                stage1=stage1_results,
                stage2=stage2_results,
                stage3=stage3_result,
                metadata=metadata
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
