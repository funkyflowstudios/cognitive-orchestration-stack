"""ARIS Orchestration Graph

LangGraph workflow definition for the research pipeline.
"""

import logging
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from .nodes import Planner, Synthesizer, ToolExecutor, Validator
from .state import ResearchState

# from langgraph.checkpoint.memory import MemorySaver  # Unused import


logger = logging.getLogger(__name__)


def create_graph():
    """Creates the research graph."""
    graph = StateGraph(ResearchState)

    graph.add_node("planner", Planner.run)
    graph.add_node("tool_executor", ToolExecutor.run)
    graph.add_node("validator", Validator.run)
    graph.add_node("synthesizer", Synthesizer.run)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "tool_executor")
    graph.add_edge("tool_executor", "validator")
    graph.add_edge("validator", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Create the graph instance
aris_graph = create_graph()


def create_research_graph() -> StateGraph:
    """Create the ARIS research workflow graph.

    Returns:
        Configured StateGraph for research workflow
    """
    return create_graph()


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
    from .nodes import initialize_job

    if job_id is None:
        job_id = str(uuid.uuid4())

    logger.info(f"Starting research job {job_id} for topic: {topic}")

    # Create initial state
    initial_state = ResearchState(
        topic=topic,
        job_id=job_id,
        job_scratch_dir=Path(""),  # Will be set by initialize_job
    )

    # Initialize the job with proper scratch directory
    initial_state = initialize_job(initial_state)

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
                str(final_state.get("final_output_path"))
                if final_state.get("final_output_path")
                else None
            ),
            "sources_found": len(
                final_state.get("scraped_content_references", [])
            ),
            "validated_sources": len(
                [
                    ref
                    for ref in final_state.get("scraped_content_references",
    [])
                    if getattr(ref, "is_validated", False)
                ]
            ),
            "error": final_state.get("error_message"),
        }

        logger.info(f"Research job {job_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}")
        return {
            "job_id": job_id,
            "topic": topic,
            "status": "failed",
            "error": str(e),
        }
