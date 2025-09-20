"""Ingest screen for data ingestion operations."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.widgets import (
    Button,
    Static,
    ProgressBar,
    OptionList,
)
from src.tui.widgets.clipboard_input import ClipboardInput
from .base_screen import BaseScreen


class IngestScreen(BaseScreen):
    """The screen for data ingestion operations."""

    def __init__(self) -> None:
        """Initialize the ingest screen."""
        super().__init__()
        self._current_worker: Optional[asyncio.Task] = None
        self._progress_total: int = 0
        self._progress_current: int = 0
        self._progress_message: str = ""
        # Disable auto-refresh for ingest screen
        self.disable_auto_refresh()

    def get_main_content(self) -> ComposeResult:
        """Compose the ingest screen content."""
        # Directory input section
        yield Static("Select directory to ingest:", id="dir-label")
        yield ClipboardInput(
            placeholder="Enter directory path...", id="dir-input"
        )

        # Action buttons
        yield Button(
            "Start Ingestion", id="start-button", variant="primary"
        )

        # Progress section
        yield Static("Progress:", id="progress-label")
        yield ProgressBar(id="progress-bar", show_eta=True)

        # Status display
        yield Static("Status: Ready", id="status-text")

        # File list
        yield Static("Files to process:", id="files-label")
        yield OptionList(id="file-list")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        super().on_mount()
        # Focus on the directory input
        self.query_one("#dir-input", ClipboardInput).focus()

    def on_input_submitted(self, event) -> None:
        """Handle when the user submits a directory path."""
        if event.input.id == "dir-input":
            self._start_ingestion()

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "start-button":
            self._start_ingestion()

    def _start_ingestion(self) -> None:
        """Start the ingestion process."""
        dir_input = self.query_one("#dir-input", ClipboardInput)
        directory = dir_input.value.strip()

        if not directory:
            self._log_message("Error: Please enter a directory path", "error")
            return

        directory_path = Path(directory)
        if not directory_path.exists():
            self._log_message(f"Error: Directory '{directory}' does not exist", "error")
            return

        if not directory_path.is_dir():
            self._log_message(f"Error: '{directory}' is not a directory", "error")
            return

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.done():
            self._current_worker.cancel()

        # Start ingestion worker
        self._current_worker = asyncio.create_task(
            self.run_ingestion(directory_path)
        )

    async def run_ingestion(self, directory: Path) -> None:
        """
        Run the actual ingestion process in a background worker.
        """
        try:
            # Update UI to show we're starting
            self.call_later(
                self._update_status_text,
                "Initializing ingestion...",
            )

            # Get list of files to process
            files = list(directory.rglob("*"))
            files = [f for f in files if f.is_file()]

            if not files:
                self.call_later(
                    self._update_status_text,
                    "No files found to process",
                )
                return

            # Update file list
            self.call_later(
                self._update_file_list,
                files,
            )

            # Initialize progress
            self.call_later(
                self._update_progress,
                0,
                len(files),
                f"Processing {len(files)} files...",
            )

            # Log start
            self.call_later(
                self._log_message,
                f"Starting ingestion of {len(files)} files from {directory}",
                "info",
            )

            # Simulate processing with real progress updates
            for i, file_path in enumerate(files):
                # Check for cancellation
                if self._current_worker and self._current_worker.cancelled():
                    self.call_later(
                        self._update_status_text,
                        "Ingestion cancelled",
                    )
                    return

                # Update progress
                self.call_later(
                    self._update_progress,
                    i + 1,
                    len(files),
                    f"Processing {file_path.name}...",
                )

                # Simulate processing time based on file size
                processing_time = min(0.1, max(0.01, file_path.stat().st_size / 1000000))
                await asyncio.sleep(processing_time)

                # Log progress
                if (i + 1) % 10 == 0 or i == len(files) - 1:
                    self.call_later(
                        self._log_message,
                        f"Processed {i + 1}/{len(files)} files",
                        "info",
                    )

            # Complete
            self.call_later(
                self._update_progress,
                len(files),
                len(files),
                "Ingestion completed!",
            )

            self.call_later(
                self._update_status_text,
                f"Successfully processed {len(files)} files",
            )

            self.call_later(
                self._log_message,
                f"Ingestion completed successfully: {len(files)} files processed",
                "success",
            )

        except asyncio.CancelledError:
            self.call_later(
                self._update_status_text,
                "Ingestion cancelled",
            )
            self.call_later(
                self._log_message,
                "Ingestion was cancelled",
                "warning",
            )
        except Exception as e:
            self.call_later(
                self._update_status_text,
                f"Ingestion failed: {str(e)}",
            )
            self.call_later(
                self._log_message,
                f"Ingestion failed: {str(e)}",
                "error",
            )

    def _update_file_list(self, files: list[Path]) -> None:
        """Update the file list display."""
        file_list = self.query_one("#file-list", OptionList)

        # Clear existing options
        file_list.clear_options()

        # Add files to the list (limit to first 50 for performance)
        for file_path in files[:50]:
            file_list.add_option(file_path.name)

        if len(files) > 50:
            file_list.add_option(f"... and {len(files) - 50} more files")

    def _update_status_text(self, message: str) -> None:
        """Update the status text display."""
        status_text = self.query_one("#status-text", Static)
        status_text.update(f"Status: {message}")

        # Also log to status log for important messages
        if "error" in message.lower() or "failed" in message.lower():
            self._log_message(message, "error")
        elif "success" in message.lower() or "completed" in message.lower():
            self._log_message(message, "success")
        elif "cancelled" in message.lower():
            self._log_message(message, "warning")
        else:
            # Only log info messages to status log if they're significant
            if "processing" in message.lower() or "initializing" in message.lower():
                self._log_message(message, "info")

    def _update_progress(self, current: int, total: Optional[int] = None, message: Optional[str] = None) -> None:
        """Update the progress bar with real-time information."""
        if total is not None:
            self._progress_total = total

        if message is not None:
            self._progress_message = message

        self._progress_current = current

        # Update progress bar
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        if self._progress_total > 0:
            progress = current / self._progress_total
            progress_bar.update(progress=progress)

        # Update status with current progress
        if self._progress_total > 0:
            percentage = int((current / self._progress_total) * 100)
            status_text = self.query_one("#status-text", Static)
            status_text.update(
                f"Status: {self._progress_message} ({current}/{self._progress_total} - {percentage}%)"
            )
        else:
            status_text = self.query_one("#status-text", Static)
            status_text.update(f"Status: {self._progress_message}")

    def _log_status(self, message: str, level: str = "info") -> None:
        """Log a message to the status log."""
        super()._log_message(message, level)