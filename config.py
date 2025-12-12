"""
Configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "AI News Agent"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # OpenAI
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # NewsData.io
    NEWSDATA_BASE_URL: str = "https://newsdata.io/api/1/news"
    NEWSDATA_MAX_SIZE: int = 10  # Free plan limit
    NEWSDATA_DEFAULT_MAX_PAGES: int = 10
    
    # Storage
    DATA_DIRECTORY: str = "data"
    RESULTS_DIRECTORY: str = "results"
    
    # Jobs
    MAX_JOBS_IN_MEMORY: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
