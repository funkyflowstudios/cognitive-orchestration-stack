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
        print("--- Node: Planner ---")
        prompt = (
            f"You are a world-class research analyst. Create a structured "
            f"research plan for the topic: \"{state.topic}\".\n"
            f"Generate a JSON object with two keys:\n"
            f"1. \"research_plan\": A concise, step-by-step plan.\n"
            f"2. \"search_queries\": A list of 4 high-quality, diverse search "
            f"engine queries to execute this plan. Use specific, targeted "
            f"keywords and include terms like \"best\", \"top\", \"popular\", "
            f"\"professional\", \"review\" to get better search results. "
            f"Focus on English-language sources.\n"
            f"Return ONLY the raw JSON object."
        )

        try:
            response = _get_ollama_client().generate(
                settings.ollama_model, prompt
            )
            response_text = response.get("response", "")

            # Clean up response text to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[
                    0
                ]
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
                search_queries = [
                    q.get("query", str(q)) for q in search_queries
                ]
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
                    "professional VST plugins review comparison"
                ]
            elif "music" in topic_lower:
                state.search_queries = [
                    f"best {state.topic} 2024",
                    f"top {state.topic} professional",
                    f"most popular {state.topic}",
                    f"{state.topic} review comparison"
                ]
            else:
                state.search_queries = [
                    f"best {state.topic} 2024",
                    f"top {state.topic} professional",
                    f"most popular {state.topic}",
                    f"{state.topic} review guide"
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
        print("--- Node: Tool Executor ---")
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
                file_path = WebScraperAgent.scrape_and_parse(
                    url, state.job_scratch_dir
                )
                state.scraped_content_references.append(
                    ScrapedContent(source_url=url, local_path=file_path)
                )
            except Exception as e:
                print(f"Failed to scrape {url}: {e}. Skipping.")

        return state


class Validator:
    """Node that validates the quality and relevance of scraped content."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        print("--- Node: Validator ---")
        for content_ref in state.scraped_content_references:
            try:
                content = content_ref.local_path.read_text(encoding="utf-8")
                prompt = \
    f"""You are a critical fact-checker. Analyze the following text scraped from {content_ref.source_url} for a report on "{state.topic}".  # noqa: E501
                Assess the text for relevance, objectivity, and \
    quality. Provide a JSON object with two keys:  # noqa: E501
                1. "validation_score": A float between 0.0 (poor) and \
    1.0 (excellent).  # noqa: E501
                2. "validation_notes": A brief,
    one-sentence justification for the score.  # noqa: E501
                Return ONLY the raw JSON object.
                --- TEXT FOR ANALYSIS (first 4000 chars) ---
                {content[:4000]}
                """

                response = _get_ollama_client().generate(
                    settings.ollama_model, prompt
                )
                response_text = response.get("response", "")

                # Clean up response text to extract JSON
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split(
                        "```"
                    )[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[
                        0
                    ]

                validation_json = yaml.safe_load(response_text)
                content_ref.validation_score = validation_json.get(
                    "validation_score", 0.0
                )
                content_ref.validation_notes = validation_json.get(
                    "validation_notes", "Validation failed."
                )
                content_ref.is_validated = True
                print(
                    f"-> Validated {content_ref.source_url} with score "
                    f"{content_ref.validation_score}"
                )
            except Exception as e:
                logger.error(
                    f"Validation failed for {content_ref.source_url}: {e}"
                )
                content_ref.validation_score = 0.0
                content_ref.validation_notes = f"Validation error: {str(e)}"
                content_ref.is_validated = False

        return state


class Synthesizer:
    """Node that synthesizes the validated information into a final article."""

    @staticmethod
    def run(state: ResearchState) -> ResearchState:
        print("--- Node: Synthesizer ---")
        validated_sources = [
            c
            for c in state.scraped_content_references
            if c.validation_score and c.validation_score >= 0.5
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

        prompt = \
    f"""You are an expert writer. Synthesize the provided source material into a comprehensive,
    well-structured Markdown article on the topic: "{state.topic}".  # noqa: E501
        Base your article ONLY on the provided information. Structure it with a title, introduction, body, and \
    \
    \
    \
    conclusion.  # noqa: E501
        --- VALIDATED SOURCE TEXT (first 15000 chars) ---
        {source_material[:15000]}
        """

        try:
            response = _get_ollama_client().generate(
                settings.ollama_model, prompt
            )
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
