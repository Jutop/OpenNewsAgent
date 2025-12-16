"""
Pydantic models for validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, description="Search query")
    languages: List[str] = Field(default=["en"], description="Language codes")
    categories: List[str] = Field(default=["science", "technology"], description="Categories")
    extra_topics: Optional[str] = Field(None, description="Additional topics")
    news_api_key: str = Field(..., description="NewsData.io API key")
    openai_api_key: str = Field(..., description="OpenAI API key")
    api_base_url: Optional[str] = Field(default=None, description="Custom API base URL (for Azure or other)")
    is_azure: Optional[bool] = Field(default=False, description="Is this an Azure OpenAI endpoint")
    api_version: Optional[str] = Field(default=None, description="Azure API version (e.g., 2024-10-21)")
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    size: int = Field(default=10, ge=1, le=10, description="Articles per page")
    max_pages: int = Field(default=10, ge=1, le=50, description="Max pages")
    
    class Config:
        extra = "ignore"  # Ignore extra fields that might be sent
    
    @validator('languages')
    def validate_languages(cls, v):
        if not v:
            raise ValueError("At least one language required")
        return v
    
    @validator('categories')
    def validate_categories(cls, v):
        if not v:
            raise ValueError("At least one category required")
        return v

class JobResponse(BaseModel):
    """Job creation response"""
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    """Job status model"""
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    query: str
    total_articles: Optional[int] = None
    error: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
