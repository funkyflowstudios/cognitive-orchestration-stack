# In agent_stack/src/main.py

from __future__ import annotations

"""Chimera CLI entry point – class-based application."""

import argparse

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.markdown import Markdown

from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState
from src.ui.animations import disintegration_frames, run_animation
from src.ui.focus import FocusController
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChimeraCLI:  # noqa: D101
    def __init__(self) -> None:
        self.toolbar_msg: str = "Type a query or 'help'"
        style = Style.from_dict({"bottom-toolbar": "bg:#0a0f14 #00a8cc"})
        self.session: PromptSession = PromptSession(
            bottom_toolbar=lambda: [
                ("class:bottom-toolbar", f" {self.toolbar_msg} "),
            ],
            style=style,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_interactive_mode(self) -> None:  # noqa: D401
        """Run interactive REPL using prompt_toolkit."""

        print(
            "Welcome to the Cognitive Orchestration Stack – "
            "Interactive Mode (type 'exit' to quit)",
        )
        while True:
            try:
                question: str = self.session.prompt("➡  ")
                if not question.strip():
                    continue
                if question.lower() in {"exit", "quit"}:
                    # Smooth fade-out without terminal flooding
                    run_animation(
                        disintegration_frames(),
                        frame_duration=0.03,
                        repeat=False,
                    )
                    print("Goodbye. ✨")
                    break
                self._handle_query(question)
            except (EOFError, KeyboardInterrupt):
                break

    def run_direct_query(self, question: str) -> None:  # noqa: D401
        """Handle a single direct question."""

        self._handle_query(question)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _handle_query(self, question: str) -> None:
        with FocusController() as focus:
            self.toolbar_msg = "[ ⚙️ EXECUTING ] - Press Ctrl+C to interrupt."
            focus.set_planning()

            def ui_cb(msg: str):  # noqa: D401
                if msg == "planning_complete":
                    pass  # summary handled internally
                elif msg.startswith("tool_start:"):
                    tool = msg.split(":", 1)[1]
                    focus.set_executing(tool)
                elif msg == "synth_start":
                    focus.set_synthesizing()

            state = AgentState(query=question, ui=ui_cb)
            final_state = GRAPH.invoke(state)
            focus.set_answer(Markdown(final_state.get("response", "")))
            self.toolbar_msg = "Type a query or 'help'"


# -------------------------------------------------------------------------
# Argument parsing
# -------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:  # noqa: D401
    parser = argparse.ArgumentParser(
        prog="chimera",
        description="Chimera – Cognitive Orchestration Stack CLI",
    )
    parser.add_argument(
        "-q",
        "--question",
        help="Ask a single question in non-interactive mode and exit",
    )
    return parser.parse_args()


def main() -> None:  # noqa: D401
    args = _parse_args()
    app = ChimeraCLI()
    if args.question:
        app.run_direct_query(args.question)
    else:
        app.start_interactive_mode()


if __name__ == "__main__":  # pragma: no cover
    main()
