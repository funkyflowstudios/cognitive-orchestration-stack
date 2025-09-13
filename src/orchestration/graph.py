from __future__ import annotations

"""LangGraph state machine assembly."""

from langgraph.graph import StateGraph

from .nodes import (
    planner_node,
    tool_executor_node,
    validation_critique_node,
    synthesizer_node,
)
from .state import AgentState

# Build the StateGraph
builder: StateGraph[AgentState] = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("executor", tool_executor_node)
builder.add_node("validator", validation_critique_node)
builder.add_node("synthesizer", synthesizer_node)

# Linear edges
builder.add_edge("planner", "executor")
builder.add_edge("executor", "validator")

# Conditional edge from validator

def _edge_selector(state: AgentState) -> str:  # noqa: D401
    """Route based on validation outcome."""

    return "replan" if state.iteration > 0 else "synth"


builder.add_conditional_edges(
    "validator", _edge_selector, {"replan": "planner", "synth": "synthesizer"}
)

# Define entry/exit
builder.set_entry_point("planner")
builder.set_finish_point("synthesizer")

# Compile graph instance
GRAPH = builder.compile()
