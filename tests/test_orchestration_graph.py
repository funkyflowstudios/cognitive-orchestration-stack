"""Tests for orchestration graph functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.graph import GRAPH, _edge_selector
from src.orchestration.state import AgentState


class TestEdgeSelector:
    """Test the edge selector function."""

    def test_edge_selector_returns_synth(self, sample_agent_state):
        """Test that edge selector always returns 'synth'."""
        result = _edge_selector(sample_agent_state)
        assert result == "synth"

    def test_edge_selector_with_different_states(self):
        """Test edge selector with different state configurations."""
        # Test with different iterations
        state1 = AgentState(query="test", iteration=0)
        state2 = AgentState(query="test", iteration=5)

        assert _edge_selector(state1) == "synth"
        assert _edge_selector(state2) == "finish"

        # Test with different responses
        state3 = AgentState(query="test", response="Some response")
        assert _edge_selector(state3) == "synth"


class TestGraphCompilation:
    """Test graph compilation and structure."""

    def test_graph_is_compiled(self):
        """Test that GRAPH is properly compiled."""
        assert GRAPH is not None
        assert hasattr(GRAPH, 'invoke')
        assert hasattr(GRAPH, 'ainvoke')

    def test_graph_invoke_method(self, sample_agent_state):
        """Test that GRAPH has invoke method."""
        # This should not raise an error
        assert callable(GRAPH.invoke)

    def test_graph_ainvoke_method(self, sample_agent_state):
        """Test that GRAPH has ainvoke method."""
        # This should not raise an error
        assert callable(GRAPH.ainvoke)


class TestGraphExecution:
    """Test graph execution with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_graph_execution_with_mocks(self, sample_agent_state):
        """Test full graph execution with mocked dependencies."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search"]}'},  # planner
                {"response": "Final synthesized response"}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = \
    ["Document 1", "Document 2"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"name": "Node 1"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Execute graph
            result = await GRAPH.ainvoke(sample_agent_state)

            # Verify result (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == sample_agent_state.query
            assert len(agent_state.plan) > 0
            assert len(agent_state.tool_output) > 0
            assert agent_state.response != ""

    def test_graph_execution_sync(self, sample_agent_state):
        """Test synchronous graph execution."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search"]}'},  # planner
                {"response": "Final synthesized response"}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["Document 1"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"name": "Node 1"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Execute graph synchronously
            result = GRAPH.invoke(sample_agent_state)

            # Verify result (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == sample_agent_state.query
            assert len(agent_state.plan) > 0
            assert len(agent_state.tool_output) > 0
            assert agent_state.response != ""

    @pytest.mark.asyncio
    async def test_graph_execution_with_ui_callbacks(self, sample_agent_state):
        """Test graph execution with UI callbacks."""
        ui_calls = []

        def ui_callback(msg: str) -> None:
            ui_calls.append(msg)

        sample_agent_state.ui = ui_callback

        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search"]}'},  # planner
                {"response": "Final synthesized response"}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["Document 1"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"name": "Node 1"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Execute graph
            await GRAPH.ainvoke(sample_agent_state)

            # Verify UI callbacks were made
            assert len(ui_calls) > 0
            # Should have planning_complete, tool_start, tool_done, synth_start, and Answer ready
            assert any("planning_complete" in call for call in ui_calls)
            assert any("tool_start:" in call for call in ui_calls)
            assert any("tool_done:" in call for call in ui_calls)
            assert any("synth_start" in call for call in ui_calls)
            assert any("Answer ready" in call for call in ui_calls)

    @pytest.mark.asyncio
    async def test_graph_execution_error_handling(self, sample_agent_state):
        """Test graph execution error handling."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks to raise exceptions
            mock_client = MagicMock()
            mock_client.generate.side_effect = Exception("LLM error")
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.side_effect = \
    Exception("ChromaDB error")
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.side_effect = Exception("Neo4j error")
            mock_get_neo4j.return_value = mock_neo4j

            # Execute graph - should handle errors gracefully
            result = await GRAPH.ainvoke(sample_agent_state)

            # Should still return a valid state (LangGraph returns dict)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == sample_agent_state.query


class TestGraphStateTransitions:
    """Test state transitions through the graph."""

    @pytest.mark.asyncio
    async def test_state_evolution_through_graph(self, sample_agent_state):
        """Test how state evolves through graph execution."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search", "graph_search"]}'},
     # planner
                {"response": "Final synthesized response"}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["Vector result"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"name": "Graph result"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Execute graph
            result = await GRAPH.ainvoke(sample_agent_state)

            # Verify state evolution (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == sample_agent_state.query  # Original query preserved
            assert len(agent_state.plan) == 2  # Plan was set by planner
            assert "vector_search" in agent_state.plan
            assert "graph_search" in agent_state.plan
            assert len(agent_state.tool_output) == 2  # Two tools executed
            assert "Vector result" in agent_state.tool_output
            assert any("Graph result" in str(output) for output in agent_state.tool_output)
            assert agent_state.response == "Final synthesized response"  # Final response set
            assert agent_state.iteration == 1  # Iteration incremented by validator
