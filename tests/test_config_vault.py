"""Tests for Vault integration and environment-specific configuration."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import (
    Settings,
    get_settings,
    load_environment_config,
    load_vault_secrets,
)


class TestVaultIntegration:
    """Test HashiCorp Vault integration."""

    def test_load_vault_secrets_success(self):
        """Test successful loading of secrets from Vault."""
        mock_vault_client = MagicMock()
        mock_vault_client.is_authenticated.return_value = True
        mock_vault_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'neo4j_uri': 'bolt://vault-host:7687',
                    'neo4j_user': 'vault_user',
                    'neo4j_password': 'vault_password',
                    'ollama_host': 'http://vault-host:11434',
                    'ollama_model': 'vault_model',
                    'ollama_embedding_model': 'vault_embedding',
                    'log_level': 'INFO'
                }
            }
        }

        with patch('src.config.hvac') as mock_hvac, \
             patch('src.config.VAULT_AVAILABLE', True):
            mock_hvac.Client.return_value = mock_vault_client

            secrets = load_vault_secrets(
                vault_addr="https://vault.example.com:8200",
                vault_token="test_token",
                secret_path="secret/data/agent_stack"
            )

            assert secrets['neo4j_uri'] == 'bolt://vault-host:7687'
            assert secrets['neo4j_user'] == 'vault_user'
            assert secrets['neo4j_password'] == 'vault_password'
            assert secrets['ollama_host'] == 'http://vault-host:11434'
            assert secrets['ollama_model'] == 'vault_model'
            assert secrets['ollama_embedding_model'] == 'vault_embedding'
            assert secrets['log_level'] == 'INFO'

    def test_load_vault_secrets_authentication_failure(self):
        """Test Vault authentication failure."""
        mock_vault_client = MagicMock()
        mock_vault_client.is_authenticated.return_value = False

        with patch('src.config.hvac') as mock_hvac, \
             patch('src.config.VAULT_AVAILABLE', True):
            mock_hvac.Client.return_value = mock_vault_client

            with pytest.raises(Exception,
    match="Failed to authenticate with Vault"):
                load_vault_secrets(
                    vault_addr="https://vault.example.com:8200",
                    vault_token="invalid_token",
                    secret_path="secret/data/agent_stack"
                )

    def test_load_vault_secrets_connection_error(self):
        """Test Vault connection error."""
        with patch('src.config.hvac') as mock_hvac, \
             patch('src.config.VAULT_AVAILABLE', True):
            mock_hvac.Client.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                load_vault_secrets(
                    vault_addr="https://vault.example.com:8200",
                    vault_token="test_token",
                    secret_path="secret/data/agent_stack"
                )

    def test_load_vault_secrets_hvac_not_available(self):
        """Test Vault integration when hvac is not available."""
        with patch('src.config.VAULT_AVAILABLE', False):
            with pytest.raises(ImportError, match="hvac package is required"):
                load_vault_secrets(
                    vault_addr="https://vault.example.com:8200",
                    vault_token="test_token",
                    secret_path="secret/data/agent_stack"
                )


class TestEnvironmentSpecificConfig:
    """Test environment-specific configuration loading."""

    def test_load_environment_config_dev(self):
        """Test loading development environment configuration."""
        # Create a temporary dev.env file
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)

        dev_config_path = config_dir / "dev.env"
        dev_config_content = """
APP_ENV=dev
NEO4J_URI=bolt://dev-host:7687
NEO4J_USER=dev_user
NEO4J_PASSWORD=dev_password
OLLAMA_HOST=http://dev-host:11434
OLLAMA_MODEL=dev_model
OLLAMA_EMBEDDING_MODEL=dev_embedding
LOG_LEVEL=DEBUG
"""
        dev_config_path.write_text(dev_config_content)

        try:
            # Clear environment variables
            with patch.dict(os.environ, {}, clear=True):
                load_environment_config("dev")

                # Check that environment variables were loaded
                assert os.getenv("APP_ENV") == "dev"
                assert os.getenv("NEO4J_URI") == "bolt://dev-host:7687"
                assert os.getenv("NEO4J_USER") == "dev_user"
                assert os.getenv("NEO4J_PASSWORD") == "dev_password"
                assert os.getenv("OLLAMA_HOST") == "http://dev-host:11434"
                assert os.getenv("OLLAMA_MODEL") == "dev_model"
                assert os.getenv("OLLAMA_EMBEDDING_MODEL") == "dev_embedding"
                assert os.getenv("LOG_LEVEL") == "DEBUG"
        finally:
            # Clean up
            if dev_config_path.exists():
                dev_config_path.unlink()

    def test_load_environment_config_prod(self):
        """Test loading production environment configuration."""
        # Create a temporary prod.env file
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)

        prod_config_path = config_dir / "prod.env"
        prod_config_content = """
APP_ENV=prod
NEO4J_URI=bolt://prod-host:7687
NEO4J_USER=prod_user
NEO4J_PASSWORD=prod_password
OLLAMA_HOST=http://prod-host:11434
OLLAMA_MODEL=prod_model
OLLAMA_EMBEDDING_MODEL=prod_embedding
LOG_LEVEL=INFO
VAULT_ADDR=https://vault.company.com:8200
VAULT_TOKEN=prod_vault_token
"""
        prod_config_path.write_text(prod_config_content)

        try:
            # Clear environment variables
            with patch.dict(os.environ, {}, clear=True):
                load_environment_config("prod")

                # Check that environment variables were loaded
                assert os.getenv("APP_ENV") == "prod"
                assert os.getenv("NEO4J_URI") == "bolt://prod-host:7687"
                assert os.getenv("NEO4J_USER") == "prod_user"
                assert os.getenv("NEO4J_PASSWORD") == "prod_password"
                assert os.getenv("OLLAMA_HOST") == "http://prod-host:11434"
                assert os.getenv("OLLAMA_MODEL") == "prod_model"
                assert os.getenv("OLLAMA_EMBEDDING_MODEL") == "prod_embedding"
                assert os.getenv("LOG_LEVEL") == "INFO"
                assert os.getenv("VAULT_ADDR") == "https://vault.company.com:8200"
                assert os.getenv("VAULT_TOKEN") == "prod_vault_token"
        finally:
            # Clean up
            if prod_config_path.exists():
                prod_config_path.unlink()

    def test_load_environment_config_nonexistent(self):
        """Test loading non-existent environment configuration."""
        with patch('src.config.load_dotenv') as mock_load_dotenv:
            load_environment_config("nonexistent")
            # Should not call load_dotenv for non-existent file
            mock_load_dotenv.assert_not_called()


class TestGetSettingsWithVault:
    """Test get_settings function with Vault integration."""

    def test_get_settings_with_vault_success(self):
        """Test get_settings with successful Vault integration."""
        mock_vault_client = MagicMock()
        mock_vault_client.is_authenticated.return_value = True
        mock_vault_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'neo4j_uri': 'bolt://vault-host:7687',
                    'neo4j_user': 'vault_user',
                    'neo4j_password': 'vault_password',
                    'ollama_host': 'http://vault-host:11434',
                    'ollama_model': 'vault_model',
                    'ollama_embedding_model': 'vault_embedding',
                    'log_level': 'INFO'
                }
            }
        }

        with patch('src.config.hvac') as mock_hvac, \
             patch('src.config.VAULT_AVAILABLE', True):
            mock_hvac.Client.return_value = mock_vault_client

            # Set up environment for Vault
            with patch.dict(os.environ, {
                "APP_ENV": "prod",
                "VAULT_ADDR": "https://vault.example.com:8200",
                "VAULT_TOKEN": "test_token",
                "VAULT_SECRET_PATH": "secret/data/agent_stack"
            }):
                # Clear cache using the cached version
                from src.config import get_cached_settings
                get_cached_settings.cache_clear()

                settings = get_settings()

                # Verify Vault secrets were loaded
                assert settings.neo4j_uri == 'bolt://vault-host:7687'
                assert settings.neo4j_user == 'vault_user'
                assert settings.neo4j_password == 'vault_password'
                assert settings.ollama_host == 'http://vault-host:11434'
                assert settings.ollama_model == 'vault_model'
                assert settings.ollama_embedding_model == 'vault_embedding'
                assert settings.log_level == 'INFO'

    def test_get_settings_with_vault_failure_fallback(self):
        """Test get_settings with Vault failure falls back to environment variables."""
        with patch('src.config.hvac') as mock_hvac, \
             patch('src.config.VAULT_AVAILABLE', True):
            mock_hvac.Client.side_effect = Exception("Vault connection failed")

            # Set up environment for Vault but with fallback values
            with patch.dict(os.environ, {
                "APP_ENV": "prod",
                "VAULT_ADDR": "https://vault.example.com:8200",
                "VAULT_TOKEN": "test_token",
                "NEO4J_URI": "bolt://fallback-host:7687",
                "NEO4J_USER": "fallback_user",
                "NEO4J_PASSWORD": "fallback_password",
                "OLLAMA_HOST": "http://fallback-host:11434",
                "OLLAMA_MODEL": "fallback_model",
                "OLLAMA_EMBEDDING_MODEL": "fallback_embedding",
                "LOG_LEVEL": "WARNING"
            }):
                # Clear cache using the cached version
                from src.config import get_cached_settings
                get_cached_settings.cache_clear()

                settings = get_settings()

                # Verify fallback values were used
                assert settings.neo4j_uri == 'bolt://fallback-host:7687'
                assert settings.neo4j_user == 'fallback_user'
                assert settings.neo4j_password == 'fallback_password'
                assert settings.ollama_host == 'http://fallback-host:11434'
                assert settings.ollama_model == 'fallback_model'
                assert settings.ollama_embedding_model == 'fallback_embedding'
                assert settings.log_level == 'WARNING'

    def test_get_settings_without_vault_config(self):
        """Test get_settings without Vault configuration uses environment variables."""
        with patch('src.config.load_environment_config'):
            # Set up environment without Vault configuration
            with patch.dict(os.environ, {
                "APP_ENV": "dev",
                "NEO4J_URI": "bolt://env-host:7687",
                "NEO4J_USER": "env_user",
                "NEO4J_PASSWORD": "env_password",
                "OLLAMA_HOST": "http://env-host:11434",
                "OLLAMA_MODEL": "env_model",
                "OLLAMA_EMBEDDING_MODEL": "env_embedding",
                "LOG_LEVEL": "DEBUG"
            }):
                # Clear cache using the cached version
                from src.config import get_cached_settings
                get_cached_settings.cache_clear()

                settings = get_settings()

                # Verify environment variables were used
                assert settings.neo4j_uri == 'bolt://env-host:7687'
                assert settings.neo4j_user == 'env_user'
                assert settings.neo4j_password == 'env_password'
                assert settings.ollama_host == 'http://env-host:11434'
                assert settings.ollama_model == 'env_model'
                assert settings.ollama_embedding_model == 'env_embedding'
                assert settings.log_level == 'DEBUG'


class TestSettingsVaultFields:
    """Test Settings class with Vault-specific fields."""

    def test_settings_vault_fields_defaults(self):
        """Test Settings with default Vault field values."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "OLLAMA_EMBEDDING_MODEL": "test_embedding"
        }, clear=True):
            settings = Settings()

            # Test Vault fields have correct defaults
            assert settings.vault_addr is None
            assert settings.vault_token is None
            assert settings.vault_secret_path == "secret/data/agent_stack"
            assert settings.vault_mount_point == "secret"
            assert settings.app_env == "dev"

    def test_settings_vault_fields_custom(self):
        """Test Settings with custom Vault field values."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "OLLAMA_EMBEDDING_MODEL": "test_embedding",
            "VAULT_ADDR": "https://custom-vault:8200",
            "VAULT_TOKEN": "custom_token",
            "VAULT_SECRET_PATH": "custom/secret/path",
            "VAULT_MOUNT_POINT": "custom_mount",
            "APP_ENV": "staging"
        }, clear=True):
            settings = Settings()

            # Test Vault fields have custom values
            assert settings.vault_addr == "https://custom-vault:8200"
            assert settings.vault_token == "custom_token"
            assert settings.vault_secret_path == "custom/secret/path"
            assert settings.vault_mount_point == "custom_mount"
            assert settings.app_env == "staging"
