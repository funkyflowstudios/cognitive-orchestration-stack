from __future__ import annotations

"""LangGraph node implementations for the reasoning workflow."""

from typing import List
import json
from src.config import get_settings
import ollama

# Instantiate LLM client once
_settings = get_settings()
_ollama_client = ollama.Client(host=_settings.ollama_host)

# Available tool names
AVAILABLE_TOOLS: List[str] = ["graph_query", "vector_search"]

from ..utils.logger import get_logger
from .state import AgentState
from src.tools.neo4j_agent import Neo4jAgent
from src.tools.chromadb_agent import ChromaDBAgent


logger = get_logger(__name__)


# --- Planner -----------------------------------------------------------------

def planner_node(state: AgentState) -> AgentState:  # noqa: D401
    """Create a naive execution plan (mock)."""

    logger.info("Planner received query: %s", state.query)
    # Build LLM prompt
    prompt = (
        "You are an expert AI planning agent. "
        "Available tools: " + ", ".join(AVAILABLE_TOOLS) + ". "
        "Given the user question delimited by <question></question>,"\
        " output ONLY a JSON array of tool names (lower_snake_case) that should be executed in order.\n"\
        "<question>" + state.query + "</question>"
    )

    try:
        llm_resp = _ollama_client.generate(model=_settings.ollama_model, prompt=prompt)
        plan = json.loads(llm_resp["response"].strip())  # type: ignore[arg-type]
        if not isinstance(plan, list):
            raise ValueError("Planner LLM did not return a list")
        # keep only known tools
        plan = [t for t in plan if t in AVAILABLE_TOOLS]
    except Exception as exc:  # noqa: BLE001
        logger.error("Planner LLM failed: %s", exc)
        plan = ["vector_search"]

    logger.info("Generated plan: %s", plan)
    state.plan = plan
    return state


# --- Tool Executor -----------------------------------------------------------

neo4j_agent = Neo4jAgent()
chroma_agent = ChromaDBAgent()


def _graph_query(query: str) -> str:
    results = neo4j_agent.query("MATCH (n) RETURN n LIMIT 1")
    return str(results)


def _vector_search(query: str) -> str:
    ids = chroma_agent.similarity_search(query)
    return f"Top document IDs: {ids}"


def tool_executor_node(state: AgentState) -> AgentState:  # noqa: D401
    """Execute the current tool from the plan (mock implementation)."""

    if not state.plan:
        logger.warning("No plan available; skipping execution.")
        return state

    tool_name = state.plan[0]
    state.current_tool = tool_name

    logger.info("Executing tool: %s", tool_name)

    # Map tool names to functions
    tool_map = {
        "graph_query": _graph_query,
        "vector_search": _vector_search,
    }

    if tool_name in tool_map:
        state.tool_output = tool_map[tool_name](state.query)
    else:
        state.tool_output = f"Tool {tool_name} not implemented"

    logger.info("Tool output: %s", state.tool_output)
    return state


# --- Validator / Critique ----------------------------------------------------

def validation_critique_node(state: AgentState) -> AgentState:  # noqa: D401
    """Simple validation that approves everything unless 'error' in output."""

    output = state.tool_output or ""
    if "error" in output.lower():
        logger.info("Validation failed; re-planning.")
        state.iteration += 1
    else:
        logger.info("Validation passed.")
    return state


# --- Synthesizer -------------------------------------------------------------

def synthesizer_node(state: AgentState) -> AgentState:  # noqa: D401
    """Call the LLM to craft the final answer from tool outputs."""

    context = state.tool_output or ""
    prompt = (
        "You are an expert AI assistant. "
        "Answer the user's question based on the provided context.\n"
        f"Question: {state.query}\n"
        f"Context: {context}\n\n"
        "Final answer:"
    )

    try:
        llm_resp = _ollama_client.generate(model=_settings.ollama_model, prompt=prompt)
        state.response = llm_resp["response"].strip()  # type: ignore[index]
    except Exception as exc:  # noqa: BLE001
        logger.error("Synthesizer LLM failed: %s", exc)
        state.response = context or "I am unable to answer at the moment."

    logger.info("Synthesized response: %s", state.response)
    return state
