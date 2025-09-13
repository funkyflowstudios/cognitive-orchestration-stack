from __future__ import annotations

"""LangGraph node implementations for the reasoning workflow."""

from typing import List

from langgraph.prebuilt import tool

from ..utils.logger import get_logger
from .state import AgentState
from src.tools.neo4j_agent import Neo4jAgent
from src.tools.chromadb_agent import ChromaDBAgent


logger = get_logger(__name__)


# --- Planner -----------------------------------------------------------------

def planner_node(state: AgentState) -> AgentState:  # noqa: D401
    """Create a naive execution plan (mock)."""

    logger.info("Planner received query: %s", state.query)
    plan: List[str] = ["vector_search"]
    logger.info("Generated plan: %s", plan)
    state.plan = plan
    return state


# --- Tool Executor -----------------------------------------------------------

neo4j_agent = Neo4jAgent()
chroma_agent = ChromaDBAgent()


def _graph_query(query: str) -> str:
    results = neo4j_agent.query("MATCH (n) RETURN n LIMIT 1")
    return str(results)


def _vector_search(query: str) -> str:
    ids = chroma_agent.similarity_search(query)
    return f"Top document IDs: {ids}"


def tool_executor_node(state: AgentState) -> AgentState:  # noqa: D401
    """Execute the current tool from the plan (mock implementation)."""

    if not state.plan:
        logger.warning("No plan available; skipping execution.")
        return state

    tool_name = state.plan[0]
    state.current_tool = tool_name

    logger.info("Executing tool: %s", tool_name)

    # Map tool names to functions
    tool_map = {
        "graph_query": _graph_query,
        "vector_search": _vector_search,
    }

    if tool_name in tool_map:
        state.tool_output = tool_map[tool_name](state.query)
    else:
        state.tool_output = f"Tool {tool_name} not implemented"

    logger.info("Tool output: %s", state.tool_output)
    return state


# --- Validator / Critique ----------------------------------------------------

def validation_critique_node(state: AgentState) -> AgentState:  # noqa: D401
    """Simple validation that approves everything unless 'error' in output."""

    output = state.tool_output or ""
    if "error" in output.lower():
        logger.info("Validation failed; re-planning.")
        state.iteration += 1
    else:
        logger.info("Validation passed.")
    return state


# --- Synthesizer -------------------------------------------------------------

def synthesizer_node(state: AgentState) -> AgentState:  # noqa: D401
    """Generate final answer by combining tool output (mock)."""

    state.response = state.tool_output or "No answer produced"
    logger.info("Synthesized response: %s", state.response)
    return state
