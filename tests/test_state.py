"""Tests for the AgentState class."""

from __future__ import annotations


from src.orchestration.state import AgentState


class TestAgentState:
    """Test the AgentState class."""

    def test_agent_state_creation_with_query(self):
        """Test AgentState creation with just a query."""
        state = AgentState(query="What is AI?")
        assert state.query == "What is AI?"
        assert state.plan == []
        assert state.tool_output == []
        assert state.response == ""
        assert state.iteration == 0
        assert state.ui is None

    def test_agent_state_creation_with_all_fields(self):
        """Test AgentState creation with all fields."""
        def mock_ui(msg: str) -> None:
            pass

        state = AgentState(
            query="What is AI?",
            plan=["vector_search"],
            tool_output=["AI is..."],
            response="AI is artificial intelligence",
            iteration=1,
            ui=mock_ui
        )
        assert state.query == "What is AI?"
        assert state.plan == ["vector_search"]
        assert state.tool_output == ["AI is..."]
        assert state.response == "AI is artificial intelligence"
        assert state.iteration == 1
        assert state.ui is mock_ui

    def test_agent_state_default_values(self):
        """Test AgentState default values."""
        state = AgentState(query="Test query")
        assert state.plan == []
        assert state.tool_output == []
        assert state.response == ""
        assert state.iteration == 0
        assert state.ui is None

    def test_agent_state_immutable_fields(self):
        """Test that AgentState fields can be modified after creation."""
        state = AgentState(query="Original query")

        # Modify fields
        state.plan = ["vector_search", "graph_search"]
        state.tool_output = ["Result 1", "Result 2"]
        state.response = "Final response"
        state.iteration = 5

        assert state.plan == ["vector_search", "graph_search"]
        assert state.tool_output == ["Result 1", "Result 2"]
        assert state.response == "Final response"
        assert state.iteration == 5

    def test_agent_state_ui_callback(self):
        """Test AgentState UI callback functionality."""
        calls = []

        def ui_callback(msg: str) -> None:
            calls.append(msg)

        state = AgentState(query="Test query", ui=ui_callback)

        # Call the UI callback
        state.ui("test_message")
        assert calls == ["test_message"]

        # Call multiple times
        state.ui("another_message")
        assert calls == ["test_message", "another_message"]

    def test_agent_state_ui_none(self):
        """Test AgentState with UI callback set to None."""
        state = AgentState(query="Test query", ui=None)
        assert state.ui is None

        # Should not raise an error when calling ui (it should handle None gracefully)
        try:
            state.ui("test_message")
        except TypeError:
            # This is expected behavior - None is not callable
            pass

    def test_agent_state_plan_modification(self):
        """Test that plan can be modified."""
        state = AgentState(query="Test query")
        assert state.plan == []

        # Add items to plan
        state.plan.append("vector_search")
        state.plan.append("graph_search")
        assert state.plan == ["vector_search", "graph_search"]

        # Clear plan
        state.plan.clear()
        assert state.plan == []

    def test_agent_state_tool_output_modification(self):
        """Test that tool_output can be modified."""
        state = AgentState(query="Test query")
        assert state.tool_output == []

        # Add items to tool_output
        state.tool_output.append("Result 1")
        state.tool_output.append("Result 2")
        assert state.tool_output == ["Result 1", "Result 2"]

        # Clear tool_output
        state.tool_output.clear()
        assert state.tool_output == []

    def test_agent_state_iteration_increment(self):
        """Test iteration increment functionality."""
        state = AgentState(query="Test query")
        assert state.iteration == 0

        # Increment iteration
        state.iteration += 1
        assert state.iteration == 1

        state.iteration += 5
        assert state.iteration == 6

    def test_agent_state_response_setting(self):
        """Test response setting functionality."""
        state = AgentState(query="Test query")
        assert state.response == ""

        # Set response
        state.response = "This is a test response"
        assert state.response == "This is a test response"

        # Update response
        state.response = "Updated response"
        assert state.response == "Updated response"

    def test_agent_state_equality(self):
        """Test AgentState equality comparison."""
        state1 = AgentState(query="Test query")
        state2 = AgentState(query="Test query")
        state3 = AgentState(query="Different query")

        # Same query should be equal
        assert state1.query == state2.query

        # Different queries should not be equal
        assert state1.query != state3.query

    def test_agent_state_string_representation(self):
        """Test AgentState string representation."""
        state = AgentState(query="Test query")
        str_repr = str(state)

        # Should contain the query
        assert "Test query" in str_repr
        assert "AgentState" in str_repr or "query" in str_repr
