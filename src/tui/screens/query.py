"""Query screen for interacting with the AI agent."""

import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical
from textual.worker import Worker

# Import the actual backend orchestration
from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState


class QueryScreen(Screen):
    """The screen for interacting with the AI agent."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the query screen."""
        super().__init__()
        self._current_worker: Optional[Worker] = None

    def compose(self) -> ComposeResult:
        """Compose the query screen."""
        yield Header()
        with Vertical(id="query-container"):
            # Use RichLog for styled, scrollable conversation history
            yield RichLog(id="conversation-log", wrap=True, highlight=True)
            yield Input(
                placeholder="Type your query here...", id="query-input"
            )
        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Focus on the input field
        self.query_one("#query-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user submits a query."""
        query_text = event.value.strip()
        if not query_text:
            return

        log = self.query_one("#conversation-log", RichLog)

        # Display the user's query
        log.write(f"[bold cyan]You:[/bold cyan] {query_text}")

        # Clear the input for the next query
        event.input.clear()

        # Show a thinking indicator and run the backend call in a worker thread
        log.write("[bold yellow]Agent is thinking...[/bold yellow]")

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()

        # Start new worker
        self._current_worker = self.run_worker(
            self.run_backend_query(query_text), exclusive=True
        )

    async def run_backend_query(self, query: str) -> None:
        """
        Run the actual backend orchestration graph.
        This method runs in a background worker to avoid freezing the UI.
        """
        try:
            # Update UI to show we're starting
            self.call_later(
                self._update_conversation_log,
                "[bold yellow]🤖 Initializing AI agent...[/bold yellow]",
            )

            # Create UI callback for progress updates
            def ui_callback(msg: str) -> None:
                if msg == "planning_complete":
                    self.call_later(
                        self._update_conversation_log,
                        "[bold blue]📋 Planning complete, executing tools...[/bold blue]",
                    )
                elif msg.startswith("tool_start:"):
                    tool = msg.split(":", 1)[1]
                    self.call_later(
                        self._update_conversation_log,
                        f"[bold cyan]🔧 Executing: {tool}[/bold cyan]",
                    )
                elif msg == "synth_start":
                    self.call_later(
                        self._update_conversation_log,
                        "[bold magenta]🧠 Synthesizing response...[/bold magenta]",
                    )

            # Create the agent state with UI callback
            state = AgentState(query=query, ui=ui_callback)

            # Run the orchestration graph
            final_state = GRAPH.invoke(state)

            # Get the final response
            response = final_state.get("response", "No response generated")

            # Display the response
            self.call_later(
                self._update_conversation_log,
                f"[bold green]Agent:[/bold green] {response}",
            )

        except asyncio.CancelledError:
            # Handle cancellation gracefully
            self.call_later(
                self._update_conversation_log,
                "[yellow]Query cancelled[/yellow]",
            )
        except Exception as e:
            self.call_later(
                self._update_conversation_log,
                f"[bold red]Error:[/bold red] {str(e)}",
            )

    def _update_conversation_log(self, message: str) -> None:
        """Update the conversation log with a message."""
        log = self.query_one("#conversation-log", RichLog)
        log.write(message)

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
