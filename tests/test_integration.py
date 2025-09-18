"""Integration tests for the complete agent stack."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState


class TestFullStackIntegration:
    """Test complete integration of all components."""

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, mock_settings):
        """Test complete agent workflow from query to response."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup comprehensive mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search", "graph_search"]}'},
     # planner
                {
                    "response": "Based on the context, AI is artificial intelligence..."
                }  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = [
                "AI is a field of computer science that focuses on creating intelligent machines.",
                "Machine learning is a subset of AI that enables computers to learn "
                "without being explicitly programmed."
            ]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [
                {"name": "Artificial Intelligence", "label": "Concept"},
                {"name": "Machine Learning", "label": "Subfield"}
            ]
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="What is artificial intelligence?")

            # Track UI callbacks
            ui_calls = []

            def ui_callback(msg: str) -> None:
                ui_calls.append(msg)
            state.ui = ui_callback

            # Execute complete workflow
            result = await GRAPH.ainvoke(state)

            # Verify final state (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "What is artificial intelligence?"
            assert len(agent_state.plan) == 2
            assert "vector_search" in agent_state.plan
            assert "graph_search" in agent_state.plan
            assert len(agent_state.tool_output) == 2
            assert "AI is a field of computer science" in agent_state.tool_output[0]
            assert "Artificial Intelligence" in agent_state.tool_output[1]
            assert (
                "Based on the context, AI is artificial intelligence"
                in agent_state.response
            )
            assert agent_state.iteration == 1

            # Verify UI callbacks
            assert "planning_complete" in ui_calls
            assert any("tool_start:vector_search" in call for call in ui_calls)
            assert any("tool_done:vector_search" in call for call in ui_calls)
            assert any("tool_start:graph_search" in call for call in ui_calls)
            assert any("tool_done:graph_search" in call for call in ui_calls)
            assert "synth_start" in ui_calls
            assert "Answer ready ✨" in ui_calls

    @pytest.mark.asyncio
    async def test_agent_workflow_with_async_tools(self, mock_settings):
        """Test agent workflow using async tools."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks for async tools
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search_async", "graph_search_async"]}'},
     # planner
                {
                    "response": "Async tools provide better performance for concurrent operations."
                }  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search_async = AsyncMock(return_value=[
                "Async vector search provides better performance for "
                "concurrent operations."
            ])
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query_async = AsyncMock(return_value=[
                {"name": "Async Operations", "label": "Performance"}
            ])
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="What are async tools?")

            # Execute workflow
            result = await GRAPH.ainvoke(state)

            # Verify results (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "What are async tools?"
            assert len(agent_state.plan) == 2
            assert "vector_search_async" in agent_state.plan
            assert "graph_search_async" in agent_state.plan
            assert len(agent_state.tool_output) == 2
            assert "Async vector search" in agent_state.tool_output[0]
            assert "Async Operations" in agent_state.tool_output[1]
            assert "Async tools provide better performance" in agent_state.response

    @pytest.mark.asyncio
    async def test_agent_workflow_error_recovery(self, mock_settings):
        """Test agent workflow with error recovery."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks with some failures
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search", "graph_search"]}'},
     # planner
                {
                    "response": "Despite some errors, here's what I can tell you about AI..."
                }  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            # ChromaDB works fine
            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = [
                "AI is artificial intelligence - the simulation of human intelligence "
                "in machines."
            ]
            mock_get_chromadb.return_value = mock_chromadb

            # Neo4j fails
            mock_neo4j = MagicMock()
            mock_neo4j.query.side_effect = Exception("Neo4j connection failed")
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="What is AI?")

            # Execute workflow - should handle Neo4j error gracefully
            result = await GRAPH.ainvoke(state)

            # Verify that we still get a response despite the error (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "What is AI?"
            assert len(agent_state.plan) == 2
            # Should have at least one successful tool output
            assert len(agent_state.tool_output) >= 1
            assert "AI is artificial intelligence" in agent_state.tool_output[0]
            assert "Despite some errors" in agent_state.response

    @pytest.mark.asyncio
    async def test_agent_workflow_llm_retry_mechanism(self, mock_settings):
        """Test agent workflow with LLM retry mechanism."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks with LLM retry scenario
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": "Invalid JSON response"},  # First attempt fails
                {"response": '{"plan": ["vector_search"]}'},
     # Second attempt succeeds
                {
                    "response": "Here's a comprehensive answer about AI..."
                }  # Synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = [
                "AI encompasses machine learning, natural language processing, "
                "and robotics."
            ]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = []
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="Explain AI")

            # Execute workflow
            result = await GRAPH.ainvoke(state)

            # Verify retry mechanism worked (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "Explain AI"
            assert len(agent_state.plan) == 1
            assert "vector_search" in agent_state.plan
            assert len(agent_state.tool_output) == 1
            assert "AI encompasses machine learning" in agent_state.tool_output[0]
            assert "Here's a comprehensive answer about AI" in agent_state.response

            # Verify LLM was called multiple times (retry)
            # 2 for planner, 1 for synthesizer
            assert mock_client.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_agent_workflow_fallback_plan(self, mock_settings):
        """Test agent workflow with fallback plan when LLM fails completely."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks with complete LLM failure in planner
            mock_client = MagicMock()
            # CORRECTED: Provide 3 failing responses for the planner's 3 retries,
            # plus 1 success response for the synthesizer.
            mock_client.generate.side_effect = [
                {"response": "Invalid JSON 1"},          # Planner attempt 1
                {"response": "Invalid JSON 2"},          # Planner attempt 2
                {"response": "Invalid JSON 3"},          # Planner attempt 3
                {"response": "Here's what I found about your query..."}  # Synthesizer works
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = [
                "Fallback search result when LLM planning fails."
            ]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = []
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="What happens when planning fails?")

            # Execute workflow
            result = await GRAPH.ainvoke(state)

            # Verify fallback plan was used (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "What happens when planning fails?"
            assert len(agent_state.plan) == 1
            assert "vector_search" in agent_state.plan  # Fallback plan
            assert len(agent_state.tool_output) == 1
            assert "Fallback search result" in agent_state.tool_output[0]
            assert "Here's what I found about your query" in agent_state.response

            # Verify LLM was called multiple times (retries + synthesizer)
            assert mock_client.generate.call_count >= 4  # 3 retries + 1 synthesizer

    def test_agent_workflow_sync_execution(self, mock_settings):
        """Test agent workflow with synchronous execution."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search"]}'},  # planner
                {"response": "Synchronous execution works perfectly."}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = [
                "Synchronous operations are straightforward and reliable."
            ]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = []
            mock_get_neo4j.return_value = mock_neo4j

            # Create test state
            state = AgentState(query="How does sync execution work?")

            # Execute workflow synchronously
            result = GRAPH.invoke(state)

            # Verify results (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.query == "How does sync execution work?"
            assert len(agent_state.plan) == 1
            assert "vector_search" in agent_state.plan
            assert len(agent_state.tool_output) == 1
            assert "Synchronous operations" in agent_state.tool_output[0]
            assert "Synchronous execution works perfectly" in agent_state.response


class TestAgentStateEvolution:
    """Test how AgentState evolves through the workflow."""

    @pytest.mark.asyncio
    async def test_state_evolution_tracking(self, mock_settings):
        """Test detailed state evolution through the workflow."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search", "graph_search"]}'},
     # planner
                {
                    "response": "Final comprehensive answer about the query."
                }  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = \
    ["Vector search result"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = \
    [{"name": "Graph result", "label": "Test"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Create initial state
            initial_state = AgentState(query="Test query")

            # Track state changes
            state_changes = []

            def ui_callback(msg: str) -> None:
                state_changes.append(f"UI: {msg}")

            initial_state.ui = ui_callback

            # Execute workflow
            final_state = await GRAPH.ainvoke(initial_state)

            # Verify state evolution (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(final_state, dict)
            agent_state = AgentState(**final_state)
            assert agent_state.query == initial_state.query  # Query preserved
            assert len(agent_state.plan) == 2  # Plan added by planner
            assert len(agent_state.tool_output) == 2  # Tool outputs added by executor
            assert agent_state.response != ""  # Response added by synthesizer
            assert agent_state.iteration == 1  # Iteration incremented by validator

            # Verify UI callbacks were made
            assert len(state_changes) > 0
            assert any("planning_complete" in change for change in state_changes)
            assert any("tool_start:" in change for change in state_changes)
            assert any("synth_start" in change for change in state_changes)

    @pytest.mark.asyncio
    async def test_state_persistence_across_iterations(self, mock_settings):
        """Test that state persists correctly across multiple iterations."""
        with (patch('src.orchestration.nodes._get_ollama_client') as mock_get_client,
              patch('src.orchestration.nodes._get_chromadb_agent') as mock_get_chromadb,
              patch('src.orchestration.nodes._get_neo4j_agent') as mock_get_neo4j):

            # Setup mocks
            mock_client = MagicMock()
            mock_client.generate.side_effect = [
                {"response": '{"plan": ["vector_search"]}'},  # planner
                {"response": "Iteration 1 response"}  # synthesizer
            ]
            mock_get_client.return_value = mock_client

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["Search result"]
            mock_get_chromadb.return_value = mock_chromadb

            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = []
            mock_get_neo4j.return_value = mock_neo4j

            # Create state with initial iteration
            state = AgentState(query="Test query", iteration=1)

            # Execute workflow
            result = await GRAPH.ainvoke(state)

            # Verify iteration was incremented (LangGraph returns dict, convert to AgentState for testing)
            assert isinstance(result, dict)
            agent_state = AgentState(**result)
            assert agent_state.iteration == 2  # 1 + 1
            assert agent_state.query == "Test query"  # Query preserved
            assert len(agent_state.plan) == 1  # Plan added
            assert len(agent_state.tool_output) == 1  # Tool output added
            assert agent_state.response != ""  # Response added
