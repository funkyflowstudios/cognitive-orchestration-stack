"""Search Agent for ARIS

Handles web search operations using DuckDuckGo search API.
"""

from typing import List, Dict, Any
import logging
from duckduckgo_search import DDGS
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.retry import retry

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """Agent responsible for executing web searches."""

    @staticmethod
    @retry
    def run_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Executes a web search and returns the results."""
        print(f"-> Searching: '{query}'")
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query, region='wt-wt', safesearch='off', timelimit='y'
            ))
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
            results = list(
                self.ddgs.text(query, max_results=self.max_results)
            )
            logger.info(
                f"Found {len(results)} results for query: {query}"
            )
            return results
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
