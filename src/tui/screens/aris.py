"""ARIS screen for running research tasks."""

import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, RichLog, Button, Static
from textual.containers import Vertical, Horizontal
from textual.worker import Worker, get_current_worker

# Import the actual ARIS backend
from src.aris.orchestration.graph import run_research_job


class ArisScreen(Screen):
    """The screen for running ARIS research tasks."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the ARIS screen."""
        super().__init__()
        self._current_worker: Optional[Worker] = None

    def compose(self) -> ComposeResult:
        """Compose the ARIS screen."""
        yield Header()
        with Vertical(id="aris-container"):
            # Topic input section
            yield Static("Enter research topic:", id="topic-label")
            yield Input(
                placeholder="Enter your research topic...", id="topic-input"
            )

            # Action buttons
            with Horizontal():
                yield Button(
                    "Start Research", id="start-button", variant="primary"
                )
                yield Button("Clear", id="clear-button")

            # Research log
            yield Static("Research Progress:", id="log-label")
            yield RichLog(id="aris-log", wrap=True, highlight=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Focus on the topic input
        self.query_one("#topic-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user submits a topic."""
        if event.input.id == "topic-input":
            self._start_research()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start-button":
            self._start_research()
        elif event.button.id == "clear-button":
            self._clear_form()

    def _start_research(self) -> None:
        """Start the ARIS research process."""
        topic_input = self.query_one("#topic-input", Input)
        topic = topic_input.value.strip()

        if not topic:
            self._log_message(
                "[red]Error:[/red] Please enter a research topic"
            )
            return

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()

        # Start research worker
        self._current_worker = self.run_worker(
            self.run_aris_research(topic), exclusive=True
        )

    def _clear_form(self) -> None:
        """Clear the form and log."""
        self.query_one("#topic-input", Input).value = ""
        log = self.query_one("#aris-log", RichLog)
        log.clear()

    def _log_message(self, message: str) -> None:
        """Log a message to the ARIS log."""
        log = self.query_one("#aris-log", RichLog)
        log.write(message)

    async def run_aris_research(self, topic: str) -> None:
        """
        Run the actual ARIS research process in a background worker.
        """
        try:
            self.call_later(
                self._log_message,
                f"[bold cyan]🔬 Starting ARIS research for:[/bold cyan] {topic}",
            )

            # Show initial progress
            self.call_later(
                self._log_message,
                "[bold yellow]📋 Initializing research environment...[/bold yellow]",
            )

            # Run the actual ARIS research job
            results = run_research_job(topic)

            # Display results
            if results["status"] == "completed":
                self.call_later(
                    self._log_message,
                    "[bold green]✅ Research completed successfully![/bold green]",
                )
                self.call_later(
                    self._log_message,
                    f"[bold]📊 Results:[/bold]",
                )
                self.call_later(
                    self._log_message,
                    f"  • Job ID: {results['job_id']}",
                )
                self.call_later(
                    self._log_message,
                    f"  • Sources found: {results['sources_found']}",
                )
                self.call_later(
                    self._log_message,
                    f"  • Validated sources: {results['validated_sources']}",
                )
                if results.get("output_path"):
                    self.call_later(
                        self._log_message,
                        f"  • Output saved to: {results['output_path']}",
                    )
            else:
                self.call_later(
                    self._log_message,
                    f"[bold red]❌ Research failed:[/bold red] {results.get('error', 'Unknown error')}",
                )

        except Exception as e:
            self.call_later(
                self._log_message, f"[red]❌ Research failed:[/red] {str(e)}"
            )

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
