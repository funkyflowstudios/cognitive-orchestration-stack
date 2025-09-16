from __future__ import annotations

from pydantic_settings import SettingsConfigDict  # NEW

"""Global configuration management for the Cognitive Orchestration Stack.

Load settings from environment variables (.env) using pydantic BaseSettings for
validation and type-safety. Supports HashiCorp Vault for production secrets
management.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pydantic_settings import BaseSettings  # Preferred (Pydantic v2)
except ImportError:  # Ultimate fallback – minimal stub for v1 users

    class BaseSettings(Any):  # type: ignore
        """Stub BaseSettings for environments lacking pydantic-settings."""

        pass


from dotenv import load_dotenv

# Optional Vault integration
try:
    import hvac

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    hvac = None

# Load .env file early (if present)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables via an .env file.
    Pydantic V2 auto maps uppercase env variables to lowercase model fields.
    Supports HashiCorp Vault for production secrets management.
    """

    # --- Vault Configuration (Optional) ---
    vault_addr: Optional[str] = None
    vault_token: Optional[str] = None
    vault_secret_path: str = "secret/data/agent_stack"
    vault_mount_point: str = "secret"

    # --- Neo4j Database Configuration ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # --- Ollama Model Configuration ---
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_embedding_model: str  # This was the missing field

    # --- Google Search API Configuration (Optional) ---
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None

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
    app_env: str = "dev"
    log_level: str = "INFO"

    # model_config tells Pydantic to load variables from a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


def load_vault_secrets(
    vault_addr: str,
    vault_token: str,
    secret_path: str,
    mount_point: str = "secret",
) -> Dict[str, Any]:
    """
    Load secrets from HashiCorp Vault.

    Args:
        vault_addr: Vault server address
        vault_token: Vault authentication token
        secret_path: Path to the secret in Vault
        mount_point: Vault mount point (default: "secret")

    Returns:
        Dictionary containing the secrets

    Raises:
        Exception: If Vault is not available or connection fails
    """
    if not VAULT_AVAILABLE:
        raise ImportError(
            "hvac package is required for Vault integration. "
            "Install with: pip install hvac"
        )

    try:
        client = hvac.Client(url=vault_addr, token=vault_token)

        # Verify the client is authenticated
        if not client.is_authenticated():
            raise Exception("Failed to authenticate with Vault")

        # Read the secret
        response = client.secrets.kv.v2.read_secret_version(
            path=secret_path, mount_point=mount_point
        )

        return response["data"]["data"]

    except Exception as e:
        logging.error(f"Failed to load secrets from Vault: {e}")
        raise


def load_environment_config(env: str = "dev") -> None:
    """
    Load environment-specific configuration file.

    Args:
        env: Environment name (dev, prod, etc.)
    """
    config_file = (
        Path(__file__).resolve().parent.parent / "config" / f"{env}.env"
    )

    if config_file.exists():
        load_dotenv(dotenv_path=config_file, override=True)
        logging.info(f"Loaded environment configuration from {config_file}")
    else:
        logging.warning(
            f"Environment configuration file not found: {config_file}"
        )


def get_settings() -> Settings:  # noqa: D401
    """
    Return Settings instance with optional Vault integration and
    environment-specific config.

    Loads environment-specific configuration first, then optionally loads
    secrets from Vault. Falls back to environment variables and .env file if
    Vault is not configured.
    """
    # Determine environment from APP_ENV or default to 'dev'
    app_env = os.getenv("APP_ENV", "dev")

    # Load environment-specific configuration
    load_environment_config(app_env)

    # Load basic settings
    settings = Settings()

    # If Vault is configured, load secrets from Vault
    if settings.vault_addr and settings.vault_token:
        try:
            vault_secrets = load_vault_secrets(
                vault_addr=settings.vault_addr,
                vault_token=settings.vault_token,
                secret_path=settings.vault_secret_path,
                mount_point=settings.vault_mount_point,
            )

            # Create a new Settings instance with Vault secrets
            # This overrides environment variables with Vault values
            vault_env_vars = {
                "NEO4J_URI": vault_secrets.get(
                    "neo4j_uri", settings.neo4j_uri
                ),
                "NEO4J_USER": vault_secrets.get(
                    "neo4j_user", settings.neo4j_user
                ),
                "NEO4J_PASSWORD": vault_secrets.get(
                    "neo4j_password", settings.neo4j_password
                ),
                "OLLAMA_HOST": vault_secrets.get(
                    "ollama_host", settings.ollama_host
                ),
                "OLLAMA_MODEL": vault_secrets.get(
                    "ollama_model", settings.ollama_model
                ),
                "OLLAMA_EMBEDDING_MODEL": vault_secrets.get(
                    "ollama_embedding_model", settings.ollama_embedding_model
                ),
                "LOG_LEVEL": vault_secrets.get(
                    "log_level", settings.log_level
                ),
            }

            # Update environment variables temporarily
            for key, value in vault_env_vars.items():
                os.environ[key] = value

            # Create new settings with Vault values
            settings = Settings()
            logging.info("Successfully loaded secrets from HashiCorp Vault")

        except Exception as e:
            logging.warning(
                f"Failed to load secrets from Vault, falling back to "
                f"environment variables: {e}"
            )
            # Return the original settings if Vault fails
            return settings

    return settings


# Cache the settings instance
@lru_cache()
def get_cached_settings() -> Settings:
    """Return cached Settings instance for performance."""
    return get_settings()
