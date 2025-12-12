"""
AI News Agent - FastAPI Web Application
Fetch and analyze news articles with AI-powered relevance classification
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime
import logging
import os

from config import settings
from models import SearchRequest, JobStatus, JobResponse
from services.news_fetcher import NewsFetcher
from services.ai_analyzer import AIAnalyzer
from services.job_manager import JobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI News Agent API",
    description="Fetch and analyze news articles with AI-powered relevance classification",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
job_manager = JobManager()

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("results", exist_ok=True)


@app.get("/")
async def root():
    """Serve the web interface"""
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/api/search", response_model=JobResponse)
async def create_search_job(
    request: SearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new news search and analysis job
    
    - **query**: Search query (any topic)
    - **languages**: List of language codes
    - **categories**: List of news categories
    - **extra_topics**: Additional context for AI analysis
    - **news_api_key**: NewsData.io API key
    - **openai_api_key**: OpenAI API key
    """
    try:
        job_id = str(uuid.uuid4())
        job_manager.create_job(job_id, request)
        
        # Run as asyncio task instead of background task
        asyncio.create_task(
            process_news_search(
                job_id=job_id,
                request=request
            )
        )
        
        logger.info(f"Created job {job_id} for query: {request.query}")
        
        return JobResponse(
            job_id=job_id,
            status="processing",
            message="Job created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status by ID"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.debug(f"Returning job status: {job.status}, progress: {job.progress}, articles: {job.total_articles}")
    return job


@app.get("/api/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """Get detailed results of a completed job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job.status}"
        )
    
    return {
        "job_id": job_id,
        "query": job.query,
        "total_articles": job.total_articles,
        "articles": job.results
    }


@app.get("/api/jobs/{job_id}/download")
async def download_results(job_id: str, format: str = "json"):
    """Download results in different formats (json, csv, xlsx)"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    try:
        file_path = job_manager.export_results(job_id, format)
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=f"results_{job_id}.{format}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    success = job_manager.delete_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job deleted successfully"}


@app.get("/api/jobs")
async def list_jobs(limit: int = 50):
    """List all jobs"""
    jobs = job_manager.list_jobs(limit=limit)
    return {"jobs": jobs}


async def process_news_search(job_id: str, request: SearchRequest):
    """Background task to process news search and AI analysis"""
    try:
        # Update status: fetching
        job_manager.update_job(job_id, status="fetching", progress=10)
        
        # Fetch articles
        fetcher = NewsFetcher(api_key=request.news_api_key)
        logger.info(f"Job {job_id}: Fetching articles for '{request.query}'")
        
        # Define progress callback to update article count in real-time
        async def update_fetch_progress(article_count: int):
            logger.info(f"Job {job_id}: Progress callback - updating with {article_count} articles")
            job_manager.update_job(
                job_id,
                status="fetching",
                progress=10 + int((article_count / (request.size * request.max_pages)) * 30),
                total_articles=article_count
            )
        
        articles = await fetcher.fetch_articles(
            query=request.query,
            languages=request.languages,
            categories=request.categories,
            size=request.size,
            max_pages=request.max_pages,
            progress_callback=update_fetch_progress
        )
        
        if not articles:
            job_manager.update_job(
                job_id,
                status="failed",
                error="No articles found",
                progress=100
            )
            return
        
        logger.info(f"Job {job_id}: Fetched {len(articles)} articles")
        
        # Move to analyzing phase
        job_manager.update_job(
            job_id,
            status="analyzing",
            progress=50,
            total_articles=len(articles)
        )
        
        # Analyze with AI
        analyzer = AIAnalyzer(
            api_key=request.openai_api_key,
            model=request.model,
            base_url=request.api_base_url
        )
        
        logger.info(f"Job {job_id}: Starting AI analysis")
        classified_articles = await analyzer.analyze_articles(
            articles=articles,
            query=request.query,
            extra_topics=request.extra_topics
        )
        
        logger.info(f"Job {job_id}: Analysis complete - {len(classified_articles)} articles classified")
        
        # Update with results
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            results=classified_articles,
            total_articles=len(classified_articles)
        )
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job_manager.update_job(
            job_id,
            status="failed",
            error=str(e),
            progress=100
        )


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Directory might not exist yet


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI News Agent...")
    print(f"📖 API Docs: http://localhost:{settings.PORT}/api/docs")
    print(f"🌐 Web App: http://localhost:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
