from __future__ import annotations

from rich.spinner import SPINNERS, Spinner
from rich.theme import Theme

"""UI theme and custom spinners for Chimera CLI.

This module defines the *Nocturne* colour palette and the custom
*Newton's Cradle* spinner described in the Chimera Design Prospectus.
"""

# ---------------------------------------------------------------------------
# Colour palette – the *Nocturne* scheme
# ---------------------------------------------------------------------------

NOCTURNE_THEME: Theme = Theme(
    {
        "info": "italic cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "panel.border": "#00a8cc",
        "accent": "bold #00a8cc",
    }
)

# ---------------------------------------------------------------------------
# Custom spinner – Newton's Cradle
# ---------------------------------------------------------------------------

_NEWTON_FRAMES: list[str] = [
    "●    ● ● ● ●",
    "  ●   ● ● ● ●",
    "   ●  ● ● ● ●",
    "    ● ● ● ● ●",
    "    ● ● ● ●  ●",
]

SPINNERS["newtons_cradle"] = {"interval": 80, "frames": _NEWTON_FRAMES}
NEWTONS_CRADLE: Spinner = Spinner("newtons_cradle")

# ---------------------------------------------------------------------------
# Zenith Edition Palette – focused cyan accent & greys
# ---------------------------------------------------------------------------

ZENITH_THEME: Theme = Theme(
    {
        # 2025 neon-pastel palette
        "accent": "bold #7ef9ff",  # neon cyan
        "accent.pink": "bold #f0a6ca",
        "accent.yellow": "bold #ffde7d",
        "accent.green": "bold #c3f584",
        "dim": "#555555",
        "focus.border": "#7ef9ff",
        "focus.title": "italic #7ef9ff",
    }
)

# ---------------------------------------------------------------------------
# Breathing Circle spinner – expands/contracts dots
# ---------------------------------------------------------------------------

_BREATH_FRAMES: list[str] = [
    "  ·  ",
    " ··· ",
    "·····",
    " ··· ",
]

SPINNERS["breathing_circle"] = {"interval": 120, "frames": _BREATH_FRAMES}
BREATHING_CIRCLE: Spinner = Spinner("breathing_circle")
