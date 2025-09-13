from __future__ import annotations

"""Main entry point to run the Cognitive Orchestration Stack."""

import sys
import argparse
import textwrap

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


# ----------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:  # noqa: D401
    parser = argparse.ArgumentParser(
        prog="cog-stack",
        description="Command-line interface to the Cognitive Orchestration Stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Example:
                python -m src.main --question "What is photosynthesis?"
            """,
        ),
    )
    parser.add_argument("--question", "-q", required=True, help="Your question to the agent")
    return parser.parse_args()


def main() -> None:  # noqa: D401
    args = _parse_args()
    print("Processing your request…\n")
    run(args.question)


if __name__ == "__main__":  # pragma: no cover
    main()
