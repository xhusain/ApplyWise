"""
Configuration Management for Job Application AI System
Loads environment variables and provides centralized config access
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    groq_api_key: str
    tavily_api_key: str
    
    # Application Settings
    app_name: str = "ApplyWise"
    debug: bool = True
    log_level: str = "INFO"
    
    # File Storage
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_file_size: int = 10485760  # 10MB
    
    # LLM Settings
    default_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to ensure single instance throughout application
    """
    return Settings()


def ensure_directories():
    """Create necessary directories if they don't exist"""
    settings = get_settings()
    
    directories = [
        settings.upload_dir,
        settings.output_dir,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ensured: {directory}")


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration...")
    settings = get_settings()
    print(f"✓ App Name: {settings.app_name}")
    print(f"✓ Groq API Key: {'*' * 20}{settings.groq_api_key[-4:]}")
    print(f"✓ Tavily API Key: {'*' * 20}{settings.tavily_api_key[-4:]}")
    print(f"✓ Default Model: {settings.default_model}")
    ensure_directories()
