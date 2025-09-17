"""Main application entry point for the Cognitive Orchestration Stack TUI."""

import sys
import logging
from pathlib import Path

from textual.app import App
from textual.logging import TextualHandler

from .screens.main_menu import MainMenuScreen
from .screens.query import QueryScreen
from .screens.ingest import IngestScreen
from .screens.aris import ArisScreen
from .screens.status import StatusScreen
from .widgets.clipboard_input import ClipboardInput


class CosApp(App):
    """The main application for the Cognitive Orchestration Stack TUI."""

    CSS_PATH = "cos.tcss"  # Load the stylesheet

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._clipboard_text = ""

    # Define key bindings for global actions
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "copy", "Copy"),
        ("ctrl+v", "paste", "Paste"),
        ("ctrl+x", "cut", "Cut"),
        ("ctrl+a", "select_all", "Select All"),
    ]

    # Define all the screens the app can display
    SCREENS = {
        "main_menu": MainMenuScreen,
        "query": QueryScreen,
        "ingest": IngestScreen,
        "aris": ArisScreen,
        "status": StatusScreen,
    }

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        # Start at the main menu
        self.push_screen("main_menu")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_copy(self) -> None:
        """Copy text from focused input widget."""
        focused = self.focused
        if isinstance(focused, ClipboardInput):
            text = focused.selected_text or focused.value
            if text:
                self._clipboard_text = text
                focused.set_clipboard_text(text)

    def action_paste(self) -> None:
        """Paste text to focused input widget."""
        focused = self.focused
        if isinstance(focused, ClipboardInput) and self._clipboard_text:
            focused._paste_text(self._clipboard_text)

    def action_cut(self) -> None:
        """Cut text from focused input widget."""
        focused = self.focused
        if isinstance(focused, ClipboardInput):
            text = focused.selected_text or focused.value
            if text:
                self._clipboard_text = text
                focused.value = ""
                focused.set_clipboard_text(text)

    def action_select_all(self) -> None:
        """Select all text in focused input widget."""
        focused = self.focused
        if isinstance(focused, ClipboardInput):
            focused.selection = (0, len(focused.value))

    def on_unmount(self) -> None:
        """Called when the app is unmounted."""
        logging.info("TUI application closed")


def setup_logging() -> None:
    """Set up logging for the TUI application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "tui.log"),
            TextualHandler(),
        ],
    )


def main() -> None:
    """Main entry point for the TUI application."""
    try:
        # Set up logging
        setup_logging()
        logging.info("Starting Cognitive Orchestration Stack TUI")

        # Create and run the app
        app = CosApp()
        app.run()

    except KeyboardInterrupt:
        logging.info("TUI interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"TUI failed to start: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
