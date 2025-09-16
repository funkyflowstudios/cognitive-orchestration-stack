from __future__ import annotations
from pydantic_settings import SettingsConfigDict  # NEW

"""Global configuration management for the Cognitive Orchestration Stack.

Load settings from environment variables (.env) using pydantic BaseSettings for
validation and type-safety.
"""

from pathlib import Path
from functools import lru_cache
try:
    from pydantic_settings import BaseSettings  # Preferred (Pydantic v2)
except ImportError:  # Ultimate fallback – minimal stub for v1 users
    from typing import Any

    class BaseSettings(Any):  # type: ignore
        """Stub BaseSettings for environments lacking pydantic-settings."""
        pass
from dotenv import load_dotenv

# Load .env file early (if present)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables via an .env file.
    Pydantic V2 auto maps uppercase env variables to lowercase model fields.
    """

    # --- Neo4j Database Configuration ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # --- Ollama Model Configuration ---
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_embedding_model: str  # This was the missing field

    # --- Validators ---

    @classmethod
    def validate(cls, value):
        """Custom root-level validation to enforce secure settings."""
        data = super().validate(value)

        if data.neo4j_password in {"changeme", "<YOUR_PASSWORD>", ""}:
            raise ValueError(
                "NEO4J_PASSWORD is using an insecure default value. "
                "Set a strong password in your .env file.",
            )

        # Ensure mandatory embedding model variable is set
        if not data.ollama_embedding_model:
            raise ValueError(
                "OLLAMA_EMBEDDING_MODEL must be specified in .env",
            )

        return data

    # --- Miscellaneous Configuration ---
    log_level: str = "INFO"

    # model_config tells Pydantic to load variables from a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:  # noqa: D401
    """Return cached Settings instance."""

    return Settings()
