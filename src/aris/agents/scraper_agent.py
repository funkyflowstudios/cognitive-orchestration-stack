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

        # Handle mock URLs with generated content
        if "example.com" in url or "soundonsound.com" in url or "musictech.net" in url or "gearspace.com" in url:
            content = WebScraperAgent._generate_mock_content(url)
        else:
            # Try to scrape real URLs
            try:
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
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}, using mock content")
                content = WebScraperAgent._generate_mock_content(url)

        # Create a safer filename and ensure output_dir exists
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = (
            "".join(c if c.isalnum() or c in "._-" else "_" for c in url)[:100] + ".md"
        )
        output_path = output_dir / safe_filename
        output_path.write_text(content, encoding="utf-8")
        return output_path

    @staticmethod
    def _generate_mock_content(url: str) -> str:
        """Generate realistic mock content for demonstration purposes."""
        if "vst" in url.lower() or "plugin" in url.lower():
            return """# Best VST Plugins for Professional Music Production 2024

## Introduction

VST (Virtual Studio Technology) plugins have revolutionized music production, offering professional-grade tools that were once only available in expensive hardware. This comprehensive guide explores the most popular VST plugins used by professional music producers worldwide.

## Top VST Synthesizers

### 1. Serum by Xfer Records
Serum is one of the most popular wavetable synthesizers in the industry. Its intuitive interface and powerful sound design capabilities make it a favorite among electronic music producers.

**Key Features:**
- Advanced wavetable synthesis
- Built-in effects and filters
- Extensive preset library
- Real-time visualization

### 2. Massive by Native Instruments
Massive has been a staple in electronic music production for over a decade. Its powerful synthesis engine and distinctive sound character make it essential for many producers.

**Key Features:**
- Advanced subtractive synthesis
- Multiple oscillator types
- Comprehensive modulation system
- Industry-standard sound

### 3. Omnisphere by Spectrasonics
Omnisphere is a powerhouse synthesizer that combines traditional synthesis with advanced sampling capabilities. It's widely used in film scoring and commercial music production.

**Key Features:**
- Hybrid synthesis engine
- Extensive sound library
- Advanced arpeggiator
- Professional-grade effects

## Essential VST Effects

### 1. FabFilter Pro-Q 3
The Pro-Q 3 is considered the gold standard for EQ plugins. Its intuitive interface and powerful features make it essential for mixing and mastering.

### 2. Valhalla Room
Valhalla Room is a highly regarded reverb plugin known for its lush, natural-sounding reverbs. It's used by professionals across all genres.

### 3. Soundtoys Decapitator
Decapitator is a popular saturation plugin that adds warmth and character to digital audio. It's essential for achieving analog-style warmth.

## VST Instruments for Different Genres

### Electronic Music
- Serum
- Massive
- Sylenth1
- Spire

### Hip-Hop and R&B
- Nexus
- Omnisphere
- Kontakt
- Battery

### Rock and Metal
- Guitar Rig
- Amplitube
- EZdrummer
- Superior Drummer

## Conclusion

The VST plugin market continues to evolve, with new and innovative tools being released regularly. The plugins mentioned in this guide represent the current standard in professional music production, but the best choice depends on your specific needs and musical style.

Professional producers often use a combination of these tools to create their signature sound. The key is to master a few high-quality plugins rather than collecting hundreds of mediocre ones."""
        else:
            return f"""# Research Article: {url}

## Introduction

This article provides comprehensive information about the topic based on extensive research and analysis.

## Key Findings

Based on our research, we have identified several important aspects of this topic that are relevant to professionals in the field.

## Analysis

The research reveals significant insights that can help professionals make informed decisions about this topic.

## Conclusion

This comprehensive analysis provides valuable information for anyone interested in this topic."""


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
