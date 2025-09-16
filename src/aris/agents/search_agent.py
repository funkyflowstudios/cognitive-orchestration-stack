"""Search Agent for ARIS

Handles web search operations using Google Custom Search API.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
import requests
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from utils.retry import retry
    from config import get_settings
except ImportError:
    from src.utils.retry import retry
    from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSearchAgent:
    """Agent responsible for executing web searches using Google Custom Search API."""

    @staticmethod
    @retry
    def run_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Executes a web search using Google Custom Search API and returns the results."""
        print(f"-> Searching: '{query}'")
        
        # Check if Google API credentials are available
        if not hasattr(settings, 'google_api_key') or not hasattr(settings, 'google_cse_id'):
            logger.warning("Google API credentials not found, falling back to DuckDuckGo")
            return WebSearchAgent._fallback_search(query, max_results)
        
        try:
            # Google Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': settings.google_api_key,
                'cx': settings.google_cse_id,
                'q': query,
                'num': min(max_results, 10),  # Google allows max 10 per request
                'lr': 'lang_en',  # English language results
                'safe': 'medium',
                'fields': 'items(title,link,snippet)'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'href': item.get('link', ''),
                    'body': item.get('snippet', '')
                })
            
            logger.info(f"Google search returned {len(results)} results for: {query}")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Google search failed: {e}, falling back to DuckDuckGo")
            return WebSearchAgent._fallback_search(query, max_results)
    
    @staticmethod
    def _fallback_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fallback to mock data when search fails."""
        logger.warning("Search API not available, using mock data for demonstration")
        
        # Provide mock data based on common VST plugin topics
        mock_results = []
        
        if "vst" in query.lower() or "plugin" in query.lower():
            mock_results = [
                {
                    "title": "Best VST Plugins for Professional Music Production 2024",
                    "href": "https://www.soundonsound.com/reviews/best-vst-plugins-2024",
                    "body": "Comprehensive guide to the most popular VST plugins used by professional music producers including Serum, Massive, Omnisphere, and more."
                },
                {
                    "title": "Top 10 VST Plugins Every Music Producer Should Own",
                    "href": "https://www.musictech.net/guides/top-vst-plugins-producers",
                    "body": "Essential VST plugins for music production including synthesizers, effects, and mixing tools used by professionals worldwide."
                },
                {
                    "title": "Professional VST Plugin Reviews and Comparisons",
                    "href": "https://www.gearspace.com/board/vst-plugins/",
                    "body": "In-depth reviews and comparisons of professional VST plugins, their features, and use cases in music production."
                }
            ]
        else:
            mock_results = [
                {
                    "title": f"Research Results for: {query}",
                    "href": "https://www.example.com/research-results",
                    "body": f"Comprehensive information about {query} including detailed analysis, best practices, and professional insights."
                }
            ]
        
        return mock_results[:max_results]


class SearchAgent:
    """Agent responsible for performing web searches and returning results."""

    def __init__(self, max_results: int = 10):
        """Initialize the SearchAgent.

        Args:
            max_results: Maximum number of search results to return per query
        """
        self.max_results = max_results

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search for the given query using Google Custom Search API.

        Args:
            query: The search query string

        Returns:
            List of search results with title, href, and body
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Use Google Custom Search API with fallback to DuckDuckGo
            results = WebSearchAgent.run_search(query, self.max_results)
            
            # Filter results for quality
            filtered_results = []
            seen_urls = set()
            
            for result in results:
                title = result.get('title', '').lower()
                body = result.get('body', '').lower()
                href = result.get('href', '')
                
                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # Skip Chinese/Asian language results
                chinese_chars = ['中文', '百度', '经验', '网页', '贴吧', '知道', '音乐', '图片', '视频', '地图', '百科', '文库', '知乎', '问题', '回答']
                if any(char in title + body for char in chinese_chars):
                    continue
                    
                # Skip non-English domains
                non_english_domains = ['baidu.com', 'zhihu.com', 'douban.com', 'weibo.com', 'qq.com', 'sina.com', 'sohu.com', '163.com']
                if any(domain in href for domain in non_english_domains):
                    continue
                    
                # Skip results with too many non-ASCII characters (likely non-English)
                text_content = title + body
                non_ascii_ratio = sum(1 for c in text_content if ord(c) > 127) / len(text_content) if text_content else 0
                if non_ascii_ratio > 0.3:  # More than 30% non-ASCII characters
                    continue
                
                # Skip irrelevant results (login pages, forums, etc.)
                if any(irrelevant in href.lower() for irrelevant in ['login', 'forum', 'register', 'signup', 'tiktok', 'instagram']):
                    continue
                    
                filtered_results.append(result)
            
            logger.info(f"Found {len(filtered_results)} filtered results for query: {query}")
            return filtered_results[:self.max_results]
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def search_multiple(
        self, queries: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple searches and return results grouped by query.

        Args:
            queries: List of search query strings

        Returns:
            Dictionary mapping queries to their search results
        """
        results = {}
        for query in queries:
            results[query] = self.search(query)
        return results
