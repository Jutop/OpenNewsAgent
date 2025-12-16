"""
AI Analyzer - Azure OpenAI integration
"""
import openai
from openai import AsyncAzureOpenAI
from typing import List, Dict, Any, Optional
import logging
import json
import re

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Analyze articles with OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None, 
                 is_azure: bool = False, api_version: Optional[str] = None):
        
        self.model = model
        self.is_azure = is_azure
        
        if is_azure:
            # Azure OpenAI configuration - using base_url like the original sync version
            api_version = api_version or "2024-10-21"
            azure_base_url = base_url or "https://api.openai.com/v1"
            
            self.client = AsyncAzureOpenAI(
                api_key=api_key,
                base_url=azure_base_url,
                api_version=api_version
            )
        else:
            # Standard OpenAI configuration
            if base_url:
                self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def analyze_articles(
        self,
        articles: List[Dict[str, Any]],
        query: str,
        extra_topics: Optional[str] = None,
        chunk_size: int = 15
    ) -> List[Dict[str, Any]]:
        """Analyze articles for relevance"""
        system_prompt = self._generate_system_prompt(query, extra_topics)
        
        logger.info(f"Analyzing {len(articles)} articles for: {query}")
        
        all_classified = []
        
        # Process in chunks
        for i in range(0, len(articles), chunk_size):
            chunk = articles[i:i + chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} articles)")
            
            try:
                classified = await self._analyze_chunk(chunk, system_prompt, query)
                all_classified.extend(classified)
            except Exception as e:
                logger.error(f"Error analyzing chunk: {str(e)}")
                continue
        
        # Sort by relevance
        relevance_order = {"Very Relevant": 0, "Relevant": 1, "Not Relevant": 2}
        all_classified.sort(key=lambda x: relevance_order.get(x.get("relevance", ""), 3))
        
        logger.info(f"Classified {len(all_classified)} articles")
        return all_classified
    
    def _generate_system_prompt(self, query: str, extra_topics: Optional[str]) -> str:
        """Generate dynamic prompt"""
        extra_info = f" Additional topics: {extra_topics}" if extra_topics else ""
        
        return f"""You are a news analyst for {query}. Analyze articles and classify their relevance.{extra_info}

**Classification:**
- **Very Relevant**: In-depth information about {query}, new developments, breakthroughs
- **Relevant**: Mention of {query} in relevant context, but not the main topic
- **Not Relevant**: Little to no connection to {query}

Return ALL articles in JSON format:
```json
[
  {{
    "article_id": "id",
    "title": "...",
    "link": "...",
    "description": "...",
    "keywords": [...],
    "category": [...],
    "relevance": "Very Relevant",
    "reasoning": "..."
  }}
]
```"""
    
    async def _analyze_chunk(
        self,
        articles: List[Dict[str, Any]],
        system_prompt: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Analyze a chunk of articles"""
        
        articles_text = self._format_articles(articles)
        
        user_prompt = f"""Analyze these articles for the topic "{query}":

{articles_text}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content
            if not response_text:
                logger.error("Empty response from AI")
                return []
                
            classified = self._extract_json(response_text.strip())
            
            return classified
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _format_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Format articles for prompt"""
        formatted = []
        for idx, article in enumerate(articles, 1):
            title = article.get("title", "No Title")
            link = article.get("link", "No Link")
            description = article.get("description", "No Description")
            keywords = article.get("keywords", [])
            category = article.get("category", [])
            
            keywords_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            category_str = ", ".join(category) if isinstance(category, list) else str(category)
            
            formatted.append(f"""Article {idx}:
Title: {title}
Link: {link}
Description: {description}
Keywords: {keywords_str}
Category: {category_str}
""")
        
        return "\n".join(formatted)
    
    def _extract_json(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract JSON from AI response"""
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                articles = json.loads(json_str)
                return articles
            else:
                articles = json.loads(response_text)
                return articles
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return []
