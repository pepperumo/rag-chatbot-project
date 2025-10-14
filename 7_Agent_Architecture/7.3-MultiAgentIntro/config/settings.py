"""
Configuration management using pydantic-settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai")
    llm_api_key: str = Field(...)
    llm_model: str = Field(default="gpt-4")
    llm_base_url: Optional[str] = Field(default="https://api.openai.com/v1")
    
    # Brave Search Configuration
    brave_api_key: str = Field(...)
    brave_search_url: str = Field(
        default="https://api.search.brave.com/res/v1/web/search"
    )
    brave_rate_limit: int = Field(default=2000)  # Monthly limit
    
    # Gmail Configuration
    gmail_credentials_path: str = Field(
        default="./credentials/credentials.json"
    )
    gmail_token_path: str = Field(
        default="./credentials/token.json"
    )
    gmail_scopes: list[str] = Field(
        default=[
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.send"
        ]
    )
    
    # Application Configuration
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    @field_validator("llm_api_key", "brave_api_key")
    @classmethod
    def validate_api_keys(cls, v):
        """Ensure API keys are not empty."""
        if not v or v.strip() == "":
            raise ValueError("API key cannot be empty")
        return v
    
    @field_validator("gmail_credentials_path")
    @classmethod
    def validate_gmail_credentials(cls, v):
        """Check if Gmail credentials file exists."""
        if not os.path.exists(v):
            # Create credentials directory if it doesn't exist
            os.makedirs(os.path.dirname(v), exist_ok=True)
            # Note: The actual credentials.json needs to be obtained from Google Cloud Console
            print(f"Warning: Gmail credentials file not found at {v}")
            print("Please download credentials.json from Google Cloud Console")
        return v


# Global settings instance
try:
    settings = Settings()
except Exception:
    # For testing, create settings with dummy values
    import os
    os.environ.setdefault("LLM_API_KEY", "test_key")
    os.environ.setdefault("BRAVE_API_KEY", "test_key")
    settings = Settings()