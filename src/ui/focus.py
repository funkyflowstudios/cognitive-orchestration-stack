from __future__ import annotations

"""Focus Pane system for Zenith UI."""

# Standard library
import time

from rich.align import Align
from rich.console import (
    Console,
    RenderableType,
)
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from .theme import ZENITH_THEME

console = Console(theme=ZENITH_THEME)


class FocusPane:  # noqa: D101
    def __init__(self) -> None:
        self.content: RenderableType = Text("")
        self.title: str = ""

    def render(self) -> Panel:  # noqa: D401
        return Panel(
            Align.center(self.content, vertical="middle"),
            title=self.title,
            border_style="focus.border",
            width=console.width - 4,
            height=10,
        )


class FocusController:  # noqa: D101
    def __init__(self) -> None:
        self.history: list[str] = []
        self._live = Live(console=console, refresh_per_second=30)
        self._current_renderable: RenderableType = Text("")

    # ---------------- helper -----------------
    def _summarise_current(self, summary: str) -> None:
        if summary:
            self.history.append(f"[ ✔️ ] {summary}")

    # --------------------- Context manager helpers -----------------------

    def __enter__(self):  # noqa: D401
        self._live.__enter__()
        self._live.update(self._current_renderable)
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: D401
        self._live.__exit__(exc_type, exc, tb)

    # --------------------------- API ------------------------------------

    def set_planning(self) -> None:  # noqa: D401
        self._current_renderable = Spinner("dots", text=" [🧠 PLANNING] Thinking...")
        self._live.update(self._current_renderable)

    def set_executing(self, tool: str) -> None:  # noqa: D401
        self._summarise_current("Planning complete")
        # Clean up tool names for better user experience
        display_name = "search" if tool == "vector_search" else tool
        self._current_renderable = Spinner(
            "dots", text=f" [⚙️ EXECUTING] Running: {display_name}"
        )
        self._live.update(self._current_renderable)

    def set_synthesizing(self) -> None:  # noqa: D401
        self._summarise_current("Execution complete")
        self._current_renderable = Spinner(
            "dots", text=" [✍️ SYNTHESIZING] Compiling the answer..."
        )
        self._live.update(self._current_renderable)

    def set_answer(self, markdown: RenderableType) -> None:  # noqa: D401
        self._summarise_current("Synthesizing complete")
        # Create a self-sizing panel that wraps the content perfectly
        answer_panel = Panel(
            markdown,
            title="[✨ ANSWER]",
            border_style="cyan",
            expand=False,  # This tells the panel to fit the content
        )
        self._current_renderable = answer_panel
        self._live.update(self._current_renderable)

    def add_history(self, summary: str) -> None:  # noqa: D401
        self.history.append(summary)

    # ----------------------- Animation helper -----------------------------

    def play_frames(
        self,
        frames: list[str],
        fps: float = 30.0,
    ) -> None:  # noqa: D401
        """Animate a list of pre-rendered frames inside this Live context.

        Each frame replaces the previous one.
        This prevents scroll-back flooding and keeps the UI focused.
        """

        delay = max(1.0 / fps, 0.01)
        for frame in frames:
            self._live.update(frame)
            time.sleep(delay)
