"""
News Fetcher - NewsData.io API integration
"""
import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    """Fetch news from NewsData.io"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1/news"
        
    async def fetch_articles(
        self,
        query: str,
        languages: List[str],
        categories: List[str],
        size: int = 10,
        max_pages: int = 10,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """Fetch articles with pagination"""
        all_articles = []
        page_count = 0
        next_page = None
        
        language_str = ",".join(languages)
        category_str = ",".join(categories)
        
        logger.info(f"Fetching: query='{query}', lang={language_str}, cat={category_str}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while page_count < max_pages:
                try:
                    params = {
                        "apikey": self.api_key,
                        "q": query,
                        "language": language_str,
                        "category": category_str,
                        "size": size,
                        "prioritydomain": "top"
                    }
                    
                    if next_page:
                        params["page"] = next_page
                    
                    logger.info(f"Fetching page {page_count + 1}...")
                    
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data.get("status") == "error":
                        error_msg = data.get("results", {}).get("message", "Unknown error")
                        raise Exception(f"API error: {error_msg}")
                    
                    results = data.get("results", [])
                    if not results:
                        break
                    
                    all_articles.extend(results)
                    logger.info(f"Fetched {len(results)} articles (total: {len(all_articles)})")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        logger.info(f"Calling progress callback with {len(all_articles)} articles")
                        await progress_callback(len(all_articles))
                    
                    next_page = data.get("nextPage")
                    if not next_page:
                        break
                    
                    page_count += 1
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error: {e.response.status_code}")
                    raise Exception(f"HTTP {e.response.status_code}")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
                    raise
        
        # Remove duplicates
        unique_articles = self._remove_duplicates(all_articles)
        logger.info(f"Removed {len(all_articles) - len(unique_articles)} duplicates")
        
        return unique_articles
    
    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles by link"""
        seen_links = set()
        unique = []
        
        for article in articles:
            link = article.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique.append(article)
        
        return unique
