"""Ingest screen for data ingestion operations."""

import asyncio
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Input,
    Button,
    Static,
    ProgressBar,
    OptionList,
)
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal
from textual.worker import Worker, get_current_worker

# Import your backend ingestion function here
# from src.scripts.ingest_data import run_ingestion


class IngestScreen(Screen):
    """The screen for data ingestion operations."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the ingest screen."""
        super().__init__()
        self._current_worker: Optional[Worker] = None
        self._selected_source: str = "file"

    def compose(self) -> ComposeResult:
        """Compose the ingest screen."""
        yield Header()
        with Vertical(id="ingest-container"):
            # Source selection
            yield Static("Select data source:", id="source-label")
            yield OptionList(
                Option("File", id="file"),
                Option("Directory", id="directory"),
                Option("URL", id="url"),
                id="source-selection",
            )

            # File path input
            yield Input(placeholder="Enter file path...", id="file-input")

            # Action buttons
            with Horizontal():
                yield Button(
                    "Start Ingestion", id="start-button", variant="primary"
                )
                yield Button("Clear", id="clear-button")

            # Progress section
            with Vertical(id="progress-container"):
                yield Static("Progress:", id="progress-label")
                yield ProgressBar(id="progress-bar")
                yield Static("Ready to ingest data", id="status-text")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Focus on the source selection
        self.query_one("#source-selection", OptionList).focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle source selection."""
        self._selected_source = str(event.option_id)
        file_input = self.query_one("#file-input", Input)

        # Update placeholder based on selection
        if event.option_id == "file":
            file_input.placeholder = "Enter file path..."
        elif event.option_id == "directory":
            file_input.placeholder = "Enter directory path..."
        elif event.option_id == "url":
            file_input.placeholder = "Enter URL..."

        # Focus on the input field
        file_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start-button":
            self._start_ingestion()
        elif event.button.id == "clear-button":
            self._clear_form()

    def _start_ingestion(self) -> None:
        """Start the ingestion process."""
        file_input = self.query_one("#file-input", Input)
        path_text = file_input.value.strip()

        if not path_text:
            self._update_status("Please enter a path", "error")
            return

        # Validate path based on source type
        if self._selected_source in ["file", "directory"]:
            path = Path(path_text)
            if not path.exists():
                self._update_status(
                    f"Path does not exist: {path_text}", "error"
                )
                return
            if self._selected_source == "file" and not path.is_file():
                self._update_status(
                    f"Path is not a file: {path_text}", "error"
                )
                return
            if self._selected_source == "directory" and not path.is_dir():
                self._update_status(
                    f"Path is not a directory: {path_text}", "error"
                )
                return

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()

        # Start ingestion worker
        self._current_worker = self.run_worker(
            self.run_ingestion_process(path_text, self._selected_source),
            exclusive=True,
        )

    def _clear_form(self) -> None:
        """Clear the form."""
        self.query_one("#file-input", Input).value = ""
        self.query_one("#progress-bar", ProgressBar).progress = 0
        self._update_status("Ready to ingest data", "info")

    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update the status text."""
        status_text = self.query_one("#status-text", Static)
        if status_type == "error":
            status_text.update(f"[red]Error:[/red] {message}")
        elif status_type == "success":
            status_text.update(f"[green]Success:[/green] {message}")
        elif status_type == "info":
            status_text.update(message)
        else:
            status_text.update(message)

    async def run_ingestion_process(self, path: str, source_type: str) -> None:
        """
        Run the actual ingestion process in a background worker.
        """
        try:
            self.call_later(
                self._update_status, "Starting ingestion...", "info"
            )

            # Simulate ingestion progress
            progress_bar = self.query_one("#progress-bar", ProgressBar)

            for i in range(101):
                if get_current_worker().is_cancelled:
                    return

                self.call_later(progress_bar.update, progress=i)
                self.call_later(
                    self._update_status, f"Processing... {i}%", "info"
                )

                # Simulate work
                await asyncio.sleep(0.05)

            # This is where you would call your actual ingestion logic
            # await run_ingestion(path, source_type)

            self.call_later(
                self._update_status,
                f"Successfully ingested data from {source_type}: {path}",
                "success",
            )

        except Exception as e:
            self.call_later(
                self._update_status, f"Ingestion failed: {str(e)}", "error"
            )

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
