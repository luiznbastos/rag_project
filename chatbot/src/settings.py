from pydantic import Field
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # RAG backend
    rag_api_base_url: str = Field(default="http://localhost:8000", alias="RAG_API_BASE_URL")

    # Database credentials
    rds_host: Optional[str] = Field(default=None, alias="RDS_HOST")
    rds_db: Optional[str] = Field(default=None, alias="RDS_DB")
    rds_user: Optional[str] = Field(default=None, alias="RDS_USER")
    rds_password: Optional[str] = Field(default=None, alias="RDS_PASSWORD")
    rds_port: int = Field(default=5432, alias="RDS_PORT")
    
    # OpenAI API key for title generation
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql://{self.rds_user}:{self.rds_password}@{self.rds_host}:{self.rds_port}/{self.rds_db}"


logger.info("Loading settings from environment variables...")
settings = Settings()
logger.info("Settings loaded successfully.")

