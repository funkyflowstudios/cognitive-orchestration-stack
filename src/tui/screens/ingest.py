"""Ingest screen for data ingestion operations."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    ProgressBar,
    OptionList,
)
from src.tui.widgets.clipboard_input import ClipboardInput
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal
from textual.worker import Worker, get_current_worker

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification
try:
    from scripts.ingest_data import ingest  # noqa: E402
except ImportError:
    # Fallback: import from the correct path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ingest_data", project_root / "scripts" / "ingest_data.py"
    )
    if spec is not None and spec.loader is not None:
        ingest_data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ingest_data)
        ingest = ingest_data.ingest
    else:
        raise ImportError("Could not load ingest_data module")


class IngestScreen(Screen):
    """The screen for data ingestion operations."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "cancel_ingestion", "Cancel"),
        ("ctrl+v", "paste", "Paste"),
        ("ctrl+x", "cut", "Cut"),
        ("ctrl+a", "select_all", "Select All"),
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
            yield ClipboardInput(
                placeholder="Enter file path...", id="file-input"
            )

            # Action buttons
            with Horizontal():
                yield Button(
                    "Start Ingestion", id="start-button", variant="primary"
                )
                yield Button("Clear", id="clear-button")
                yield Button(
                    "Cancel",
                    id="cancel-button",
                    variant="error",
                    disabled=True
                )

            # Progress section
            with Vertical(id="progress-container"):
                yield Static("Progress:", id="progress-label")
                yield ProgressBar(id="progress-bar")
                yield Static("Ready to ingest data", id="status-text")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Initialize progress bar to be static
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.progress = 0
        progress_bar.total = 100  # Set a total to make it static

        # Focus on the source selection
        self.query_one("#source-selection", OptionList).focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle source selection."""
        self._selected_source = str(event.option_id)
        file_input = self.query_one("#file-input", ClipboardInput)

        # Update placeholder and provide helpful examples
        if event.option_id == "file":
            file_input.placeholder = (
                "Enter file path (e.g., data/AI Agent Ecosystems_ Research "
                "Synthesis.docx)..."
            )
            # Pre-populate with a common file path
            file_input.value = (
                "data/AI Agent Ecosystems_ Research Synthesis.docx"
            )
        elif event.option_id == "directory":
            file_input.placeholder = (
                "Enter directory path (e.g., data/)... "
                "WARNING: Large directories may take 10-30 minutes!"
            )
            file_input.value = "data/"
        elif event.option_id == "url":
            file_input.placeholder = "Enter URL..."
            file_input.value = ""

        # Focus on the input field
        file_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start-button":
            self._start_ingestion()
        elif event.button.id == "clear-button":
            self._clear_form()
        elif event.button.id == "cancel-button":
            self._cancel_ingestion()

    def _start_ingestion(self) -> None:
        """Start the ingestion process."""
        file_input = self.query_one("#file-input", ClipboardInput)
        path_text = file_input.value.strip()

        if not path_text:
            self._update_status("Please enter a path", "error")
            return

        # Validate path based on source type BEFORE starting worker
        if self._selected_source in ["file", "directory"]:
            # Handle both relative and absolute paths
            if not Path(path_text).is_absolute():
                # If relative path, make it relative to project root
                project_root = Path(__file__).parent.parent.parent.parent
                path = project_root / path_text
            else:
                path = Path(path_text)

            if not path.exists():
                self._update_status(
                    f"Path does not exist: {path_text}\nFull path: {path}",
                    "error"
                )
                return
            if self._selected_source == "file" and not path.is_file():
                self._update_status(
                    f"Path is not a file: {path_text}\nFull path: {path}",
                    "error"
                )
                return
            if self._selected_source == "directory" and not path.is_dir():
                self._update_status(
                    f"Path is not a directory: {path_text}\nFull path: {path}",
                    "error"
                )
                return

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()

        # Only start worker if validation passed
        # Update button states
        start_button = self.query_one("#start-button", Button)
        cancel_button = self.query_one("#cancel-button", Button)
        start_button.disabled = True
        cancel_button.disabled = False

        # Start the ingestion process in a background worker
        self._current_worker = self.run_worker(
            self.run_ingestion_process(path_text, self._selected_source),
            exclusive=True,
            name="ingestion"
        )

    def _clear_form(self) -> None:
        """Clear the form."""
        self.query_one("#file-input", ClipboardInput).value = ""
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.progress = 0
        progress_bar.total = 100  # Keep it static
        self._update_status("Ready to ingest data", "info")

        # Reset button states
        start_button = self.query_one("#start-button", Button)
        cancel_button = self.query_one("#cancel-button", Button)
        start_button.disabled = False
        cancel_button.disabled = True

    def _cancel_ingestion(self) -> None:
        """Cancel the current ingestion process."""
        # Cancel any running workers
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()
            print("Cancelled ingestion worker")

        # Also cancel any workers with the ingestion name
        for worker in self.app.workers:
            if worker.name == "ingestion" and not worker.is_finished:
                worker.cancel()
                print(f"Cancelled worker: {worker.name}")

        self._update_status("Ingestion cancelled", "error")
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.progress = 0
        progress_bar.total = 100  # Keep it static

        # Reset button states
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        """Reset button states to default."""
        start_button = self.query_one("#start-button", Button)
        cancel_button = self.query_one("#cancel-button", Button)
        start_button.disabled = False
        cancel_button.disabled = True

    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update the status text."""
        status_text = self.query_one("#status-text", Static)
        if status_type == "error":
            status_text.update(f"❌ Error: {message}")
        elif status_type == "success":
            status_text.update(f"✅ Success: {message}")
        elif status_type == "info":
            status_text.update(message)
        else:
            status_text.update(message)

    def _safe_ingest(self, path: Path) -> dict:
        """Safely run ingestion with proper error handling."""
        try:
            # Run the actual ingestion
            print(f"Starting ingestion of: {path}")
            ingest(path)
            print(f"Completed ingestion of: {path}")
            return {"success": True, "message": "Data ingested successfully"}
        except Exception as e:
            error_msg = str(e)
            print(f"Ingestion error: {error_msg}")
            if ("Connection refused" in error_msg or
                    "ConnectionError" in error_msg):
                return {
                    "success": False,
                    "message": (
                        "Required services are not running. "
                        "Please start them first."
                    )
                }
            else:
                return {
                    "success": False,
                    "message": f"Ingestion failed: {error_msg}"
                }

    async def run_ingestion_process(self, path: str, source_type: str) -> None:
        """
        Run the actual ingestion process in a background worker.
        """
        try:
            self.call_later(
                self._update_status, "Starting ingestion...", "info"
            )

            progress_bar = self.query_one("#progress-bar", ProgressBar)

            # Update progress to show we're starting
            self.call_later(setattr, progress_bar, "progress", 10)
            self.call_later(
                self._update_status, "Starting ingestion...", "info"
            )

            # Path validation already done in _start_ingestion()
            # No need to validate again here

            # Update progress
            self.call_later(setattr, progress_bar, "progress", 30)
            self.call_later(
                self._update_status, "Running ingestion pipeline...", "info"
            )

            # Check for cancellation before starting the actual work
            if get_current_worker().is_cancelled:
                print("Worker cancelled before starting ingestion")
                return

            # Run the actual ingestion logic
            if source_type in ["file", "directory"]:
                # For file/directory ingestion, use the safe ingest function
                try:
                    # Update progress
                    self.call_later(setattr, progress_bar, "progress", 30)
                    self.call_later(
                        self._update_status, "Processing files...", "info"
                    )

                    # Check for cancellation before running ingestion
                    if get_current_worker().is_cancelled:
                        print("Worker cancelled before running ingestion")
                        return

                    # Calculate timeout based on data size
                    # For directories, estimate 1 minute per 10MB of data
                    if source_type == "directory":
                        # Count files in directory to estimate size
                        try:
                            path_obj = Path(path)
                            file_count = len([
                                f for f in path_obj.rglob("*") if f.is_file()
                            ])
                            # Estimate 30 sec per file, min 5 min, max 30 min
                            timeout_seconds = max(300, min(1800, file_count * 30))
                        except Exception:
                            timeout_seconds = 600  # 10 min default
                    else:
                        timeout_seconds = 300  # 5 minutes for single files

                    self.call_later(
                        self._update_status,
                        f"Processing... (timeout: {timeout_seconds//60} min)",
                        "info"
                    )

                    # Run ingestion with calculated timeout
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self._safe_ingest, Path(path)
                        ),
                        timeout=timeout_seconds
                    )

                    # Check for cancellation after ingestion
                    if get_current_worker().is_cancelled:
                        print("Worker cancelled after ingestion")
                        return

                    if result["success"]:
                        self.call_later(setattr, progress_bar, "progress", 100)
                        self.call_later(
                            self._update_status,
                            result["message"],
                            "success"
                        )
                        # Reset button states on success
                        self.call_later(self._reset_buttons)
                        # Reset progress bar to static after completion
                        self.call_later(setattr, progress_bar, "total", 100)
                    else:
                        self.call_later(
                            self._update_status,
                            result["message"],
                            "error"
                        )
                        # Reset button states on error
                        self.call_later(self._reset_buttons)
                        # Reset progress bar to static after error
                        self.call_later(setattr, progress_bar, "total", 100)
                        return
                except asyncio.TimeoutError:
                    timeout_msg = (
                        f"Ingestion timed out after {timeout_seconds//60} min. "
                        "Try processing fewer files or individual files instead."
                    )
                    self.call_later(
                        self._update_status,
                        timeout_msg,
                        "error"
                    )
                    self.call_later(self._reset_buttons)
                    # Reset progress bar to static after timeout
                    self.call_later(setattr, progress_bar, "total", 100)
                    return
                except Exception as e:
                    self.call_later(
                        self._update_status,
                        f"Ingestion failed: {str(e)}",
                        "error"
                    )
                    self.call_later(self._reset_buttons)
                    # Reset progress bar to static after error
                    self.call_later(setattr, progress_bar, "total", 100)
                    return
            else:
                # For URL ingestion, we'd need a different approach
                self.call_later(
                    self._update_status,
                    "URL ingestion not yet implemented",
                    "error"
                )
                return

            # Check for cancellation after work
            if get_current_worker().is_cancelled:
                return

            # Update progress to completion
            self.call_later(setattr, progress_bar, "progress", 100)
            self.call_later(
                self._update_status,
                f"Successfully ingested data from {source_type}: {path}",
                "success",
            )

        except Exception as e:
            self.call_later(
                self._update_status, f"Ingestion failed: {str(e)}", "error"
            )
            self.call_later(self._reset_buttons)

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

    def action_cancel_ingestion(self) -> None:
        """Cancel the current ingestion process."""
        self._cancel_ingestion()
