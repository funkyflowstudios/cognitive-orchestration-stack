"""Custom input widget with clipboard support."""

import subprocess
import sys
from textual.widgets import Input
from textual.events import Key
from textual.message import Message


class ClipboardInput(Input):
    """Input widget with clipboard support for copy/paste operations."""

    class ClipboardMessage(Message):
        """Message sent when clipboard operation is requested."""

        def __init__(self, operation: str, text: str = "") -> None:
            self.operation = operation  # "copy", "paste", "cut"
            self.text = text
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._clipboard_text = ""

    def _get_system_clipboard(self) -> str:
        """Get text from system clipboard."""
        try:
            if sys.platform == "win32":
                # Windows
                result = subprocess.run(
                    ["powershell", "-command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            elif sys.platform == "darwin":
                # macOS
                result = subprocess.run(
                    ["pbpaste"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            else:
                # Linux
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
        except Exception as e:
            print(f"Error getting system clipboard: {e}")
            return ""

    def _set_system_clipboard(self, text: str) -> None:
        """Set text to system clipboard."""
        try:
            if sys.platform == "win32":
                # Windows
                subprocess.run(
                    ["powershell", "-command", f"Set-Clipboard -Value '{text}'"],
                    check=True
                )
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(
                    ["pbcopy"],
                    input=text,
                    text=True,
                    check=True
                )
            else:
                # Linux
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text,
                    text=True,
                    check=True
                )
        except Exception as e:
            print(f"Error setting system clipboard: {e}")

    async def on_key(self, event: Key) -> None:
        """Handle key events for clipboard operations."""
        try:
            if event.key == "ctrl+c":
                # Copy selected text or all text
                text: str = str(getattr(self, 'value', ''))  # Just use the full value for now
                if text:
                    # Set system clipboard
                    self._set_system_clipboard(text)
                    # Also set internal clipboard
                    self._clipboard_text = text
                    if hasattr(self.app, '_clipboard_text'):
                        self.app._clipboard_text = text
                    print(f"📋 Copied to system clipboard: '{text}'")
                    self.post_message(self.ClipboardMessage("copy", text))
                    event.prevent_default()
            elif event.key == "ctrl+v":
                # Paste from system clipboard first, then internal
                system_text = self._get_system_clipboard()
                internal_text = getattr(self.app, '_clipboard_text', None) or self._clipboard_text

                # Use system clipboard if available, otherwise internal
                clipboard_text = system_text or internal_text

                if clipboard_text:
                    print(f"📋 Pasting from {'system' if system_text else 'internal'} clipboard: '{clipboard_text}'")
                    self._paste_text(clipboard_text)
                    self.post_message(
                        self.ClipboardMessage("paste", clipboard_text)
                    )
                    event.prevent_default()
                else:
                    print("📋 No clipboard text to paste")
            elif event.key == "ctrl+x":
                # Cut selected text or all text
                cut_text: str = str(getattr(self, 'value', ''))  # Just use the full value for now
                if cut_text:
                    # Set system clipboard
                    self._set_system_clipboard(cut_text)
                    # Also set internal clipboard
                    self._clipboard_text = cut_text
                    if hasattr(self.app, '_clipboard_text'):
                        self.app._clipboard_text = cut_text
                    self.value = ""
                    print(f"✂️ Cut to system clipboard: '{cut_text}'")
                    self.post_message(self.ClipboardMessage("cut", cut_text))
                    event.prevent_default()
            elif event.key == "ctrl+a":
                # Select all text
                self.selection = (0, len(self.value))
                print("📋 Selected all text")
                event.prevent_default()
            # Don't call super().on_key() as Input doesn't have this method
            # The parent Input widget will handle other keys automatically
        except Exception as e:
            print(f"Error in ClipboardInput.on_key: {e}")
            # Don't call super().on_key() as it doesn't exist

    def _paste_text(self, text: str) -> None:
        """Paste text at the current cursor position."""
        try:
            # Get current cursor position
            cursor_pos: int = int(getattr(self, 'cursor_position', 0))
            current_value = self.value

            # Insert text at cursor position
            new_value = current_value[:cursor_pos] + text + current_value[cursor_pos:]
            self.value = new_value

            # Move cursor to end of pasted text
            self.cursor_position = cursor_pos + len(text)

        except Exception as e:
            print(f"Error in _paste_text: {e}")
            # Fallback - just append to the end
            self.value = self.value + text

    def set_clipboard_text(self, text: str) -> None:
        """Set clipboard text (called by parent app)."""
        self._clipboard_text = text
