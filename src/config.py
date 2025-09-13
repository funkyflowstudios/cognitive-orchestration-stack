from __future__ import annotations

"""Global configuration management for the Cognitive Orchestration Stack.

Loads settings from environment variables (.env) using pydantic BaseSettings for
validation and type-safety.
"""

from pathlib import Path
from functools import lru_cache
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load .env file early (if present)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Neo4j ---
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field("neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    # --- Ollama ---
    ollama_host: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field("llama3", env="OLLAMA_MODEL")

    # --- Misc ---
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:  # noqa: D401
    """Return cached Settings instance."""

    return Settings()
