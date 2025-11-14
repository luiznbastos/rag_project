"""
API request/response models.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str
    top_k: Optional[int] = 5
    use_reranking: Optional[bool] = True


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    query: str
    response: str
    sources: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    vector_service: bool
    database_service: bool


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: str


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""
    conversations: List[ConversationResponse]
    total: int


class MessageCreate(BaseModel):
    """Request model for creating a message."""
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None


class MessageResponse(BaseModel):
    """Response model for message data."""
    message_id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    """Response model for listing messages in a conversation."""
    conversation_id: str
    messages: List[MessageResponse]
    total: int

