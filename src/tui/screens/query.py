"""Query screen for interacting with the AI agent."""

import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.widgets import Input, RichLog
from textual.worker import Worker

# Import the actual backend orchestration
from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState

from ..widgets.clipboard_input import ClipboardInput
from .base_screen import BaseScreen


class QueryScreen(BaseScreen):
    """The screen for interacting with the AI agent."""

    def __init__(self) -> None:
        """Initialize the query screen."""
        super().__init__()
        self._current_worker: Optional[Worker] = None
        # Disable auto-refresh for query screen
        self.disable_auto_refresh()

    def get_main_content(self) -> ComposeResult:
        """Compose the query screen content."""
        # Use RichLog for styled, scrollable conversation history
        yield RichLog(id="conversation-log", wrap=True, highlight=True, max_lines=100)
        yield ClipboardInput(placeholder="Type your query here...", id="query-input")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        super().on_mount()
        # Focus on the input field
        self.query_one("#query-input", ClipboardInput).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user submits a query."""
        query_text = event.value.strip()
        if not query_text:
            return

        log = self.query_one("#conversation-log", RichLog)

        # Display the user's query
        log.write(f"👤 You: {query_text}")

        # Clear the input for the next query
        event.input.clear()

        # Show a thinking indicator and run the backend call in a worker thread
        log.write("🤔 Agent is thinking...")

        # Cancel any existing worker
        if self._current_worker and not self._current_worker.is_finished:
            self._current_worker.cancel()

        # Start new worker - create a callable that captures the query
        async def worker_func():
            await self.run_backend_query(query_text)

        self._current_worker = self.run_worker(worker_func, exclusive=True)

    async def run_backend_query(self, query: str) -> None:
        """
        Run the actual backend orchestration graph.
        This method runs in a background worker to avoid freezing the UI.
        """
        try:
            # Update UI to show we're starting
            self.call_later(
                self._update_conversation_log,
                "🤖 Initializing AI agent...",
            )

            # Create UI callback for progress updates
            def ui_callback(msg: str) -> None:
                if msg == "planning_complete":
                    self.call_later(
                        self._update_conversation_log,
                        "📋 Planning complete, executing tools...",
                    )
                elif msg.startswith("tool_start:"):
                    tool = msg.split(":", 1)[1]
                    self.call_later(
                        self._update_conversation_log,
                        f"🔧 Executing: {tool}",
                    )
                elif msg == "synth_start":
                    self.call_later(
                        self._update_conversation_log,
                        "🧠 Synthesizing response...",
                    )

            # Create the agent state with UI callback
            state = AgentState(query=query, ui=ui_callback)

            # Run the orchestration graph in a thread executor to prevent blocking
            final_state = await asyncio.get_event_loop().run_in_executor(
                None, GRAPH.invoke, state
            )

            # Get the final response
            response = final_state.get("response", "No response generated")

            # Display the response
            self.call_later(
                self._update_conversation_log,
                f"🤖 Agent: {response}",
            )

        except Exception as e:
            self.call_later(
                self._update_conversation_log,
                f"❌ Error: {str(e)}",
            )

    def _update_conversation_log(self, message: str) -> None:
        """Update the conversation log with a message."""
        log = self.query_one("#conversation-log", RichLog)
        log.write(message)
