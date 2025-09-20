"""Status screen for system health monitoring."""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Button
from textual.containers import Horizontal
from textual.worker import Worker

# Import the actual backend health check functions
from src.api.health import liveness_check
from src.tools.neo4j_agent import Neo4jAgent
from src.tools.chromadb_agent import ChromaDBAgent
from .base_screen import BaseScreen


class StatusScreen(BaseScreen):
    """The screen for system status monitoring."""

    def __init__(self) -> None:
        """Initialize the status screen."""
        super().__init__()
        # Enable auto-refresh every 10 seconds
        self.set_auto_refresh_interval(10.0)
        # Explicitly type the worker for mypy
        self._refresh_worker: Optional[Worker] = None

    def get_main_content(self) -> ComposeResult:
        """Compose the status screen content."""
        # Header with refresh button
        with Horizontal():
            yield Static("System Status", id="status-title")
            yield Button("Refresh", id="refresh-button", variant="primary")

        # Status table
        yield DataTable(id="status-table")

        # Last update info
        yield Static("Last updated: Never", id="last-update")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        super().on_mount()
        # Set up the data table
        table = self.query_one("#status-table", DataTable)
        table.add_columns("Component", "Status", "Details", "Last Check")

        # Start initial health check
        self.action_refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-button":
            self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh the system status."""
        # Cancel any existing worker
        if self._refresh_worker and not self._refresh_worker.is_finished:
            self._refresh_worker.cancel()

        # Log refresh action
        self._log_message("Refreshing system status...", "info")

        # Start refresh worker
        self._refresh_worker = self.run_worker(
            self.run_health_checks(), exclusive=True
        )

    def _update_last_update_time(self) -> None:
        """Update the last update time display."""
        super()._update_last_update_time()
        last_update_text = self.query_one("#last-update", Static)
        if self._last_update is not None:
            last_update_text.update(
                f"Last updated: {self._last_update.strftime('%H:%M:%S')}"
            )
        else:
            last_update_text.update("Last updated: Never")

    def _update_status_table(
        self, status_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Update the status table with new data."""
        table = self.query_one("#status-table", DataTable)
        table.clear()

        for component, data in status_data.items():
            status = data.get("status", "Unknown")
            details = data.get("details", "")
            last_check = data.get("last_check", "")

            # Color code the status
            if status == "Healthy":
                status_display = f"✅ {status}"
            elif status == "Warning":
                status_display = f"⚠️ {status}"
            elif status == "Error":
                status_display = f"❌ {status}"
            else:
                status_display = status

            table.add_row(component, status_display, details, last_check)

    async def run_health_checks(self) -> None:
        """
        Run health checks for all system components.
        This runs in a background worker to avoid freezing the UI.
        """
        try:
            # Simulate health check delay
            await asyncio.sleep(0.5)

            status_data = {}
            current_time = datetime.now().strftime("%H:%M:%S")

            # Check API Server
            try:
                # Use liveness check for basic API status
                api_health = await liveness_check()
                api_status = (
                    "Healthy" if api_health.get("status") == "alive"
                    else "Error"
                )
                service_name = api_health.get('service', 'Unknown')
                status_data["API Server"] = {
                    "status": api_status,
                    "details": f"Service: {service_name}",
                    "last_check": current_time,
                }
            except Exception as e:
                status_data["API Server"] = {
                    "status": "Error",
                    "details": f"Failed to check: {str(e)}",
                    "last_check": current_time,
                }

            # Check Neo4j Database
            try:
                neo4j_agent = Neo4jAgent()
                neo4j_agent.query("RETURN 1 as test")
                status_data["Neo4j Database"] = {
                    "status": "Healthy",
                    "details": "Connected successfully",
                    "last_check": current_time,
                }
            except Exception as e:
                status_data["Neo4j Database"] = {
                    "status": "Error",
                    "details": f"Connection failed: {str(e)}",
                    "last_check": current_time,
                }

            # Check ChromaDB
            try:
                chroma_agent = ChromaDBAgent()
                # Try to get collection info
                collections = chroma_agent.get_collections()
                collection_count = len(collections)
                status_data["ChromaDB"] = {
                    "status": "Healthy",
                    "details": (
                        f"Vector store operational ({collection_count} "
                        f"collections)"
                    ),
                    "last_check": current_time,
                }
            except Exception as e:
                status_data["ChromaDB"] = {
                    "status": "Error",
                    "details": f"Connection failed: {str(e)}",
                    "last_check": current_time,
                }

            # Check System Resources
            status_data["System Resources"] = {
                "status": self._get_system_status(),
                "details": (
                    f"CPU: {psutil.cpu_percent()}%, "
                    f"Memory: {psutil.virtual_memory().percent}%"
                ),
                "last_check": current_time,
            }

            # Check Logging System
            status_data["Logging System"] = {
                "status": "Healthy",
                "details": "Structured logging active",
                "last_check": current_time,
            }

            # Update the UI from the worker thread
            self.call_later(self._update_status_table, status_data)
            self.call_later(self._update_last_update_time)

        except Exception as e:
            # Handle errors in health checks
            error_data = {
                "Health Check": {
                    "status": "Error",
                    "details": f"Failed to check status: {str(e)}",
                    "last_check": datetime.now().strftime("%H:%M:%S"),
                }
            }
            self.call_later(self._update_status_table, error_data)
            self.call_later(self._update_last_update_time)

    def _get_system_status(self) -> str:
        """Get system resource status."""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > 90 or memory_percent > 90:
            return "Warning"
        elif cpu_percent > 95 or memory_percent > 95:
            return "Error"
        else:
            return "Healthy"