from __future__ import annotations

from unittest.mock import patch

from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState


@patch("src.orchestration.nodes._ollama_client")
@patch("src.orchestration.nodes._vector_search", return_value="Paris")
@patch("src.orchestration.nodes._graph_query", return_value="[]")
def test_full_flow(mock_gq, mock_vs, mock_llm):
    # Planner LLM returns plan
    mock_llm.generate.side_effect = [
        {"response": "[\"vector_search\"]"},  # planner
        {"response": "Answer is Paris"},  # synthesizer
    ]

    state = AgentState(query="Capital of France?")
    final_state = GRAPH.invoke(state)

    # Validate tool executed and final response
    mock_vs.assert_called_once()
    assert final_state["response"] == "Answer is Paris"
