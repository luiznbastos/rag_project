"""
Database models for PostgreSQL with pgvector.
Contains SQLAlchemy models for conversations/messages/document_chunks and Pydantic models.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

Base = declarative_base()


class Conversation(Base):
    """SQLAlchemy model for conversations table."""
    __tablename__ = "conversations"
    
    conversation_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """SQLAlchemy model for messages table."""
    __tablename__ = "messages"
    
    message_id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")


class ConversationPydantic(BaseModel):
    """Pydantic model for Conversation conversion."""
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessagePydantic(BaseModel):
    """Pydantic model for Message conversion."""
    message_id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentChunk(Base):
    """SQLAlchemy model for document chunks with vector search support."""
    __tablename__ = "document_chunks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(String(256), nullable=False, index=True)
    chunk_id = Column(String(256), nullable=False)
    filename = Column(String(256), nullable=False)
    chunk_text = Column(Text, nullable=False)
    dense_vector = Column(Vector(3072))  # OpenAI text-embedding-3-large
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_id', name='uq_document_chunk'),
    )


class DocumentChunkPydantic(BaseModel):
    """Pydantic model for DocumentChunk."""
    id: int
    document_id: str
    chunk_id: str
    filename: str
    chunk_text: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

