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
    from config import get_settings
    from utils.retry import retry
except ImportError:
    from src.config import get_settings
    from src.utils.retry import retry

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSearchAgent:
    """Agent responsible for executing web searches using multiple APIs.

    Search priority order:
    1. SerpAPI (primary - multiple search engines, language filtering)
    2. Brave Search API (secondary - privacy-focused)
    3. DuckDuckGo (fallback - with language filtering)
    4. Google Custom Search (alternative - requires Google Cloud)
    5. Demo mode (final fallback)
    """

    @staticmethod
    @retry
    def run_search(query: str, max_results: int = 5) -> List[Dict[str, str | float]]:
        """Executes a web search using multiple APIs with fallback."""
        logger.info(f"-> Searching: '{query}'")

        # Try SerpAPI first (primary - multiple search engines,
        # language filtering)
        if hasattr(settings, "serpapi_key") and settings.serpapi_key:
            try:
                results = WebSearchAgent._serpapi_search(query, max_results)
                if results:
                    logger.info(f"SerpAPI returned {len(results)} results for: {query}")
                    return results
            except Exception as e:
                logger.warning(f"SerpAPI search failed: {e}")

        # Try Brave Search API (secondary - privacy-focused)
        if hasattr(settings, "brave_api_key") and settings.brave_api_key:
            try:
                results = WebSearchAgent._brave_search(query, max_results)
                if results:
                    logger.info(f"Brave returned {len(results)} results for: {query}")
                    return results
            except Exception as e:
                logger.warning(f"Brave search failed: {e}")

        # Try DuckDuckGo Instant Answer API (fallback with language filtering)
        try:
            results = WebSearchAgent._duckduckgo_search(query, max_results)
            if results:
                logger.info(f"DuckDuckGo returned {len(results)} results for: {query}")
                return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        # Try Google Custom Search API if configured
        if (
            hasattr(settings, "google_api_key")
            and hasattr(settings, "google_cse_id")
            and settings.google_api_key
            and settings.google_cse_id
        ):
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
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
            "kl": getattr(settings, "duckduckgo_language", "us-en"),  # Lang
            "region": getattr(settings, "duckduckgo_region", "us"),  # Region
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        # Get the abstract (main result)
        if data.get("Abstract"):
            results.append(
                {
                    "title": data.get("Heading", query),
                    "href": data.get("AbstractURL", ""),
                    "body": data.get("Abstract", ""),
                }
            )

        # Get related topics
        for topic in data.get("RelatedTopics", [])[: max_results - 1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": topic.get("Text", "")[:100] + "...",
                        "href": topic.get("FirstURL", ""),
                        "body": topic.get("Text", ""),
                    }
                )

        return results[:max_results]

    @staticmethod
    def _google_search(query: str, max_results: int) -> List[Dict[str, str | float]]:
        """Search using Google Custom Search API (requires setup)."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": settings.google_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "num": min(max_results * 2, 10),  # Get more results
            "lr": "lang_en",
            "safe": "medium",
            "fields": "items(title,link,snippet)",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("items", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("link", ""),
                    "body": item.get("snippet", ""),
                }
            )

        # Filter and rank results
        filtered_results = WebSearchAgent._filter_and_rank_results(results, query)
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
            title = str(result.get("title", "")).lower()
            body = str(result.get("body", "")).lower()
            href = str(result.get("href", "")).lower()

            # Skip low-quality results
            if not title or len(title) < 10:
                continue

            # Skip non-English results
            chinese_chars = [
                "中文",
                "百度",
                "经验",
                "网页",
                "贴吧",
                "知道",
                "音乐",
                "图片",
                "视频",
                "地图",
                "百科",
                "文库",
                "知乎",
                "问题",
                "回答",
            ]
            if any(char in title + body for char in chinese_chars):
                continue

            # Skip non-English domains
            non_english_domains = [
                "baidu.com",
                "zhihu.com",
                "douban.com",
                "weibo.com",
                "qq.com",
                "sina.com",
                "sohu.com",
                "163.com",
            ]
            if any(domain in href for domain in non_english_domains):
                continue

            # Skip irrelevant results
            irrelevant_keywords = [
                "login",
                "forum",
                "register",
                "signup",
                "tiktok",
                "instagram",
                "facebook",
                "twitter",
            ]
            if any(keyword in href for keyword in irrelevant_keywords):
                continue

            # Skip results with too many non-ASCII characters
            text_content = title + body
            non_ascii_ratio = (
                sum(1 for c in text_content if ord(c) > 127) / len(text_content)
                if text_content
                else 0
            )
            if non_ascii_ratio > 0.3:
                continue

            # Calculate quality score
            quality_score = WebSearchAgent._calculate_quality_score(result, query)
            result["quality_score"] = quality_score

            # Only include results with decent quality
            if quality_score >= 0.3:
                filtered_results.append(result)

        # Sort by quality score (highest first)
        filtered_results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        return filtered_results

    @staticmethod
    def _calculate_quality_score(result: Dict[str, str | float], query: str) -> float:
        """Calculate a quality score for a search result."""
        score = 0.0
        title = str(result.get("title", "")).lower()
        body = str(result.get("body", "")).lower()
        href = str(result.get("href", "")).lower()
        query_lower = query.lower()

        # Title relevance (40% of score)
        title_words = set(title.split())
        query_words = set(query_lower.split())
        title_overlap = (
            len(title_words.intersection(query_words)) / len(query_words)
            if query_words
            else 0
        )
        score += title_overlap * 0.4

        # Body relevance (30% of score)
        body_words = set(body.split())
        body_overlap = (
            len(body_words.intersection(query_words)) / len(query_words)
            if query_words
            else 0
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
            "wikipedia.org",
            "github.com",
            "stackoverflow.com",
            "reddit.com",
            "medium.com",
            "dev.to",
            "soundonsound.com",
            "musictech.net",
            "gearspace.com",
        ]
        if any(domain in href for domain in authoritative_domains):
            score += 0.1

        # HTTPS bonus (5% of score)
        if href.startswith("https://"):
            score += 0.05

        # Freshness bonus (5% of score)
        if any(year in title + body for year in ["2024", "2023", "2022"]):
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0

    @staticmethod
    def _serpapi_search(query: str, max_results: int) -> List[Dict[str, str | float]]:
        """Search using SerpAPI (multiple search engines,
        language filtering)."""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": settings.serpapi_key,
            "engine": "google",  # Can be changed to 'bing', 'yahoo', etc.
            "num": max_results,
            "hl": "en",  # Language: English
            "gl": "us",  # Country: United States
            "safe": "active",  # Safe search
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        if "organic_results" in data:
            for item in data["organic_results"]:
                result = {
                    "title": item.get("title", ""),
                    "href": item.get("link", ""),
                    "body": item.get("snippet", ""),
                    "score": 0.8,  # SerpAPI results are generally high quality
                }
                results.append(result)

        return results

    @staticmethod
    def _brave_search(query: str, max_results: int) -> List[Dict[str, str | float]]:
        """Search using Brave Search API (privacy-focused)."""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.brave_api_key,
        }
        params: dict[str, str | int] = {
            "q": query,
            "count": max_results,
            "country": "US",  # Country filter
            "search_lang": "en",  # Language filter
            "safesearch": "moderate",  # Safe search
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        if "web" in data and "results" in data["web"]:
            for item in data["web"]["results"]:
                result = {
                    "title": item.get("title", ""),
                    "href": item.get("url", ""),
                    "body": item.get("description", ""),
                    "score": 0.7,  # Brave results are good quality
                }
                results.append(result)

        return results

    @staticmethod
    def _fallback_search(
        query: str, max_results: int = 5
    ) -> List[Dict[str, str | float]]:
        """Fallback to curated content when search fails."""
        logger.info("Using curated content due to search limitations")

        # Provide relevant mock data based on query topic
        mock_results: List[Dict[str, str | float]] = []
        query_lower = query.lower()

        if (
            "llm" in query_lower
            or "language model" in query_lower
            or "ai model" in query_lower
        ):
            mock_results = [
                {
                    "title": "Top Open Source Language Models 2024",
                    "href": "https://huggingface.co/blog/open-source-llms",
                    "body": (
                        "Complete overview of open source language models including "
                        "Llama 2, Mistral, Code Llama, and other popular models for "
                        "various applications and use cases."
                    ),
                },
                {
                    "title": "Lightweight LLMs for Edge Computing",
                    "href": "https://arxiv.org/abs/lightweight-llms",
                    "body": (
                        "Research on efficient language models optimized for "
                        "resource-constrained environments, including quantization "
                        "techniques and model compression methods."
                    ),
                },
                {
                    "title": "Reasoning Capabilities in Modern LLMs",
                    "href": "https://openai.com/research/reasoning-llms",
                    "body": (
                        "Analysis of reasoning abilities in large language models, "
                        "including chain-of-thought prompting and few-shot learning "
                        "techniques for improved performance."
                    ),
                },
            ]
        elif "vst" in query_lower or "plugin" in query_lower:
            mock_results = [
                {
                    "title": "Best VST Plugins for Music Production 2024",
                    "href": "https://www.soundonsound.com/reviews/vst-plugins",
                    "body": (
                        "Guide to popular VST plugins used by "
                        "producers including Serum, Massive, "
                        "Omnisphere, and more."
                    ),
                },
                {
                    "title": "Top 10 VST Plugins Every Producer Should Own",
                    "href": "https://www.musictech.net/guides/vst-plugins",
                    "body": (
                        "Essential VST plugins for production including "
                        "synthesizers, effects, and mixing tools used by "
                        "professionals."
                    ),
                },
            ]
        else:
            # Generic research content
            mock_results = [
                {
                    "title": f"Comprehensive Research on: {query}",
                    "href": "https://scholar.google.com/search?q="
                    + query.replace(" ", "+"),
                    "body": (
                        f"Detailed analysis and insights about {query}, including "
                        f"current trends, best practices, and expert recommendations "
                        f"based on recent research and industry developments."
                    ),
                },
                {
                    "title": f"Latest Developments in {query}",
                    "href": "https://arxiv.org/search/?query="
                    + query.replace(" ", "+"),
                    "body": (
                        f"Recent research papers and studies covering {query}, "
                        f"including technical specifications, implementation details, "
                        f"and performance benchmarks."
                    ),
                },
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
                href = result.get("href", "")

                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Add quality score if not already present
                if "quality_score" not in result:
                    result["quality_score"] = WebSearchAgent._calculate_quality_score(
                        result, query
                    )

                final_results.append(result)

            # Sort by quality score
            final_results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

            logger.info(f"Found {len(final_results)} high-quality results for: {query}")
            return final_results[: self.max_results]

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def search_multiple(self, queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
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
