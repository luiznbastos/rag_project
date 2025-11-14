"""
Main FastAPI application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from src.core.config import settings
    from src.core.dependencies import initialize_services, cleanup_services
    from src.api.endpoints import health, ask, conversations
except ImportError:
    from core.config import settings
    from core.dependencies import initialize_services, cleanup_services
    from api.endpoints import health, ask, conversations

logging.basicConfig(level=logging.INFO, format=settings.log_format)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    logger.info("Initializing services...")
    await initialize_services()
    logger.info("All services initialized successfully")
    yield
    logger.info("Cleaning up services...")
    await cleanup_services()


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_config["allow_origins"],
    allow_credentials=settings.cors_config["allow_credentials"],
    allow_methods=settings.cors_config["allow_methods"],
    allow_headers=settings.cors_config["allow_headers"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(ask.router, tags=["rag"])
app.include_router(conversations.router, tags=["conversations"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": settings.api_description,
        "version": settings.api_version,
        "endpoints": {
            "ask": "/ask",
            "health": "/health",
            "conversations": "/conversations",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

