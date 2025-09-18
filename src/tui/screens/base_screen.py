"""Base screen class with common functionality for all TUI screens."""

import asyncio
from typing import Optional, Any, Dict
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, RichLog, Static
from textual.containers import Vertical, ScrollableContainer
from textual.worker import Worker


class BaseScreen(Screen):
    """Base screen class with common functionality for scrolling and real-time updates."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "copy", "Copy"),
        ("ctrl+v", "paste", "Paste"),
        ("ctrl+x", "cut", "Cut"),
        ("ctrl+a", "select_all", "Select All"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self) -> None:
        """Initialize the base screen."""
        super().__init__()
        self._refresh_worker: Optional[Worker] = None
        self._last_update: Optional[datetime] = None
        self._auto_refresh_interval: float = 5.0  # 5 seconds default
        self._auto_refresh_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        """Compose the base screen layout."""
        yield Header()
        with Vertical(id="screen-container"):
            # Main content area with scrolling
            with ScrollableContainer(id="main-content"):
                yield from self.get_main_content()

            # Status/log area at the bottom
            yield RichLog(id="status-log", wrap=True, highlight=True, max_lines=100)

        yield Footer()

    def get_main_content(self) -> ComposeResult:
        """Override this method to provide screen-specific content."""
        yield Static("Override get_main_content() in your screen class")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Start auto-refresh if enabled
        if self._auto_refresh_interval > 0:
            self._start_auto_refresh()

    def on_unmount(self) -> None:
        """Called when the screen is unmounted."""
        # Stop auto-refresh
        self._stop_auto_refresh()

    def _start_auto_refresh(self) -> None:
        """Start the auto-refresh task."""
        if self._auto_refresh_task and not self._auto_refresh_task.done():
            self._auto_refresh_task.cancel()

        self._auto_refresh_task = asyncio.create_task(self._auto_refresh_loop())

    def _stop_auto_refresh(self) -> None:
        """Stop the auto-refresh task."""
        if self._auto_refresh_task and not self._auto_refresh_task.done():
            self._auto_refresh_task.cancel()

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop that runs in the background."""
        while True:
            try:
                await asyncio.sleep(self._auto_refresh_interval)
                if not self._refresh_worker or self._refresh_worker.is_finished:
                    self.action_refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log_message(f"Auto-refresh error: {e}", "error")

    def _log_message(self, message: str, level: str = "info") -> None:
        """Log a message to the status log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log = self.query_one("#status-log", RichLog)

        if level == "error":
            log.write(f"[{timestamp}] ❌ {message}")
        elif level == "warning":
            log.write(f"[{timestamp}] ⚠️ {message}")
        elif level == "success":
            log.write(f"[{timestamp}] ✅ {message}")
        else:
            log.write(f"[{timestamp}] ℹ️ {message}")

        # Auto-scroll to bottom
        log.scroll_end()

    def _log_status(self, message: str, level: str = "info") -> None:
        """Log a status message to the status log (for system-level info)."""
        self._log_message(message, level)

    def _update_last_update_time(self) -> None:
        """Update the last update time."""
        self._last_update = datetime.now()

    def action_refresh(self) -> None:
        """Refresh the screen data."""
        # Override in subclasses for specific refresh logic
        self._log_message("Refresh requested", "info")

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_copy(self) -> None:
        """Copy text from focused input widget."""
        self.app.action_copy()

    def action_paste(self) -> None:
        """Paste text to focused input widget."""
        self.app.action_paste()

    def action_cut(self) -> None:
        """Cut text from focused input widget."""
        self.app.action_cut()

    def action_select_all(self) -> None:
        """Select all text in focused input widget."""
        self.app.action_select_all()

    def set_auto_refresh_interval(self, interval: float) -> None:
        """Set the auto-refresh interval in seconds."""
        self._auto_refresh_interval = interval
        if self._auto_refresh_interval > 0:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def disable_auto_refresh(self) -> None:
        """Disable auto-refresh."""
        self.set_auto_refresh_interval(0)

    def enable_auto_refresh(self, interval: float = 5.0) -> None:
        """Enable auto-refresh with specified interval."""
        self.set_auto_refresh_interval(interval)
