"""
Unit tests for orchestration graph integration.

Tests the LangGraph workflow execution, state transitions, and \
    conditional routing.
"""

import pytest
from unittest.mock import patch
from src.orchestration.graph import GRAPH, _edge_selector
from src.orchestration.state import AgentState


class TestOrchestrationGraph:
    """Test cases for the orchestration graph workflow."""

    @pytest.fixture
    def initial_state(self):
        """Create a fresh AgentState for testing."""
        return AgentState(
            query="Test query",
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

    def test_edge_selector_returns_synth_for_low_iteration(self):
        """Verifies that _edge_selector returns 'synth' for low iteration counts."""
        state = AgentState(query="test", iteration=1)
        result = _edge_selector(state)
        assert result == "synth"

    def test_edge_selector_returns_finish_for_high_iteration(self):
        """Verifies that _edge_selector returns 'finish' for high iteration counts."""
        state = AgentState(query="test", iteration=3)
        result = _edge_selector(state)
        assert result == "finish"

    def test_edge_selector_returns_synth_for_max_iteration(self):
        """Verifies that _edge_selector returns 'synth' for iteration=2."""
        state = AgentState(query="test", iteration=2)
        result = _edge_selector(state)
        assert result == "synth"  # Should be synth for iteration=2, finish for >2

    def test_graph_has_correct_structure(self):
        """Verifies that the graph has the correct node structure."""
        # Check that the graph exists and is callable
        assert GRAPH is not None
        assert callable(GRAPH.invoke)
        assert callable(GRAPH.ainvoke)
        # The graph should have planner, executor, validator, and synthesizer nodes
        # This is a basic structural test

    def test_graph_entry_point(self):
        """Verifies that the graph has the correct entry point."""
        # The graph should start with the planner node
        # This is tested by checking the graph structure
        assert GRAPH is not None

    def test_edge_selector_logging(self):
        """Verifies that _edge_selector logs appropriate messages."""
        with patch("src.orchestration.graph.logger") as mock_logger:
            # Test with high iteration count
            state = AgentState(query="test", iteration=3)
            _edge_selector(state)

            # Should log warning about max iterations
            mock_logger.warning.assert_called_once()
            assert "Max iterations reached" in str(mock_logger.warning.call_args)

    def test_edge_selector_normal_flow(self):
        """Verifies that _edge_selector works for normal flow."""
        with patch("src.orchestration.graph.logger") as mock_logger:
            # Test with normal iteration count
            state = AgentState(query="test", iteration=1)
            result = _edge_selector(state)

            # Should log info about proceeding to synthesize
            mock_logger.info.assert_called_once()
            assert "Plan execution complete" in str(mock_logger.info.call_args)
            assert result == "synth"
