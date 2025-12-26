from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None
    model_personas: Optional[Dict[str, str]] = None
    mode: Optional[str] = "standard"


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    attachments: Optional[List[Dict[str, str]]] = None  # List of {name, content, type}


class ConfigUpdateRequest(BaseModel):
    """Request to update council configuration."""
    council_models: List[str]
    chairman_model: str


class CostEstimateRequest(BaseModel):
    """Request to estimate cost of a query."""
    content: str
    conversation_id: Optional[str] = None


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
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None
    model_personas: Optional[Dict[str, str]] = None
    mode: Optional[str] = "standard"
