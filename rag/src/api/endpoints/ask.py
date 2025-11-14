"""
Ask endpoint for RAG queries.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

try:
    from src.models.api import QueryRequest, QueryResponse
    from src.services.rag_service import RagService
    from src.core.dependencies import get_rag_service
except ImportError:
    from models.api import QueryRequest, QueryResponse
    from services.rag_service import RagService
    from core.dependencies import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask(
    request: QueryRequest,
    rag_service: RagService = Depends(get_rag_service)
):
    """Process document query with hybrid search and optional reranking."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        return await rag_service.process_query(request)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

