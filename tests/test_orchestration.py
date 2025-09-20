"""Legacy orchestration tests - kept for backward compatibility.

These tests are maintained for backward compatibility but new tests
should be added to test_orchestration_nodes.py and test_orchestration_graph.py.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.orchestration.nodes import (
    planner_node,
    synthesizer_node,
    tool_executor_node_async,
)
from src.orchestration.state import AgentState

# ----------------------------
# Fixtures
# ----------------------------


@pytest.mark.asyncio
@patch("src.orchestration.nodes._get_ollama_client")
async def test_planner_generates_plan(mock_get_client):
    """Test that planner generates a plan correctly."""
    # Configure mock LLM to return JSON list as string
    mock_client = mock_get_client.return_value
    mock_client.generate.return_value = {"response": '["vector_search"]'}

    base_state = AgentState(query="What is AI?")
    plan_result = planner_node(base_state)

    assert plan_result["plan"] == ["vector_search"]


@pytest.mark.asyncio
@patch("src.orchestration.nodes._get_ollama_client")
@patch("src.orchestration.nodes.vector_search", return_value="doc1")
async def test_executor_dispatch(mock_vs, mock_get_client):
    """Test that executor dispatches tools correctly."""
    # Configure mock LLM for planner
    mock_client = mock_get_client.return_value
    mock_client.generate.return_value = {"response": '["vector_search"]'}

    # Create state with plan
    base_state = AgentState(query="What is AI?")
    plan_result = planner_node(base_state)
    base_state.plan = plan_result["plan"]

    # Ensure TOOL_MAP uses the patched function during this test
    from src.orchestration import nodes as _nodes

    with patch.dict(_nodes.TOOL_MAP, {"vector_search": mock_vs}):
        out_state = await tool_executor_node_async(base_state)

    # The executor returns a dict with a list under 'tool_output'
    assert out_state["tool_output"] == ["doc1"]

    # vector_search should be called exactly once with the full AgentState
    mock_vs.assert_called_once_with(base_state)


@pytest.mark.asyncio
@patch("src.orchestration.nodes._get_ollama_client")
async def test_synthesizer_calls_llm(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.generate.return_value = {"response": "AI is …"}

    st = AgentState(query="What is AI?", tool_output=["context"])
    res_state = synthesizer_node(st)

    mock_client.generate.assert_called_once()
    assert res_state["response"].startswith("AI")
