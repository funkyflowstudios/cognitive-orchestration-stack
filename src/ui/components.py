from __future__ import annotations

"""Reusable Rich components for Chimera CLI."""

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from .theme import NEWTONS_CRADLE, NOCTURNE_THEME

__all__ = ["render_panel"]


def render_panel(
    content: str | RenderableType,
    title: str | None = None,
) -> Panel:  # noqa: D401
    """Return a themed Rich Panel with optional title."""

    return Panel(
        content,
        title=title,
        style="panel.border",
    )


class WaterfallDisplay:  # noqa: D101
    def __init__(self) -> None:
        self.entries: list[str] = []
        self.console: Console = Console(theme=NOCTURNE_THEME)
        self._spinner: Spinner = NEWTONS_CRADLE
        self._live: Live | None = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def start(self) -> None:  # noqa: D401
        """Begin live display context."""

        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=8,
        )
        self._live.__enter__()

    def stop(self) -> None:  # noqa: D401
        """End live display context."""

        if self._live is not None:
            self._live.__exit__(None, None, None)
            self._live = None

    def update(self, message: str) -> None:  # noqa: D401
        """Append a new step and refresh display."""

        self.entries.append(message)
        if self._live is not None:
            self._live.update(self._render())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _render(self) -> RenderableType:  # noqa: D401
        if not self.entries:
            return self._spinner
        rendered: list[Text] = []
        last_index: int = len(self.entries) - 1
        for idx, msg in enumerate(self.entries):
            prefix = "└─" if idx == last_index else "├─"
            rendered.append(
                Text(f"{prefix} {msg}"),
            )
        return Group(
            *rendered,
            self._spinner,
        )
