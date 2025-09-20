"""Tests for orchestration nodes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration.nodes import (
    TOOL_MAP,
    graph_search,
    graph_search_async,
    planner_node,
    synthesizer_node,
    tool_executor_node_async,
    vector_search,
    vector_search_async,
)


class TestPlannerNode:
    """Test the planner node functionality."""

    @pytest.mark.asyncio
    async def test_planner_node_success(self, mock_ollama_client, sample_agent_state):
        """Test successful planner node execution."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.return_value = {
                "response": '{"plan": ["vector_search", "graph_search"]}'
            }

            result = planner_node(sample_agent_state)

            assert "plan" in result
            assert result["plan"] == ["vector_search", "graph_search"]
            mock_ollama_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_planner_node_single_tool(
        self, mock_ollama_client, sample_agent_state
    ):
        """Test planner node with single tool."""
        mock_ollama_client.generate.return_value = {
            "response": '{"plan": ["vector_search"]}'
        }

        result = planner_node(sample_agent_state)

        assert result["plan"] == ["vector_search"]

    @pytest.mark.asyncio
    async def test_planner_node_invalid_json_retry(
        self, mock_ollama_client, sample_agent_state
    ):
        """Test planner node with invalid JSON that gets retried."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.side_effect = [
                {"response": "Invalid JSON response"},
                {"response": '{"plan": ["vector_search"]}'},
            ]

            result = planner_node(sample_agent_state)

            assert result["plan"] == ["vector_search"]
            assert mock_ollama_client.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_planner_node_fallback_on_max_retries(
        self, mock_ollama_client, sample_agent_state
    ):
        """Test planner node fallback after max retries."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.return_value = {
                "response": "Always invalid JSON"
            }

            result = planner_node(sample_agent_state)

            assert result["plan"] == ["vector_search"]  # Fallback plan
            assert mock_ollama_client.generate.call_count == 3  # Max retries

    @pytest.mark.asyncio
    async def test_planner_node_invalid_plan_format(
        self, mock_ollama_client, sample_agent_state
    ):
        """Test planner node with invalid plan format."""
        mock_ollama_client.generate.return_value = {
            "response": '{"plan": "not_a_list"}'
        }

        result = planner_node(sample_agent_state)

        assert result["plan"] == ["vector_search"]  # Fallback plan

    @pytest.mark.asyncio
    async def test_planner_node_ui_callback(
        self, mock_ollama_client, sample_agent_state
    ):
        """Test planner node UI callback."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.return_value = {
                "response": '{"plan": ["vector_search"]}'
            }

            ui_calls = []

            def ui_callback(msg: str) -> None:
                ui_calls.append(msg)

            sample_agent_state.ui = ui_callback

            planner_node(sample_agent_state)

            assert "planning_complete" in ui_calls


class TestToolExecutorNodeAsync:
    """Test the async tool executor node functionality."""

    @pytest.mark.asyncio
    async def test_tool_executor_sync_tools(self, sample_agent_state_with_plan):
        """Test tool executor with synchronous tools."""
        with patch.dict(
            TOOL_MAP,
            {
                "vector_search": MagicMock(return_value="Vector search result"),
                "graph_search": MagicMock(return_value="Graph search result"),
            },
        ):
            result = await tool_executor_node_async(sample_agent_state_with_plan)

            assert "tool_output" in result
            assert len(result["tool_output"]) == 2
            assert "Vector search result" in result["tool_output"]
            assert "Graph search result" in result["tool_output"]

    @pytest.mark.asyncio
    async def test_tool_executor_async_tools(self, sample_agent_state_with_plan):
        """Test tool executor with asynchronous tools."""
        # Modify plan to use async tools
        sample_agent_state_with_plan.plan = [
            "vector_search_async",
            "graph_search_async",
        ]

        with patch.dict(
            TOOL_MAP,
            {
                "vector_search_async": AsyncMock(return_value="Async vector result"),
                "graph_search_async": AsyncMock(return_value="Async graph result"),
            },
        ):
            result = await tool_executor_node_async(sample_agent_state_with_plan)

            assert "tool_output" in result
            assert len(result["tool_output"]) == 2
            assert "Async vector result" in result["tool_output"]
            assert "Async graph result" in result["tool_output"]

    @pytest.mark.asyncio
    async def test_tool_executor_mixed_tools(self, sample_agent_state_with_plan):
        """Test tool executor with mixed sync and async tools."""
        sample_agent_state_with_plan.plan = ["vector_search", "graph_search_async"]

        with patch.dict(
            TOOL_MAP,
            {
                "vector_search": MagicMock(return_value="Sync vector result"),
                "graph_search_async": AsyncMock(return_value="Async graph result"),
            },
        ):
            result = await tool_executor_node_async(sample_agent_state_with_plan)

            assert "tool_output" in result
            assert len(result["tool_output"]) == 2
            assert "Sync vector result" in result["tool_output"]
            assert "Async graph result" in result["tool_output"]

    @pytest.mark.asyncio
    async def test_tool_executor_ui_callbacks(self, sample_agent_state_with_plan):
        """Test tool executor UI callbacks."""
        ui_calls = []

        def ui_callback(msg: str) -> None:
            ui_calls.append(msg)

        sample_agent_state_with_plan.ui = ui_callback

        with patch.dict(
            TOOL_MAP,
            {
                "vector_search": MagicMock(return_value="Vector result"),
                "graph_search": MagicMock(return_value="Graph result"),
            },
        ):
            await tool_executor_node_async(sample_agent_state_with_plan)

            # Check that UI callbacks were made
            assert any("tool_start:vector_search" in call for call in ui_calls)
            assert any("tool_done:vector_search" in call for call in ui_calls)
            assert any("tool_start:graph_search" in call for call in ui_calls)
            assert any("tool_done:graph_search" in call for call in ui_calls)

    @pytest.mark.asyncio
    async def test_tool_executor_empty_plan(self, sample_agent_state):
        """Test tool executor with empty plan."""
        sample_agent_state.plan = []

        result = await tool_executor_node_async(sample_agent_state)

        assert "tool_output" in result
        assert result["tool_output"] == []


class TestSynthesizerNode:
    """Test the synthesizer node functionality."""

    @pytest.mark.asyncio
    async def test_synthesizer_node_success(
        self, mock_ollama_client, sample_agent_state_with_outputs
    ):
        """Test successful synthesizer node execution."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.return_value = {
                "response": (
                    "Artificial Intelligence (AI) is a field of computer science..."
                )
            }

            result = synthesizer_node(sample_agent_state_with_outputs)

            assert "response" in result
            assert "Artificial Intelligence" in result["response"]
            mock_ollama_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesizer_node_ui_callbacks(
        self, mock_ollama_client, sample_agent_state_with_outputs
    ):
        """Test synthesizer node UI callbacks."""
        ui_calls = []

        def ui_callback(msg: str) -> None:
            ui_calls.append(msg)

        sample_agent_state_with_outputs.ui = ui_callback
        mock_ollama_client.generate.return_value = {"response": "Test response"}

        synthesizer_node(sample_agent_state_with_outputs)

        assert "synth_start" in ui_calls
        assert "Answer ready ✨" in ui_calls

    @pytest.mark.asyncio
    async def test_synthesizer_node_context_handling(
        self, mock_ollama_client, sample_agent_state_with_outputs
    ):
        """Test synthesizer node context handling."""
        with patch("src.orchestration.nodes._get_ollama_client") as mock_get_client:
            mock_get_client.return_value = mock_ollama_client
            mock_ollama_client.generate.return_value = {"response": "Test response"}

            synthesizer_node(sample_agent_state_with_outputs)

            # Check that the generate method was called with context
            call_args = mock_ollama_client.generate.call_args
            prompt = call_args[0][1]  # Second argument is the prompt

            assert "Context from tools:" in prompt
            assert "AI is a field of computer science..." in prompt
            assert "Machine learning is a subset of AI..." in prompt
            assert "What is artificial intelligence?" in prompt


class TestToolFunctions:
    """Test individual tool functions."""

    def test_vector_search(self, mock_chromadb_agent, sample_agent_state):
        """Test vector search tool."""
        with patch(
            "src.orchestration.nodes._get_chromadb_agent",
            return_value=mock_chromadb_agent,
        ):
            result = vector_search(sample_agent_state)

            assert result == "Mock document 1\nMock document 2"
            mock_chromadb_agent.similarity_search.assert_called_once_with(
                sample_agent_state.query
            )

    @pytest.mark.asyncio
    async def test_vector_search_async(self, mock_chromadb_agent, sample_agent_state):
        """Test async vector search tool."""
        with patch(
            "src.orchestration.nodes._get_chromadb_agent",
            return_value=mock_chromadb_agent,
        ):
            result = await vector_search_async(sample_agent_state)

            assert result == "Mock async document 1\nMock async document 2"
            mock_chromadb_agent.similarity_search_async.assert_called_once_with(
                sample_agent_state.query
            )

    def test_graph_search(self, mock_neo4j_agent, sample_agent_state):
        """Test graph search tool."""
        with patch(
            "src.orchestration.nodes._get_neo4j_agent", return_value=mock_neo4j_agent
        ):
            result = graph_search(sample_agent_state)

            assert "Test Node" in result
            mock_neo4j_agent.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_graph_search_async(self, mock_neo4j_agent, sample_agent_state):
        """Test async graph search tool."""
        with patch(
            "src.orchestration.nodes._get_neo4j_agent", return_value=mock_neo4j_agent
        ):
            result = await graph_search_async(sample_agent_state)

            assert "Test Async Node" in result
            mock_neo4j_agent.query_async.assert_called_once()


class TestToolMap:
    """Test the TOOL_MAP configuration."""

    def test_tool_map_contains_all_tools(self):
        """Test that TOOL_MAP contains all expected tools."""
        expected_tools = [
            "vector_search",
            "graph_search",
            "vector_search_async",
            "graph_search_async",
        ]

        for tool in expected_tools:
            assert tool in TOOL_MAP
            assert callable(TOOL_MAP[tool])

    def test_tool_map_tool_types(self):
        """Test that tools in TOOL_MAP are callable."""
        for tool_name, tool_func in TOOL_MAP.items():
            assert callable(tool_func), f"Tool {tool_name} is not callable"
