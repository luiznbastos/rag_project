"""
Conversation Service for managing chat conversations and messages.
"""
import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select, delete

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    from src.core.config import settings
    from src.models.api import (
        ConversationCreate, ConversationResponse, MessageCreate, MessageResponse,
        ConversationListResponse, ConversationMessagesResponse
    )
    from src.models.db import Conversation, Message, Base
    from src.utils.database_client import DatabaseClient
except ImportError:
    from core.config import settings
    from models.api import (
        ConversationCreate, ConversationResponse, MessageCreate, MessageResponse,
        ConversationListResponse, ConversationMessagesResponse
    )
    from models.db import Conversation, Message, Base
    from utils.database_client import DatabaseClient

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""
    
    def __init__(self, db_client: DatabaseClient = None):
        """
        Initialize the conversation service.
        
        Args:
            db_client: Database client for PostgreSQL operations
        """
        self.db_client = db_client
        self._session_factory = None
        self._db_initialized = False
        
        # Initialize OpenAI client for title generation
        self.openai_client = None
        if OPENAI_AVAILABLE and hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
    def _ensure_db_connection(self):
        """Initialize database connection if not already done."""
        if self.db_client is None and not self._db_initialized:
            try:
                from src.core.config import settings
                
                db_client = DatabaseClient(settings.database_url)
                self.db_client = db_client
                self._session_factory = sessionmaker(bind=db_client.engine)
                self._db_initialized = True
                logger.info("Database connection initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize database connection: {e}")
                raise
    
    def _get_session(self) -> Session:
        """Get a SQLAlchemy session."""
        if not self._session_factory:
            self._ensure_db_connection()
        return self._session_factory()
    
    def generate_conversation_title(self, first_query: str) -> str:
        """
        Generate a concise title from the first user query using OpenAI.
        
        Args:
            first_query: The first message from the user
            
        Returns:
            str: Generated title (max 5 words)
        """
        if not self.openai_client or not OPENAI_AVAILABLE:
            return first_query[:50] + "..." if len(first_query) > 50 else first_query
        
        try:
            prompt = f'''Extract a short, concise title (max 5 words) that summarizes this question:
            "{first_query}"
            
            Return only the title, nothing else.'''
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise titles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20
            )
            
            title = response.choices[0].message.content.strip()
            if len(title) > 100:
                title = title[:100] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return first_query[:50] + "..." if len(first_query) > 50 else first_query
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            conversation_id = str(uuid.uuid4())
            now = datetime.now()
            
            conversation = Conversation(
                conversation_id=conversation_id,
                title=conversation_data.title,
                created_at=now,
                updated_at=now
            )
            
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            session.close()
            
            logger.info(f"Created conversation '{conversation_data.title}' (ID: {conversation_id[:8]}...)")
            
            return ConversationResponse(
                conversation_id=conversation_id,
                title=conversation_data.title,
                created_at=now,
                updated_at=now
            )
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def list_conversations(self, limit: int = 50) -> ConversationListResponse:
        """Get list of conversations."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            stmt = select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
            results = session.execute(stmt).scalars().all()
            session.close()
            
            conversations = []
            for conv in results:
                conversations.append(ConversationResponse(
                    conversation_id=conv.conversation_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at
                ))
            
            return ConversationListResponse(
                conversations=conversations,
                total=len(conversations)
            )
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get a specific conversation."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            stmt = select(Conversation).where(Conversation.conversation_id == conversation_id)
            result = session.execute(stmt).scalar_one_or_none()
            session.close()
            
            if not result:
                return None
            
            return ConversationResponse(
                conversation_id=result.conversation_id,
                title=result.title,
                created_at=result.created_at,
                updated_at=result.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            # Delete messages first (foreign key constraint)
            delete_msgs = delete(Message).where(Message.conversation_id == conversation_id)
            session.execute(delete_msgs)
            
            # Delete conversation
            delete_conv = delete(Conversation).where(Conversation.conversation_id == conversation_id)
            session.execute(delete_conv)
            
            session.commit()
            session.close()
            
            logger.info(f"Deleted conversation {conversation_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise
    
    async def get_messages(self, conversation_id: str) -> ConversationMessagesResponse:
        """Get all messages for a conversation."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
            results = session.execute(stmt).scalars().all()
            session.close()
            
            messages = []
            for msg in results:
                sources = None
                if msg.sources:
                    try:
                        sources = json.loads(msg.sources) if isinstance(msg.sources, str) else msg.sources
                    except (json.JSONDecodeError, TypeError):
                        sources = None
                
                messages.append(MessageResponse(
                    message_id=msg.message_id,
                    conversation_id=msg.conversation_id,
                    role=msg.role,
                    content=msg.content,
                    sources=sources,
                    created_at=msg.created_at
                ))
            
            return ConversationMessagesResponse(
                conversation_id=conversation_id,
                messages=messages,
                total=len(messages)
            )
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise
    
    async def add_message(self, conversation_id: str, message_data: MessageCreate) -> MessageResponse:
        """Add a message to a conversation."""
        try:
            self._ensure_db_connection()
            session = self._get_session()
            
            message_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Convert sources to JSON string for database storage
            sources_json = None
            if message_data.sources:
                sources_json = json.dumps(message_data.sources)
            elif message_data.sources is not None:
                sources_json = json.dumps([])
            
            message = Message(
                message_id=message_id,
                conversation_id=conversation_id,
                role=message_data.role,
                content=message_data.content,
                sources=sources_json,
                created_at=now
            )
            
            session.add(message)
            
            # Update conversation timestamp
            conv_stmt = select(Conversation).where(Conversation.conversation_id == conversation_id)
            conv = session.execute(conv_stmt).scalar_one()
            conv.updated_at = now
            
            session.commit()
            session.refresh(message)
            session.close()
            
            logger.info(f"Added {message_data.role} message to conversation {conversation_id[:8]}...")
            
            return MessageResponse(
                message_id=message_id,
                conversation_id=conversation_id,
                role=message_data.role,
                content=message_data.content,
                sources=message_data.sources,
                created_at=now
            )
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise

