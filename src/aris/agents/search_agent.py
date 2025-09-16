"""Search Agent for ARIS

Handles web search operations using DuckDuckGo search API.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from duckduckgo_search import DDGS

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from utils.retry import retry
except ImportError:
    from src.utils.retry import retry

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """Agent responsible for executing web searches."""

    @staticmethod
    @retry
    def run_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Executes a web search and returns the results."""
        print(f"-> Searching: '{query}'")
        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query, region="wt-wt", safesearch="off", timelimit="y"
                )
            )
            return results[:max_results]


class SearchAgent:
    """Agent responsible for performing web searches and returning results."""

    def __init__(self, max_results: int = 10):
        """Initialize the SearchAgent.

        Args:
            max_results: Maximum number of search results to return per query
        """
        self.max_results = max_results
        self.ddgs = DDGS()

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search for the given query.

        Args:
            query: The search query string

        Returns:
            List of search results with title, href, and body
        """
        try:
            logger.info(f"Searching for: {query}")
            # Add language filter to get English results
            results = list(self.ddgs.text(
                query,
                max_results=self.max_results,
                region="us-en",  # US English region
                safesearch="moderate"
            ))

            # Filter out non-English results
            english_results = []
            for result in results:
                title = result.get('title', '').lower()
                body = result.get('body', '').lower()
                href = result.get('href', '')

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

                english_results.append(result)

            logger.info(f"Found {len(english_results)} English results for query: {query}")
            return english_results
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
