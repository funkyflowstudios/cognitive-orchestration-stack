from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.nodes import (
    planner_node,
    tool_executor_node,
    synthesizer_node,
)
from src.orchestration.state import AgentState


@pytest.fixture()
@patch("src.orchestration.nodes._ollama_client")
def planner_state(mock_llm):
    # Configure mock LLM to return JSON list
    mock_llm.generate.return_value = {"response": "[\"vector_search\"]"}
    st = AgentState(query="What is AI?")
    return planner_node(st)


def test_planner_generates_plan(planner_state):
    assert planner_state.plan == ["vector_search"]


@patch("src.orchestration.nodes._vector_search", return_value="doc1")
def test_executor_dispatch(mock_vs, planner_state):
    out_state = tool_executor_node(planner_state)
    assert out_state.tool_output == "doc1"
    mock_vs.assert_called_once_with("What is AI?")


@patch("src.orchestration.nodes._ollama_client")
def test_synthesizer_calls_llm(mock_llm):
    mock_llm.generate.return_value = {"response": "AI is …"}
    st = AgentState(query="What is AI?", tool_output="context")
    res_state = synthesizer_node(st)
    mock_llm.generate.assert_called_once()
    assert res_state.response.startswith("AI")
