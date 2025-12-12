"""
Job Manager - Manage background jobs
"""
from typing import Dict, Optional, List, Any
from datetime import datetime
import json
import os
import csv
import pandas as pd
from models import SearchRequest, JobStatus
import logging

logger = logging.getLogger(__name__)

class JobManager:
    """Manage job state and storage"""
    
    def __init__(self, max_jobs: int = 100):
        self.jobs: Dict[str, JobStatus] = {}
        self.max_jobs = max_jobs
        
        os.makedirs("data", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        
        # Load existing results from disk
        self._load_existing_results()
    
    def create_job(self, job_id: str, request: SearchRequest) -> JobStatus:
        """Create new job"""
        now = datetime.now()
        
        job = JobStatus(
            job_id=job_id,
            status="created",
            progress=0,
            created_at=now,
            updated_at=now,
            query=request.query,
            total_articles=None,
            error=None,
            results=None
        )
        
        self.jobs[job_id] = job
        
        if len(self.jobs) > self.max_jobs:
            self._cleanup_old_jobs()
        
        return job
    
    def get_job(self, job_id: str) -> Optional[JobStatus]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        total_articles: Optional[int] = None,
        error: Optional[str] = None,
        results: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[JobStatus]:
        """Update job"""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if total_articles is not None:
            job.total_articles = total_articles
        if error:
            job.error = error
        if results is not None:
            job.results = results
        
        job.updated_at = datetime.now()
        
        if status == "completed" and results:
            self._save_results(job_id, results, job.query)
        
        return job
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            
            for ext in ['json', 'csv', 'xlsx']:
                file_path = f"results/{job_id}.{ext}"
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return True
        return False
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List jobs"""
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda x: x.updated_at, reverse=True)
        
        return [
            {
                "job_id": job.job_id,
                "status": job.status,
                "query": job.query,
                "progress": job.progress,
                "total_articles": job.total_articles,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
            for job in jobs_list[:limit]
        ]
    
    def _save_results(self, job_id: str, results: List[Dict[str, Any]], query: str):
        """Save results to JSON"""
        try:
            file_path = f"results/{job_id}.json"
            
            data = {
                "job_id": job_id,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "total_articles": len(results),
                "articles": results
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved results: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
    
    def export_results(self, job_id: str, format: str = "json") -> str:
        """Export results in different formats"""
        job = self.jobs.get(job_id)
        if not job or not job.results:
            raise Exception("Job not found or no results")
        
        if format == "json":
            return f"results/{job_id}.json"
        elif format == "csv":
            csv_path = f"results/{job_id}.csv"
            self._export_to_csv(job.results, csv_path)
            return csv_path
        elif format == "xlsx":
            xlsx_path = f"results/{job_id}.xlsx"
            self._export_to_xlsx(job.results, xlsx_path)
            return xlsx_path
        else:
            raise Exception(f"Unsupported format: {format}")
    
    def _export_to_csv(self, results: List[Dict[str, Any]], file_path: str):
        """Export to CSV"""
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Relevance", "Article ID", "Title", "Description",
                    "Link", "Keywords", "Category", "Reasoning"
                ])
                
                for article in results:
                    keywords = ", ".join(article.get("keywords", [])) if isinstance(article.get("keywords"), list) else article.get("keywords", "")
                    category = ", ".join(article.get("category", [])) if isinstance(article.get("category"), list) else article.get("category", "")
                    
                    writer.writerow([
                        article.get("relevance", ""),
                        article.get("article_id", ""),
                        article.get("title", ""),
                        article.get("description", ""),
                        article.get("link", ""),
                        keywords,
                        category,
                        article.get("reasoning", "")
                    ])
            
            logger.info(f"Exported to CSV: {file_path}")
        except Exception as e:
            logger.error(f"CSV export error: {str(e)}")
            raise
    
    def _export_to_xlsx(self, results: List[Dict[str, Any]], file_path: str):
        """Export to Excel"""
        try:
            data = []
            for article in results:
                keywords = ", ".join(article.get("keywords", [])) if isinstance(article.get("keywords"), list) else article.get("keywords", "")
                category = ", ".join(article.get("category", [])) if isinstance(article.get("category"), list) else article.get("category", "")
                
                data.append({
                    "Relevance": article.get("relevance", ""),
                    "Article ID": article.get("article_id", ""),
                    "Title": article.get("title", ""),
                    "Description": article.get("description", ""),
                    "Link": article.get("link", ""),
                    "Keywords": keywords,
                    "Category": category,
                    "Reasoning": article.get("reasoning", "")
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"Exported to Excel: {file_path}")
        except Exception as e:
            logger.error(f"Excel export error: {str(e)}")
            raise
    
    def _cleanup_old_jobs(self):
        """Remove oldest jobs"""
        if len(self.jobs) <= self.max_jobs:
            return
        
        sorted_jobs = sorted(self.jobs.items(), key=lambda x: x[1].created_at)
        jobs_to_remove = len(self.jobs) - self.max_jobs
        
        for i in range(jobs_to_remove):
            job_id = sorted_jobs[i][0]
            self.delete_job(job_id)
            logger.info(f"Cleaned up job: {job_id}")    
    def _load_existing_results(self):
        """Load existing result files from disk on startup"""
        try:
            for filename in os.listdir("results"):
                if filename.endswith(".json"):
                    job_id = filename.replace(".json", "")
                    file_path = f"results/{filename}"
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Get file modification time
                        file_stat = os.stat(file_path)
                        modified_time = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        # Create job status from saved data
                        job = JobStatus(
                            job_id=job_id,
                            status="completed",
                            progress=100,
                            created_at=modified_time,
                            updated_at=modified_time,
                            query=data.get("query", "Unknown"),
                            total_articles=data.get("total_articles", len(data.get("articles", []))),
                            error=None,
                            results=data.get("articles", [])
                        )
                        
                        self.jobs[job_id] = job
                        
                    except Exception as e:
                        logger.error(f"Error loading result file {filename}: {str(e)}")
                        
            logger.info(f"Loaded {len(self.jobs)} existing results from disk")
        except Exception as e:
            logger.error(f"Error loading existing results: {str(e)}")