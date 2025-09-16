"""Scraper Agent for ARIS

Handles content extraction and validation from web pages.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from utils.retry import retry
except ImportError:
    from src.utils.retry import retry

logger = logging.getLogger(__name__)


class WebScraperAgent:
    """Agent responsible for scraping and parsing web content."""

    @staticmethod
    @retry
    def scrape_and_parse(url: str, output_dir: Path) -> Path:
        """Scrapes a URL, parses its content to Markdown, and saves it."""
        print(f"-> Scraping: {url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        elements = partition_html(text=response.text)
        content = "\n\n".join([str(el) for el in elements])

        # Create a safer filename and ensure output_dir exists
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = (
            "".join(c if c.isalnum() or c in "._-" else "_" for c in url)[:100] + ".md"
        )
        output_path = output_dir / safe_filename
        output_path.write_text(content, encoding="utf-8")
        return output_path


class ScraperAgent:
    """Agent responsible for scraping and validating web content."""

    def __init__(self, timeout: int = 30):
        """Initialize the ScraperAgent.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            }
        )

    def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a single URL.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing scraped content and metadata, or None if
            failed
        """
        try:
            logger.info(f"Scraping URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract basic metadata
            title = soup.find("title")
            title_text = (
                title.get_text().strip() if title else "No title found"
            )

            # Use unstructured to extract clean text
            elements = partition_html(text=response.text)
            content_text = "\n".join([str(element) for element in elements])

            result = {
                "url": url,
                "title": title_text,
                "content": content_text,
                "status_code": response.status_code,
                "content_length": len(content_text),
            }

            logger.info(
                f"Successfully scraped {url}: "
                f"{len(content_text)} characters"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None

    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape content from multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of scraped content dictionaries
        """
        results = []
        for url in urls:
            result = self.scrape_url(url)
            if result:
                results.append(result)
        return results

    def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scraped content quality.

        Args:
            content: Scraped content dictionary

        Returns:
            Content dictionary with validation metadata added
        """
        validation_score = 0.0
        validation_notes = []

        # Check content length
        content_length = content.get("content_length", 0)
        if content_length > 1000:
            validation_score += 0.3
        elif content_length > 500:
            validation_score += 0.2
        else:
            validation_notes.append("Content too short")

        # Check for title
        if content.get("title") and content["title"] != "No title found":
            validation_score += 0.2
        else:
            validation_notes.append("No valid title found")

        # Check for meaningful content (basic heuristic)
        content_text = content.get("content", "")
        if len(content_text.split()) > 100:
            validation_score += 0.3
        else:
            validation_notes.append("Insufficient text content")

        # Check for common content indicators
        content_lower = content_text.lower()
        keywords = ["article", "research", "study", "analysis"]
        if any(keyword in content_lower for keyword in keywords):
            validation_score += 0.2
        else:
            validation_notes.append("No clear research content indicators")

        content["validation_score"] = validation_score
        content["validation_notes"] = (
            "; ".join(validation_notes)
            if validation_notes
            else "Content appears valid"
        )
        content["is_validated"] = validation_score >= 0.6

        return content
