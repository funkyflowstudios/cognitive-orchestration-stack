"""Main menu screen for the Cognitive Orchestration Stack TUI."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, OptionList, Static
from textual.widgets.option_list import Option
from textual.containers import Vertical


class MainMenuScreen(Screen):
    """The main menu screen for the application."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu screen."""
        yield Header()
        # Use a container to center the menu content
        with Vertical(id="main-menu-container"):
            yield Static("Cognitive Orchestration Stack", id="main-title")
            yield Static("Select a feature to continue", id="main-subtitle")
            yield OptionList(
                Option("Query the Agent", id="query"),
                Option("Ingest Data", id="ingest"),
                Option("Run ARIS Research Task", id="aris"),
                Option("System Status", id="status"),
                Option("Quit", id="quit"),
                id="main-options",
            )
        yield Footer()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle menu item selection."""
        if event.option_id == "quit":
            self.app.exit()
        else:
            # Switch to the selected screen
            self.app.push_screen(str(event.option_id))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
