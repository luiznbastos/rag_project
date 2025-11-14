"""
Dependency injection for services.
"""
import logging
from typing import Optional
import openai

try:
    from src.utils.vector_db import VectorDatabase
    from src.services.rag_service import RagService
    from src.services.conversation_service import ConversationService
    from src.models.api import HealthResponse
    from src.core.config import settings
    from src.utils.database_client import DatabaseClient
    from src.models.db import Base
except ImportError:
    from utils.vector_db import VectorDatabase
    from services.rag_service import RagService
    from services.conversation_service import ConversationService
    from models.api import HealthResponse
    from core.config import settings
    from utils.database_client import DatabaseClient
    from models.db import Base

logger = logging.getLogger(__name__)

# Global service instances
vector_database: Optional[VectorDatabase] = None
database_client: Optional[DatabaseClient] = None
openai_client: Optional[openai.OpenAI] = None

# State management
_services_initialized = False


async def initialize_services():
    """Initialize all services during application startup."""
    global vector_database, database_client, openai_client, _services_initialized
    
    # Initialize OpenAI client
    if settings.openai_api_key:
        openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI client initialized")
    else:
        openai_client = None
        logger.warning("OpenAI client not initialized - API key not provided")
    
    # Initialize Vector Database (PostgreSQL + pgvector)
    try:
        vector_database = VectorDatabase(db_url=settings.database_url)
        await vector_database.initialize()
        logger.info("Vector Database initialized with pgvector")
    except Exception as e:
        logger.error(f"Failed to initialize Vector Database: {e}")
        raise
    
    # Initialize Database Client for PostgreSQL
    try:
        database_client = DatabaseClient(settings.database_url)
        # Create tables if they don't exist
        Base.metadata.create_all(database_client.engine)
        logger.info("Database client initialized and tables created")
    except Exception as e:
        logger.error(f"Failed to initialize Database Client: {e}")
        raise
    
    _services_initialized = True


async def cleanup_services():
    """Cleanup services during application shutdown."""
    if vector_database:
        await vector_database.close()
        logger.info("Vector Database closed")
    
    if database_client:
        database_client.close()
        logger.info("Database client closed")


# Dependency injection functions

async def get_rag_service() -> RagService:
    """Get RAG service instance."""
    if not _services_initialized:
        raise RuntimeError("Services not initialized")
    if not vector_database:
        raise RuntimeError("Vector Database not initialized")
    if not openai_client:
        raise RuntimeError("OpenAI client not initialized")
    
    return RagService(vector_database, openai_client)


async def get_conversation_service() -> ConversationService:
    """Get conversation service instance."""
    if not _services_initialized:
        raise RuntimeError("Services not initialized")
    
    return ConversationService(db_client=database_client)


async def get_health_status() -> HealthResponse:
    """Get health status of all services."""
    return HealthResponse(
        status="healthy",
        vector_service=vector_database is not None,
        database_service=database_client is not None
    )

