from __future__ import annotations

"""Frame-by-frame console animation utilities."""

import math
import random
import shutil
import socket
import sys
from datetime import datetime
from time import sleep
from typing import List

from rich.console import Console

# Force terminal clears even when Rich is unsure (e.g., in some Windows shells)
console = Console(force_terminal=True)


__all__ = [
    "run_animation",
    "play_cognitive_bloom_animation",
]


_CLEAR_CMD = "cls" if sys.platform.startswith("win") else "clear"


def _clear() -> None:
    # Use rich Console clear for better cross-platform support and to
    # integrate smoothly with other rich-rendered components.
    # Clear the entire screen *and* reposition the cursor to (0,0) so that
    # subsequent frames overwrite the previous one instead of scrolling.
    console.clear(home=True)


def run_animation(
    frames: List[str],
    frame_duration: float = 0.08,
    repeat: bool = False,
) -> None:  # noqa: D401
    """Render frames inside a Live context to avoid terminal flooding.

    Each frame overwrites the previous one in-place. If *repeat* is True, the
    sequence loops indefinitely until interrupted.
    """

    try:
        # Use full-screen mode so each frame replaces the previous without
        # injecting additional lines and causing scroll-back flooding.
        with console.screen() as screen:
            screen.update(frames[0])
            while True:
                for frame in frames:
                    screen.update(frame)
                    sleep(frame_duration)
                if not repeat:
                    break
    except KeyboardInterrupt:  # noqa: WPS329
        pass


class _Particle:  # noqa: D401
    """Light-weight particle used in the Cognitive Bloom animation."""

    def __init__(self, x: float, y: float, char: str) -> None:
        self.x: float = x
        self.y: float = y
        # Random initial outward velocity
        angle: float = random.uniform(0.0, 2.0 * math.pi)
        speed: float = random.uniform(0.5, 1.5)
        self.vx: float = math.cos(angle) * speed
        self.vy: float = math.sin(angle) * speed
        self.char: str = char
        self.life: int = random.randint(20, 40)

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def update(self, cx: float, cy: float) -> None:  # noqa: D401
        """Update position / velocity with weak centre-orbit gravity."""

        # Attraction towards orbit of radius r0 around centre
        dx: float = self.x - cx
        dy: float = self.y - cy
        r: float = math.hypot(dx, dy) + 1e-6
        desired_r: float = 8.0  # target orbital radius
        # Radial force
        force_mag: float = (desired_r - r) * 0.02
        self.vx += (dx / r) * force_mag
        self.vy += (dy / r) * force_mag

        # Dampen velocity slightly
        self.vx *= 0.98
        self.vy *= 0.98

        # Integrate
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def is_alive(self) -> bool:  # noqa: D401
        return self.life > 0


# -------------------------------------------------------------------------
# Cognitive Bloom animation
# -------------------------------------------------------------------------


def play_cognitive_bloom_animation() -> None:  # noqa: D401
    """Generate and play the *Cognitive Bloom* intro (≈1.5 s)."""

    # Terminal size
    cols, rows = shutil.get_terminal_size((80, 24))
    cx: float = cols / 2.0
    cy: float = rows / 2.0

    # Seed chars from hostname + timestamp
    seed_chars: str = socket.gethostname() + datetime.now().strftime("%H%M%S")
    char_iter = iter(seed_chars * 5)  # repeat to ensure enough chars

    particles: list[_Particle] = []
    frames: list[str] = []

    total_frames: int = 90  # ~60 fps * 1.5 s
    for frame_idx in range(total_frames):
        # Emit burst each frame (few particles)
        for _ in range(4):
            try:
                ch: str = next(char_iter)
            except StopIteration:
                ch = random.choice(seed_chars)
            particles.append(_Particle(cx, cy, ch))

        # Update particles
        for p in list(particles):  # noqa: WPS422 (list copy intentional)
            p.update(cx, cy)
            if not p.is_alive:
                particles.remove(p)

        # Prepare blank grid
        grid: list[list[str]] = [[" " for _ in range(cols)] for _ in range(rows)]
        for p in particles:
            x_i = int(round(p.x))
            y_i = int(round(p.y))
            if 0 <= x_i < cols and 0 <= y_i < rows:
                grid[y_i][x_i] = p.char

        frame_str: str = "\n".join("".join(row) for row in grid)
        frames.append(frame_str)

    # Glyph collapse (brain+gear pulse)
    glyph: str = "🧠⚙️"
    for _ in range(10):  # pulse frames
        grid = [[" " for _ in range(cols)] for _ in range(rows)]
        gx = int(cx - len(glyph) / 2)
        gy = int(cy)
        for idx, ch in enumerate(glyph):
            if 0 <= gx + idx < cols and 0 <= gy < rows:
                grid[gy][gx + idx] = ch
        frame_str = "\n".join("".join(row) for row in grid)
        frames.append(frame_str)

    # Final blank frame
    frames.append("\n" * rows)

    run_animation(frames, frame_duration=0.02, repeat=False)


def play_graceful_exit_animation() -> None:  # noqa: D401
    """Animate fade-out and panel shrink before application exit."""

    cols, rows = shutil.get_terminal_size((80, 24))

    # ----------------------------- Fade phase -----------------------------
    grey_chars = ["▓", "▒", "░", " "]
    frame_strings: list[str] = []
    for step in range(15):
        density = step / 15.0
        rows_chars: list[str] = []
        for _ in range(rows):
            line = "".join(
                random.choice(grey_chars[: int(density * 4) or 1]) for _ in range(cols)
            )
            rows_chars.append(line)
        frame_strings.append("\n".join(rows_chars))

    # ----------------------------- Shrink phase ---------------------------
    left, right = 0, cols - 1
    top, bottom = 0, rows - 1
    while left < right and top < bottom:
        grid_matrix: list[list[str]] = [[" " for _ in range(cols)] for _ in range(rows)]
        for x in range(left, right + 1):
            if 0 <= top < rows:
                grid_matrix[top][x] = "░"
            if 0 <= bottom < rows:
                grid_matrix[bottom][x] = "░"
        for y in range(top, bottom + 1):
            if 0 <= y < rows and 0 <= left < cols:
                grid_matrix[y][left] = "░"
            if 0 <= y < rows and 0 <= right < cols:
                grid_matrix[y][right] = "░"
        frame_strings.append(
            "\n".join("".join(r) for r in grid_matrix),
        )
        left += 2
        right -= 2
        top += 1
        bottom -= 1

    # final blank
    frame_strings.append("\n" * rows)

    run_animation(frame_strings, frame_duration=0.03)

    # Ensure terminal is cleared after animation
    _clear()


# -------------------------------------------------------------------------
# Card-flip transition
# -------------------------------------------------------------------------

_SHADES: list[str] = ["▓", "▒", "░", " "]


def card_flip_frames(
    old: str,
    new: str,
    width: int,
    height: int,
    steps: int = 15,
) -> list[str]:  # noqa: D401
    """Generate frames that flip from *old* to *new* content."""

    frames: list[str] = []
    for step in range(steps):
        progress = step / steps
        # Determine column slice to reveal new content
        slice_cols = int(progress * width)
        frame_lines: list[str] = []
        for y in range(height):
            if y < len(new.splitlines()):
                new_line = new.splitlines()[y]
            else:
                new_line = " " * width
            # Build mixed line
            shade_idx = min(int(progress * 4), 3)
            shade = _SHADES[shade_idx]
            filler = shade * (width - slice_cols)
            line = new_line[:slice_cols] + filler
            frame_lines.append(line)
        frames.append("\n".join(frame_lines))
    frames.append(new)  # final frame fully new
    return frames


# -------------------------------------------------------------------------
# Horizon Overture intro – thin cyan line then prompt drop
# -------------------------------------------------------------------------


def overture_frames() -> list[str]:  # noqa: D401
    """Return frames for the Zenith horizon intro (~0.7 s)."""

    cols, rows = shutil.get_terminal_size((80, 24))
    center_y = rows // 2

    frames: list[str] = []
    step = max(cols // 20, 1)
    for length in range(0, cols + 1, step):
        line = " " * length + "─" * (cols - length)
        grid = [" " * cols for _ in range(rows)]
        grid[center_y] = line
        frames.append("\n".join(grid))

    # hold a few frames
    frames.extend([frames[-1]] * 2)

    # prompt drop
    grid = [" " * cols for _ in range(rows)]
    grid[center_y] = "─" * cols
    for y in range(center_y, center_y + 3):
        grid_copy = grid.copy()
        if 0 <= y < rows:
            prompt_line = list(grid_copy[y])
            mid = cols // 2
            prompt_line[mid] = ">"
            grid_copy[y] = "".join(prompt_line)
        frames.append("\n".join(grid_copy))

    # final cleared prompt line
    final = [" " * cols for _ in range(rows)]
    final[center_y + 2] = "> "
    frames.append("\n".join(final))

    return frames


def disintegration_frames() -> list[str]:  # noqa: D401
    """Return frames for fade-out then clear (~0.3 s)."""

    cols, rows = shutil.get_terminal_size((80, 24))
    steps = 10
    frames: list[str] = []
    for idx in range(steps):
        ratio = idx / steps
        shade = "." if ratio > 0.7 else ("▒" if ratio > 0.4 else "▓")
        frames.append("\n".join([shade * cols for _ in range(rows)]))

    frames.append("\n" * rows)
    return frames


# Backward-compat wrappers -----------------------------------------------


def play_overture() -> None:  # pragma: no cover
    run_animation(overture_frames(), frame_duration=0.025)


def play_disintegration_exit() -> None:  # pragma: no cover
    run_animation(disintegration_frames(), frame_duration=0.03)
