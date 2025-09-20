"""ARIS Orchestration Nodes

Individual processing nodes for the research pipeline.
"""

import sys
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..agents.scraper_agent import WebScraperAgent  # noqa: E402
from ..agents.search_agent import WebSearchAgent  # noqa: E402
from .state import ResearchState, ScrapedContent  # noqa: E402

try:
    from config import get_settings  # noqa: E402
    from utils.logger import get_logger  # noqa: E402
except ImportError:
    from src.utils.logger import get_logger  # noqa: E402
    from src.config import get_settings  # noqa: E402

import ollama  # noqa: E402

logger = get_logger(__name__)
settings = get_settings()

# Lazy initialization to avoid connection attempts during import
OLLAMA_CLIENT: ollama.Client | None = None


def _get_ollama_client():
    """Get or create Ollama client lazily."""
    global OLLAMA_CLIENT
    if OLLAMA_CLIENT is None:
        OLLAMA_CLIENT = ollama.Client(host=settings.ollama_host)
    return OLLAMA_CLIENT


class Planner:
    """Node that creates a research plan based on the topic."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        logger.info("--- Node: Planner ---")
        prompt = (
            f"You are a world-class research analyst. Create a comprehensive "
            f'research plan for the topic: "{state.topic}".\n'
            f"Generate a JSON object with two keys:\n"
            f'1. "research_plan": A detailed, step-by-step research strategy that covers '
            f"different aspects, perspectives, and depth levels of the topic.\n"
            f'2. "search_queries": A list of 6-8 diverse, high-quality search queries '
            f"that will gather comprehensive information. Include queries for:\n"
            f"   - General overview and basics\n"
            f"   - Specific tools, models, or technologies\n"
            f"   - Comparisons and reviews\n"
            f"   - Technical details and implementation\n"
            f"   - Professional use cases\n"
            f"   - Open source and free alternatives\n"
            f"   - Recent developments and trends\n"
            f"Use specific, targeted keywords and focus on English-language sources.\n"
            f"Return ONLY the raw JSON object."
        )

        try:
            response = _get_ollama_client().generate(settings.ollama_model, prompt)
            response_text = response.get("response", "")

            # Clean up response text to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            plan_json = yaml.safe_load(response_text)
            research_plan = plan_json.get("research_plan", {})
            # Ensure research_plan is a dict, not a list
            if isinstance(research_plan, list):
                research_plan = {"steps": research_plan}
            state.research_plan = research_plan
            search_queries = plan_json.get("search_queries", [])
            # Ensure search_queries are strings, not dicts
            if search_queries and isinstance(search_queries[0], dict):
                search_queries = [q.get("query", str(q)) for q in search_queries]
            state.search_queries = search_queries
        except Exception as e:
            logger.error(f"Error in Planner: {e}")
            # Fallback to better queries based on topic
            topic_lower = state.topic.lower()
            if "vst" in topic_lower or "plugin" in topic_lower:
                state.search_queries = [
                    "best VST plugins 2024 professional music production",
                    "top VST plugins used by music producers",
                    "most popular VST plugins music production",
                    "professional VST plugins review comparison",
                ]
            elif "music" in topic_lower:
                state.search_queries = [
                    f"best {state.topic} 2024",
                    f"top {state.topic} professional",
                    f"most popular {state.topic}",
                    f"{state.topic} review comparison",
                ]
            else:
                state.search_queries = [
                    f"best {state.topic} 2024",
                    f"top {state.topic} professional",
                    f"most popular {state.topic}",
                    f"{state.topic} review guide",
                ]
            state.research_plan = {
                "topic": state.topic,
                "approach": "fallback research with targeted queries",
            }

        return state


class ToolExecutor:
    """Node that executes the search and scrape tools."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        logger.info("--- Node: Tool Executor ---")
        all_urls = set()
        for query in state.search_queries:
            try:
                search_results = WebSearchAgent.run_search(query)
                for result in search_results:
                    if "href" in result:
                        all_urls.add(result["href"])
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")

        for url in all_urls:
            try:
                file_path = WebScraperAgent.scrape_and_parse(url, state.job_scratch_dir)
                state.scraped_content_references.append(
                    ScrapedContent(source_url=url, local_path=file_path)
                )
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}. Skipping.")

        return state


class Validator:
    """Node that validates the quality and relevance of scraped content."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        logger.info("--- Node: Validator ---")
        for content_ref in state.scraped_content_references:
            try:
                content = content_ref.local_path.read_text(encoding="utf-8")
                prompt = f"""You are a critical fact-checker. Analyze the following text scraped from {content_ref.source_url} for a report on "{state.topic}".

                Assess the text for:
                - Relevance to the specific topic: "{state.topic}"
                - Technical accuracy and detail
                - Objectivity and quality
                - Specific recommendations, comparisons, or actionable information
                - Depth of information provided

                Provide a JSON object with two keys:
                1. "validation_score": A float between 0.0 (poor) and 1.0 (excellent)
                2. "validation_notes": A brief, one-sentence justification for the score

                Return ONLY the raw JSON object.
                --- TEXT FOR ANALYSIS (first 4000 chars) ---
                {content[:4000]}
                """

                response = _get_ollama_client().generate(settings.ollama_model, prompt)
                response_text = response.get("response", "")

                # Clean up response text to extract JSON
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]

                # Try to extract JSON object more robustly
                import re
                import json

                # Look for JSON object with validation_score
                json_patterns = [
                    r'\{[^{}]*"validation_score"[^{}]*\}',  # Simple case
                    r'\{[^{}]*"validation_score"[^{}]*"validation_notes"[^{}]*\}',  # With notes
                    r'\{[^{}]*"validation_score"[^{}]*"validation_notes"[^{}]*\}',  # With notes
                ]

                validation_json = None
                for pattern in json_patterns:
                    match = re.search(pattern, response_text, re.DOTALL)
                    if match:
                        try:
                            validation_json = json.loads(match.group(0))
                            break
                        except json.JSONDecodeError:
                            continue

                # If no JSON found, try to parse the whole response
                if validation_json is None:
                    try:
                        validation_json = yaml.safe_load(response_text)
                    except Exception:
                        # Last resort: try to extract just the score and notes
                        score_match = re.search(r'"validation_score":\s*([0-9.]+)', response_text)
                        notes_match = re.search(r'"validation_notes":\s*"([^"]*)"', response_text)

                        validation_json = {
                            "validation_score": float(score_match.group(1)) if score_match else 0.0,
                            "validation_notes": notes_match.group(1) if notes_match else "Parsed from malformed response"
                        }
                content_ref.validation_score = validation_json.get(
                    "validation_score", 0.0
                )
                content_ref.validation_notes = validation_json.get(
                    "validation_notes", "Validation failed."
                )
                content_ref.is_validated = True
                logger.info(
                    f"-> Validated {content_ref.source_url} with score "
                    f"{content_ref.validation_score}"
                )
            except Exception as e:
                logger.error(f"Validation failed for {content_ref.source_url}: {e}")
                content_ref.validation_score = 0.0
                content_ref.validation_notes = f"Validation error: {str(e)}"
                content_ref.is_validated = False

        return state


class Synthesizer:
    """Node that synthesizes the validated information into a final article."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        logger.info("--- Node: Synthesizer ---")
        validated_sources = [
            c
            for c in state.scraped_content_references
            if c.validation_score and c.validation_score >= 0.3
        ]
        if not validated_sources:
            state.error_message = (
                "No high-quality content found to synthesize an article."
            )
            return state

        source_texts = [
            f"--- SOURCE: {c.source_url} ---\n"
            f"{c.local_path.read_text(encoding='utf-8')}"
            for c in validated_sources
        ]
        source_material = "\n\n".join(source_texts)

        prompt = f"""You are an expert technical writer. Create a comprehensive, well-structured Markdown article on the topic: "{state.topic}".

        CRITICAL REQUIREMENTS:
        - Create a THOROUGH, DETAILED article that is AT LEAST 2000-3000 words long
        - Use ALL the provided source material to create the most complete and informative article possible
        - Include specific details, technical information, and practical examples from the sources
        - Write in a professional, informative style suitable for technical readers

        MANDATORY STRUCTURE:
        1. Clear, descriptive title
        2. Introduction explaining the topic and its importance (300+ words)
        3. Multiple detailed sections covering different aspects (each section 400+ words):
           - Overview of available models/tools
           - Technical comparisons and specifications
           - Implementation details and requirements
           - Use cases and applications
           - Pros and cons analysis
           - Performance benchmarks and evaluations
        4. Specific recommendations and best practices
        5. Conclusion with key takeaways and future outlook (300+ words)

        INSTRUCTIONS:
        - Base your article ONLY on the provided source material
        - Extract and synthesize information from ALL sources
        - Include specific model names, technical specifications, and performance data
        - Provide practical implementation advice and code examples where available
        - Make the article comprehensive and valuable for both beginners and experts

        --- VALIDATED SOURCE TEXT (first 50000 chars) ---
        {source_material[:50000]}
        """

        try:
            response = _get_ollama_client().generate(settings.ollama_model, prompt)
            response_text = response.get("response", "")
            state.synthesized_article_markdown = response_text

            # Save synthesized content
            output_file = state.job_scratch_dir / "synthesized_article.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            state.final_output_path = output_file

        except Exception as e:
            logger.error(f"Error in Synthesizer: {e}")
            state.error_message = f"Synthesis failed: {str(e)}"

        return state


# Legacy functions for backward compatibility
def initialize_job(state: ResearchState) -> ResearchState:
    """Initialize a new research job with scratch directory."""
    logger.info(f"Initializing job {state.job_id} for topic: {state.topic}")

    # Create scratch directory within the project workspace
    project_root = Path(__file__).parent.parent.parent.parent
    scratch_base = project_root / "scratch"
    scratch_base.mkdir(exist_ok=True)

    scratch_dir = scratch_base / f"aris_{state.job_id}"
    state.job_scratch_dir = scratch_dir
    scratch_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created scratch directory: {scratch_dir}")
    return state


def plan_research(state: ResearchState) -> ResearchState:
    """Plan the research approach and generate search queries."""
    return Planner.run(state)


def execute_search(state: ResearchState) -> ResearchState:
    """Execute web searches using the search agent."""
    return ToolExecutor.run(state)


def scrape_content(state: ResearchState) -> ResearchState:
    """Scrape content from search results."""
    return ToolExecutor.run(state)


def synthesize_content(state: ResearchState) -> ResearchState:
    """Synthesize scraped content into a final article."""
    return Synthesizer.run(state)


def cleanup_job(state: ResearchState) -> ResearchState:
    """Clean up temporary files and finalize job."""
    logger.info(f"Cleaning up job {state.job_id}")
    logger.info(f"Job {state.job_id} completed successfully")
    logger.info(f"Final output: {state.final_output_path}")
    return state
