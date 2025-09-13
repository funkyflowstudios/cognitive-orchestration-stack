from __future__ import annotations

"""Main entry point to run the Cognitive Orchestration Stack."""

import sys

from orchestration.graph import GRAPH
from orchestration.state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)


def run(query: str) -> None:  # noqa: D401
    """Execute the LangGraph workflow with the given user query."""

    state = AgentState(query=query)
    final_state = GRAPH(state)
    logger.info("Final response: %s", final_state.response)
    print(final_state.response)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.main \"<your query>\"")
        sys.exit(1)
    run(sys.argv[1])
