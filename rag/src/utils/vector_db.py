import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from openai import AsyncOpenAI

try:
    from src.models.db import DocumentChunk, Base
except ImportError:
    from models.db import DocumentChunk, Base

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Semantic vector database using PostgreSQL + pgvector.
    
    Features:
    - Pure semantic search using cosine similarity
    - OpenAI embeddings (text-embedding-3-large)
    - Efficient SQL queries with proper LIMIT
    - Pure SQLAlchemy implementation
    """
    
    def __init__(self, db_url: str):
        """
        Initialize the vector database.
        
        Args:
            db_url: PostgreSQL connection URL
        """
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set. Embedding generation will fail.")
            self.openai_client = None
        else:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
    
    async def initialize(self):
        """Create tables using SQLAlchemy (idempotent)."""
        await asyncio.to_thread(Base.metadata.create_all, self.engine)
        logger.info("Vector database initialized")
    
    async def get_embedding(self, text: str, model: str = "text-embedding-3-large") -> List[float]:
        """
        Generate dense embedding using OpenAI.
        
        Args:
            text: Text to embed
            model: OpenAI model to use
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured. Set OPENAI_API_KEY.")
        
        text = text.replace("\n", " ").strip()
        if not text:
            return []
        
        try:
            response = await self.openai_client.embeddings.create(
                input=[text],
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def add_document_sections(self, sections: List[Dict[str, Any]]) -> List[int]:
        """
        Add document chunks with embeddings to PostgreSQL.
        
        Args:
            sections: List of dicts with keys: document_id, chunk_id, filename, chunk_text
            
        Returns:
            List of inserted chunk IDs
        """
        if not sections:
            return []
        
        session = self.SessionLocal()
        inserted_ids = []
        
        try:
            for section in sections:
                # Validate required fields
                text_to_embed = section.get("chunk_text")
                document_id = section.get("document_id")
                chunk_id = section.get("chunk_id")
                filename = section.get("filename")
                
                if not all([text_to_embed, document_id, chunk_id, filename]):
                    logger.warning(f"Skipping incomplete section: {section}")
                    continue
                
                # Generate embedding
                dense_vector = await self.get_embedding(text_to_embed)
                
                # Create chunk object (text_search_vector auto-populated by trigger)
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    filename=filename,
                    chunk_text=text_to_embed,
                    dense_vector=dense_vector
                )
                
                # Merge for upsert behavior (update if exists, insert if not)
                session.merge(chunk)
            
            session.commit()
            logger.info(f"Successfully upserted {len(sections)} chunks")
            
            # Get inserted IDs
            inserted_ids = [
                chunk.id for chunk in 
                session.query(DocumentChunk).filter(
                    DocumentChunk.document_id.in_([s['document_id'] for s in sections])
                ).all()
            ]
            
            return inserted_ids
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise
        finally:
            session.close()
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search using cosine similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of dicts with keys: id, document_id, chunk_id, filename, chunk_text,
                                    distance, similarity
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured")
        
        try:
            # Generate query embedding for vector search
            query_embedding = await self.get_embedding(query)
            
            session = self.SessionLocal()
            try:
                # Simple vector similarity search
                results = session.query(
                    DocumentChunk,
                    DocumentChunk.dense_vector.cosine_distance(query_embedding).label('distance')
                ).order_by(
                    DocumentChunk.dense_vector.cosine_distance(query_embedding)
                ).limit(top_k).all()
                
                # Format results
                formatted = []
                for chunk, distance in results:
                    similarity = 1 - float(distance)  # Convert distance to similarity
                    formatted.append({
                        'id': chunk.id,
                        'document_id': chunk.document_id,
                        'chunk_id': chunk.chunk_id,
                        'filename': chunk.filename,
                        'chunk_text': chunk.chunk_text,
                        'distance': float(distance),
                        'similarity': similarity
                    })
                
                logger.info(f"Semantic search: returned {len(formatted)} results")
                return formatted
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents."""
        session = self.SessionLocal()
        try:
            count = session.query(DocumentChunk).count()
            return {"total_chunks": count}
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
        finally:
            session.close()
    
    async def close(self):
        """Close connections."""
        if self.openai_client:
            await self.openai_client.close()
        logger.info("VectorDatabase closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
