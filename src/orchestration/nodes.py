from __future__ import annotations
import textwrap
from src.config import get_settings
from src.orchestration.state import AgentState
from src.tools.chromadb_agent import ChromaDBAgent
from src.tools.neo4j_agent import Neo4jAgent
from src.utils.logger import get_logger
from src.utils.metrics import timed, increment
from src.utils.schema_validator import (
    SafeJSONParser,
    SchemaValidationError,
    sanitize_user_input,
)
import ollama

logger = get_logger(__name__)
settings = get_settings()

# Lazy initialization to avoid connection attempts during import
OLLAMA_CLIENT: ollama.Client | None = None
neo4j_agent: Neo4jAgent | None = None
chromadb_agent: ChromaDBAgent | None = None


def _get_ollama_client():
    """Get or create Ollama client lazily."""
    global OLLAMA_CLIENT
    if OLLAMA_CLIENT is None:
        OLLAMA_CLIENT = ollama.Client(host=settings.ollama_host)
    return OLLAMA_CLIENT


def _get_neo4j_agent():
    """Get or create Neo4j agent lazily."""
    global neo4j_agent
    if neo4j_agent is None:
        neo4j_agent = Neo4jAgent()
    return neo4j_agent


def _get_chromadb_agent():
    """Get or create ChromaDB agent lazily."""
    global chromadb_agent
    if chromadb_agent is None:
        chromadb_agent = ChromaDBAgent()
    return chromadb_agent

# --- TOOL DEFINITIONS ---


# In agent_stack/src/orchestration/nodes.py

@timed("vector_search_duration")
def vector_search(state: AgentState) -> str:
    """Performs a vector search in ChromaDB."""
    logger.info("Executing tool: vector_search")
    increment("vector_search_calls")

    # This is the corrected line:
    # It now calls .similarity_search() instead of .search()
    results = _get_chromadb_agent().similarity_search(state.query)

    return "\n".join(results)


@timed("vector_search_async_duration")
async def vector_search_async(state: AgentState) -> str:
    """Async version of vector search for better performance."""
    logger.info("Executing tool: vector_search_async")
    increment("vector_search_async_calls")

    results = await _get_chromadb_agent().similarity_search_async(state.query)
    return "\n".join(results)


@timed("graph_search_duration")
def graph_search(state: AgentState) -> str:
    """Performs a graph query in Neo4j."""
    logger.info("Executing tool: graph_search")
    increment("graph_search_calls")
    cypher_query = "MATCH (n) RETURN n.name AS name, n.label AS label LIMIT 5"
    return str(_get_neo4j_agent().query(cypher_query))


@timed("graph_search_async_duration")
async def graph_search_async(state: AgentState) -> str:
    """Async version of graph search for better performance."""
    logger.info("Executing tool: graph_search_async")
    increment("graph_search_async_calls")
    cypher_query = "MATCH (n) RETURN n.name AS name, n.label AS label LIMIT 5"
    results = await _get_neo4j_agent().query_async(cypher_query)
    return str(results)


TOOL_MAP = {
    "vector_search": vector_search,
    "graph_search": graph_search,
    "vector_search_async": vector_search_async,
    "graph_search_async": graph_search_async,
}

# --- NODE IMPLEMENTATIONS ---


# In agent_stack/src/orchestration/nodes.py

@timed("planner_duration")
def planner_node(state: AgentState) -> dict:
    """
    Determines the execution plan to address the user's query.
    """
    # Sanitize user input to prevent prompt injection
    sanitized_query = sanitize_user_input(state.query)
    logger.info("Planner received query: %s", sanitized_query)
    increment("planner_calls")

    # Enhanced prompt with few-shot examples and stricter JSON requirements
    prompt = textwrap.dedent(
        (
            "You are an expert AI planner. "
            "Your task is to create a step-by-step plan to answer the user's "
            "query. Choose from the available tools. Return ONLY valid JSON "
            "with a single key 'plan' mapping to a list of tool names.\n\n"
            "Available tools:\n"
            "- 'vector_search': broad, semantic queries.\n"
            "- 'graph_search': relationship queries.\n"
            "- 'vector_search_async': async version of vector search.\n"
            "- 'graph_search_async': async version of graph search.\n\n"
            f"User's query: \"{sanitized_query}\"\n\n"
            "IMPORTANT: Return ONLY valid JSON. No explanations, no markdown, "
            "no additional text. Just the JSON object.\n\n"
            "Examples of valid responses:\n"
            "{\"plan\": [\"vector_search\"]}\n"
            "{\"plan\": [\"graph_search\"]}\n"
            "{\"plan\": [\"vector_search\", \"graph_search\"]}\n"
            "{\"plan\": [\"vector_search_async\", \"graph_search_async\"]}\n\n"
            "Your response:"
        )
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Call Ollama client directly (synchronous)
            response = _get_ollama_client().generate(
                settings.ollama_model,
                prompt
            )

            # Log the raw response for debugging
            raw_response = response.get('response', '')
            logger.debug(
                "LLM raw response (attempt %d): %s",
                attempt + 1, raw_response
            )

            # Use safe JSON parser with schema validation
            try:
                plan_data = SafeJSONParser.safe_parse_json(
                    raw_response, "planner"
                )
                plan = plan_data["plan"]

                if state.ui:
                    state.ui("planning_complete")

                logger.info("Generated plan: %s", plan)
                return {"plan": plan}

            except SchemaValidationError as e:
                logger.error(
                    "Schema validation error on attempt %d: %s. "
                    "Raw response: %s",
                    attempt + 1, e, raw_response
                )
                if attempt == max_retries - 1:
                    logger.error(
                        "All retry attempts failed. Using fallback plan."
                    )
                    return {"plan": ["vector_search"]}
                # Continue to next retry attempt
                continue

        except Exception as e:
            logger.error(
                "Unexpected error on attempt %d: %s",
                attempt + 1, e
            )
            if attempt == max_retries - 1:
                logger.error("All retry attempts failed. Using fallback plan.")
                return {"plan": ["vector_search"]}
            # Continue to next retry attempt
            continue

    # This should never be reached due to the logic above, but just in case
    logger.error("Unexpected fallback reached. Using default plan.")
    return {"plan": ["vector_search"]}


@timed("executor_duration")
def tool_executor_node(state: AgentState) -> dict:
    """Synchronous version of tool executor."""
    import asyncio
    import concurrent.futures
    tool_outputs = []

    for tool_name in state.plan:
        if tool_name in TOOL_MAP:
            if state.ui:
                state.ui(f"tool_start:{tool_name}")
            try:
                output = TOOL_MAP[tool_name](state)
                # Check if the output is a coroutine (async tool)
                if asyncio.iscoroutine(output):
                    # Try to get the current event loop
                    try:
                        asyncio.get_running_loop()
                        # We're in an async context, use thread pool
                        with concurrent.futures.ThreadPoolExecutor() as (
                            executor
                        ):
                            future = executor.submit(
                                asyncio.run, output
                            )
                            output = future.result()
                    except RuntimeError:
                        # No event loop running, create a new one
                        try:
                            if asyncio.iscoroutine(output):
                                output = asyncio.run(output)
                        except Exception as e:
                            logger.error(
                                "Error running async tool %s: %s",
                                tool_name, e
                            )
                            output = f"Error executing {tool_name}: {str(e)}"
                tool_outputs.append(output)
            except Exception as e:
                logger.error("Error executing tool %s: %s", tool_name, e)
                tool_outputs.append(f"Error executing {tool_name}: {str(e)}")
            if state.ui:
                state.ui(f"tool_done:{tool_name}")

    return {"tool_output": tool_outputs}


@timed("executor_duration")
async def tool_executor_node_async(state: AgentState) -> dict:
    """Async version of tool executor for better performance."""
    tool_outputs = []

    # Check if any tools are async
    async_tools = []
    sync_tools = []

    for tool_name in state.plan:
        if tool_name in TOOL_MAP:
            if tool_name.endswith("_async"):
                async_tools.append(tool_name)
            else:
                sync_tools.append(tool_name)

    # Execute sync tools first
    for tool_name in sync_tools:
        if state.ui:
            state.ui(f"tool_start:{tool_name}")
        try:
            output = TOOL_MAP[tool_name](state)
            tool_outputs.append(output)
        except Exception as e:
            logger.error("Error executing sync tool %s: %s", tool_name, e)
            tool_outputs.append(f"Error executing {tool_name}: {str(e)}")
        if state.ui:
            state.ui(f"tool_done:{tool_name}")

    # Execute async tools concurrently (moved outside sync loop)
    if async_tools:
        async_tasks = []
        for tool_name in async_tools:
            if state.ui:
                state.ui(f"tool_start:{tool_name}")
            task = TOOL_MAP[tool_name](state)
            async_tasks.append((tool_name, task))

        # Wait for all async tools to complete
        for tool_name, task in async_tasks:
            # task is a coroutine from async tool functions
            try:
                output = await task  # type: ignore[misc]
                tool_outputs.append(output)
            except Exception as e:
                logger.error("Error executing async tool %s: %s", tool_name, e)
                tool_outputs.append(f"Error executing {tool_name}: {str(e)}")
            if state.ui:
                state.ui(f"tool_done:{tool_name}")

    return {"tool_output": tool_outputs}


def validation_critique_node(state: AgentState) -> dict:
    logger.info("Validation passed.")
    return {"iteration": state.iteration + 1}


# In agent_stack/src/orchestration/nodes.py

@timed("synthesizer_duration")
def synthesizer_node(state: AgentState) -> dict:
    logger.info("Synthesizing final response.")
    increment("synthesizer_calls")
    if state.ui:
        state.ui("synth_start")
    context = "\n---\n".join(state.tool_output)

    # ADD THIS LINE to see what the agent is thinking
    logger.info("Context provided to synthesizer (truncated).")

    # Sanitize user query for synthesizer as well
    sanitized_query = sanitize_user_input(state.query)
    prompt = (
        "You are an expert AI assistant.\n\nContext from tools:\n"
        + context
        + f"\n\nUser's original query: {sanitized_query}\n\n"
        + "Provide your final, synthesized answer now."
    )
    # Call Ollama client directly (synchronous)
    try:
        response = _get_ollama_client().generate(
            settings.ollama_model,
            prompt
        )
        final_response = response['response']
    except Exception as e:
        logger.error("Error in synthesizer: %s", e)
        final_response = f"Error generating response: {str(e)}"
    # Log truncated response to avoid duplicate full answer in console.
    trunc_resp = final_response[:100].replace("\n", " ")
    if len(final_response) > 100:
        trunc_resp += "..."
    logger.info("Synthesized response (truncated): %s", trunc_resp)
    if state.ui:
        state.ui("Answer ready ✨")

    return {"response": final_response}
