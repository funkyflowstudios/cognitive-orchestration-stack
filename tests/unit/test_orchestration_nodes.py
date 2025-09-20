# tests/unit/test_orchestration_nodes.py

from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.nodes import (
    graph_search,
    planner_node,
    synthesizer_node,
    tool_executor_node,
    validation_critique_node,
    vector_search,
)
from src.orchestration.state import AgentState


# A fixture to provide a default, clean state for each test
@pytest.fixture
def initial_state() -> AgentState:
    """Provides a baseline AgentState for tests."""
    return AgentState(
        query="Test query",
        plan=[],
        tool_output=[],
        response="",
        iteration=0,
    )


def test_planner_node_creates_plan(initial_state):
    """
    Verifies that the planner_node creates a valid execution plan.
    """
    # Mock the Ollama client to return a valid JSON response
    mock_response = {"response": '{"plan": ["vector_search", "graph_search"]}'}

    with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = planner_node(initial_state)

        # Verify the plan was created in the returned dict
        assert "plan" in result
        assert len(result["plan"]) == 2
        assert "vector_search" in result["plan"]
        assert "graph_search" in result["plan"]
        mock_client.generate.assert_called_once()


def test_planner_node_handles_invalid_json(initial_state):
    """
    Verifies that the planner_node handles invalid JSON responses gracefully.
    """
    # Mock the Ollama client to return invalid JSON
    mock_response = {"response": "Invalid JSON response"}

    with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = planner_node(initial_state)

        # Should fall back to default plan
        assert "plan" in result
        assert len(result["plan"]) == 1
        assert result["plan"][0] == "vector_search"


def test_tool_executor_node_executes_plan(initial_state):
    """
    Verifies that the tool_executor_node executes the planned tools.
    """
    initial_state.plan = ["vector_search", "graph_search"]

    with patch(
        "src.orchestration.nodes.TOOL_MAP",
        {
            "vector_search": lambda state: "Vector search results",
            "graph_search": lambda state: "Graph search results",
        },
    ):
        result = tool_executor_node(initial_state)

        # Verify results were stored in the returned dict
        assert "tool_output" in result
        assert len(result["tool_output"]) == 2
        assert "Vector search results" in result["tool_output"]
        assert "Graph search results" in result["tool_output"]


def test_vector_search_returns_results(initial_state):
    """
    Verifies that vector_search returns search results.
    """
    with patch("src.orchestration.nodes._get_chromadb_agent") as mock_get_agent:
        mock_agent = MagicMock()
        mock_agent.similarity_search.return_value = ["Result 1", "Result 2"]
        mock_get_agent.return_value = mock_agent

        result = vector_search(initial_state)

        # Verify the agent was called with the query
        mock_agent.similarity_search.assert_called_once_with(initial_state.query)

        # Verify results are formatted correctly
        assert "Result 1" in result
        assert "Result 2" in result


def test_graph_search_returns_results(initial_state):
    """
    Verifies that graph_search returns search results.
    """
    with patch("src.orchestration.nodes._get_neo4j_agent") as mock_get_agent:
        mock_agent = MagicMock()
        mock_agent.query.return_value = [{"name": "Node1", "label": "Entity"}]
        mock_get_agent.return_value = mock_agent

        result = graph_search(initial_state)

        # Verify the agent was called
        mock_agent.query.assert_called_once()

        # Verify results are formatted correctly
        assert "Node1" in result
        assert "Entity" in result


def test_validation_critique_node_validates_response(initial_state):
    """
    Verifies that validation_critique_node validates the tool outputs.
    """
    initial_state.tool_output = ["Tool result 1", "Tool result 2"]
    initial_state.iteration = 0

    result = validation_critique_node(initial_state)

    # Verify iteration was incremented in the returned dict
    assert "iteration" in result
    assert result["iteration"] == 1


def test_synthesizer_node_creates_final_response(initial_state):
    """
    Verifies that synthesizer_node creates the final response.
    """
    initial_state.tool_output = ["Tool result 1", "Tool result 2"]

    # Mock the Ollama client to return synthesis response
    mock_response = {
        "response": "This is the final synthesized response based on the tool results."
    }

    with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = synthesizer_node(initial_state)

        # Verify the client was called
        mock_client.generate.assert_called_once()

        # Verify response was set in the returned dict
        assert "response" in result
        assert (
            result["response"]
            == "This is the final synthesized response based on the tool results."
        )


def test_planner_node_sanitizes_input(initial_state):
    """
    Verifies that the planner_node sanitizes user input to prevent injection.
    """
    # Set a potentially malicious query
    initial_state.query = "'; DROP TABLE users; --"

    with (
        patch("src.orchestration.nodes._get_ollama_client") as mock_get_client,
        patch("src.orchestration.nodes.sanitize_user_input") as mock_sanitize,
    ):

        mock_client = MagicMock()
        mock_client.generate.return_value = {"response": '{"plan": ["vector_search"]}'}
        mock_get_client.return_value = mock_client
        mock_sanitize.return_value = "sanitized query"

        planner_node(initial_state)

        # Verify sanitization was called
        mock_sanitize.assert_called_once_with(initial_state.query)


def test_tool_executor_handles_tool_failures(initial_state):
    """
    Verifies that tool_executor_node handles tool failures gracefully.
    """
    initial_state.plan = ["vector_search", "graph_search"]

    def failing_vector_search(state):
        raise Exception("Vector search failed")

    with patch(
        "src.orchestration.nodes.TOOL_MAP",
        {
            "vector_search": failing_vector_search,
            "graph_search": lambda state: "Graph search results",
        },
    ):
        result = tool_executor_node(initial_state)

        # Verify error handling - both tools should be attempted,
        # but only successful ones in output
        assert "tool_output" in result
        assert len(result["tool_output"]) == 2  # Both tools attempted
        assert (
            "Error executing vector_search: Vector search failed"
            in result["tool_output"]
        )
        assert "Graph search results" in result["tool_output"]
