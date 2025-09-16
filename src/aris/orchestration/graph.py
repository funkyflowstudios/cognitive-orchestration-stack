"""ARIS Orchestration Graph

LangGraph workflow definition for the research pipeline.
"""

from typing import Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ResearchState
from .nodes import (
    initialize_job,
    plan_research,
    execute_search,
    scrape_content,
    synthesize_content,
    cleanup_job
)

logger = logging.getLogger(__name__)


def create_research_graph() -> StateGraph:
    """Create the ARIS research workflow graph.

    Returns:
        Configured StateGraph for research workflow
    """
    logger.info("Creating ARIS research workflow graph")

    # Create the state graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("initialize", initialize_job)
    workflow.add_node("plan", plan_research)
    workflow.add_node("search", execute_search)
    workflow.add_node("scrape", scrape_content)
    workflow.add_node("synthesize", synthesize_content)
    workflow.add_node("cleanup", cleanup_job)

    # Define the workflow edges
    workflow.set_entry_point("initialize")

    workflow.add_edge("initialize", "plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "scrape")
    workflow.add_edge("scrape", "synthesize")
    workflow.add_edge("synthesize", "cleanup")
    workflow.add_edge("cleanup", END)

    # Compile the graph
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)

    logger.info("ARIS research workflow graph created successfully")
    return compiled_graph


def run_research_job(
    topic: str, job_id: Optional[str] = None
) -> Dict[str, Any]:
    """Run a complete research job using the ARIS workflow.

    Args:
        topic: The research topic
        job_id: Optional job ID (will be generated if not provided)

    Returns:
        Dictionary containing job results and metadata
    """
    import uuid
    from pathlib import Path

    if job_id is None:
        job_id = str(uuid.uuid4())

    logger.info(
        f"Starting research job {job_id} for topic: {topic}"
    )

    # Create initial state
    initial_state = ResearchState(
        topic=topic,
        job_id=job_id,
        job_scratch_dir=Path("")  # Will be set by initialize_job
    )

    # Create and run the graph
    graph = create_research_graph()

    try:
        # Run the workflow
        final_state = graph.invoke(initial_state)

        result = {
            "job_id": job_id,
            "topic": topic,
            "status": "completed",
            "output_path": (
                str(final_state.final_output_path)
                if final_state.final_output_path else None
            ),
            "sources_found": len(final_state.scraped_content_references),
            "validated_sources": len([
                ref for ref in final_state.scraped_content_references
                if ref.is_validated
            ]),
            "error": final_state.error_message
        }

        logger.info(f"Research job {job_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}")
        return {
            "job_id": job_id,
            "topic": topic,
            "status": "failed",
            "error": str(e)
        }
