"""ARIS Orchestration Nodes

Individual processing nodes for the research pipeline.
"""

import logging
from pathlib import Path
import tempfile

from .state import ResearchState, ScrapedContent
from ..agents.search_agent import SearchAgent
from ..agents.scraper_agent import ScraperAgent

logger = logging.getLogger(__name__)


def initialize_job(state: ResearchState) -> ResearchState:
    """Initialize a new research job with scratch directory.

    Args:
        state: Current research state

    Returns:
        Updated state with initialized job directory
    """
    logger.info(
        f"Initializing job {state.job_id} for topic: {state.topic}"
    )

    # Create scratch directory
    scratch_dir = Path(
        tempfile.mkdtemp(prefix=f"aris_{state.job_id}_")
    )
    state.job_scratch_dir = scratch_dir
    scratch_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Created scratch directory: {scratch_dir}")
    return state


def plan_research(state: ResearchState) -> ResearchState:
    """Plan the research approach and generate search queries.

    Args:
        state: Current research state

    Returns:
        Updated state with research plan and search queries
    """
    logger.info(f"Planning research for topic: {state.topic}")

    # Generate search queries based on the topic
    base_queries = [
        f"{state.topic} overview",
        f"{state.topic} research",
        f"{state.topic} analysis",
        f"{state.topic} best practices",
        f"{state.topic} trends"
    ]

    state.search_queries = base_queries
    state.research_plan = {
        "topic": state.topic,
        "approach": "comprehensive web research",
        "queries": base_queries,
        "expected_sources": len(base_queries) * 5  # Estimate
    }

    logger.info(f"Generated {len(base_queries)} search queries")
    return state


def execute_search(state: ResearchState) -> ResearchState:
    """Execute web searches using the search agent.

    Args:
        state: Current research state

    Returns:
        Updated state with search results
    """
    logger.info(
        f"Executing searches for {len(state.search_queries)} queries"
    )

    search_agent = SearchAgent(max_results=5)
    search_results = search_agent.search_multiple(state.search_queries)

    # Store search results in scratch directory
    results_file = state.job_scratch_dir / "search_results.json"
    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(search_results, f, indent=2, ensure_ascii=False)

    logger.info(f"Search completed, results saved to {results_file}")
    return state


def scrape_content(state: ResearchState) -> ResearchState:
    """Scrape content from search results.

    Args:
        state: Current research state

    Returns:
        Updated state with scraped content references
    """
    logger.info("Starting content scraping phase")

    # Load search results
    results_file = state.job_scratch_dir / "search_results.json"
    if not results_file.exists():
        logger.error("No search results found")
        state.error_message = "No search results available for scraping"
        return state

    import json
    with open(results_file, 'r', encoding='utf-8') as f:
        search_results = json.load(f)

    # Extract URLs from search results
    urls = []
    for query_results in search_results.values():
        for result in query_results:
            if 'href' in result:
                urls.append(result['href'])

    # Scrape content
    scraper_agent = ScraperAgent()
    scraped_content = scraper_agent.scrape_multiple(urls)

    # Create content references
    content_references = []
    for i, content in enumerate(scraped_content):
        if content:  # Only process successful scrapes
            # Save content to file
            content_file = state.job_scratch_dir / f"content_{i}.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content['content'])

            # Validate content
            validated_content = scraper_agent.validate_content(content)

            # Create reference
            reference = ScrapedContent(
                source_url=content['url'],
                local_path=content_file,
                validation_score=validated_content.get('validation_score'),
                validation_notes=validated_content.get('validation_notes'),
                is_validated=validated_content.get('is_validated', False)
            )
            content_references.append(reference)

    state.scraped_content_references = content_references
    logger.info(f"Scraped {len(content_references)} content pieces")

    return state


def synthesize_content(state: ResearchState) -> ResearchState:
    """Synthesize scraped content into a final article.

    Args:
        state: Current research state

    Returns:
        Updated state with synthesized article
    """
    logger.info("Starting content synthesis")

    if not state.scraped_content_references:
        logger.error("No content to synthesize")
        state.error_message = "No valid content found for synthesis"
        return state

    # Read all validated content
    content_pieces = []
    for ref in state.scraped_content_references:
        if ref.is_validated and ref.local_path.exists():
            with open(ref.local_path, 'r', encoding='utf-8') as f:
                content_pieces.append(f.read())

    if not content_pieces:
        logger.error("No validated content found")
        state.error_message = "No validated content available for synthesis"
        return state

    # Simple synthesis (in a real implementation, this would use an LLM)
    synthesized_content = f"# Research Report: {state.topic}\n\n"
    synthesized_content += (
        f"## Overview\n\nThis report synthesizes findings from "
        f"{len(content_pieces)} sources.\n\n"
    )

    for i, content in enumerate(content_pieces[:3]):  # Limit to first 3
        synthesized_content += f"## Source {i+1}\n\n{content[:500]}...\n\n"

    synthesized_content += (
        f"\n## Summary\n\nResearch completed on {state.topic} with "
        f"{len(content_pieces)} validated sources."
    )

    state.synthesized_article_markdown = synthesized_content

    # Save synthesized content
    output_file = state.job_scratch_dir / "synthesized_article.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(synthesized_content)

    state.final_output_path = output_file
    logger.info(f"Synthesis completed, saved to {output_file}")

    return state


def cleanup_job(state: ResearchState) -> ResearchState:
    """Clean up temporary files and finalize job.

    Args:
        state: Current research state

    Returns:
        Updated state with cleanup completed
    """
    logger.info(f"Cleaning up job {state.job_id}")

    # In a production system, you might want to archive results
    # or move them to a permanent location
    logger.info(f"Job {state.job_id} completed successfully")
    logger.info(f"Final output: {state.final_output_path}")

    return state
