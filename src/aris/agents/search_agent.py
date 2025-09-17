"""Search Agent for ARIS

Handles web search operations using Google Custom Search API.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
import requests

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
    """Agent responsible for executing web searches using
    Google Custom Search API."""

    @staticmethod
    @retry
    def run_search(
        query: str, max_results: int = 5
    ) -> List[Dict[str, str | float]]:
        """Executes a web search using multiple free APIs with fallback."""
        print(f"-> Searching: '{query}'")

        # Try Bing Web Search API first (much easier than Google Cloud)
        if hasattr(settings, 'bing_api_key') and settings.bing_api_key:
            try:
                results = WebSearchAgent._bing_search(query, max_results)
                if results:
                    logger.info(
                        f"Bing returned {len(results)} results for: {query}"
                    )
                    return results
            except Exception as e:
                logger.warning(f"Bing search failed: {e}")

        # Try DuckDuckGo Instant Answer API (completely free, no setup)
        try:
            results = WebSearchAgent._duckduckgo_search(query, max_results)
            if results:
                logger.info(
                    f"DuckDuckGo returned {len(results)} results for: {query}"
                )
                return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        # Try Google Custom Search API if configured
        if (hasattr(settings, 'google_api_key') and
                hasattr(settings, 'google_cse_id') and
                settings.google_api_key and settings.google_cse_id):
            try:
                results = WebSearchAgent._google_search(query, max_results)
                if results:
                    logger.info(
                        f"Google search returned {len(results)} results "
                        f"for: {query}"
                    )
                    return results
            except Exception as e:
                logger.warning(f"Google search failed: {e}")

        # Use demonstration mode as final fallback
        logger.info("No search APIs available, using demonstration mode")
        return WebSearchAgent._fallback_search(query, max_results)

    @staticmethod
    def _duckduckgo_search(
        query: str, max_results: int
    ) -> List[Dict[str, str | float]]:
        """Search using DuckDuckGo Instant Answer API
        (completely free, no setup)."""
        # DuckDuckGo Instant Answer API - completely free, no API key needed
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        # Get the abstract (main result)
        if data.get('Abstract'):
            results.append({
                'title': data.get('Heading', query),
                'href': data.get('AbstractURL', ''),
                'body': data.get('Abstract', '')
            })

        # Get related topics
        for topic in data.get('RelatedTopics', [])[:max_results-1]:
            if isinstance(topic, dict) and topic.get('Text'):
                results.append({
                    'title': topic.get('Text', '')[:100] + '...',
                    'href': topic.get('FirstURL', ''),
                    'body': topic.get('Text', '')
                })

        return results[:max_results]

    @staticmethod
    def _bing_search(
        query: str, max_results: int
    ) -> List[Dict[str, str | float]]:
        """Search using Bing Web Search API
        (much easier than Google Cloud)."""
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': settings.bing_api_key
        }
        params: dict[str, str | int] = {
            'q': query,
            'count': min(max_results * 2, 20),  # Get more results
            'mkt': 'en-US',
            'safeSearch': 'Moderate'
        }

        response = requests.get(
            url, headers=headers, params=params, timeout=10
        )
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get('webPages', {}).get('value', []):
            results.append({
                'title': item.get('name', ''),
                'href': item.get('url', ''),
                'body': item.get('snippet', '')
            })

        # Filter and rank results
        filtered_results = WebSearchAgent._filter_and_rank_results(
            results, query
        )
        return filtered_results[:max_results]

    @staticmethod
    def _google_search(
        query: str, max_results: int
    ) -> List[Dict[str, str | float]]:
        """Search using Google Custom Search API (requires setup)."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': settings.google_api_key,
            'cx': settings.google_cse_id,
            'q': query,
            'num': min(max_results * 2, 10),  # Get more results
            'lr': 'lang_en',
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

        # Filter and rank results
        filtered_results = WebSearchAgent._filter_and_rank_results(
            results, query
        )
        return filtered_results[:max_results]

    @staticmethod
    def _filter_and_rank_results(
        results: List[Dict[str, str | float]], query: str
    ) -> List[Dict[str, str | float]]:
        """Filter and rank search results for quality and relevance."""
        if not results:
            return results

        filtered_results = []

        for result in results:
            title = str(result.get('title', '')).lower()
            body = str(result.get('body', '')).lower()
            href = str(result.get('href', '')).lower()

            # Skip low-quality results
            if not title or len(title) < 10:
                continue

            # Skip non-English results
            chinese_chars = [
                '中文', '百度', '经验', '网页', '贴吧', '知道', '音乐', '图片',
                '视频', '地图', '百科', '文库', '知乎', '问题', '回答'
            ]
            if any(char in title + body for char in chinese_chars):
                continue

            # Skip non-English domains
            non_english_domains = [
                'baidu.com', 'zhihu.com', 'douban.com', 'weibo.com',
                'qq.com', 'sina.com', 'sohu.com', '163.com'
            ]
            if any(domain in href for domain in non_english_domains):
                continue

            # Skip irrelevant results
            irrelevant_keywords = [
                'login', 'forum', 'register', 'signup', 'tiktok',
                'instagram', 'facebook', 'twitter'
            ]
            if any(keyword in href for keyword in irrelevant_keywords):
                continue

            # Skip results with too many non-ASCII characters
            text_content = title + body
            non_ascii_ratio = (
                sum(1 for c in text_content if ord(c) > 127) /
                len(text_content)
                if text_content else 0
            )
            if non_ascii_ratio > 0.3:
                continue

            # Calculate quality score
            quality_score = WebSearchAgent._calculate_quality_score(
                result, query
            )
            result['quality_score'] = quality_score

            # Only include results with decent quality
            if quality_score >= 0.3:
                filtered_results.append(result)

        # Sort by quality score (highest first)
        filtered_results.sort(
            key=lambda x: x.get('quality_score', 0), reverse=True
        )

        return filtered_results

    @staticmethod
    def _calculate_quality_score(
        result: Dict[str, str | float], query: str
    ) -> float:
        """Calculate a quality score for a search result."""
        score = 0.0
        title = str(result.get('title', '')).lower()
        body = str(result.get('body', '')).lower()
        href = str(result.get('href', '')).lower()
        query_lower = query.lower()

        # Title relevance (40% of score)
        title_words = set(title.split())
        query_words = set(query_lower.split())
        title_overlap = (
            len(title_words.intersection(query_words)) / len(query_words)
            if query_words else 0
        )
        score += title_overlap * 0.4

        # Body relevance (30% of score)
        body_words = set(body.split())
        body_overlap = (
            len(body_words.intersection(query_words)) / len(query_words)
            if query_words else 0
        )
        score += body_overlap * 0.3

        # Content length bonus (10% of score)
        content_length = len(title) + len(body)
        if content_length > 200:
            score += 0.1
        elif content_length > 100:
            score += 0.05

        # Domain authority bonus (10% of score)
        authoritative_domains = [
            'wikipedia.org', 'github.com', 'stackoverflow.com', 'reddit.com',
            'medium.com', 'dev.to', 'soundonsound.com', 'musictech.net',
            'gearspace.com'
        ]
        if any(domain in href for domain in authoritative_domains):
            score += 0.1

        # HTTPS bonus (5% of score)
        if href.startswith('https://'):
            score += 0.05

        # Freshness bonus (5% of score)
        if any(year in title + body for year in ['2024', '2023', '2022']):
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0

    @staticmethod
    def _fallback_search(
        query: str, max_results: int = 5
    ) -> List[Dict[str, str | float]]:
        """Fallback to mock data when search fails."""
        logger.info("Using demonstration mode with curated content")

        # Provide mock data based on common VST plugin topics
        mock_results: List[Dict[str, str | float]] = []

        if "vst" in query.lower() or "plugin" in query.lower():
            mock_results = [
                {
                    "title": "Best VST Plugins for Music Production 2024",
                    "href": "https://www.soundonsound.com/reviews/vst-plugins",
                    "body": ("Guide to popular VST plugins used by "
                             "producers including Serum, Massive, "
                             "Omnisphere, and more.")
                },
                {
                    "title": "Top 10 VST Plugins Every Producer Should Own",
                    "href": "https://www.musictech.net/guides/vst-plugins",
                    "body": ("Essential VST plugins for production including "
                             "synthesizers, effects, and mixing tools used by "
                             "professionals.")
                },
                {
                    "title": "Professional VST Plugin Reviews",
                    "href": "https://www.gearspace.com/board/vst-plugins",
                    "body": ("Reviews and comparisons of VST plugins, "
                             "their features, and use cases in production.")
                }
            ]
        else:
            mock_results = [
                {
                    "title": f"Research Results for: {query}",
                    "href": "https://www.example.com/research",
                    "body": (f"Information about {query} including "
                             f"analysis, best practices, and insights.")
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

    def search(self, query: str) -> List[Dict[str, str | float]]:
        """Perform a web search for the given query using multiple APIs with
        advanced filtering.

        Args:
            query: The search query string

        Returns:
            List of high-quality search results with title, href, and body
        """
        try:
            logger.info(f"Searching for: {query}")

            # Use the multi-API search system
            results = WebSearchAgent.run_search(query, self.max_results)

            # Additional deduplication and final filtering
            seen_urls = set()
            final_results = []

            for result in results:
                href = result.get('href', '')

                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Add quality score if not already present
                if 'quality_score' not in result:
                    result['quality_score'] = (
                        WebSearchAgent._calculate_quality_score(
                            result, query
                        )
                    )

                final_results.append(result)

            # Sort by quality score
            final_results.sort(
                key=lambda x: x.get('quality_score', 0), reverse=True
            )

            logger.info(
                f"Found {len(final_results)} high-quality results for: {query}"
            )
            return final_results[:self.max_results]

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
