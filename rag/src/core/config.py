"""
Application settings and configuration.
"""
import logging
from typing import Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings and configuration."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    
    # Database credentials
    rds_user: str = Field(default="company_admin", alias="RDS_USER")
    rds_password: str = Field(default="diU59nM8Z0t+bb&x", alias="RDS_PASSWORD")
    rds_host: str = Field(
        default="streamlit-fastapi-company.cet4y0iaow4o.us-east-1.rds.amazonaws.com", 
        alias="RDS_HOST"
    )
    rds_db: str = Field(default="company", alias="RDS_DB")
    rds_port: int = Field(default=5432, alias="RDS_PORT")
    
    # API metadata
    api_title: str = Field(default="Simple RAG API")
    api_description: str = Field(default="RAG API for document queries")
    api_version: str = Field(default="0.0.1")
    
    # Chunking configuration
    chunk_size: int = Field(default=2000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    
    # Logging configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def cors_config(self) -> Dict[str, Any]:
        """CORS configuration for the API."""
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "DELETE"],
            "allow_headers": ["*"],
        }
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql://{self.rds_user}:{self.rds_password}@{self.rds_host}:{self.rds_port}/{self.rds_db}"
    
    def validate(self) -> bool:
        """Validate required configuration settings."""
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set. Some features may not work.")
            return False
        return True


settings = Settings()
settings.validate()

