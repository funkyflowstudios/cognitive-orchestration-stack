# In agent_stack/src/orchestration/graph.py

from __future__ import annotations
from langgraph.graph import StateGraph
from .state import AgentState
from .nodes import (
    planner_node,
    tool_executor_node,
    validation_critique_node,
    synthesizer_node,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _edge_selector(state: AgentState) -> str:
    """Route based on iteration count to prevent infinite loops."""
    if state.iteration > 2:
        logger.warning("Max iterations reached. Finishing.")
        return "finish"
    logger.info("Plan execution complete. Proceeding to synthesize.")
    return "synth"


# Single unified graph that handles both sync and async nodes
builder = StateGraph(AgentState)
builder.add_node("planner", planner_node)
builder.add_node("executor", tool_executor_node)
builder.add_node("validator", validation_critique_node)
builder.add_node("synthesizer", synthesizer_node)

builder.set_entry_point("planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "validator")

builder.add_conditional_edges(
    "validator",
    _edge_selector,
    {"synth": "synthesizer", "finish": "__end__"},
)
builder.add_edge("synthesizer", "__end__")

# Single graph that can be invoked with either .invoke() or .ainvoke()
GRAPH = builder.compile()
