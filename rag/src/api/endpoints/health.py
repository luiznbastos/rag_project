"""
Health check endpoint.
"""
from fastapi import APIRouter, Depends

try:
    from src.models.api import HealthResponse
    from src.core.dependencies import get_health_status
except ImportError:
    from models.api import HealthResponse
    from core.dependencies import get_health_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(health_status: HealthResponse = Depends(get_health_status)):
    """Health check endpoint."""
    return health_status

