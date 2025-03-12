#!/usr/bin/env python3
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration class that loads from environment variables."""
    
    # Basic configurations
    api_port: int = Field(8080, description="Port for the bot API")
    linkedin_email: str = Field(..., description="LinkedIn email account")
    linkedin_password: str = Field(..., description="LinkedIn password")
    apply_limit: int = Field(200, description="Maximum number of applications")
    
    # Style
    style_choice: str = Field("Modern Blue", description="Resume style choice")
    
    # Browser fingerprinting
    sec_ch_ua: str = Field(
        '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        description="User-Agent Client Hints header"
    )
    sec_ch_ua_platform: str = Field("Windows", description="User-Agent platform")
    user_agent: str = Field(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        description="Complete User-Agent header"
    )
    
    # Integration
    backend_token: str = Field(..., description="Authentication token for the backend")
    backend_url: str = Field(..., description="Backend API URL")
    bot_id: str = Field(..., description="Bot ID")
    
    # Optional services
    gotenberg_url: Optional[str] = Field(None, description="Gotenberg PDF service URL (optional)")
    
    class Config:
        env_file = ".env"


def load_config() -> Settings:
    """Loads and validates environment variables."""
    try:
        config = Settings()
        return config
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}") 