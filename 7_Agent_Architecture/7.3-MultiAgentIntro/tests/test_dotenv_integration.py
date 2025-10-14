"""
Tests for dotenv integration in settings.
"""

import os
import pytest
from unittest.mock import patch
from dotenv import load_dotenv

from config.settings import Settings


def test_dotenv_is_loaded():
    """Test that dotenv is properly imported and available."""
    # Test that we can import load_dotenv
    from dotenv import load_dotenv
    assert callable(load_dotenv)


def test_settings_with_env_variables():
    """Test that settings properly load from environment variables."""
    # Set test environment variables
    test_env = {
        'LLM_API_KEY': 'test_llm_key',
        'BRAVE_API_KEY': 'test_brave_key',
        'LLM_PROVIDER': 'test_provider',
        'LLM_MODEL': 'test_model',
        'APP_ENV': 'testing',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        settings = Settings()
        
        assert settings.llm_api_key == 'test_llm_key'
        assert settings.brave_api_key == 'test_brave_key'
        assert settings.llm_provider == 'test_provider'
        assert settings.llm_model == 'test_model'
        assert settings.app_env == 'testing'
        assert settings.log_level == 'DEBUG'


def test_dotenv_loads_example_file():
    """Test that we can load from .env.example file."""
    # Clear existing env vars first
    for key in ['LLM_PROVIDER', 'LLM_MODEL', 'GMAIL_CREDENTIALS_PATH', 'BRAVE_API_KEY']:
        if key in os.environ:
            del os.environ[key]
    
    # Load from .env.example
    load_dotenv('.env.example')
    
    # Check that variables are loaded
    assert os.getenv('LLM_PROVIDER') == 'openai'
    assert os.getenv('LLM_MODEL') == 'gpt-4'
    assert os.getenv('GMAIL_CREDENTIALS_PATH') == './credentials/credentials.json'
    assert 'BSA-' in os.getenv('BRAVE_API_KEY', '')


def test_settings_model_config_includes_env_file():
    """Test that settings model config is properly configured for .env files."""
    settings = Settings()
    
    # Check that model_config includes .env file
    assert hasattr(settings, 'model_config')
    assert settings.model_config.get('env_file') == '.env'
    assert settings.model_config.get('env_file_encoding') == 'utf-8'
    assert settings.model_config.get('case_sensitive') is False