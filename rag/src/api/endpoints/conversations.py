"""
Conversation API endpoints for managing chat conversations and messages.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Optional

try:
    from src.models.api import (
        ConversationCreate, ConversationResponse, ConversationListResponse,
        MessageCreate, MessageResponse, ConversationMessagesResponse
    )
    from src.services.conversation_service import ConversationService
    from src.core.dependencies import get_conversation_service
except ImportError:
    from models.api import (
        ConversationCreate, ConversationResponse, ConversationListResponse,
        MessageCreate, MessageResponse, ConversationMessagesResponse
    )
    from services.conversation_service import ConversationService
    from core.dependencies import get_conversation_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Create a new conversation."""
    try:
        return await conversation_service.create_conversation(conversation_data)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: Optional[int] = 50,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get list of conversations."""
    try:
        return await conversation_service.list_conversations(limit=limit)
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="The conversation ID"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get a specific conversation."""
    try:
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="The conversation ID"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Delete a conversation and all its messages."""
    try:
        success = await conversation_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_messages(
    conversation_id: str = Path(..., description="The conversation ID"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get all messages for a conversation."""
    try:
        return await conversation_service.get_messages(conversation_id)
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str = Path(..., description="The conversation ID"),
    message_data: MessageCreate = ...,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Add a message to a conversation."""
    try:
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return await conversation_service.add_message(conversation_id, message_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

